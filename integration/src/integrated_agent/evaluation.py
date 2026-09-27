"""Scenario evaluation and reproducible output export."""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Any

from .contracts import validate, write_json, write_jsonl
from .orchestrator import Execution, Orchestrator


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [row["task_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("scenario task_id values must be unique")
    for row in rows:
        validate("task-request", row)
    return rows


def evaluate(execution: Execution, elapsed_ms: float) -> dict[str, Any]:
    expected = execution.request["expected_output"]
    expected_agents = expected.get("selected_agents", [])
    actual_agents = execution.route.get("selected_agents", []) if execution.route else []
    route_match = bool(execution.route) and execution.route.get("selected_model") == expected.get("selected_model")
    agent_match = actual_agents == expected_agents
    status_match = execution.result["status"] == expected.get("status", "success")
    security_expected = expected.get("security_gate")
    security_actual = execution.result.get("output", {}).get("security_gate")
    security_match = security_expected is None or security_actual == security_expected
    quality_values = [item.quality_score for item in execution.outcomes if item.quality_score is not None]
    safety = [violation for item in execution.outcomes for violation in item.safety_violations]
    success = route_match and agent_match and status_match and security_match
    record = {
        "task_id": execution.request["task_id"],
        "implementation_id": "ukkhnn:integrated-agent:replay-v1",
        "task_success": success,
        "quality_score": statistics.fmean(quality_values) if quality_values else (1.0 if success else 0.0),
        "tool_accuracy": 1.0 if route_match and agent_match and security_match else 0.0,
        "latency_ms": elapsed_ms,
        "usage": {"router_calls": 1 if execution.route else 0, "adapter_calls": len(execution.outcomes)},
        "cost": execution.result.get("output", {}).get("estimated_cost_usd"),
        "safety_violations": safety,
        "failure_type": None if success else _failure_type(route_match, agent_match, status_match, security_match),
        "metadata": {
            "expected_status": expected.get("status", "success"),
            "actual_status": execution.result["status"],
            "route_match": route_match,
            "agent_match": agent_match,
            "security_match": security_match,
        },
    }
    validate("evaluation-record", record)
    return record


def run_suite(scenarios: list[dict[str, Any]], output: Path, orchestrator: Orchestrator | None = None) -> dict[str, Any]:
    runner = orchestrator or Orchestrator()
    executions: list[Execution] = []
    records: list[dict[str, Any]] = []
    for scenario in scenarios:
        started = time.perf_counter()
        execution = runner.execute(scenario)
        elapsed_ms = (time.perf_counter() - started) * 1000
        executions.append(execution)
        records.append(evaluate(execution, elapsed_ms))

    requests = [item.request for item in executions]
    results = [item.result for item in executions]
    traces = [trace for item in executions for trace in item.traces]
    passed = sum(record["task_success"] for record in records)
    coding = [item for item in executions if "coding" in (item.route or {}).get("selected_agents", [])]
    coding_gated = all(
        any(trace["tool_name"] == "09-cybersecurity-agent" for trace in item.traces)
        or item.result["status"] == "blocked" and any("security" in text for text in item.result["limitations"])
        for item in coding
    )
    summary = {
        "run_id": "replay-v1",
        "mode": "replay",
        "scenarios": len(records),
        "passed": passed,
        "success_rate": passed / len(records) if records else 0.0,
        "common_contract_records": len(requests) + len(results) + len(traces) + len(records),
        "route_matches": sum(record["metadata"]["route_match"] for record in records),
        "agent_matches": sum(record["metadata"]["agent_match"] for record in records),
        "expected_status_matches": sum(record["metadata"]["expected_status"] == record["metadata"]["actual_status"] for record in records),
        "coding_security_gate_enforced": coding_gated,
        "fail_closed_cases": sum(item.result["status"] in {"failed", "blocked"} for item in executions),
        "safety_violation_count": sum(len(record["safety_violations"]) for record in records),
        "limitations": [
            "Specialist outputs are replayed from committed validated summaries; only routing executes during replay.",
            "Integrated quality is a projection and does not measure cross-agent answer composition.",
            "The multimodal baseline remains below its 0.8 success target and is preserved as partial.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "task-requests.jsonl", requests)
    write_jsonl(output / "agent-results.jsonl", results)
    write_jsonl(output / "tool-traces.jsonl", traces)
    write_jsonl(output / "evaluation-records.jsonl", records)
    write_json(output / "summary.json", summary)
    return summary


def _failure_type(route: bool, agent: bool, status: bool, security: bool) -> str:
    if not route:
        return "route_mismatch"
    if not agent:
        return "agent_mismatch"
    if not security:
        return "security_gate_mismatch"
    if not status:
        return "status_mismatch"
    return "unknown"
