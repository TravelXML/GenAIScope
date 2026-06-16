"""Tests for memory vector + hybrid search and degrade path."""

import tempfile
from pathlib import Path

import pytest

from genaiscope.embeddings.local_hash import LocalHashEmbedder
from genaiscope.memory.factory import MemoryStore
from genaiscope.vector.local_vector import LocalVectorStore


def _make_store(tmp_path: Path, with_embedder: bool = True):
    emb = LocalHashEmbedder() if with_embedder else None
    vs = LocalVectorStore(db_path=tmp_path / "v.db") if with_embedder else None
    return MemoryStore(db_path=tmp_path / "m.db", embedder=emb, vector_store=vs)


def test_add_creates_vector(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    item = store.add("User prefers concise answers", importance=8)
    assert item.id
    assert store._vector_store.count() == 1  # type: ignore[attr-defined]
    store.close()


def test_hybrid_search_with_embedder(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    store.add("User prefers concise answers and clear style", memory_type="preference", importance=8)
    store.add("Redis is the production backend", memory_type="general")
    results = store.search("concise answers style preference", mode="hybrid")
    assert len(results) > 0
    top = results[0]
    assert top.fused_score > 0
    store.close()


def test_vector_mode(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    store.add("Sapan prefers bullet points for feature lists", memory_type="preference")
    results = store.search("feature list format", mode="vector")
    assert len(results) > 0
    assert results[0].vector_score > 0
    store.close()


def test_search_without_embedder_degrades(tmp_path: Path) -> None:
    """Hybrid/vector modes fall back to keyword when no embedder."""
    store = _make_store(tmp_path, with_embedder=False)
    store.add("Answer in bullets", memory_type="preference")
    results = store.search("bullets", mode="hybrid")
    assert len(results) > 0
    assert all(r.vector_score == 0.0 for r in results)
    store.close()


def test_delete_removes_vector(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    item = store.add("some content")
    assert store._vector_store.count() == 1  # type: ignore[attr-defined]
    store.delete(item.id)
    assert store._vector_store.count() == 0  # type: ignore[attr-defined]
    store.close()


def test_search_result_has_new_fields(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    store.add("concise answers", memory_type="preference", importance=7)
    results = store.search("concise", mode="hybrid")
    assert results
    r = results[0]
    assert hasattr(r, "vector_score")
    assert hasattr(r, "keyword_score")
    assert hasattr(r, "fused_score")
    assert hasattr(r, "embedder_name")
    assert r.embedder_name != ""
    store.close()
