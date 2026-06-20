"""Semantic memory compaction — cluster and merge near-duplicate memories.

Reuses the embeddings already stored by ``BaseMemoryStore.add()`` (no extra
embedding cost) to catch paraphrased duplicates that text-based dedupe
(``genaiscope.memory.dedupe``) misses. Falls back to text-based dedupe when no
embedder/vector store is configured, so this is always safe to call.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from genaiscope.analyzers import CostAnalyzer
from genaiscope.memory.base import BaseMemoryStore
from genaiscope.memory.dedupe import find_duplicates
from genaiscope.memory.models import MemoryItem
from genaiscope.memory.utils import estimate_tokens
from genaiscope.vector.base import BaseVectorStore
from genaiscope.vector.similarity import cosine_similarity

Summarizer = Callable[[list[str]], str]

_SCOPE_FIELDS = ("user_id", "workspace_id", "project_id", "agent_id", "session_id")
_COST_MODELS = ("gpt-4", "claude-3-sonnet", "gemini-pro")


class CompactionReport(BaseModel):
    """Result of a compaction run."""

    clusters_found: int = 0
    memories_merged: int = 0
    tokens_saved: int = 0
    chars_saved: int = 0
    semantic: bool = True
    synthesis_used: bool = False
    dry_run: bool = True
    strategy: str = "synthesize"
    threshold: float = 0.92
    merged_ids: list[str] = Field(default_factory=list)
    deleted_ids: list[str] = Field(default_factory=list)
    failed_clusters: list[dict[str, Any]] = Field(default_factory=list)
    dollar_savings: dict[str, float] = Field(default_factory=dict)


def _semantic_similar(
    left: MemoryItem,
    right: MemoryItem,
    vectors: dict[str, list[float]],
    threshold: float,
) -> bool:
    if left.id == right.id:
        return True
    if left.memory_type != right.memory_type:
        return False
    if any(getattr(left, field) != getattr(right, field) for field in _SCOPE_FIELDS):
        return False
    return cosine_similarity(vectors[left.id], vectors[right.id]) >= threshold


def semantic_compaction_available(store: BaseMemoryStore) -> bool:
    """Whether the store's vector store backend supports ``get_vector``."""

    vector_store = getattr(store, "_vector_store", None)
    if vector_store is None:
        return False
    return type(vector_store).get_vector is not BaseVectorStore.get_vector


def find_semantic_duplicates(
    store: BaseMemoryStore,
    threshold: float = 0.92,
    user_id: str | None = None,
    project_id: str | None = None,
) -> list[list[MemoryItem]]:
    """Group memories whose embeddings are similar above ``threshold``.

    Returns an empty list when the store has no vector store configured, or
    the vector store doesn't support ``get_vector``. Check
    ``semantic_compaction_available(store)`` to distinguish "unavailable"
    from "ran fine, no duplicates found".
    """

    if not semantic_compaction_available(store):
        return []
    vector_store = store._vector_store  # type: ignore[attr-defined]

    items = store.list(user_id=user_id, project_id=project_id, limit=100000)

    vectors: dict[str, list[float]] = {}
    for item in items:
        try:
            vec = vector_store.get_vector(item.id)
        except Exception:
            vec = None
        if vec is not None:
            vectors[item.id] = vec

    eligible = [item for item in items if item.id in vectors]
    groups: list[list[MemoryItem]] = []
    consumed: set[str] = set()
    for anchor in eligible:
        if anchor.id in consumed:
            continue
        group = [
            candidate
            for candidate in eligible
            if candidate.id not in consumed and _semantic_similar(anchor, candidate, vectors, threshold)
        ]
        if len(group) > 1:
            groups.append(group)
            consumed.update(candidate.id for candidate in group)
    return groups


def compact_memories(
    store: BaseMemoryStore,
    *,
    strategy: str = "synthesize",
    summarizer: Summarizer | None = None,
    threshold: float = 0.92,
    dry_run: bool = True,
    user_id: str | None = None,
    project_id: str | None = None,
) -> CompactionReport:
    """Cluster near-duplicate memories and merge each cluster into one.

    strategy="synthesize" calls ``summarizer`` (if provided) to write one
    merged sentence preserving all facts in the cluster; without a summarizer
    it falls back to "keep_best" (highest importance, newest tie-break).
    """

    if strategy not in ("synthesize", "keep_best"):
        raise ValueError(f"Unknown compaction strategy: {strategy}")

    semantic = semantic_compaction_available(store)
    if semantic:
        clusters = find_semantic_duplicates(store, threshold=threshold, user_id=user_id, project_id=project_id)
    else:
        clusters = find_duplicates(store, user_id=user_id, project_id=project_id)

    report = CompactionReport(
        clusters_found=len(clusters),
        semantic=semantic,
        dry_run=dry_run,
        strategy=strategy,
        threshold=threshold,
    )

    for cluster in clusters:
        try:
            tokens_before = sum(estimate_tokens(item.content) for item in cluster)
            chars_before = sum(len(item.content) for item in cluster)
            survivor = max(cluster, key=lambda item: (item.importance, item.created_at))

            if strategy == "synthesize" and summarizer is not None:
                merged_text = summarizer([item.content for item in cluster])
                report.synthesis_used = True
            else:
                merged_text = survivor.content

            tokens_after = estimate_tokens(merged_text)
            report.tokens_saved += max(0, tokens_before - tokens_after)
            report.chars_saved += max(0, chars_before - len(merged_text))
            report.memories_merged += len(cluster) - 1

            if not dry_run:
                merged_tags = sorted(set().union(*(item.tags for item in cluster)))
                new_item = store.add(
                    merged_text,
                    memory_type=cluster[0].memory_type,
                    tags=merged_tags,
                    importance=max(item.importance for item in cluster),
                    source="compaction",
                    metadata={
                        "compacted_from": [item.id for item in cluster],
                        "compaction_strategy": strategy,
                    },
                    user_id=survivor.user_id,
                    workspace_id=survivor.workspace_id,
                    project_id=survivor.project_id,
                    agent_id=survivor.agent_id,
                    session_id=survivor.session_id,
                )
                report.merged_ids.append(new_item.id)
                for item in cluster:
                    if store.delete(item.id):
                        report.deleted_ids.append(item.id)
        except Exception as exc:
            report.failed_clusters.append({"ids": [item.id for item in cluster], "error": str(exc)})

    analyzer = CostAnalyzer()
    report.dollar_savings = {
        model: analyzer.estimate_cost(model, report.tokens_saved, 0)["total_cost"] for model in _COST_MODELS
    }
    return report
