"""Models for Context Doctor diagnosis reports."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DiagnosisReport(BaseModel):
    """A Context Doctor health report for one prompt/response interaction."""

    context_health_score: int = 0
    prompt_clarity_score: int = 0
    context_completeness_score: int = 0
    memory_match_score: int = 0
    model_fit_score: int = 0
    token_efficiency_score: int = 0
    hallucination_risk_score: int = 0
    answer_specificity_score: int = 0
    missing_context: list[str] = Field(default_factory=list)
    detected_entities: list[str] = Field(default_factory=list)
    detected_intent: str = "general_request"
    prompt_issues: list[str] = Field(default_factory=list)
    recommended_prompt: str = ""
    recommended_model_type: str = "writing"
    improvement_tips: list[str] = Field(default_factory=list)
