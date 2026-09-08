# 라우팅 클라이언트. 분류 -> 모델 호출 -> 폴백 -> 계측을 한 곳에서 처리한다.
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .classify import Decision, classify
from .fallback import with_fallback


@dataclass
class RoutedResponse:
    output: str
    decision: Decision
    used_route: str
    provider: str = ""
    model_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    router_cost_usd: float = 0.0
    fallback_attempts: list[tuple[str, str]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def total_cost_usd(self) -> float:
        # 라우터 자체 비용을 빼고 비교하지 않는다.
        return self.cost_usd + self.router_cost_usd


class RoutedClient:
    def __init__(self, strategy: str = "hybrid", *, timeout_s: float = 30.0):
        self.strategy = strategy
        self.timeout_s = timeout_s

    def invoke(self, prompt: str) -> RoutedResponse:
        from evalkit.models import estimate_cost, make_chat_model, resolve

        t_router = time.perf_counter()
        decision = classify(prompt, self.strategy)
        router_ms = (time.perf_counter() - t_router) * 1000

        def call(route: str):
            return make_chat_model(route=route).invoke(prompt)

        t0 = time.perf_counter()
        reply, used_route, attempts = with_fallback(call, decision.route, timeout_s=self.timeout_s)
        latency_ms = (time.perf_counter() - t0) * 1000

        usage = getattr(reply, "usage_metadata", None) or {}
        in_tok = int(usage.get("input_tokens", 0))
        out_tok = int(usage.get("output_tokens", 0))
        spec = resolve(used_route)
        return RoutedResponse(
            output=str(reply.content),
            decision=decision,
            used_route=used_route,
            provider=spec["provider"],
            model_id=spec["model"],
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=estimate_cost(used_route, in_tok, out_tok),
            latency_ms=latency_ms,
            router_cost_usd=0.0,  # TODO: llm 분류를 쓸 때 분류 호출 토큰을 여기 더한다
            fallback_attempts=attempts,
            extra={"router_ms": router_ms},
        )
