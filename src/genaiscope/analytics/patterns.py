"""Repeated prompt-pattern analysis over historical traces and memories.

Reads the `category`/`tags`/`context_health_score`/`missing_context` fields
that GenAIScope.trace()/log_interaction() persist into trace metadata (see
core/scope.py) -- no separate pattern-storage table needed.
"""

from __future__ import annotations

from collections import Counter
from datetime import timedelta
from typing import TYPE_CHECKING

from genaiscope.analytics.models import PromptPatterns
from genaiscope.memory.utils import utc_now

if TYPE_CHECKING:
    from genaiscope.memory import BaseMemoryStore
    from genaiscope.tracing import LocalTracer

_WEAK_HEALTH_THRESHOLD = 60


def prompt_patterns(
    memory: BaseMemoryStore | None,
    tracer: LocalTracer,
    days: int = 30,
    limit: int = 5000,
) -> PromptPatterns:
    """Summarize repeated prompt/category patterns over the last `days`."""

    cutoff = utc_now() - timedelta(days=days)
    traces = [t for t in tracer.list(limit=limit) if t.created_at >= cutoff]

    category_counter: Counter[str] = Counter()
    tag_counter: Counter[str] = Counter()
    health_by_category: dict[str, list[int]] = {}
    tokens_by_category: dict[str, int] = {}
    model_by_category: dict[str, Counter[str]] = {}
    missing_context_counter: Counter[str] = Counter()
    entity_counter: Counter[str] = Counter()

    for trace in traces:
        category = str(trace.metadata.get("category") or trace.name or "uncategorized")
        category_counter[category] += 1
        for tag in trace.metadata.get("tags", []) or []:
            tag_counter[tag] += 1
        for item in trace.metadata.get("missing_context", []) or []:
            missing_context_counter[f"Prompts missing: {item}"] += 1
        for entity in trace.metadata.get("detected_entities", []) or []:
            entity_counter[entity] += 1

        score = trace.metadata.get("context_health_score")
        if isinstance(score, (int, float)):
            health_by_category.setdefault(category, []).append(int(score))

        tokens_by_category[category] = (
            tokens_by_category.get(category, 0) + trace.input_tokens + trace.output_tokens
        )
        model_by_category.setdefault(category, Counter())[trace.model or "unknown"] += 1

    average_health = {
        category: round(sum(scores) / len(scores), 1) for category, scores in health_by_category.items()
    }

    repeated_weak_patterns = [desc for desc, count in missing_context_counter.most_common(5) if count >= 2]
    if not repeated_weak_patterns:
        repeated_weak_patterns = [
            f"{category} prompts average a low health score ({score})"
            for category, score in average_health.items()
            if score < _WEAK_HEALTH_THRESHOLD
        ]

    best_categories = [c for c, s in sorted(average_health.items(), key=lambda kv: -kv[1]) if s >= _WEAK_HEALTH_THRESHOLD]
    best_prompt_templates = [
        f"Using my background in {{profile}}, answer questions in the '{category}' category "
        "with explicit audience, length, and tone."
        for category in best_categories[:3]
    ]

    model_performance_by_category = {
        category: dict(counts) for category, counts in model_by_category.items()
    }

    return PromptPatterns(
        top_topics=[category for category, _ in category_counter.most_common(10)],
        repeated_weak_patterns=repeated_weak_patterns,
        best_prompt_templates=best_prompt_templates,
        most_used_entities=[entity for entity, _ in entity_counter.most_common(10)],
        most_used_tags=[tag for tag, _ in tag_counter.most_common(10)],
        most_frequent_categories=[category for category, _ in category_counter.most_common(5)],
        average_health_score_by_category=average_health,
        token_usage_by_category=tokens_by_category,
        model_performance_by_category=model_performance_by_category,
    )
