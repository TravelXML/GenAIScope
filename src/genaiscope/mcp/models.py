"""MCP tool request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MemoryRememberRequest(BaseModel):
    content: str
    user_id: str | None = None
    project_id: str | None = None
    workspace_id: str | None = None
    memory_type: str = "general"
    tags: list[str] = Field(default_factory=list)
    importance: int = 5
    ttl_days: int | None = None


class MemorySearchRequest(BaseModel):
    query: str
    user_id: str | None = None
    project_id: str | None = None
    workspace_id: str | None = None
    memory_type: str | None = None
    tags: list[str] = Field(default_factory=list)
    limit: int = 10
    mode: str = "hybrid"


class MemoryContextRequest(BaseModel):
    query: str
    user_id: str | None = None
    project_id: str | None = None
    workspace_id: str | None = None
    limit: int = 10
    max_chars: int | None = None


class MemoryListRequest(BaseModel):
    user_id: str | None = None
    project_id: str | None = None
    memory_type: str | None = None
    limit: int = 20
