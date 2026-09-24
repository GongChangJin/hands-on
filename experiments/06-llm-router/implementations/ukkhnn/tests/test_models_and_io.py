import json

import pytest
from pydantic import ValidationError

from llm_router.io import load_dataset, load_metrics, load_policy
from llm_router.models import LogicalModel, TaskRequest


def test_shared_dataset_has_40_unique_valid_cases():
    cases = load_dataset()

    assert len(cases) == 40
    assert len({case.task_id for case in cases}) == 40
    assert sum(not case.signals_complete for case in cases) == 4


def test_metrics_cover_every_logical_model_and_agent():
    metrics = load_metrics()

    assert set(metrics.logical_models) == set(LogicalModel)
    assert metrics.logical_models[LogicalModel.LOCAL].actual_model == "qwen2.5:latest"
    assert metrics.agents["browser"].quality_score is None


def test_policy_has_safe_thresholds():
    policy = load_policy()

    assert policy.confidence_threshold == 0.7
    assert policy.circuit_breaker_failures >= 2


def test_task_request_rejects_unknown_fields():
    payload = {
        "task_id": "x",
        "prompt": "hello",
        "unexpected": "not allowed",
    }

    with pytest.raises(ValidationError):
        TaskRequest.model_validate(payload)


def test_dataset_is_line_delimited_json():
    from llm_router.io import shared_dir

    lines = (shared_dir() / "task-requests.jsonl").read_text(encoding="utf-8").splitlines()
    assert all(isinstance(json.loads(line), dict) for line in lines)
