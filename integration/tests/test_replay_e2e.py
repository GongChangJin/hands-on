from __future__ import annotations

import json

from integrated_agent.evaluation import load_scenarios, run_suite
from integrated_agent.paths import INTEGRATION_DIR


def test_replay_suite_routes_and_fails_closed(tmp_path) -> None:
    scenarios = load_scenarios(INTEGRATION_DIR / "scenarios/replay-v1.jsonl")
    summary = run_suite(scenarios, tmp_path)
    assert summary["passed"] == summary["scenarios"] == 10
    assert summary["route_matches"] == 10
    assert summary["agent_matches"] == 10
    assert summary["coding_security_gate_enforced"] is True
    assert summary["fail_closed_cases"] == 3
    for filename in (
        "task-requests.jsonl",
        "agent-results.jsonl",
        "tool-traces.jsonl",
        "evaluation-records.jsonl",
        "summary.json",
    ):
        assert (tmp_path / filename).is_file()
    records = [json.loads(line) for line in (tmp_path / "evaluation-records.jsonl").read_text().splitlines()]
    assert all(item["task_success"] for item in records)
