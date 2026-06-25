"""Models for the model router recommendation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RouterRecommendation(BaseModel):
    """Result of router.recommend()."""

    recommended_model_type: str
    reason: str
    suggested_providers: list[str] = Field(default_factory=list)
    cost_sensitivity: str = "medium"
