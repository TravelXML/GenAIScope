"""In-process SQLite-backed vector store with pure-Python cosine search.

Uses numpy when available for speed; falls back to pure Python.
"""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any

from genaiscope.memory.utils import default_db_path, ensure_parent
from genaiscope.vector.base import BaseVectorStore
from genaiscope.vector.models import VectorMatch


def _cosine_score(a: list[float], b: list[float]) -> float:
    """Pure-Python cosine similarity for pre-normalized vectors."""
    try:
        import numpy as np  # type: ignore[import-not-found]

        return float(np.dot(a, b))
    except ImportError:
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (na * nb)


class LocalVectorStore(BaseVectorStore):
    """SQLite-persisted vector store with in-process cosine search."""

    def __init__(self, db_path: str | Path | None = None, table: str = "vectors") -> None:
        self.db_path = Path(db_path) if db_path else default_db_path().with_suffix(".vectors.db")
        ensure_parent(self.db_path)
        self._table = table
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self._conn.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                vector_id TEXT PRIMARY KEY,
                vector    TEXT NOT NULL,
                metadata  TEXT NOT NULL DEFAULT '{{}}'
            );
            """
        )
        self._conn.commit()

    def upsert(self, vector_id: str, vector: list[float], metadata: dict) -> None:
        self._conn.execute(
            f"INSERT OR REPLACE INTO {self._table} (vector_id, vector, metadata) VALUES (?, ?, ?)",
            (vector_id, json.dumps(vector), json.dumps(metadata)),
        )
        self._conn.commit()

    def query(
        self,
        vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        rows = self._conn.execute(
            f"SELECT vector_id, vector, metadata FROM {self._table}"
        ).fetchall()

        scored: list[VectorMatch] = []
        for row in rows:
            meta: dict[str, Any] = json.loads(row["metadata"])
            if filters and not all(meta.get(k) == v for k, v in filters.items() if v is not None):
                continue
            vec: list[float] = json.loads(row["vector"])
            score = _cosine_score(vector, vec)
            scored.append(VectorMatch(vector_id=row["vector_id"], score=score, metadata=meta))

        return sorted(scored, key=lambda m: m.score, reverse=True)[:top_k]

    def delete(self, vector_id: str) -> bool:
        cursor = self._conn.execute(
            f"DELETE FROM {self._table} WHERE vector_id = ?", (vector_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def count(self) -> int:
        return self._conn.execute(f"SELECT COUNT(*) FROM {self._table}").fetchone()[0]
