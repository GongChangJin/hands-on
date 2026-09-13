"""TaskRequest → AgentResult adapter for the later LLM Router project."""

from __future__ import annotations

from typing import Any

from .contracts import validate_contract
from .workflow import MultimodalAgent


async def route_task(request: dict[str, Any], *, agent: MultimodalAgent) -> dict[str, Any]:
    validate_contract("task-request", request)
    if request["task_type"] != "vision":
        result = {
            "task_id": request["task_id"],
            "status": "blocked",
            "output": None,
            "evidence": [],
            "actions": [],
            "limitations": ["이 adapter는 vision TaskRequest만 처리합니다."],
            "metadata": {"error_type": "unsupported_task_type"},
        }
        validate_contract("agent-result", result)
        return result
    return (await agent.run(request)).agent_result


class MultimodalRouterAdapter:
    def __init__(self, agent: MultimodalAgent) -> None:
        self.agent = agent

    async def __call__(self, request: dict[str, Any]) -> dict[str, Any]:
        return await route_task(request, agent=self.agent)
