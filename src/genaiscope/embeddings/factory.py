"""Embedding backend factory."""

from __future__ import annotations

from typing import Any

from genaiscope.core.errors import EmbeddingBackendError
from genaiscope.embeddings.base import BaseEmbedder


def get_embedder(backend: str = "local", **kwargs: Any) -> BaseEmbedder:
    """Return a configured embedder instance.

    backend options: "local" | "local_hash" | "sentence-transformers" | "openai"
    """
    b = backend.lower().replace("_", "-")

    if b in ("local", "local-hash", "local_hash"):
        from genaiscope.embeddings.local_hash import LocalHashEmbedder

        dims = kwargs.get("dimensions", 256)
        return LocalHashEmbedder(dimensions=dims)

    if b in ("sentence-transformers", "st"):
        from genaiscope.embeddings.sentence_transformers import SentenceTransformerEmbedder

        model = kwargs.get("model", "all-MiniLM-L6-v2")
        return SentenceTransformerEmbedder(model_name=model)

    if b == "openai":
        from genaiscope.embeddings.openai_embeddings import OpenAIEmbedder

        model = kwargs.get("model", "text-embedding-3-small")
        api_key = kwargs.get("api_key")
        return OpenAIEmbedder(model=model, api_key=api_key)

    raise EmbeddingBackendError(
        f"Unknown embedding backend: {backend!r}. "
        "Valid options: 'local', 'sentence-transformers', 'openai'."
    )
