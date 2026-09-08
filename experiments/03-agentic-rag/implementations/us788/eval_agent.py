# run_eval.py 에서 --agent eval_agent:build 로 부르는 어댑터.
from __future__ import annotations

import evalkit_bridge  # noqa: F401  경로 등록

from evalkit import AgentResult, Task  # noqa: E402
from evalkit.models import estimate_cost, resolve  # noqa: E402

from agent.graph import build_graph  # noqa: E402


def build(route: str = "balanced"):
    graph = build_graph()

    def agent(task: Task) -> AgentResult:
        state = graph.invoke({"question": task.prompt, "route": route, "attempts": 0})
        spec = resolve(route)
        return AgentResult(
            output=state.get("answer", ""),
            tool_calls=[],
            input_tokens=state.get("input_tokens", 0),
            output_tokens=state.get("output_tokens", 0),
            cost_usd=estimate_cost(route, state.get("input_tokens", 0), state.get("output_tokens", 0)),
            logical_route=route,
            provider=spec["provider"],
            model_id=spec["model"],
            forbidden_actions=state.get("forbidden_actions", 0),
            extra={"attempts": state.get("attempts", 0), "docs": [d.cite() for d in state.get("docs", [])]},
        )

    return agent
