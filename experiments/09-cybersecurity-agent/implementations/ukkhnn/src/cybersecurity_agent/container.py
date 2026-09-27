"""Bounded Docker adapter for deterministic security tools."""

from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from pathlib import Path

from .io import shared_dir
from .models import SecurityPolicy, ToolExecution


class ContainerPolicyError(RuntimeError):
    pass


def make_world_readable(root: Path) -> None:
    root.chmod(0o755)
    for path in root.rglob("*"):
        path.chmod(0o755 if path.is_dir() else 0o644)


class ContainerRunner:
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy

    def ensure_image(self) -> dict:
        inspect = subprocess.run(
            ["docker", "image", "inspect", self.policy.container_image, "--format", "{{json .}}"],
            capture_output=True,
            text=True,
        )
        if inspect.returncode != 0:
            command = [
                "docker", "build",
                "--build-arg", f"SEMGREP_VERSION={self.policy.semgrep_version}",
                "--build-arg", f"BANDIT_VERSION={self.policy.bandit_version}",
                "--build-arg", f"PYTEST_VERSION={self.policy.pytest_version}",
                "-f", str(shared_dir() / "container" / "Dockerfile"),
                "-t", self.policy.container_image,
                str(shared_dir()),
            ]
            subprocess.run(command, check=True)
            inspect = subprocess.run(
                ["docker", "image", "inspect", self.policy.container_image, "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                check=True,
            )
        payload = json.loads(inspect.stdout)
        return {"id": payload["Id"], "created": payload["Created"], "architecture": payload["Architecture"]}

    def _base_command(self, workspace: Path, container_name: str | None = None) -> list[str]:
        make_world_readable(workspace)
        command = [
            "docker", "run", "--rm",
            "--network", self.policy.network,
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--pids-limit", str(self.policy.pids_limit),
            "--memory", f"{self.policy.memory_mb}m",
            "--cpus", str(self.policy.cpus),
            "--user", "65532:65532",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=128m",
            "-e", "HOME=/tmp",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e", "SEMGREP_SEND_METRICS=off",
            "-e", "SEMGREP_ENABLE_VERSION_CHECK=0",
            "-e", "SERVICE_API_KEY=runtime-service-key",
            "-e", "BACKUP_PASSWORD=runtime-backup-password",
            "-v", f"{workspace.resolve()}:/workspace:ro",
        ]
        if container_name:
            command.extend(["--name", container_name])
        if self.policy.read_only_root:
            command.append("--read-only")
        command.append(self.policy.container_image)
        return command

    @staticmethod
    def _timeout_output(value: str | bytes | None) -> str:
        if isinstance(value, bytes):
            return value.decode(errors="replace")
        return value or ""

    @staticmethod
    def _remove_container(container_name: str) -> str:
        try:
            cleanup = subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return f"container_cleanup_failed:{type(error).__name__}"
        if cleanup.returncode == 0:
            return "container_cleanup:removed"
        detail = cleanup.stderr.strip().replace("\n", " ")[-200:]
        return f"container_cleanup_unconfirmed:{detail or cleanup.returncode}"

    def run(self, workspace: Path, tool: str, args: list[str], acceptable_codes: set[int]) -> ToolExecution:
        if tool not in self.policy.allowed_tools:
            raise ContainerPolicyError(f"tool_not_allowed:{tool}")
        container_name = f"gcj-security-{uuid.uuid4().hex}"
        command = [*self._base_command(workspace, container_name), tool, *args]
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.policy.timeout_seconds,
                env={key: value for key, value in os.environ.items() if key not in {"UPSTAGE_API_KEY", "OPENAI_API_KEY"}},
            )
            timed_out = False
        except subprocess.TimeoutExpired as error:
            cleanup_status = self._remove_container(container_name)
            stderr = self._timeout_output(error.stderr)
            return ToolExecution(
                tool=tool,
                exit_code=124,
                duration_ms=(time.perf_counter() - started) * 1000,
                stdout=self._timeout_output(error.stdout),
                stderr=f"{stderr}\n{cleanup_status}".strip(),
                timed_out=True,
                container_args=command[2:command.index(self.policy.container_image)],
            )
        result = ToolExecution(
            tool=tool,
            exit_code=completed.returncode,
            duration_ms=(time.perf_counter() - started) * 1000,
            stdout=completed.stdout,
            stderr=completed.stderr,
            timed_out=timed_out,
            container_args=command[2:command.index(self.policy.container_image)],
        )
        if completed.returncode not in acceptable_codes:
            raise RuntimeError(f"{tool} failed with {completed.returncode}: {completed.stderr[-500:]}")
        return result

    def tool_versions(self, workspace: Path) -> dict[str, str]:
        versions = {}
        for tool, args in (("semgrep", ["--version"]), ("bandit", ["--version"]), ("pytest", ["--version"])):
            result = self.run(workspace, tool, args, {0})
            versions[tool] = (result.stdout or result.stderr).strip().splitlines()[0]
        return versions

    def isolation_probes(self, workspace: Path) -> list[dict]:
        probes = [
            ("network_none", ["python", "-c", "import socket; socket.create_connection(('example.invalid', 80), 1)"]),
            ("read_only_root", ["python", "-c", "from pathlib import Path; Path('/probe').write_text('x')"]),
            ("host_not_mounted", ["python", "-c", "from pathlib import Path; raise SystemExit(0 if not Path('/host').exists() else 1)"]),
        ]
        rows = []
        for name, payload in probes:
            command = [*self._base_command(workspace), *payload]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=10)
            expected = completed.returncode != 0 if name != "host_not_mounted" else completed.returncode == 0
            rows.append({
                "scenario": name,
                "passed": expected,
                "exit_code": completed.returncode,
                "stderr_tail": completed.stderr.strip()[-240:],
            })
        return rows
