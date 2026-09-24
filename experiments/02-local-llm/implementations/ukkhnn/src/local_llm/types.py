"""Adapter-neutral generation types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class GenerationRequest:
    task_id: str
    system: str
    prompt: str
    response_schema: dict[str, Any]


@dataclass
class GenerationResponse:
    text: str = ""
    model: str = ""
    total_latency_ms: float = 0.0
    first_token_latency_ms: float | None = None
    prompt_tokens: int = 0
    output_tokens: int = 0
    generation_tokens_per_second: float | None = None
    load_duration_ms: float | None = None
    prompt_eval_duration_ms: float | None = None
    generation_duration_ms: float | None = None
    cost_usd: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class LLMAdapter(Protocol):
    adapter_name: str
    model: str

    def generate(self, request: GenerationRequest) -> GenerationResponse: ...

    def inspect(self) -> dict[str, Any]: ...

    def warmup(self) -> GenerationResponse: ...
