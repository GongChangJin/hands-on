"""Lazy local embedding adapter; no document text is sent to an API."""

from __future__ import annotations

from pathlib import Path


DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class LocalFastEmbed:
    def __init__(self, model_name: str = DEFAULT_MODEL, cache_dir: Path | None = None) -> None:
        self.model_name = model_name
        self.cache_dir = cache_dir
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from fastembed import TextEmbedding

            kwargs = {"model_name": self.model_name}
            if self.cache_dir is not None:
                kwargs["cache_dir"] = str(self.cache_dir)
            self._model = TextEmbedding(**kwargs)
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self.model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(self.model.query_embed(text)).tolist()
