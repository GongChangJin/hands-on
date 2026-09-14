import argparse
import asyncio
import inspect
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import agent_eval.experiment as experiment_module
from agent_eval.dataset import default_dataset_path, load_examples
from agent_eval.experiment import (
    _answer_contains_required_text,
    _handoff_route_correct,
    _required_tools_used,
    _safe_tool_use,
    _tool_accuracy,
    _tool_execution_success,
)


def test_golden_dataset_has_twenty_learning_cases() -> None:
    examples = load_examples(default_dataset_path())

    assert len(examples) == 20
    assert all("input" in example and "output" in example for example in examples)
    assert {example["metadata"]["category"] for example in examples} == {
        "calculator",
        "project",
        "combined",
    }


def test_answer_contains_required_text() -> None:
    assert _answer_contains_required_text(
        {"answer": "결과는 42이며 상태는 ACTIVE입니다."},
        {"required_texts": ["42", "active"]},
    )


def test_required_tools_used() -> None:
    assert _required_tools_used(
        {"tools": ["calculator", "lookup_project_status"]},
        {"required_tools": ["calculator"]},
    )


def test_tool_accuracy_penalizes_unexpected_tools() -> None:
    assert _tool_accuracy(
        {"tools": ["calculator", "lookup_project_status"]},
        {"required_tools": ["calculator"]},
    ) == 0.5
    assert not _safe_tool_use(
        {"tools": ["calculator", "lookup_project_status"]},
        {"required_tools": ["calculator"]},
    )
    assert _tool_accuracy(
        {"tools": ["calculator", "calculator"]},
        {"required_tools": ["calculator"]},
    ) == 0.5


def test_handoff_route() -> None:
    assert _handoff_route_correct(
        {"agent": "Combined Specialist"},
        {"expected_agent": "Combined Specialist"},
    )


def test_tool_execution_error_is_preserved() -> None:
    assert not _tool_execution_success(
        {"tool_traces": [{"error": "tool failed"}]}
    )


def test_evaluators_treat_missing_task_output_as_failure() -> None:
    expected = {"required_texts": ["42"], "required_tools": ["calculator"]}

    assert not _answer_contains_required_text(None, expected)
    assert not _required_tools_used(None, expected)


def test_experiment_uses_async_phoenix_client(monkeypatch) -> None:
    fake_client = SimpleNamespace(
        datasets=SimpleNamespace(get_dataset=AsyncMock(return_value="dataset")),
        experiments=SimpleNamespace(run_experiment=AsyncMock(return_value=None)),
    )
    fake_api_client = SimpleNamespace(
        models=SimpleNamespace(list=AsyncMock(return_value=[])),
        close=AsyncMock(),
    )
    fake_tracer = SimpleNamespace(shutdown=lambda: None)
    args = argparse.Namespace(
        provider="deepseek",
        model=None,
        architecture="single",
        dataset="dataset",
        repetitions=1,
        llm_judge=False,
        report_dir=Path("reports/test"),
        phoenix_url="http://localhost:6006",
        phoenix_endpoint="http://localhost:6006/v1/traces",
    )

    monkeypatch.setattr(experiment_module, "AsyncClient", lambda **_: fake_client)
    monkeypatch.setattr(experiment_module, "build_client", lambda *_: fake_api_client)
    monkeypatch.setattr(experiment_module, "build_model", lambda *_, **__: object())
    monkeypatch.setattr(experiment_module, "build_agent", lambda *_: object())
    monkeypatch.setattr(experiment_module, "configure_phoenix", lambda **_: fake_tracer)
    monkeypatch.setattr(experiment_module, "build_records", lambda *_, **__: [])
    monkeypatch.setattr(
        experiment_module,
        "summarize_records",
        lambda *_, **__: {"experiment_id": "experiment"},
    )
    monkeypatch.setattr(experiment_module, "export_report", lambda *_, **__: Path("report.md"))
    fake_client.experiments.run_experiment.return_value = {"experiment_id": "experiment"}

    asyncio.run(experiment_module.run(args))

    fake_client.datasets.get_dataset.assert_awaited_once_with(dataset="dataset")
    fake_client.experiments.run_experiment.assert_awaited_once()
    task = fake_client.experiments.run_experiment.await_args.kwargs["task"]
    assert inspect.iscoroutinefunction(task)
    fake_api_client.models.list.assert_awaited_once()
    assert fake_client.experiments.run_experiment.await_args.kwargs["concurrency"] == 1
    assert fake_client.experiments.run_experiment.await_args.kwargs["repetitions"] == 1
    assert fake_client.experiments.run_experiment.await_args.kwargs["retries"] == 0
    fake_api_client.close.assert_awaited_once()
