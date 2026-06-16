"""Tests for LocalVectorStore — always runs."""

import tempfile
from pathlib import Path

import pytest

from genaiscope.vector.local_vector import LocalVectorStore


def _unit_vec(dim: int = 4, idx: int = 0) -> list[float]:
    v = [0.0] * dim
    v[idx] = 1.0
    return v


def test_upsert_and_count(tmp_path: Path) -> None:
    store = LocalVectorStore(db_path=tmp_path / "v.db")
    store.upsert("a", _unit_vec(idx=0), {"user_id": "u1"})
    store.upsert("b", _unit_vec(idx=1), {"user_id": "u2"})
    assert store.count() == 2


def test_query_top_k(tmp_path: Path) -> None:
    store = LocalVectorStore(db_path=tmp_path / "v.db")
    store.upsert("a", _unit_vec(idx=0), {})
    store.upsert("b", _unit_vec(idx=1), {})
    store.upsert("c", _unit_vec(idx=2), {})
    results = store.query(_unit_vec(idx=0), top_k=2)
    assert len(results) == 2
    assert results[0].vector_id == "a"
    assert results[0].score > 0.9


def test_query_filters(tmp_path: Path) -> None:
    store = LocalVectorStore(db_path=tmp_path / "v.db")
    store.upsert("a", _unit_vec(idx=0), {"user_id": "alice"})
    store.upsert("b", _unit_vec(idx=0), {"user_id": "bob"})
    results = store.query(_unit_vec(idx=0), top_k=10, filters={"user_id": "alice"})
    ids = {r.vector_id for r in results}
    assert "a" in ids
    assert "b" not in ids


def test_delete(tmp_path: Path) -> None:
    store = LocalVectorStore(db_path=tmp_path / "v.db")
    store.upsert("x", _unit_vec(idx=0), {})
    assert store.count() == 1
    assert store.delete("x") is True
    assert store.count() == 0
    assert store.delete("x") is False


def test_upsert_replace(tmp_path: Path) -> None:
    store = LocalVectorStore(db_path=tmp_path / "v.db")
    store.upsert("dup", _unit_vec(idx=0), {"v": 1})
    store.upsert("dup", _unit_vec(idx=1), {"v": 2})
    assert store.count() == 1
    results = store.query(_unit_vec(idx=1), top_k=1)
    assert results[0].vector_id == "dup"
