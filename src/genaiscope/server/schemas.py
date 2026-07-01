"""Pydantic request/response schemas for the REST API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RememberRequest(BaseModel):
    content: str
    memory_type: str = "general"
    user_id: str | None = None
    project_id: str | None = None
    workspace_id: str | None = None
    agent_id: str | None = None
    session_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    importance: int = 5
    ttl_days: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: str
    user_id: str | None = None
    project_id: str | None = None
    workspace_id: str | None = None
    memory_type: str | None = None
    limit: int = 10
    mode: str = "hybrid"


class ContextRequest(BaseModel):
    query: str
    user_id: str | None = None
    project_id: str | None = None
    workspace_id: str | None = None
    limit: int = 10
    max_chars: int | None = None
    mode: str = "hybrid"


class PromptRequest(BaseModel):
    prompt: str
    user_id: str | None = None
    project_id: str | None = None


class GatewayAskRequest(BaseModel):
    prompt: str
    provider: str = "auto"
    model: str | None = None
    user_id: str | None = None
    project_id: str | None = None
    privacy_sensitive: bool = False
    cost_sensitive: bool = False


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class SearchResultItem(BaseModel):
    id: str
    content: str
    score: float
    match_type: str
    ranking_reason: str
    memory_type: str
    keyword_score: float = 0.0
    vector_score: float = 0.0
    fused_score: float = 0.0
    embedder_name: str = "none"


class ContextResponse(BaseModel):
    query: str
    text: str
    memory_count: int
    char_count: int
    embedder_used: str
    mode: str
    memories: list[dict[str, Any]] = Field(default_factory=list)
