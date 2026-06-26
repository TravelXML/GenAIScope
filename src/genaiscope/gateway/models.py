"""Models for GatewayClient."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GatewayResponse(BaseModel):
    """Result of GatewayClient.complete()."""

    text: str
    provider: str
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    context_health_score: int | None = None
    attempted_providers: list[str] = Field(default_factory=list)
