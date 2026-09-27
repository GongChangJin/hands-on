from __future__ import annotations

import copy

import pytest

from integrated_agent.adapters import AdapterOutcome, ArtifactAdapter
from integrated_agent.evaluation import load_scenarios
from integrated_agent.orchestrator import Orchestrator
from integrated_agent.paths import INTEGRATION_DIR


class StubRouter:
    def route(self, task):
        expected = task["expected_output"]
        return {
            "task_id": task["task_id"],
            "selected_model": expected["selected_model"],
            "selected_agents": expected["selected_agents"],
            "reason": ["test route"],
            "strategy": "rule",
            "blocked": False,
        }, 1.0


class CountingArtifacts(ArtifactAdapter):
    def __init__(self):
        self.calls = []

    def run(self, name):
        self.calls.append(name)
        return AdapterOutcome(
            name=f"project-{name}",
            status="success",
            output={"summary": {"fixture": {"decision": "approve"}}, "artifact": f"{name}/summary.json"},
            source=name,
            claim="test",
            latency_ms=1.0,
            quality_score=1.0,
            tool_accuracy=1.0,
            cost=0.0,
            safety_violations=[],
        )


@pytest.fixture
def scenarios():
    return {item["task_id"]: item for item in load_scenarios(INTEGRATION_DIR / "scenarios/replay-v1.jsonl")}


def test_coding_always_calls_security_gate(scenarios) -> None:
    artifacts = CountingArtifacts()
    execution = Orchestrator(router=StubRouter(), artifacts=artifacts).execute(scenarios["integration-coding-001"])
    assert execution.result["status"] == "success"
    assert artifacts.calls == ["coding", "security"]
    assert execution.result["output"]["security_gate"] == "approve"


@pytest.mark.parametrize("task_id", ["integration-security-timeout-001", "integration-security-schema-001"])
def test_security_boundary_faults_fail_closed(scenarios, task_id) -> None:
    execution = Orchestrator(router=StubRouter(), artifacts=CountingArtifacts()).execute(scenarios[task_id])
    assert execution.result["status"] == "blocked"
    assert execution.result["output"]["security_gate"] == "block"
    assert any("security_gate_failed" in item for item in execution.result["limitations"])


def test_local_only_rejects_external_specialist(scenarios) -> None:
    request = copy.deepcopy(scenarios["integration-local-001"])
    request["expected_output"]["selected_agents"] = ["rag"]
    execution = Orchestrator(router=StubRouter(), artifacts=CountingArtifacts()).execute(request)
    assert execution.result["status"] == "blocked"
    assert "local_only_external_adapter" in execution.result["limitations"][0]
