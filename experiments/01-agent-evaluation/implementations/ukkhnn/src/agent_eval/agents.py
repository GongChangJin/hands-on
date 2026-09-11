"""Small scripted agents used to test the evaluator before using real models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class AgentExecution:
    result: dict[str, Any]
    traces: list[dict[str, Any]]


class Agent(Protocol):
    implementation_id: str

    def run(self, task: dict[str, Any]) -> AgentExecution:
        """Execute one validated task."""


def _scripted_success(task: dict[str, Any], implementation_id: str) -> AgentExecution:
    constraints = task["constraints"]
    required_tools = constraints.get("required_tools", [])
    error_tools = set(constraints.get("error_tools", []))

    traces = []
    for tool_name in required_tools:
        has_error = tool_name in error_tools
        traces.append(
            {
                "task_id": task["task_id"],
                "tool_name": tool_name,
                "input_summary": f"scripted input for {tool_name}",
                "result_summary": "scripted error" if has_error else "scripted success",
                "duration_ms": 1.0,
                "error": "simulated tool failure" if has_error else None,
                "metadata": {"scripted": True},
            }
        )

    result = {
        "task_id": task["task_id"],
        "status": "success",
        "output": task["expected_output"],
        "evidence": [],
        "actions": [f"use_tool:{name}" for name in required_tools],
        "limitations": [],
        "metadata": {"implementation_id": implementation_id, "scripted": True},
    }
    return AgentExecution(result=result, traces=traces)


class OracleScriptedAgent:
    """Always follows the fixture; useful for proving the happy path."""

    implementation_id = "ukkhnn/scripted-oracle"

    def run(self, task: dict[str, Any]) -> AgentExecution:
        return _scripted_success(task, self.implementation_id)


class FlawedScriptedAgent:
    """Fails in several known ways so failure recording can be tested."""

    implementation_id = "ukkhnn/scripted-flawed"

    def run(self, task: dict[str, Any]) -> AgentExecution:
        task_id = task["task_id"]

        if task_id == "eval-005":
            raise RuntimeError("simulated agent crash")

        execution = _scripted_success(task, self.implementation_id)
        result = dict(execution.result)
        traces = list(execution.traces)

        if task_id == "eval-002":
            result["output"] = "41"
        elif task_id == "eval-003":
            traces = [
                {
                    "task_id": task_id,
                    "tool_name": "unapproved_web_search",
                    "input_summary": "wrong tool input",
                    "result_summary": "wrong tool result",
                    "duration_ms": 1.0,
                    "error": None,
                    "metadata": {"scripted": True},
                }
            ]
        elif task_id == "eval-004":
            result["status"] = "partial"

        return AgentExecution(result=result, traces=traces)
