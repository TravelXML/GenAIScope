"""OpenAI embedding backend.

Requires: pip install "genaiscope[providers]" and OPENAI_API_KEY set.
"""

from __future__ import annotations

import os

from genaiscope.core.errors import EmbeddingBackendError
from genaiscope.embeddings.base import BaseEmbedder

_DEFAULT_MODEL = "text-embedding-3-small"
_DEFAULT_DIMS = 1536


class OpenAIEmbedder(BaseEmbedder):
    """OpenAI embeddings API backend."""

    name = "openai"

    def __init__(self, model: str = _DEFAULT_MODEL, api_key: str | None = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise EmbeddingBackendError(
                "openai is not installed. "
                'Run: pip install "genaiscope[providers]"'
            ) from exc

        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise EmbeddingBackendError(
                "OPENAI_API_KEY is not set. Export it or pass api_key= to OpenAIEmbedder."
            )

        self._client = OpenAI(api_key=key)
        self._model = model
        self.name = f"openai/{model}"
        self.dimensions = _DEFAULT_DIMS

    def embed(self, text: str) -> list[float]:
        resp = self._client.embeddings.create(input=[text], model=self._model)
        return resp.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(input=texts, model=self._model)
        return [item.embedding for item in sorted(resp.data, key=lambda x: x.index)]
