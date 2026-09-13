from __future__ import annotations

import asyncio

from agentic_rag.agent import AgenticRAG

from conftest import FakeGateway, FakeRetriever, product_chunk, task


def test_mixed_question_retrieves_formulates_and_calculates() -> None:
    chunk = product_chunk()
    gateway = FakeGateway(
        {
            "plan": [{"action": "search_then_calculate", "search_query": "Starter 사용자 요금"}],
            "grade": [{"relevant": True, "relevant_chunk_ids": [chunk.chunk_id]}],
            "formulate": [{"expression": "49000 + (5 - 3) * 12000"}],
            "answer": [{"answer": "총액은 73,000원입니다.", "citation_chunk_ids": [chunk.chunk_id]}],
        }
    )
    result = asyncio.run(
        AgenticRAG(gateway, FakeRetriever([chunk])).run(
            task("Starter를 사용자 5명이 쓰면?", ["retriever", "calculator"])
        )
    )
    assert result["status"] == "success"
    assert result["actions"] == ["retriever", "calculator"]
    assert {item["source"] for item in result["evidence"]} == {
        "product-policy-v1",
        "calculator",
    }
    assert result["metadata"]["tool_traces"][1]["result_summary"] == "73000"


def test_irrelevant_search_rewrites_once_then_returns_no_answer() -> None:
    chunk = product_chunk()
    retriever = FakeRetriever([chunk])
    gateway = FakeGateway(
        {
            "plan": [{"action": "search", "search_query": "서울 주소"}],
            "grade": [
                {"relevant": False, "relevant_chunk_ids": [], "improved_query": "회사 사무실 위치"},
                {"relevant": False, "relevant_chunk_ids": [], "improved_query": "서울 사무실 주소"},
            ],
            "rewrite": [{"query": "회사 서울 사무실 주소 위치"}],
        }
    )
    result = asyncio.run(
        AgenticRAG(gateway, retriever).run(task("서울 사무실 주소는?", ["retriever"], 2))
    )
    assert result["status"] == "partial"
    assert "확인할 수 없습니다" in result["output"]
    assert result["actions"] == ["retriever", "retriever"]
    assert len(retriever.queries) == 2
    assert result["evidence"] == []


def test_pure_calculation_does_not_retrieve() -> None:
    gateway = FakeGateway(
        {
            "plan": [{"action": "calculate", "expression": "17 * 23"}],
            "answer": [{"answer": "결과는 391입니다.", "citation_chunk_ids": []}],
        }
    )
    result = asyncio.run(
        AgenticRAG(gateway, FakeRetriever([])).run(task("17 곱하기 23", ["calculator"], 1))
    )
    assert result["status"] == "success"
    assert result["actions"] == ["calculator"]
    assert result["evidence"][0]["location"] == "expression:17 * 23"


def test_disallowed_calculator_is_not_executed_or_traced() -> None:
    gateway = FakeGateway(
        {
            "plan": [{"action": "calculate", "expression": "17 * 23"}],
            "answer": [{"answer": "계산할 수 없습니다.", "citation_chunk_ids": []}],
        }
    )
    result = asyncio.run(
        AgenticRAG(gateway, FakeRetriever([])).run(task("17 곱하기 23", ["retriever"], 1))
    )
    assert result["status"] == "failed"
    assert result["actions"] == []
    assert any("허용하지" in reason for reason in result["limitations"])
