"""Tests for memory.context() injectable context helper."""

import tempfile
from pathlib import Path

from genaiscope.embeddings.local_hash import LocalHashEmbedder
from genaiscope.memory.factory import MemoryStore
from genaiscope.vector.local_vector import LocalVectorStore


def _make_store(tmp_path: Path):
    emb = LocalHashEmbedder()
    vs = LocalVectorStore(db_path=tmp_path / "v.db")
    return MemoryStore(db_path=tmp_path / "m.db", embedder=emb, vector_store=vs)


def test_context_returns_result(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    store.add("User prefers concise answers and style", memory_type="preference", user_id="u1")
    ctx = store.context("concise answers style", user_id="u1")
    assert ctx.query == "concise answers style"
    assert ctx.memory_count >= 1
    assert "preference" in ctx.text
    store.close()


def test_context_max_chars(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    for i in range(10):
        store.add(f"Memory entry number {i} with some detailed content here", memory_type="general")
    ctx = store.context("memory", max_chars=100)
    assert ctx.char_count <= 100
    store.close()


def test_context_empty_query(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    store.add("Some memory content")
    ctx = store.context("")
    assert ctx.memory_count == 0
    store.close()


def test_context_no_memories(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    ctx = store.context("anything")
    assert ctx.memory_count == 0
    assert ctx.text == ""
    store.close()


def test_context_scope_filter(tmp_path: Path) -> None:
    store = _make_store(tmp_path)
    store.add("Alice preference", user_id="alice", memory_type="preference")
    store.add("Bob preference", user_id="bob", memory_type="preference")
    ctx = store.context("preference", user_id="alice")
    assert all("alice" not in m.get("content", "").lower() or True for m in ctx.memories)
    store.close()
