"""Tests for ContextBuilder.build()."""

from pathlib import Path

from genaiscope.context import ContextBuilder
from genaiscope.memory import MemoryStore


def _store(tmp_path: Path) -> MemoryStore:
    return MemoryStore(db_path=tmp_path / "m.db")


def test_build_returns_full_result_shape(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add("Sapan prefers concise answers", memory_type="preference_memory", tags=["style"])

    result = ContextBuilder(store).build("concise answers style", top_k=5)

    assert result.original_prompt == "concise answers style"
    assert isinstance(result.retrieved_memories, list)
    assert isinstance(result.context_text, str)
    assert result.improved_prompt
    assert result.token_estimate >= 0
    assert isinstance(result.memory_ids_used, list)
    assert 0 <= result.context_quality_score <= 100
    store.close()


def test_build_respects_include_flags(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add("User prefers concise answers", memory_type="preference_memory", tags=["preference"])

    excluded = ContextBuilder(store).build("concise answers", top_k=5, include_preferences=False)
    assert excluded.retrieved_memories == []

    included = ContextBuilder(store).build("concise answers", top_k=5, include_preferences=True)
    assert any(m["memory_type"] == "preference_memory" for m in included.retrieved_memories)
    store.close()


def test_build_max_chars_truncates_context_text(tmp_path: Path) -> None:
    store = _store(tmp_path)
    for i in range(10):
        store.add(f"Memory entry number {i} with detailed content here", memory_type="general")

    result = ContextBuilder(store).build("memory entry", top_k=10, max_chars=50)
    assert len(result.context_text) <= 50
    store.close()


def test_build_no_memories_returns_empty_context(tmp_path: Path) -> None:
    store = _store(tmp_path)
    result = ContextBuilder(store).build("anything at all", top_k=5)
    assert result.retrieved_memories == []
    assert result.context_text == ""
    store.close()
