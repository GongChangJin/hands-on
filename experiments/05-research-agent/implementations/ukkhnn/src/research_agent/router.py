"""Router-facing TaskRequest → AgentResult research interface."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .contracts import validate_contract


def _blocked(task: dict[str, Any]) -> dict[str, Any]:
    result = {
        "task_id": task["task_id"],
        "status": "blocked",
        "output": None,
        "evidence": [],
        "actions": [],
        "limitations": ["The research agent accepts only task_type=research and made no external call."],
        "metadata": {"blocked_reason": "unsupported_task_type", "external_calls": 0},
    }
    validate_contract("agent-result", result)
    return result


def route_task(
    task: dict[str, Any],
    research_handler: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    validate_contract("task-request", task)
    if task["task_type"] != "research":
        return _blocked(task)
    result = research_handler(task)
    validate_contract("agent-result", result)
    if result["status"] == "success" and not result["evidence"]:
        raise ValueError("A successful research AgentResult must contain verified evidence")
    return result
