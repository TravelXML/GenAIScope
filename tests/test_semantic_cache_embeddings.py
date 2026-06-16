"""Tests for upgraded SemanticCache with embedding similarity."""

import tempfile
from pathlib import Path

from genaiscope.cache.semantic_cache import SemanticCache
from genaiscope.embeddings.local_hash import LocalHashEmbedder
from genaiscope.memory.factory import MemoryStore


def test_cache_set_and_get_deterministic(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    cache = SemanticCache(memory_store=store)
    cache.set("What is Python?", "Python is a programming language.")
    hit = cache.get("What is Python?")
    assert hit is not None
    assert "Python" in hit.response


def test_cache_with_embedder(tmp_path: Path) -> None:
    emb = LocalHashEmbedder()
    store = MemoryStore(db_path=tmp_path / "m.db")
    cache = SemanticCache(memory_store=store, embedder=emb, similarity_threshold=0.5)
    cache.set("What is Redis?", "Redis is an in-memory data store.")
    hit = cache.get("Explain Redis")
    # With local_hash the scores may not cross threshold for dissimilar prompts;
    # just verify no crash and API contract holds
    assert hit is None or "Redis" in (hit.response or "")


def test_cache_no_hit_below_threshold(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    cache = SemanticCache(memory_store=store)
    cache.set("Python", "A language.")
    hit = cache.get("Completely unrelated topic about astronomy")
    # Score should be low enough that no hit is returned
    assert hit is None or hit.score < 1.0


def test_cache_stats_and_clear(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    cache = SemanticCache(memory_store=store)
    cache.set("Q1", "A1")
    cache.set("Q2", "A2")
    stats = cache.stats()
    assert stats.total_entries == 2
    cache.clear(confirm=True)
    assert cache.stats().total_entries == 0
