"""MCP tool implementations — thin wrappers over MemoryStore.

These functions are called by the MCP server for each tool invocation.
They work against a single shared MemoryStore built at server startup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from genaiscope.memory.base import BaseMemoryStore


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
