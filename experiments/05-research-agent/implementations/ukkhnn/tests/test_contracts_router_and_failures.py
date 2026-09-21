from __future__ import annotations

import json

import httpx
import pytest

from research_agent.contracts import validate_contract, validate_research
from research_agent.deepseek import DeepSeekGateway
from research_agent.http import ResilientClient
from research_agent.router import route_task
from research_agent.types import WorkflowFailure
from research_agent.workflow import _apply_extracted_papers, validate_shared


def test_shared_question_and_tasks_are_valid() -> None:
    result = validate_shared()
    assert result["status"] == "valid"
    assert result["seed_queries"] == 4
    assert result["tasks"] == 5
    assert result["minimum_verified_papers"] == 10


def task(task_type: str) -> dict:
    return {
        "task_id": f"task-{task_type}",
        "task_type": task_type,
        "input": {"question": "test"},
        "constraints": {"allowed_tools": [], "forbidden_actions": ["invent"]},
        "expected_output": {},
    }


def test_router_blocks_non_research_without_calling_handler() -> None:
    called = False

    def handler(value):
        nonlocal called
        called = True
        raise AssertionError("must not call")

    result = route_task(task("routing"), handler)
    validate_contract("agent-result", result)
    assert result["status"] == "blocked"
    assert result["metadata"]["external_calls"] == 0
    assert called is False


def test_router_validates_research_result_and_blocks_success_without_evidence() -> None:
    def handler(value):
        return {"task_id": value["task_id"], "status": "success", "output": {}, "evidence": [], "actions": [], "limitations": []}

    with pytest.raises(ValueError, match="verified evidence"):
        route_task(task("research"), handler)


@pytest.mark.parametrize(
    ("status", "kind"),
    [(401, "authentication"), (429, "rate_limit"), (500, "server_error")],
)
def test_http_failure_types_are_explicit(status: int, kind: str) -> None:
    resilient = ResilientClient(
        client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(status))),
        maximum_attempts=1,
    )
    with pytest.raises(WorkflowFailure) as caught:
        resilient.request("crossref", "GET", "https://example.test")
    assert caught.value.kind == kind


def test_deepseek_parsing_failure_is_explicit() -> None:
    client = httpx.Client(
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"model": "deepseek-flash", "choices": [{"message": {"content": "not json"}}], "usage": {}})
        ),
    )
    with pytest.raises(WorkflowFailure) as caught:
        DeepSeekGateway(client=client, api_key="test").complete_json(system="safe", user="safe")
    assert caught.value.kind == "model_parsing"


def test_claim_and_hypothesis_contracts_cannot_be_mixed() -> None:
    claim = {
        "claim_id": "claim-1",
        "claim": "A paper result",
        "claim_type": "paper_result",
        "paper_record_id": "paper-1",
        "paper_title": "Paper",
        "identifiers": {"doi": "10.5555/test"},
        "source_url": "https://doi.org/10.5555/test",
        "evidence_location": "abstract",
        "evidence_type": "abstract",
        "quote": None,
        "paraphrase": "Result paraphrase",
        "verified": True,
        "extraction_uncertainty": "abstract only",
    }
    validate_research("claim-evidence", claim)
    hypothesis = {
        "hypothesis_id": "hypothesis-1",
        "hypothesis": "A follow-up hypothesis",
        "derived_from_claim_ids": ["claim-1"],
        "rationale": "Derived separately",
        "falsification_test": "Run a controlled ablation",
        "confidence": 0.5,
        "attribution": "agent_hypothesis_not_paper_conclusion",
    }
    validate_research("hypothesis", hypothesis)
    hypothesis["attribution"] = "paper_conclusion"
    with pytest.raises(Exception):
        validate_research("hypothesis", hypothesis)


def test_targeted_extraction_attaches_a_valid_claim_to_missing_paper() -> None:
    paper = {
        "record_id": "paper-1",
        "title": "Corrective Retrieval for RAG",
        "identifiers": {"doi": "10.5555/test"},
        "source_records": [{"source_url": "https://doi.org/10.5555/test"}],
        "analysis": {"paper_claims": []},
    }
    returned = [
        {
            "record_id": "paper-1",
            "research_objective": "Improve retrieval quality",
            "methodology": "Corrective retrieval",
            "paper_claims": [
                {
                    "claim": "The paper proposes corrective retrieval for RAG.",
                    "paraphrase": "A corrective retrieval method is introduced.",
                }
            ],
            "extraction_uncertainty": "Abstract excerpt only",
        }
    ]
    claims: list[dict] = []
    covered = _apply_extracted_papers(returned, [paper], claims)
    assert covered == {"paper-1"}
    assert claims[0]["paper_record_id"] == "paper-1"
    assert paper["analysis"]["paper_claims"][0]["claim_id"] == claims[0]["claim_id"]
