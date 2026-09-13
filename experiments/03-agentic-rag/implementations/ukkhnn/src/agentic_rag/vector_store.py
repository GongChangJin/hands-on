"""Qdrant-backed local vector index."""

from __future__ import annotations

from pathlib import Path

from qdrant_client import QdrantClient, models

from .types import Chunk, EmbeddingModel


class QdrantVectorStore:
    def __init__(
        self,
        *,
        path: Path | str,
        collection_name: str,
        embeddings: EmbeddingModel,
    ) -> None:
        self.path = path
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.client = QdrantClient(path=str(path)) if str(path) != ":memory:" else QdrantClient(":memory:")

    def collection_exists(self) -> bool:
        return self.client.collection_exists(self.collection_name)

    def index(self, chunks: list[Chunk]) -> int:
        if not chunks:
            raise ValueError("색인할 chunk가 없습니다.")
        vectors = self.embeddings.embed_documents([chunk.text for chunk in chunks])
        if not vectors or not vectors[0]:
            raise ValueError("로컬 임베딩이 빈 vector를 반환했습니다.")
        if self.collection_exists():
            self.client.delete_collection(self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(size=len(vectors[0]), distance=models.Distance.COSINE),
        )
        points = [
            models.PointStruct(id=index, vector=vector, payload=chunk.as_payload())
            for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
        ]
        self.client.upsert(collection_name=self.collection_name, points=points, wait=True)
        return len(points)

    def search(
        self,
        query: str,
        *,
        limit: int,
        score_threshold: float | None,
    ) -> list[Chunk]:
        if not self.collection_exists():
            raise RuntimeError("Qdrant collection이 없습니다. 먼저 `agentic-rag index`를 실행하세요.")
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=self.embeddings.embed_query(query),
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
        )
        return [
            Chunk(
                chunk_id=str(point.payload["chunk_id"]),
                document_id=str(point.payload["document_id"]),
                title=str(point.payload["title"]),
                location=str(point.payload["location"]),
                text=str(point.payload["text"]),
                version=str(point.payload.get("version", "")),
                score=float(point.score),
            )
            for point in response.points
            if point.payload
        ]

    def close(self) -> None:
        self.client.close()
