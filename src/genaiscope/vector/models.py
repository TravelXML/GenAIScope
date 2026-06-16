"""Vector store data models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class VectorRecord(BaseModel):
    """A vector with its id and metadata to upsert."""

    vector_id: str
    vector: list[float]
    metadata: dict[str, Any] = Field(default_factory=dict)


class VectorMatch(BaseModel):
    """A query result from the vector store."""

    vector_id: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)
