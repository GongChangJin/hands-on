"""Small runtime types that keep usage and failures explicit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    requests: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cached_input_tokens += other.cached_input_tokens
        self.requests += other.requests

    def as_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "total_tokens": self.total_tokens,
            "requests": self.requests,
        }


@dataclass
class ModelResult:
    value: dict[str, Any]
    usage: Usage
    response_model: str
    latency_ms: float
    cost_usd: float
    pricing_tier: str


@dataclass
class RunStats:
    latencies_ms: list[float] = field(default_factory=list)
    requests_by_source: dict[str, int] = field(default_factory=dict)
    failures: list[dict[str, Any]] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    cost_usd: float = 0.0

    def request(self, source: str, latency_ms: float) -> None:
        self.requests_by_source[source] = self.requests_by_source.get(source, 0) + 1
        self.latencies_ms.append(latency_ms)


class WorkflowFailure(RuntimeError):
    def __init__(self, kind: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.kind = kind
        self.retryable = retryable
