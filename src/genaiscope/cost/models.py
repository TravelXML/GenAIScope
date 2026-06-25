"""Models for CostEstimator."""

from __future__ import annotations

from pydantic import BaseModel


class CostEstimate(BaseModel):
    """Result of CostEstimator.estimate()."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    priced: bool = True
