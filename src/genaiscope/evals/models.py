"""Models for the memory retrieval eval harness."""

from __future__ import annotations

from typing import Any

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


class AgentStep(BaseModel):
    """One step of an `AgentTrajectory` -- a single tool/action call."""

    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    expected_output: str | None = None


class AgentTrajectory(BaseModel):
    """A multi-step task an agent is expected to carry out."""

    task: str
    steps: list[AgentStep] = Field(default_factory=list)


class AgentStepResult(BaseModel):
    name: str
    passed: bool
    actual_output: str = ""
    latency_ms: float = 0.0
    error: str | None = None


class AgentEvalReport(BaseModel):
    task: str
    task_id: str
    steps_total: int = 0
    steps_passed: int = 0
    step_completion_rate: float = 0.0
    total_latency_ms: float = 0.0
    step_results: list[AgentStepResult] = Field(default_factory=list)
