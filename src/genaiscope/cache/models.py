"""Semantic cache models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CacheHit(BaseModel):
    """A hybrid text cache hit."""

    response: str
    score: float
    memory_id: str
    model: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CacheStats(BaseModel):
    """Semantic cache aggregate statistics."""

    total_entries: int = 0
