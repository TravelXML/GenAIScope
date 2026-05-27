"""Tests for local memory search."""

from genaiscope.memory import MemoryStore


def test_memory_search_filters_and_ranking(tmp_path):
    store = MemoryStore(db_path=tmp_path / "memory.db")
    store.add("User prefers concise answers.", memory_type="preference", user_id="u1")
    store.add("Project uses SQLite for local memory.", memory_type="project", user_id="u2")

    results = store.search("concise answers", user_id="u1")
    assert results
    assert results[0].item.user_id == "u1"
    assert store.search("SQLite", memory_type="project")[0].item.memory_type == "project"
    assert store.search("not-present") == []
    store.close()
