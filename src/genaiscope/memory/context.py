"""context() helper — builds an injectable memory block for assistants."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContextResult(BaseModel):
    """Result of memory.context() — ready-to-inject text for assistants."""

    query: str
    memories: list[dict] = Field(default_factory=list)
    text: str = ""
    char_count: int = 0
    memory_count: int = 0
    embedder_used: str = "none"
    mode: str = "hybrid"
