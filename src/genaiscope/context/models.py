"""Models for ContextBuilder."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ContextBuildResult(BaseModel):
    """Result of ContextBuilder.build()."""

    original_prompt: str
    retrieved_memories: list[dict[str, Any]] = Field(default_factory=list)
    context_text: str = ""
    improved_prompt: str = ""
    token_estimate: int = 0
    memory_ids_used: list[str] = Field(default_factory=list)
    context_quality_score: int = 0
