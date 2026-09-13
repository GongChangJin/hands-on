from __future__ import annotations

import hashlib

from agentic_rag.types import Chunk
from agentic_rag.vector_store import QdrantVectorStore


class HashEmbeddings:
    model_name = "test-hash"

    @staticmethod
    def _embed(text: str) -> list[float]:
        vector = [0.0] * 32
        for token in text.lower().split():
            vector[int(hashlib.sha256(token.encode()).hexdigest(), 16) % 32] += 1.0
        return vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def test_qdrant_indexes_payload_and_returns_location(tmp_path) -> None:
    chunks = [
        Chunk("doc-a::L1-L1", "doc-a", "요금", "L1-L1", "Team 요금 129000", "v1"),
        Chunk("doc-b::L1-L1", "doc-b", "장애", "L1-L1", "P1 복구 4시간", "v1"),
    ]
    store = QdrantVectorStore(
        path=tmp_path / "qdrant",
        collection_name="test",
        embeddings=HashEmbeddings(),
    )
    try:
        assert store.index(chunks) == 2
        result = store.search("Team 요금", limit=1, score_threshold=None)
        assert result[0].document_id == "doc-a"
        assert result[0].location == "L1-L1"
        assert result[0].score is not None
    finally:
        store.close()
