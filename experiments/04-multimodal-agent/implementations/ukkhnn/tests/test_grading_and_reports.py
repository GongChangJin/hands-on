from __future__ import annotations

import asyncio
import json
from pathlib import Path

from multimodal_agent.evaluation import (
    load_adaptive_tasks,
    load_tasks,
    run_adaptive_evaluation,
    run_evaluation,
)
from multimodal_agent.paths import TASKS_PATH
from multimodal_agent.reporting import compare_results
from multimodal_agent.types import RawModelResponse, Usage
from multimodal_agent.workflow import MultimodalAgent

from conftest import LabelGateway


def test_evaluation_exports_all_four_formats(tmp_path: Path) -> None:
    gateway = LabelGateway()
    tasks = load_tasks(TASKS_PATH, condition="image-only", limit=3)
    output = tmp_path / "only"
    summary = asyncio.run(
        run_evaluation(
            MultimodalAgent(gateway),
            tasks,
            output=output,
            condition="image-only",
        )
    )
    assert summary["runs"] == 3
    assert summary["success_rate"] == 1.0
    assert summary["schema_compliance_rate"] == 1.0
    assert summary["privacy_exposure_count"] == 0
    assert summary["usage"]["total_tokens"] == 1170
    assert {path.name for path in output.iterdir()} == {
        "records.jsonl",
        "records.csv",
        "summary.json",
        "report.md",
    }
    records = [json.loads(line) for line in (output / "records.jsonl").read_text().splitlines()]
    assert len(records) == 3
    assert all("agent_result" in row["metadata"] for row in records)
    assert all("tool_traces" in row["metadata"] for row in records)


def test_comparison_has_condition_metrics_and_deltas(tmp_path: Path) -> None:
    only_dir = tmp_path / "only"
    context_dir = tmp_path / "context"
    for condition, output in (("image-only", only_dir), ("image-with-context", context_dir)):
        tasks = load_tasks(TASKS_PATH, condition=condition, limit=2)
        asyncio.run(
            run_evaluation(
                MultimodalAgent(LabelGateway()),
                tasks,
                output=output,
                condition=condition,
            )
        )
    comparison = tmp_path / "comparison.md"
    value = compare_results(only_dir, context_dir, comparison)
    assert comparison.read_text() == value
    assert "image-only" in value
    assert "image-with-context" in value
    assert "classification accuracy" in value
    assert "severity accuracy" in value
    assert "latency p95" in value
    assert "calculated cost USD" in value


def test_limit_must_be_positive() -> None:
    import pytest

    with pytest.raises(ValueError, match="limit"):
        load_tasks(TASKS_PATH, condition="image-only", limit=0)


def test_normal_screen_can_pass_without_error_evidence(tmp_path: Path) -> None:
    tasks = load_tasks(TASKS_PATH, condition="image-only")[-1:]
    summary = asyncio.run(
        run_evaluation(
            MultimodalAgent(LabelGateway()),
            tasks,
            output=tmp_path / "normal",
            condition="image-only",
        )
    )
    assert summary["success_rate"] == 1.0
    assert summary["evidence_accuracy"] == 1.0


class MissThenLabelGateway(LabelGateway):
    async def analyze(self, *, image, prompt):
        if "Input condition: image-only" in prompt:
            self.calls += 1
            self.prompts.append(prompt)
            return RawModelResponse(
                content=json.dumps(
                    {"summary": "No issue found.", "overall_severity": "none", "errors": []}
                ),
                usage=Usage(input_tokens=300, output_tokens=90, requests=1),
                model=self.model_name,
                latency_ms=10.0,
                cost_usd=0.0001254,
                pricing_tier="off-peak",
            )
        return await super().analyze(image=image, prompt=prompt)


def test_adaptive_evaluation_retries_empty_analysis_with_context(tmp_path: Path) -> None:
    gateway = MissThenLabelGateway()
    summary = asyncio.run(
        run_adaptive_evaluation(
            MultimodalAgent(gateway),
            load_adaptive_tasks(TASKS_PATH, limit=1),
            output=tmp_path / "adaptive",
        )
    )
    assert summary["success_rate"] == 1.0
    assert summary["context_retry_count"] == 1
    assert summary["usage"]["requests"] == 2
    record = json.loads((tmp_path / "adaptive" / "records.jsonl").read_text().splitlines()[0])
    assert record["metadata"]["adaptive"] == {
        "context_retried": True,
        "selected_phase": "image-with-context",
    }
