"""Dashboard recommendation heuristics."""

from __future__ import annotations

from collections import Counter

from genaiscope.memory import MemoryItem, MemoryStats
from genaiscope.tracing import TraceItem, TraceStats


def generate_recommendations(
    memory_stats: MemoryStats,
    memories: list[MemoryItem],
    trace_stats: TraceStats,
    traces: list[TraceItem],
) -> list[str]:
    """Generate local heuristic recommendations."""

    recommendations: list[str] = []
    if memory_stats.low_quality_prompts:
        recommendations.append("Review prompts with scores below 60 and add clearer constraints.")
    if any(item.memory_type == "prompt" and not item.prompt_suggestions for item in memories):
        recommendations.append("Add output format and success criteria to vague prompts.")
    if any(not item.tags for item in memories):
        recommendations.append("Add tags to untagged memories to improve retrieval.")
    if traces and any((trace.latency_ms or 0) > 3000 for trace in traces):
        recommendations.append(
            "Review high-latency traces and consider smaller prompts or caching."
        )
    repeated = [
        name for name, count in Counter(trace.name for trace in traces).items() if count > 1
    ]
    if repeated:
        recommendations.append("Consider caching repeated trace names to reduce cost and latency.")
    if memory_stats.expired_memories:
        recommendations.append("Remove expired memories to keep local context clean.")
    if memory_stats.total_documents and any(
        not item.metadata for item in memories if item.memory_type == "document"
    ):
        recommendations.append("Add structured metadata to document chunks.")
    if trace_stats.total_estimated_cost > 0:
        recommendations.append("Monitor highest-cost traces before moving workflows to production.")
    return recommendations or [
        "Local data looks healthy. Add more prompts, files, and traces for richer insights."
    ]
