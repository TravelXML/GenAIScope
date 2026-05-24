"""Data models for GenAIScope."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Provider(str, Enum):
    """Supported AI providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    CUSTOM = "custom"


class ScopeConfig(BaseModel):
    """Configuration for GenAIScope."""

    provider: Provider = Provider.OPENAI
    api_key: Optional[str] = None
    model: str = "gpt-4"
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 30
    retries: int = 3

    class Config:
        """Pydantic config."""

        extra = "allow"


class EvaluationResult(BaseModel):
    """Result of an evaluation."""

    score: float = Field(ge=0.0, le=1.0)
    label: str
    reasoning: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InspectionReport(BaseModel):
    """Report from inspection."""

    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    title: str
    description: str
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    evaluations: List[EvaluationResult] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> str:
        """Get a text summary of the report."""
        lines = [f"# {self.title}", f"\n{self.description}", f"\nTimestamp: {self.timestamp}"]

        if self.evaluations:
            lines.append("\n## Evaluations")
            for eval_result in self.evaluations:
                lines.append(f"  - {eval_result.label}: {eval_result.score:.2f}")
                lines.append(f"    Reasoning: {eval_result.reasoning}")

        if self.metrics:
            lines.append("\n## Metrics")
            for key, value in self.metrics.items():
                lines.append(f"  - {key}: {value}")

        if self.warnings:
            lines.append("\n## Warnings")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        if self.errors:
            lines.append("\n## Errors")
            for error in self.errors:
                lines.append(f"  - {error}")

        return "\n".join(lines)
