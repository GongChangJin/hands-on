# run_eval.py 어댑터. 전략별로 factory 를 만들어 같은 태스크셋에 돌린다.
from __future__ import annotations

import evalkit_bridge  # noqa: F401

from evalkit import AgentResult, Task  # noqa: E402

from router import RoutedClient  # noqa: E402


def build(strategy: str = "hybrid"):
    client = RoutedClient(strategy=strategy)

    def agent(task: Task) -> AgentResult:
        r = client.invoke(task.prompt)
        return AgentResult(
            output=r.output,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            cost_usd=r.total_cost_usd,
            latency_ms=r.latency_ms,
            logical_route=r.used_route,
            provider=r.provider,
            model_id=r.model_id,
            extra={
                "planned_route": r.decision.route,
                "strategy": r.decision.strategy,
                "confidence": r.decision.confidence,
                "fallbacks": r.fallback_attempts,
            },
        )

    return agent


def build_baseline():
    return build("all_frontier")


def build_rule():
    return build("rule")


def build_hybrid():
    return build("hybrid")
