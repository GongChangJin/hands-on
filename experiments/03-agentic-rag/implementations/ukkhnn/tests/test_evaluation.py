from __future__ import annotations

from pathlib import Path

from agentic_rag.evaluation import grade_result, load_tasks, summarize


PROJECT_DIR = Path(__file__).resolve().parents[3]


def test_shared_evaluation_set_covers_required_categories() -> None:
    tasks = load_tasks(PROJECT_DIR / "shared" / "evals" / "tasks.jsonl")
    assert len(tasks) == 19
    categories = {task["expected_output"]["category"] for task in tasks}
    assert categories == {"retrieval", "calculation", "mixed", "no_answer", "safety"}


def test_deterministic_grader_checks_tools_evidence_and_formula() -> None:
    task = {
        "task_id": "case",
        "task_type": "rag",
        "input": "Team 연간 요금",
        "constraints": {
            "allowed_tools": ["retriever", "calculator"],
            "forbidden_actions": [],
            "max_steps": 9,
            "max_tool_calls": 3,
        },
        "expected_output": {
            "category": "mixed",
            "required_terms": ["1315800"],
            "expected_sources": ["product-policy-v1"],
            "required_tools": ["retriever", "calculator"],
            "expected_expression": "129000 * 12 * 0.85",
        },
    }
    result = {
        "task_id": "case",
        "status": "success",
        "output": "1,315,800원",
        "evidence": [
            {"source": "product-policy-v1", "location": "L8-L12", "claim": "요금"},
            {"source": "calculator", "location": "expression:x", "claim": "계산"},
        ],
        "actions": ["retriever", "calculator"],
        "limitations": [],
        "metadata": {
            "implementation_id": "test",
            "provider": "upstage",
            "model": "fake",
            "latency_ms": 10,
            "usage": {},
            "estimated_cost_usd": 0.0,
            "safety_violations": [],
            "tool_traces": [
                {"tool_name": "retriever", "error": None},
                {"tool_name": "calculator", "result_summary": "1315800", "error": None},
            ],
        },
    }
    record = grade_result(task, result)
    assert record["task_success"] is True
    assert summarize([record])["success_rate"] == 1.0
