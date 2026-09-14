import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from agent_eval.contracts import CONTRACT_NAMES, validate_contract
from agent_eval.experiment import _failure_output
from agent_eval.report import comparison_markdown, export_report, summarize_records


REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"


VALID_CONTRACTS = {
    "task-request": {
        "task_id": "case-1",
        "task_type": "evaluation",
        "input": "question",
        "constraints": {"allowed_tools": [], "forbidden_actions": []},
        "expected_output": {},
    },
    "agent-result": {
        "task_id": "case-1",
        "status": "success",
        "output": "answer",
        "evidence": [],
        "actions": [],
        "limitations": [],
    },
    "tool-trace": {
        "task_id": "case-1",
        "tool_name": "calculator",
        "input_summary": "1+1",
        "result_summary": "2",
        "duration_ms": 1.0,
    },
    "evaluation-record": {
        "task_id": "case-1",
        "implementation_id": "ukkhnn:test",
        "task_success": True,
        "latency_ms": 1.0,
        "safety_violations": [],
    },
}


@pytest.mark.parametrize("contract_name", CONTRACT_NAMES)
def test_all_shared_contracts_validate(contract_name: str) -> None:
    validate_contract(contract_name, VALID_CONTRACTS[contract_name])


def test_invalid_contract_is_rejected() -> None:
    with pytest.raises(ValidationError):
        validate_contract("evaluation-record", {"task_id": "missing-fields"})


def test_failures_are_preserved_as_agent_results() -> None:
    output = _failure_output("case-1", "handoff", "provider unavailable")

    assert output["agent_result"]["status"] == "failed"
    assert output["error"] == "provider unavailable"


def test_report_exports_jsonl_csv_markdown(tmp_path) -> None:
    records = [
        {
            "task_id": "case-1",
            "implementation_id": "ukkhnn:upstage:solar-pro4:single",
            "task_success": True,
            "quality_score": 1.0,
            "tool_accuracy": 1.0,
            "latency_ms": 100.0,
            "usage": {
                "requests": 1,
                "input_tokens": 10,
                "output_tokens": 2,
                "total_tokens": 12,
            },
            "cost": 0.001,
            "safety_violations": [],
            "failure_type": None,
            "metadata": {},
        },
        {
            "task_id": "case-2",
            "implementation_id": "ukkhnn:upstage:solar-pro4:single",
            "task_success": False,
            "quality_score": 0.0,
            "tool_accuracy": 0.5,
            "latency_ms": 300.0,
            "usage": {
                "requests": 1,
                "input_tokens": 12,
                "output_tokens": 3,
                "total_tokens": 15,
            },
            "cost": 0.002,
            "safety_violations": ["unexpected_tool:x"],
            "failure_type": "safety_violation",
            "metadata": {},
        },
    ]
    summary = summarize_records(
        records,
        experiment_id="experiment-1",
        provider="upstage",
        model_name="solar-pro4",
        architecture="single",
    )

    report_path = export_report(records, summary, tmp_path)

    assert summary["success_rate"] == 0.5
    assert summary["latency_p50_ms"] == 200.0
    assert summary["latency_p95_ms"] == pytest.approx(290.0)
    assert report_path.exists()
    assert (tmp_path / "records.csv").exists()
    assert len((tmp_path / "records.jsonl").read_text().splitlines()) == 2
    assert json.loads((tmp_path / "summary.json").read_text())["runs"] == 2
    assert "single" in comparison_markdown([summary])


def _load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_saved_architecture_regression_results() -> None:
    comparison_dir = REPORTS_DIR / "upstage-solar-pro4-architecture-v2"
    single = _load_records(comparison_dir / "single" / "records.jsonl")
    handoff = _load_records(comparison_dir / "handoff" / "records.jsonl")

    assert len(single) == len(handoff) == 20
    assert sum(record["task_success"] for record in single) == 20
    assert sum(record["task_success"] for record in handoff) == 19
    assert [record["task_id"] for record in handoff if not record["task_success"]] == [
        "calc-divide"
    ]
    for record in [*single, *handoff]:
        validate_contract("evaluation-record", record)


def test_saved_llm_evaluations_are_separate_from_code_success() -> None:
    records = _load_records(
        REPORTS_DIR / "upstage-solar-pro4-single-llm-judge" / "records.jsonl"
    )

    assert len(records) == 20
    assert all(record["task_success"] for record in records)
    assert all(
        record["metadata"]["evaluations"]["semantic-quality-llm"]["kind"] == "LLM"
        for record in records
    )
