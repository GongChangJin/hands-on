"""Small data types shared by ingestion, retrieval, and the graph."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    title: str
    location: str
    text: str
    version: str = ""
    score: float | None = None

    def as_payload(self) -> dict[str, Any]:
        value = asdict(self)
        value.pop("score", None)
        return value


class EmbeddingModel(Protocol):
    model_name: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class Retriever(Protocol):
    def search(self, query: str, *, limit: int, score_threshold: float | None) -> list[Chunk]: ...


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def as_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "total_tokens": self.total_tokens,
            "llm_calls": self.calls,
        }


class Gateway(Protocol):
    provider: str
    model_name: str
    usage: Usage

    def reset_usage(self) -> None: ...

    async def complete_json(
        self,
        *,
        operation: str,
        system: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]: ...
