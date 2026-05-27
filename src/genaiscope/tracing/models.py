"""Models for local tracing."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TraceItem(BaseModel):
    """A recorded local trace."""

    id: str
    name: str
    input_text: str | None = None
    output_text: str | None = None
    model: str | None = None
    provider: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: float | None = None
    status: str = "success"
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TraceStats(BaseModel):
    """Aggregate trace statistics."""

    total_traces: int = 0
    success_count: int = 0
    error_count: int = 0
    total_estimated_cost: float = 0.0
    average_latency_ms: float | None = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    traces_by_model: dict[str, int] = Field(default_factory=dict)
    traces_by_provider: dict[str, int] = Field(default_factory=dict)
