"""Lightweight semantic cache foundation using memory search."""

from __future__ import annotations

from typing import Any

from genaiscope.cache.models import CacheHit, CacheStats
from genaiscope.memory import BaseMemoryStore, MemoryStore


class SemanticCache:
    """Local-first cache with deterministic hybrid text retrieval."""

    def __init__(self, memory_store: BaseMemoryStore | None = None, **store_kwargs: Any):
        self.memory_store = memory_store or MemoryStore(**store_kwargs)

    def set(self, prompt: str, response: str, model: str | None = None, **scopes: Any) -> str:
        """Cache one prompt-response pair."""

        item = self.memory_store.add(
            prompt, memory_type="cache", source="semantic_cache",
            metadata={"response": response, "model": model}, **scopes,
        )
        return item.id

    def get(self, prompt: str, min_score: float = 0.5, **scopes: Any) -> CacheHit | None:
        """Retrieve the closest cached prompt."""

        results = self.memory_store.search(prompt, memory_type="cache", limit=1, **scopes)
        if not results or results[0].score < min_score:
            return None
        result = results[0]
        return CacheHit(
            response=str(result.item.metadata["response"]), score=result.score,
            memory_id=result.item.id, model=result.item.metadata.get("model"),
            metadata=result.item.metadata,
        )

    def stats(self) -> CacheStats:
        return CacheStats(total_entries=len(self.memory_store.list(memory_type="cache", limit=100000)))

    def clear(self, confirm: bool = False) -> int:
        return self.memory_store.clear(confirm=confirm, memory_type="cache")
