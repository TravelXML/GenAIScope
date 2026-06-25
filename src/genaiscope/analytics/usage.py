"""Token/cost/latency usage analytics over recorded traces."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from genaiscope.analytics.models import UsageSummary
from genaiscope.memory.utils import utc_now

if TYPE_CHECKING:
    from genaiscope.tracing import LocalTracer
    from genaiscope.tracing.models import TraceItem


def _category_of(trace: TraceItem) -> str:
    return str(trace.metadata.get("category") or trace.name or "uncategorized")


def usage_summary(tracer: LocalTracer, days: int = 7, limit: int = 5000) -> UsageSummary:
    """Aggregate token/cost/latency stats over the last `days` of traces."""

    cutoff = utc_now() - timedelta(days=days)
    traces = [t for t in tracer.list(limit=limit) if t.created_at >= cutoff]

    if not traces:
        return UsageSummary()

    total_input = sum(t.input_tokens for t in traces)
    total_output = sum(t.output_tokens for t in traces)
    total_cost = sum(t.estimated_cost for t in traces)
    latencies = [t.latency_ms for t in traces if t.latency_ms is not None]

    cost_by_provider: dict[str, float] = {}
    cost_by_model: dict[str, float] = {}
    tokens_by_category: dict[str, int] = {}

    for trace in traces:
        provider = trace.provider or "unknown"
        model = trace.model or "unknown"
        category = _category_of(trace)
        cost_by_provider[provider] = cost_by_provider.get(provider, 0.0) + trace.estimated_cost
        cost_by_model[model] = cost_by_model.get(model, 0.0) + trace.estimated_cost
        tokens_by_category[category] = tokens_by_category.get(category, 0) + trace.input_tokens + trace.output_tokens

    return UsageSummary(
        total_requests=len(traces),
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_tokens=total_input + total_output,
        total_estimated_cost=total_cost,
        average_latency_ms=(sum(latencies) / len(latencies)) if latencies else None,
        cost_by_provider=cost_by_provider,
        cost_by_model=cost_by_model,
        tokens_by_category=tokens_by_category,
    )
