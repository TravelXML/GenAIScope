"""Embedding models and result types."""

from __future__ import annotations

from pydantic import BaseModel


class EmbeddingResult(BaseModel):
    """Result of a single text embedding."""

    text: str
    vector: list[float]
    embedder_name: str
    dimensions: int
