"""Tests for cross-encoder reranking -- real model, no network mocking needed
(downloads/caches `cross-encoder/ms-marco-MiniLM-L-6-v2` on first use)."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from genaiscope.core.errors import EmbeddingBackendError
from genaiscope.memory.factory import MemoryStore
from genaiscope.memory.models import MemoryItem, MemorySearchResult
from genaiscope.memory.rerank import CrossEncoderReranker


def _candidate(content: str, fused_score: float) -> MemorySearchResult:
    now = datetime.now(UTC)
    item = MemoryItem(id=str(uuid4()), content=content, memory_type="general", created_at=now, updated_at=now)
    return MemorySearchResult(item=item, score=fused_score, match_type="keyword", fused_score=fused_score)


def test_cross_encoder_missing_raises() -> None:
    try:
        import sentence_transformers  # noqa: F401

        pytest.skip("sentence-transformers is installed — skip missing-dep test")
    except ImportError:
        with pytest.raises(EmbeddingBackendError, match="sentence-transformers"):
            CrossEncoderReranker()


def test_rerank_reorders_by_relevance() -> None:
    pytest.importorskip("sentence_transformers")
    candidates = [
        _candidate("The weather today is sunny with a light breeze.", fused_score=0.5),
        _candidate("Python is a popular programming language for data science.", fused_score=0.5),
    ]

    results = CrossEncoderReranker().rerank("What programming language is good for data science?", candidates, top_k=2)

    assert len(results) == 2
    assert "Python" in results[0].item.content
    assert all(r.ranking_reason == "cross_encoder_rerank" for r in results)


def test_rerank_respects_top_k() -> None:
    pytest.importorskip("sentence_transformers")
    candidates = [_candidate(f"memory number {i}", fused_score=0.1 * i) for i in range(5)]

    results = CrossEncoderReranker().rerank("memory", candidates, top_k=2)

    assert len(results) == 2


def test_rerank_empty_candidates_returns_empty() -> None:
    pytest.importorskip("sentence_transformers")
    assert CrossEncoderReranker().rerank("anything", [], top_k=5) == []


def test_memory_store_search_with_rerank(tmp_path: Path) -> None:
    pytest.importorskip("sentence_transformers")
    store = MemoryStore(db_path=tmp_path / "m.db")
    store.add("Python is great for data science and machine learning", memory_type="general")
    store.add("The weather is sunny today", memory_type="general")

    results = store.search("data science programming", mode="hybrid", limit=1, rerank=True)

    assert len(results) == 1
    assert results[0].ranking_reason == "cross_encoder_rerank"
    store.close()
