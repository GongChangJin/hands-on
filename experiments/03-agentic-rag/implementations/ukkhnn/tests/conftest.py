from __future__ import annotations

from typing import Any

from agentic_rag.types import Chunk, Usage


class FakeGateway:
    provider = "upstage"
    model_name = "fake-solar"

    def __init__(self, responses: dict[str, list[dict[str, Any]]]) -> None:
        self.responses = {key: list(values) for key, values in responses.items()}
        self.usage = Usage()

    def reset_usage(self) -> None:
        self.usage = Usage()

    async def complete_json(self, *, operation: str, system: str, payload: dict[str, Any]):
        self.usage.calls += 1
        self.usage.input_tokens += 10
        self.usage.output_tokens += 5
        return self.responses[operation].pop(0)


class FakeRetriever:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.queries: list[str] = []

    def search(self, query: str, *, limit: int, score_threshold: float | None):
        self.queries.append(query)
        return self.chunks[:limit]


def product_chunk() -> Chunk:
    return Chunk(
        chunk_id="product-policy-v1::L8-L8",
        document_id="product-policy-v1",
        title="상품 및 지원 정책",
        location="L8-L8",
        text="Starter는 월 49,000원이며 사용자 3명을 포함한다. 추가 사용자는 12,000원이다.",
        version="2026-09-01",
        score=0.91,
    )


def task(question: str, allowed_tools: list[str], max_tool_calls: int = 3) -> dict[str, Any]:
    return {
        "task_id": "test-task",
        "task_type": "rag",
        "input": question,
        "constraints": {
            "allowed_tools": allowed_tools,
            "forbidden_actions": ["추측"],
            "max_steps": 9,
            "max_tool_calls": max_tool_calls,
        },
        "expected_output": {},
    }
