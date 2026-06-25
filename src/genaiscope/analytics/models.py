"""Models for usage analytics and prompt pattern analysis."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UsageSummary(BaseModel):
    """Result of analytics.usage_summary()."""

    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_estimated_cost: float = 0.0
    average_latency_ms: float | None = None
    cost_by_provider: dict[str, float] = Field(default_factory=dict)
    cost_by_model: dict[str, float] = Field(default_factory=dict)
    tokens_by_category: dict[str, int] = Field(default_factory=dict)


class PromptPatterns(BaseModel):
    """Result of analytics.prompt_patterns()."""

    top_topics: list[str] = Field(default_factory=list)
    repeated_weak_patterns: list[str] = Field(default_factory=list)
    best_prompt_templates: list[str] = Field(default_factory=list)
    most_used_entities: list[str] = Field(default_factory=list)
    most_used_tags: list[str] = Field(default_factory=list)
    most_frequent_categories: list[str] = Field(default_factory=list)
    average_health_score_by_category: dict[str, float] = Field(default_factory=dict)
    token_usage_by_category: dict[str, int] = Field(default_factory=dict)
    model_performance_by_category: dict[str, dict[str, Any]] = Field(default_factory=dict)
