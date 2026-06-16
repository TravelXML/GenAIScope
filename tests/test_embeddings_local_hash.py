"""Tests for LocalHashEmbedder — always runs, no deps."""

import math

from genaiscope.embeddings.local_hash import LocalHashEmbedder


def _l2_norm(vec: list[float]) -> float:
    return math.sqrt(sum(x * x for x in vec))


def test_dimensions_default() -> None:
    emb = LocalHashEmbedder()
    assert emb.dimensions == 256
    vec = emb.embed("hello world")
    assert len(vec) == 256


def test_dimensions_custom() -> None:
    emb = LocalHashEmbedder(dimensions=64)
    vec = emb.embed("test")
    assert len(vec) == 64


def test_normalized() -> None:
    emb = LocalHashEmbedder()
    vec = emb.embed("GenAIScope memory toolkit")
    norm = _l2_norm(vec)
    assert abs(norm - 1.0) < 1e-6


def test_deterministic() -> None:
    emb = LocalHashEmbedder()
    text = "User prefers concise CTO-level answers"
    v1 = emb.embed(text)
    v2 = emb.embed(text)
    assert v1 == v2


def test_different_texts_differ() -> None:
    emb = LocalHashEmbedder()
    v1 = emb.embed("apple pie")
    v2 = emb.embed("redis vector search")
    assert v1 != v2


def test_embed_batch() -> None:
    emb = LocalHashEmbedder()
    texts = ["alpha", "beta", "gamma"]
    batch = emb.embed_batch(texts)
    singles = [emb.embed(t) for t in texts]
    assert batch == singles


def test_empty_text() -> None:
    emb = LocalHashEmbedder()
    vec = emb.embed("")
    assert len(vec) == 256
