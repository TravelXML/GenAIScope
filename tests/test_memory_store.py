"""Tests for local memory store."""

from genaiscope.memory import MemoryStore


def test_memory_store_crud_and_stats(tmp_path):
    store = MemoryStore(db_path=tmp_path / "memory.db")
    item = store.add(
        "User prefers concise CTO-level answers.",
        memory_type="preference",
        user_id="sapan",
        tags=["Style", "style"],
        metadata={"source": "test"},
    )

    assert store.get(item.id) == item
    assert store.list(user_id="sapan")[0].tags == ["style"]
    assert store.stats().total_memories == 1
    assert store.stats().memories_by_type["preference"] == 1
    assert store.delete(item.id) is True
    assert store.clear(confirm=True) == 0
    store.close()
