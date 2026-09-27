"""Subprocess and artifact adapters for the independently packaged projects."""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import implementation


class AdapterError(RuntimeError):
    """A downstream implementation could not return a usable result."""


class AdapterTimeout(AdapterError):
    """A downstream implementation exceeded its bounded execution time."""


@dataclass(frozen=True)
class AdapterOutcome:
    name: str
    status: str
    output: dict[str, Any]
    source: str
    claim: str
    latency_ms: float
    quality_score: float | None
    tool_accuracy: float | None
    cost: float | None
    safety_violations: list[str]
    mode: str = "replay"


def _run_json(command: list[str], cwd: Path, timeout_seconds: float) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd / "src")
    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise AdapterTimeout(f"command timed out after {timeout_seconds:g}s") from error
    latency_ms = (time.perf_counter() - started) * 1000
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip() or f"exit={process.returncode}"
        raise AdapterError(detail[-1000:])
    try:
        return json.loads(process.stdout), latency_ms
    except json.JSONDecodeError as error:
        raise AdapterError("downstream returned invalid JSON") from error


class RouterAdapter:
    name = "06-llm-router"

    def __init__(self, timeout_seconds: float = 10) -> None:
        self.root = implementation("06", "llm-router")
        self.timeout_seconds = timeout_seconds

    def route(self, task: dict[str, Any]) -> tuple[dict[str, Any], float]:
        payload = task["input"] if isinstance(task["input"], dict) else {"prompt": str(task["input"])}
        command = [
            str(self.root / ".venv" / "bin" / "python"),
            "-m",
            "llm_router.cli",
            "route",
            str(payload.get("prompt", task["task_id"])),
            "--data-scope",
            str(payload.get("data_scope", "public")),
            "--complexity",
            str(payload.get("complexity", "moderate")),
            "--risk",
            str(payload.get("risk", "low")),
        ]
        for modality in payload.get("modalities", ["text"]):
            if modality != "text":
                command.extend(["--modality", modality])
        for capability in payload.get("required_capabilities", []):
            command.extend(["--capability", capability])
        if payload.get("needs_current_info"):
            command.append("--current")
        if not payload.get("signals_complete", True):
            command.append("--infer")
        decision, latency_ms = _run_json(command, self.root, self.timeout_seconds)
        required = {
            "selected_model",
            "selected_agents",
            "reason",
            "strategy",
            "blocked",
        }
        if not required <= decision.keys():
            raise AdapterError("router output is missing required fields")
        decision["task_id"] = task["task_id"]
        return decision, latency_ms


@dataclass(frozen=True)
class ArtifactSpec:
    project: str
    path: Path
    success_key: str
    quality_key: str | None
    latency_key: str
    cost_key: str | None
    safety_key: str | None
    success_threshold: float = 0.8


ARTIFACTS: dict[str, ArtifactSpec] = {
    "small": ArtifactSpec(
        "02-local-llm",
        implementation("02", "local-llm") / "results/qwen2.5-3b-q4_k_m/summary.json",
        "success_rate", "success_rate", "latency_p50_ms", "estimated_cost_usd", "safety_violation_count",
    ),
    "local": ArtifactSpec(
        "02-local-llm",
        implementation("02", "local-llm") / "results/qwen2.5-7b-q4_k_m/summary.json",
        "success_rate", "success_rate", "latency_p50_ms", "estimated_cost_usd", "safety_violation_count",
    ),
    "balanced": ArtifactSpec(
        "02-local-llm",
        implementation("02", "local-llm") / "results/solar-pro4-api/summary.json",
        "success_rate", "success_rate", "latency_p50_ms", "estimated_cost_usd", "safety_violation_count",
    ),
    "frontier": ArtifactSpec(
        "02-local-llm",
        implementation("02", "local-llm") / "results/solar-pro4-api/summary.json",
        "success_rate", "success_rate", "latency_p50_ms", "estimated_cost_usd", "safety_violation_count",
    ),
    "rag": ArtifactSpec(
        "03-agentic-rag",
        implementation("03", "agentic-rag") / "results/upstage-solar-pro4-full-19-v2/summary.json",
        "success_rate", "success_rate", "p50_latency_ms", "estimated_cost_usd", "safety_violations",
    ),
    "vision": ArtifactSpec(
        "04-multimodal-agent",
        implementation("04", "multimodal-agent") / "results/deepseek-adaptive-context-v2/summary.json",
        "success_rate", "success_rate", "latency_p50_ms", "calculated_cost_usd", "safety_violation_count",
    ),
    "research": ArtifactSpec(
        "05-research-agent",
        implementation("05", "research-agent") / "results/remediation-v2/semantic-scholar-only-evaluation/summary.json",
        "task_success", "evidence_coverage", "latency_p50_ms", "calculated_cost_usd", "safety_violations",
    ),
    "browser": ArtifactSpec(
        "07-computer-use-agent",
        implementation("07", "computer-use-agent") / "results/playwright-local-site/adaptive-screenshot/summary.json",
        "success_rate", "success_rate", "latency_p50_ms", None, "safety_violation_count",
    ),
    "coding": ArtifactSpec(
        "08-coding-agent",
        implementation("08", "coding-agent") / "results/reference-replay-v1/summary.json",
        "success_rate", "success_rate", "latency_p50_ms", "cost_usd", "safety_violation_count",
    ),
    "security": ArtifactSpec(
        "09-cybersecurity-agent",
        implementation("09", "cybersecurity-agent") / "results/deterministic-container-v2/summary.json",
        "fixture.decision", "fixture.remediation_rate", "fixture.metadata.isolation_probes_passed", None, None,
    ),
}


def _nested(payload: dict[str, Any], dotted: str | None, default: Any = None) -> Any:
    if dotted is None:
        return default
    value: Any = payload
    for key in dotted.split("."):
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


class ArtifactAdapter:
    def run(self, name: str) -> AdapterOutcome:
        spec = ARTIFACTS[name]
        try:
            summary = json.loads(spec.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AdapterError(f"cannot read {spec.path}") from error
        raw_success = _nested(summary, spec.success_key)
        if name == "security":
            succeeded = raw_success == "approve"
            latency_ms = 0.0
        else:
            succeeded = bool(raw_success) if isinstance(raw_success, bool) else float(raw_success) >= spec.success_threshold
            latency_ms = float(_nested(summary, spec.latency_key, 0.0))
        safety_value = _nested(summary, spec.safety_key, [])
        if isinstance(safety_value, int):
            violations = [f"reported_safety_violations={safety_value}"] if safety_value else []
        else:
            violations = [str(item) for item in (safety_value or [])]
        quality = _nested(summary, spec.quality_key)
        cost = _nested(summary, spec.cost_key)
        return AdapterOutcome(
            name=spec.project,
            status="success" if succeeded and not violations else "partial",
            output={"summary": summary, "artifact": str(spec.path.relative_to(spec.path.parents[5]))},
            source=spec.project,
            claim=f"validated artifact reports {spec.success_key}={raw_success}",
            latency_ms=latency_ms,
            quality_score=float(quality) if isinstance(quality, (int, float)) else None,
            tool_accuracy=None,
            cost=float(cost) if isinstance(cost, (int, float)) else None,
            safety_violations=violations,
        )


class FaultAdapter:
    """Deterministic boundary faults used by the integration evaluation suite."""

    def raise_for(self, fault: str | None, stage: str) -> None:
        if fault != f"{stage}_timeout" and fault != f"{stage}_invalid_schema":
            return
        if fault.endswith("timeout"):
            raise AdapterTimeout(f"injected {stage} timeout")
        raise AdapterError(f"injected {stage} invalid schema")
