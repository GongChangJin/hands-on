"""Small types crossing preprocessing, provider, and evaluation boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class PreparedImage:
    source_path: Path
    relative_path: str
    png_bytes: bytes
    sha256: str
    width: int
    height: int
    source_bytes: int
    metadata_removed: tuple[str, ...]
    label: dict[str, Any]


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    requests: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def as_dict(self) -> dict[str, int]:
        return {
            "requests": self.requests,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True)
class RawModelResponse:
    content: str
    usage: Usage
    model: str
    latency_ms: float
    cost_usd: float
    pricing_tier: str


class VisionGateway(Protocol):
    provider: str
    model_name: str

    async def analyze(self, *, image: PreparedImage, prompt: str) -> RawModelResponse: ...


@dataclass
class RunOutcome:
    agent_result: dict[str, Any]
    tool_traces: list[dict[str, Any]]
    evaluation_record: dict[str, Any]
    usage: Usage = field(default_factory=Usage)
    cost_usd: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "agent_result": self.agent_result,
            "tool_traces": self.tool_traces,
            "evaluation_record": self.evaluation_record,
        }
