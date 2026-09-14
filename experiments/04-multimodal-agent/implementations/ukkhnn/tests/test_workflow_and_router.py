from __future__ import annotations

import asyncio
import json

import pytest

import multimodal_agent.workflow as workflow_module
from multimodal_agent.contracts import validate_contract
from multimodal_agent.privacy import PrivacyFinding
from multimodal_agent.provider import ProviderFailure
from multimodal_agent.router import route_task
from multimodal_agent.types import RawModelResponse, Usage
from multimodal_agent.workflow import MultimodalAgent

from conftest import LabelGateway, task_for


def test_workflow_returns_all_valid_contracts(label_gateway: LabelGateway) -> None:
    outcome = asyncio.run(MultimodalAgent(label_gateway).run(task_for()))
    validate_contract("agent-result", outcome.agent_result)
    validate_contract("evaluation-record", outcome.evaluation_record)
    for trace in outcome.tool_traces:
        validate_contract("tool-trace", trace)
    assert outcome.agent_result["status"] == "success"
    assert outcome.evaluation_record["task_success"] is True
    assert [trace["tool_name"] for trace in outcome.tool_traces] == [
        "image_preprocessor",
        "privacy_scanner",
        "deepseek_vision",
        "output_parser",
        "deterministic_grader",
    ]


def test_context_condition_includes_only_compact_context(label_gateway: LabelGateway) -> None:
    outcome = asyncio.run(
        MultimodalAgent(label_gateway).run(task_for("image-with-context"))
    )
    assert outcome.evaluation_record["task_success"] is True
    assert "user_description" in label_gateway.prompts[0]
    serialized_traces = json.dumps(outcome.tool_traces)
    assert "main > section.order-summary" not in serialized_traces
    assert "base64" not in serialized_traces


def test_privacy_finding_blocks_before_provider(
    label_gateway: LabelGateway, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        workflow_module,
        "scan_texts",
        lambda values: [PrivacyFinding(kind="email", source="image_manifest")],
    )
    outcome = asyncio.run(MultimodalAgent(label_gateway).run(task_for()))
    assert outcome.agent_result["status"] == "blocked"
    assert outcome.agent_result["metadata"]["error_type"] == "privacy_pattern_detected"
    assert label_gateway.calls == 0
    assert outcome.evaluation_record["metadata"]["model_called"] is False
    assert outcome.evaluation_record["metadata"]["graders"]["privacy_exposure"] == 0


class FailingGateway:
    provider = "deepseek"
    model_name = "deepseek-v4-flash-vision-exp"

    def __init__(self, kind: str) -> None:
        self.kind = kind

    async def analyze(self, *, image, prompt):
        raise ProviderFailure(self.kind, f"{self.kind} failure")


class MalformedGateway:
    provider = "deepseek"
    model_name = "deepseek-v4-flash-vision-exp"

    async def analyze(self, *, image, prompt):
        return RawModelResponse(
            content="not json",
            usage=Usage(input_tokens=12, output_tokens=4, requests=1),
            model=self.model_name,
            latency_ms=4.0,
            cost_usd=0.00000528,
            pricing_tier="off-peak",
        )


@pytest.mark.parametrize("kind", ["timeout", "rate_limit", "authentication"])
def test_provider_failures_are_retained(kind: str) -> None:
    outcome = asyncio.run(MultimodalAgent(FailingGateway(kind)).run(task_for()))
    assert outcome.agent_result["status"] == "failed"
    assert outcome.evaluation_record["failure_type"] == kind
    assert outcome.evaluation_record["task_success"] is False


def test_parse_failures_retain_usage_and_failure_type() -> None:
    outcome = asyncio.run(MultimodalAgent(MalformedGateway()).run(task_for()))
    assert outcome.evaluation_record["failure_type"] == "output_parse_error"
    assert outcome.evaluation_record["usage"]["total_tokens"] == 16
    assert outcome.evaluation_record["cost"] == pytest.approx(0.00000528)


def test_router_returns_agent_result(label_gateway: LabelGateway) -> None:
    result = asyncio.run(route_task(task_for(), agent=MultimodalAgent(label_gateway)))
    validate_contract("agent-result", result)
    assert result["status"] == "success"


def test_router_blocks_non_vision_without_call(label_gateway: LabelGateway) -> None:
    task = task_for()
    task["task_type"] = "routing"
    result = asyncio.run(route_task(task, agent=MultimodalAgent(label_gateway)))
    assert result["status"] == "blocked"
    assert result["metadata"]["error_type"] == "unsupported_task_type"
    assert label_gateway.calls == 0
