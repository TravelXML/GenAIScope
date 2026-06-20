"""Tests for semantic memory compaction — clustering, merge strategies, and the
recall-regression guarantee against the existing eval harness."""

from pathlib import Path

from genaiscope.embeddings.local_hash import LocalHashEmbedder
from genaiscope.evals.memory_eval import compute_metrics
from genaiscope.memory.compaction import compact_memories, find_semantic_duplicates
from genaiscope.memory.factory import MemoryStore
from genaiscope.vector.local_vector import LocalVectorStore


def _store_with_embeddings(tmp_path: Path) -> MemoryStore:
    embedder = LocalHashEmbedder()
    vector_store = LocalVectorStore(db_path=tmp_path / "v.db")
    return MemoryStore(db_path=tmp_path / "m.db", embedder=embedder, vector_store=vector_store)


def test_find_semantic_duplicates_clusters_near_duplicates(tmp_path: Path) -> None:
    store = _store_with_embeddings(tmp_path)
    a = store.add("User prefers concise CTO-level answers", memory_type="preference", importance=8)
    b = store.add("User prefers concise CTO level answer", memory_type="preference", importance=5)
    store.add("Redis is the production memory backend for high-traffic apps", memory_type="general")

    groups = find_semantic_duplicates(store, threshold=0.5)
    assert len(groups) == 1
    ids = {item.id for item in groups[0]}
    assert ids == {a.id, b.id}
    store.close()


def test_compact_memories_keep_best_merges_and_deletes(tmp_path: Path) -> None:
    store = _store_with_embeddings(tmp_path)
    store.add("User prefers concise CTO-level answers", memory_type="preference", importance=8, tags=["style"])
    store.add("User prefers concise CTO level answer", memory_type="preference", importance=3, tags=["tone"])
    before_total = store.stats().total_memories

    report = compact_memories(store, strategy="keep_best", threshold=0.5, dry_run=False)

    assert report.semantic is True
    assert report.clusters_found == 1
    assert report.memories_merged == 1
    assert len(report.deleted_ids) == 2
    assert len(report.merged_ids) == 1

    after_total = store.stats().total_memories
    assert after_total == before_total - 1

    survivor = store.get(report.merged_ids[0])
    assert survivor is not None
    assert survivor.content == "User prefers concise CTO-level answers"  # higher-importance item wins
    assert set(survivor.tags) == {"style", "tone"}  # tags unioned
    assert survivor.importance == 8
    store.close()


def test_compact_memories_synthesize_uses_summarizer(tmp_path: Path) -> None:
    store = _store_with_embeddings(tmp_path)
    store.add("User prefers concise CTO-level answers", memory_type="preference")
    store.add("User prefers concise CTO level answer", memory_type="preference")

    captured: list[list[str]] = []

    def stub_summarizer(texts: list[str]) -> str:
        captured.append(texts)
        return "; ".join(texts)

    report = compact_memories(
        store, strategy="synthesize", summarizer=stub_summarizer, threshold=0.5, dry_run=False
    )

    assert report.synthesis_used is True
    assert len(captured) == 1
    survivor = store.get(report.merged_ids[0])
    assert survivor is not None
    assert "User prefers concise CTO-level answers" in survivor.content
    assert "User prefers concise CTO level answer" in survivor.content
    store.close()


def test_compact_memories_dry_run_does_not_modify_store(tmp_path: Path) -> None:
    store = _store_with_embeddings(tmp_path)
    store.add("User prefers concise CTO-level answers", memory_type="preference")
    store.add("User prefers concise CTO level answer", memory_type="preference")
    before_total = store.stats().total_memories

    report = compact_memories(store, strategy="keep_best", threshold=0.5, dry_run=True)

    assert report.dry_run is True
    assert report.memories_merged == 1
    assert report.merged_ids == []
    assert report.deleted_ids == []
    assert store.stats().total_memories == before_total
    store.close()


def test_compact_memories_falls_back_to_text_dedupe_without_embedder(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")  # no embedder/vector store configured
    store.add("User prefers concise answers", memory_type="preference")
    store.add("User prefers concise answers", memory_type="preference")  # exact text duplicate

    report = compact_memories(store, strategy="keep_best", dry_run=False)

    assert report.semantic is False
    assert report.clusters_found == 1
    assert report.memories_merged == 1
    store.close()


def test_compact_memories_isolates_failed_clusters(tmp_path: Path) -> None:
    store = _store_with_embeddings(tmp_path)
    store.add("User prefers concise CTO-level answers", memory_type="preference")
    store.add("User prefers concise CTO level answer", memory_type="preference")

    def failing_summarizer(texts: list[str]) -> str:
        raise RuntimeError("boom")

    report = compact_memories(
        store, strategy="synthesize", summarizer=failing_summarizer, threshold=0.5, dry_run=False
    )

    assert len(report.failed_clusters) == 1
    assert report.merged_ids == []
    assert report.deleted_ids == []
    store.close()


def test_compaction_does_not_regress_recall(tmp_path: Path) -> None:
    """The core proof point: compaction must not hurt retrieval quality."""

    store = _store_with_embeddings(tmp_path)
    near_dup_a = store.add("User prefers concise CTO-level answers", memory_type="preference", importance=8)
    near_dup_b = store.add("User prefers concise CTO level answer", memory_type="preference", importance=5)
    unrelated = store.add("Redis is the production memory backend for high-traffic apps", memory_type="general")

    queries = {
        "how should I answer the user": [near_dup_a.id, near_dup_b.id],
        "Redis backend usage": [unrelated.id],
    }

    def recall_for(store) -> float:
        results_per_query = [
            [r.item.id for r in store.search(q, limit=5, mode="hybrid")] for q in queries
        ]
        expected_per_query = list(queries.values())
        recall, _, _ = compute_metrics(results_per_query, expected_per_query, top_k=5)
        return recall

    recall_before = recall_for(store)

    report = compact_memories(store, strategy="keep_best", threshold=0.5, dry_run=False)
    assert report.memories_merged == 1
    assert store.stats().total_memories == 2  # 3 seeds minus 1 merged duplicate

    # The merged-away ids no longer exist; re-derive expected ids against the new store state.
    queries["how should I answer the user"] = [item.id for item in store.list(limit=10) if item.source == "compaction"]
    recall_after = recall_for(store)

    assert recall_after >= recall_before
    store.close()
