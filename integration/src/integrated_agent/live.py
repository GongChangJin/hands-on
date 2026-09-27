"""Small live-smoke run across executable project boundaries."""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adapters import AdapterError, AdapterTimeout, RouterAdapter
from .contracts import validate, write_json, write_jsonl
from .evaluation import load_scenarios
from .paths import INTEGRATION_DIR, implementation


@dataclass(frozen=True)
class CommandResult:
    payload: dict[str, Any]
    latency_ms: float


def _keychain_secret(name: str) -> str | None:
    result = subprocess.run(
        ["security", "find-generic-password", "-s", name, "-a", os.environ.get("USER", ""), "-w"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def _command(
    command: list[str],
    cwd: Path,
    timeout_seconds: float,
    *,
    env_additions: dict[str, str] | None = None,
    summary_path: Path | None = None,
) -> CommandResult:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd / "src")
    env.update(env_additions or {})
    started = time.perf_counter()
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
        raise AdapterTimeout(f"live command timed out after {timeout_seconds:g}s") from error
    elapsed = (time.perf_counter() - started) * 1000
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip() or f"exit={process.returncode}"
        raise AdapterError(detail[-1500:])
    if summary_path is not None:
        try:
            return CommandResult(json.loads(summary_path.read_text(encoding="utf-8")), elapsed)
        except (OSError, json.JSONDecodeError) as error:
            raise AdapterError(f"missing or invalid summary: {summary_path}") from error
    try:
        return CommandResult(json.loads(process.stdout), elapsed)
    except json.JSONDecodeError as error:
        raise AdapterError("live command returned invalid JSON") from error


def run_live_smoke(output: Path) -> dict[str, Any]:
    """Run one bounded flow per executable agent class and normalize the records."""
    scenarios = {item["task_id"]: item for item in load_scenarios(INTEGRATION_DIR / "scenarios/replay-v1.jsonl")}
    selected = [
        scenarios["integration-rag-001"],
        scenarios["integration-research-001"],
        scenarios["integration-browser-001"],
        scenarios["integration-coding-001"],
    ]
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    router = RouterAdapter()
    results: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    upstage_key = _keychain_secret("UPSTAGE_API_KEY")
    paid_cost = 0.0
    route_matches = 0

    for request in selected:
        task_id = request["task_id"]
        expected = request["expected_output"]
        started = time.perf_counter()
        route: dict[str, Any] | None = None
        error: str | None = None
        stage_status = "failed"
        security_gate = "not_required"
        stage_payload: dict[str, Any] = {}
        stage_name = expected["selected_agents"][0]
        try:
            route, route_ms = router.route(request)
            traces.append(_trace(task_id, "06-llm-router", route_ms, f"model={route['selected_model']} agent={stage_name}"))
            if route["selected_model"] != expected["selected_model"] or route["selected_agents"] != expected["selected_agents"]:
                raise AdapterError("live route did not match the expected policy")
            route_matches += 1
            if stage_name == "rag":
                if not upstage_key:
                    raise AdapterError("UPSTAGE_API_KEY is unavailable in Keychain")
                root = implementation("03", "agentic-rag")
                command = [
                    str(root / ".venv/bin/python"), "-m", "agentic_rag.cli", "ask",
                    "Team 요금제의 월 기본요금과 포함 사용자는 몇 명인가?",
                    "--task-id", task_id, "--provider", "upstage", "--no-phoenix",
                ]
                run = _command(command, root, 180, env_additions={"UPSTAGE_API_KEY": upstage_key})
                stage_status = str(run.payload.get("status", "failed"))
                paid_cost += float(run.payload.get("metadata", {}).get("estimated_cost_usd", 0.0))
                write_json(raw / "rag" / "result.json", run.payload)
            elif stage_name == "research":
                root = implementation("05", "research-agent")
                destination = raw / "research"
                run = _command(
                    [str(root / ".venv/bin/python"), "-m", "research_agent.cli", "run-all", "--output", str(destination), "--offline", "--no-phoenix"],
                    root,
                    180,
                )
                stage_status = "success" if run.payload.get("success") else "failed"
            elif stage_name == "browser":
                root = implementation("07", "computer-use-agent")
                destination = raw / "browser"
                run = _command(
                    [str(root / ".venv/bin/python"), "-m", "computer_use_agent.cli", "--output", str(destination)],
                    root,
                    240,
                )
                recommended = run.payload.get("conditions", {}).get(run.payload.get("recommended_condition"), {})
                stage_status = "success" if recommended.get("success_rate", 0) >= 0.8 and run.payload.get("safety", {}).get("pass_rate") == 1.0 else "failed"
            else:
                root = implementation("08", "coding-agent")
                destination = raw / "coding"
                run = _command(
                    [str(root / ".venv/bin/python"), "-m", "coding_agent.cli", "--task", "coding-tags-001", "--provider", "replay", "--output", str(destination)],
                    root,
                    180,
                )
                stage_status = "success" if run.payload.get("success_rate", 0) >= 0.8 else "failed"
            stage_payload = run.payload
            traces.append(_trace(task_id, f"{stage_name}-live", run.latency_ms, "completed"))

            if stage_status != "success":
                raise AdapterError(f"{stage_name} returned semantic status={stage_status}")

            if stage_name == "coding":
                security_gate = "block"
                security_root = implementation("09", "cybersecurity-agent")
                security_output = raw / "security"
                security_run = _command(
                    [str(security_root / ".venv/bin/python"), "-m", "cybersecurity_agent.cli", "--output", str(security_output)],
                    security_root,
                    300,
                    summary_path=security_output / "summary.json",
                )
                traces.append(_trace(task_id, "09-cybersecurity-agent", security_run.latency_ms, security_run.payload["fixture"]["decision"]))
                if security_run.payload["fixture"]["decision"] != "approve":
                    raise AdapterError("security gate blocked the coding result")
                security_gate = "approve"
        except AdapterError as caught:
            error = str(caught)
            traces.append(_trace(task_id, f"{stage_name}-live", 0, "failed", error))

        elapsed = (time.perf_counter() - started) * 1000
        status = "success" if error is None else ("blocked" if stage_name == "coding" else stage_status)
        result = {
            "task_id": task_id,
            "status": status,
            "output": {"route": route, "stage": stage_name, "summary": stage_payload, "security_gate": security_gate},
            "evidence": [{"source": f"{stage_name}-live", "location": "agent-results.jsonl", "claim": "bounded live smoke completed"}] if error is None else [],
            "actions": [trace["tool_name"] for trace in traces if trace["task_id"] == task_id],
            "limitations": ([error] if error else []) + (["Research smoke uses the deterministic offline corpus."] if stage_name == "research" else []),
            "metadata": {"mode": "live-smoke", "provider": "upstage" if stage_name == "rag" else "local"},
        }
        validate("agent-result", result)
        results.append(result)
        record = {
            "task_id": task_id,
            "implementation_id": "ukkhnn:integrated-agent:live-smoke-v1",
            "task_success": error is None,
            "quality_score": 1.0 if error is None else 0.0,
            "tool_accuracy": 1.0 if error is None else 0.0,
            "latency_ms": elapsed,
            "usage": {"route_calls": 1, "live_stage_calls": 2 if stage_name == "coding" else 1},
            "cost": float(stage_payload.get("metadata", {}).get("estimated_cost_usd", 0.0)) if stage_name == "rag" and stage_payload else 0.0,
            "safety_violations": [],
            "failure_type": None if error is None else "live_smoke_failure",
            "metadata": {"stage": stage_name, "security_gate": security_gate},
        }
        validate("evaluation-record", record)
        evaluations.append(record)

    passed = sum(item["task_success"] for item in evaluations)
    summary = {
        "run_id": "live-smoke-v1",
        "mode": "live-smoke",
        "scenarios": len(evaluations),
        "passed": passed,
        "success_rate": passed / len(evaluations),
        "route_matches": route_matches,
        "coding_security_gate_enforced": any(item["metadata"].get("security_gate") == "approve" for item in evaluations),
        "paid_provider_calls": ["03-agentic-rag/upstage"],
        "estimated_paid_cost_usd": paid_cost,
        "offline_stages": ["05-research-agent"],
        "limitations": [
            "The RAG request is live and paid; Research uses its deterministic offline corpus because no DeepSeek key is registered.",
            "Coding uses its validated replay patch provider while tests and the container security gate execute live.",
            "This smoke run checks connectivity and boundaries, not statistical quality.",
        ],
    }
    write_jsonl(output / "task-requests.jsonl", selected)
    write_jsonl(output / "agent-results.jsonl", results)
    write_jsonl(output / "tool-traces.jsonl", traces)
    write_jsonl(output / "evaluation-records.jsonl", evaluations)
    write_json(output / "summary.json", summary)
    return summary


def _trace(task_id: str, tool: str, duration_ms: float, result: str, error: str | None = None) -> dict[str, Any]:
    trace = {
        "task_id": task_id,
        "tool_name": tool,
        "input_summary": "bounded integration live-smoke",
        "result_summary": result,
        "duration_ms": max(0.0, duration_ms),
        "error": error,
        "metadata": {"mode": "live-smoke"},
    }
    validate("tool-trace", trace)
    return trace
