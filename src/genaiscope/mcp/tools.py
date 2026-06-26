"""MCP tool implementations — thin wrappers over MemoryStore.

These functions are called by the MCP server for each tool invocation.
They work against a single shared MemoryStore built at server startup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from genaiscope.memory.base import BaseMemoryStore
    from genaiscope.tracing import LocalTracer

_NO_TRACER_ERROR = {
    "error": "Tracing is not enabled on this server. Restart with --trace to use this tool."
}


def tool_memory_remember(store: BaseMemoryStore, **kwargs: Any) -> dict[str, Any]:
    item = store.add(**kwargs)
    return {"id": item.id, "memory_type": item.memory_type, "content": item.content[:120]}


def tool_memory_search(store: BaseMemoryStore, query: str, **kwargs: Any) -> dict[str, Any]:
    results = store.search(query, **kwargs)
    return {
        "results": [
            {
                "id": r.item.id,
                "content": r.item.content,
                "score": r.score,
                "match_type": r.match_type,
                "ranking_reason": r.ranking_reason,
            }
            for r in results
        ]
    }


def tool_memory_context(store: BaseMemoryStore, query: str, **kwargs: Any) -> dict[str, Any]:
    ctx = store.context(query, **kwargs)
    return {
        "query": ctx.query,
        "text": ctx.text,
        "memory_count": ctx.memory_count,
        "char_count": ctx.char_count,
        "embedder_used": ctx.embedder_used,
        "mode": ctx.mode,
    }


def tool_memory_add_prompt(store: BaseMemoryStore, prompt: str, **kwargs: Any) -> dict[str, Any]:
    item = store.add_prompt(prompt, **kwargs)
    return {
        "id": item.id,
        "prompt_score": item.prompt_score,
        "risk_level": item.prompt_risk_level,
        "comments": item.prompt_comments,
        "suggestions": item.prompt_suggestions,
    }


def tool_memory_list(store: BaseMemoryStore, **kwargs: Any) -> dict[str, Any]:
    items = store.list(**kwargs)
    return {
        "memories": [
            {"id": i.id, "content": i.content[:120], "memory_type": i.memory_type, "importance": i.importance}
            for i in items
        ]
    }


def tool_memory_stats(store: BaseMemoryStore) -> dict[str, Any]:
    stats = store.stats()
    return stats.model_dump()


def tool_doctor_diagnose(
    store: BaseMemoryStore,
    prompt: str,
    response: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    from genaiscope.context import ContextBuilder
    from genaiscope.doctor import ContextDoctor

    ctx = ContextBuilder(store).build(prompt, top_k=top_k)
    report = ContextDoctor().diagnose(
        prompt=prompt,
        response=response,
        memories_used=ctx.retrieved_memories,
        provider=provider,
        model=model,
    )
    return report.model_dump()


def tool_analytics_usage_summary(tracer: LocalTracer | None, days: int = 7) -> dict[str, Any]:
    if tracer is None:
        return dict(_NO_TRACER_ERROR)
    from genaiscope.analytics import usage_summary

    return usage_summary(tracer, days=days).model_dump()


def tool_analytics_prompt_patterns(
    store: BaseMemoryStore, tracer: LocalTracer | None, days: int = 30
) -> dict[str, Any]:
    if tracer is None:
        return dict(_NO_TRACER_ERROR)
    from genaiscope.analytics import prompt_patterns

    return prompt_patterns(store, tracer, days=days).model_dump()


def tool_report_generate(
    store: BaseMemoryStore,
    tracer: LocalTracer | None,
    out: str = "genaiscope_report.html",
    days: int = 30,
) -> dict[str, Any]:
    if tracer is None:
        return dict(_NO_TRACER_ERROR)
    from genaiscope.report import generate_html

    path = generate_html(out, memory=store, tracer=tracer, days=days)
    return {"path": str(path)}
