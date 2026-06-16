"""Semantic cache — embedding similarity when available, deterministic text fallback."""

from __future__ import annotations

import contextlib
import math
from typing import Any

from genaiscope.cache.models import CacheHit, CacheStats
from genaiscope.embeddings.base import BaseEmbedder
from genaiscope.memory import BaseMemoryStore, MemoryStore


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


class SemanticCache:
    """Local-first cache with embedding similarity (deterministic fallback)."""

    def __init__(
        self,
        memory_store: BaseMemoryStore | None = None,
        embedder: BaseEmbedder | None = None,
        similarity_threshold: float = 0.92,
        **store_kwargs: Any,
    ):
        self.memory_store = memory_store or MemoryStore(**store_kwargs)
        self._embedder = embedder
        self.similarity_threshold = similarity_threshold

        # build an in-memory embedding index for cache entries (keyed by memory id)
        self._embedding_index: dict[str, list[float]] = {}

    def set(self, prompt: str, response: str, model: str | None = None, **scopes: Any) -> str:
        """Cache one prompt-response pair."""
        item = self.memory_store.add(
            prompt, memory_type="cache", source="semantic_cache",
            metadata={"response": response, "model": model}, **scopes,
        )
        if self._embedder:
            with contextlib.suppress(Exception):
                self._embedding_index[item.id] = self._embedder.embed(prompt)
        return item.id

    def get(self, prompt: str, min_score: float = 0.5, **scopes: Any) -> CacheHit | None:
        """Retrieve the closest cached prompt."""

        if self._embedder and self._embedding_index:
            try:
                q_vec = self._embedder.embed(prompt)
                best_id: str | None = None
                best_score = -1.0
                for mid, stored_vec in self._embedding_index.items():
                    s = _cosine(q_vec, stored_vec)
                    if s > best_score:
                        best_score = s
                        best_id = mid
                if best_id and best_score >= self.similarity_threshold:
                    item = self.memory_store.get(best_id)
                    if item and item.metadata.get("response"):
                        return CacheHit(
                            response=str(item.metadata["response"]),
                            score=best_score,
                            memory_id=best_id,
                            model=item.metadata.get("model"),
                            metadata=item.metadata,
                        )
            except Exception:
                pass

        # deterministic fallback
        results = self.memory_store.search(prompt, memory_type="cache", limit=1, **scopes)
        if not results or results[0].score < min_score:
            return None
        result = results[0]
        return CacheHit(
            response=str(result.item.metadata["response"]),
            score=result.score,
            memory_id=result.item.id,
            model=result.item.metadata.get("model"),
            metadata=result.item.metadata,
        )

    def stats(self) -> CacheStats:
        return CacheStats(
            total_entries=len(self.memory_store.list(memory_type="cache", limit=100000))
        )

    def clear(self, confirm: bool = False) -> int:
        self._embedding_index.clear()
        return self.memory_store.clear(confirm=confirm, memory_type="cache")
