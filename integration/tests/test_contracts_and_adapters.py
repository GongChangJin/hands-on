from __future__ import annotations

import json

import pytest
from jsonschema import ValidationError

from integrated_agent.adapters import ARTIFACTS, AdapterError, ArtifactAdapter, FaultAdapter
from integrated_agent.contracts import validate
from integrated_agent.evaluation import load_scenarios
from integrated_agent.paths import INTEGRATION_DIR


def test_all_scenarios_use_the_common_task_contract() -> None:
    scenarios = load_scenarios(INTEGRATION_DIR / "scenarios/replay-v1.jsonl")
    assert len(scenarios) >= 7
    assert len({item["task_id"] for item in scenarios}) == len(scenarios)


def test_common_contract_rejects_unknown_fields() -> None:
    scenario = json.loads((INTEGRATION_DIR / "scenarios/replay-v1.jsonl").read_text().splitlines()[0])
    scenario["unknown"] = True
    with pytest.raises(ValidationError):
        validate("task-request", scenario)


@pytest.mark.parametrize("name", sorted(ARTIFACTS))
def test_every_adapter_artifact_is_readable(name: str) -> None:
    outcome = ArtifactAdapter().run(name)
    assert outcome.name
    assert outcome.source
    assert outcome.latency_ms >= 0


@pytest.mark.parametrize("fault", ["rag_timeout", "security_timeout"])
def test_fault_adapter_raises_timeout(fault: str) -> None:
    with pytest.raises(AdapterError, match="timeout"):
        FaultAdapter().raise_for(fault, fault.removesuffix("_timeout"))
