"""Models for local GenAIScope memory."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PromptQualityReport(BaseModel):
    """Heuristic prompt quality analysis."""

    score: int
    risk_level: str
    comments: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)
    detected_issues: list[str] = Field(default_factory=list)


class MemoryItem(BaseModel):
    """A stored memory item."""

    id: str
    content: str
    memory_type: str = "general"
    user_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    agent_id: str | None = None
    session_id: str | None = None
    source: str = "manual"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    importance: int = 5
    visibility: str = "private"
    ttl_seconds: int | None = None
    prompt_score: int | None = None
    prompt_risk_level: str | None = None
    prompt_comments: list[str] = Field(default_factory=list)
    prompt_suggestions: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MemorySearchResult(BaseModel):
    """A memory search result with score details."""

    item: MemoryItem
    score: float
    match_type: str
    matched_terms: list[str] = Field(default_factory=list)
    ranking_reason: str = ""
    keyword_score: float = 0.0
    vector_score: float = 0.0
    fused_score: float = 0.0
    embedder_name: str = "none"


class MemoryStats(BaseModel):
    """Aggregate memory statistics."""

    total_memories: int = 0
    memories_by_type: dict[str, int] = Field(default_factory=dict)
    memories_by_source: dict[str, int] = Field(default_factory=dict)
    memories_by_user: dict[str, int] = Field(default_factory=dict)
    memories_by_workspace: dict[str, int] = Field(default_factory=dict)
    memories_by_project: dict[str, int] = Field(default_factory=dict)
    total_prompts: int = 0
    average_prompt_score: float | None = None
    low_quality_prompts: int = 0
    total_documents: int = 0
    expired_memories: int = 0
    recent_memories: int = 0
    duplicate_memories: int = 0
