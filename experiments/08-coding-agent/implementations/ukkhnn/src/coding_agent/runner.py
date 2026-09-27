"""Fixed subprocess adapters for pytest and Ruff."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from .models import CommandResult

OUTPUT_LIMIT = 8000


def _safe_environment(workspace: Path) -> dict[str, str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(workspace / "src"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "LC_ALL": "C.UTF-8",
    }
    return environment


def run_fixed(
    name: str,
    arguments: list[str],
    workspace: Path,
    timeout_seconds: int,
) -> CommandResult:
    command = [sys.executable, "-m", *arguments]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=workspace,
            env=_safe_environment(workspace),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return CommandResult(
            name=name,
            command=command[1:],
            returncode=completed.returncode,
            stdout=completed.stdout[-OUTPUT_LIMIT:],
            stderr=completed.stderr[-OUTPUT_LIMIT:],
            duration_ms=(time.perf_counter() - started) * 1000,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
        return CommandResult(
            name=name,
            command=command[1:],
            returncode=124,
            stdout=stdout[-OUTPUT_LIMIT:],
            stderr=stderr[-OUTPUT_LIMIT:],
            duration_ms=(time.perf_counter() - started) * 1000,
            timed_out=True,
        )


def run_tests(
    workspace: Path,
    timeout_seconds: int,
    *,
    include_regression: bool = True,
    include_judge: bool = False,
) -> CommandResult:
    paths = ["tests/public"]
    if include_regression and (workspace / "tests" / "regression").exists():
        paths.append("tests/regression")
    if include_judge and (workspace / "tests" / "judge").exists():
        paths.append("tests/judge")
    return run_fixed("pytest", ["pytest", "-q", *paths], workspace, timeout_seconds)


def run_single_regression(workspace: Path, relative_path: str, timeout_seconds: int) -> CommandResult:
    return run_fixed("pytest-regression-original", ["pytest", "-q", relative_path], workspace, timeout_seconds)


def run_lint(workspace: Path, timeout_seconds: int) -> CommandResult:
    return run_fixed("ruff", ["ruff", "check", "src", "tests"], workspace, timeout_seconds)
