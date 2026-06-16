"""Sentence-Transformers embedding backend.

Requires: pip install "genaiscope[embeddings]"
"""

from __future__ import annotations

from genaiscope.core.errors import EmbeddingBackendError
from genaiscope.embeddings.base import BaseEmbedder

_DEFAULT_MODEL = "all-MiniLM-L6-v2"


class SentenceTransformerEmbedder(BaseEmbedder):
    """Local CPU-friendly model via sentence-transformers."""

    name = "sentence-transformers"

    def __init__(self, model_name: str = _DEFAULT_MODEL) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingBackendError(
                "sentence-transformers is not installed. "
                'Run: pip install "genaiscope[embeddings]"'
            ) from exc
        self._model = SentenceTransformer(model_name)
        self.dimensions = self._model.get_sentence_embedding_dimension() or 384
        self.name = f"sentence-transformers/{model_name}"

    def embed(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()
