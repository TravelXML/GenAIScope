"""Models for the memory retrieval eval harness."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvalQuery(BaseModel):
    query: str
    expected_ids: list[str] = Field(default_factory=list)


class EvalSeed(BaseModel):
    id: str
    content: str
    memory_type: str = "general"
    tags: list[str] = Field(default_factory=list)
    importance: int = 5


class EvalDataset(BaseModel):
    seeds: list[EvalSeed] = Field(default_factory=list)
    queries: list[EvalQuery] = Field(default_factory=list)


class ModeEvalResult(BaseModel):
    mode: str
    embedder: str = "none"
    recall_at_k: float
    precision_at_k: float
    mrr: float
    queries_evaluated: int
    top_k: int


class EvalReport(BaseModel):
    results: list[ModeEvalResult] = Field(default_factory=list)
    dataset_size: int = 0
    top_k: int = 5
