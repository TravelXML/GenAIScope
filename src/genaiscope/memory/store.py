"""SQLite-backed local memory store."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any

from genaiscope.memory.models import MemoryItem, MemorySearchResult, MemoryStats
from genaiscope.memory.prompt_quality import analyze_prompt_quality
from genaiscope.memory.search import search_memories
from genaiscope.memory.utils import (
    default_db_path,
    ensure_parent,
    iso_now,
    json_dumps,
    json_loads,
    normalize_memory_type,
    normalize_tags,
    parse_datetime,
    utc_now,
)


class MemoryStore:
    """Local SQLite memory store."""

    def __init__(self, db_path: str | Path | None = None, auto_create: bool = True):
        self.db_path = Path(db_path) if db_path else default_db_path()
        ensure_parent(self.db_path)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        if auto_create:
            self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL DEFAULT 'general',
                user_id TEXT,
                source TEXT DEFAULT 'manual',
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                search_text TEXT,
                prompt_score INTEGER,
                prompt_risk_level TEXT,
                prompt_comments TEXT DEFAULT '[]',
                prompt_suggestions TEXT DEFAULT '[]',
                expires_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
            CREATE INDEX IF NOT EXISTS idx_memories_memory_type ON memories(memory_type);
            CREATE INDEX IF NOT EXISTS idx_memories_source ON memories(source);
            CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at);
            CREATE INDEX IF NOT EXISTS idx_memories_expires_at ON memories(expires_at);
            """
        )
        self.connection.commit()

    def add(
        self,
        content: str,
        memory_type: str = "general",
        user_id: str | None = None,
        source: str = "manual",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        ttl_days: int | None = None,
    ) -> MemoryItem:
        """Add a memory item."""

        if not content.strip():
            raise ValueError("content must not be empty")
        now = iso_now()
        expires_at = (utc_now() + timedelta(days=ttl_days)).isoformat() if ttl_days else None
        clean_tags = normalize_tags(tags)
        clean_type = normalize_memory_type(memory_type)
        item_id = str(uuid.uuid4())
        prompt_score = None
        prompt_risk_level = None
        prompt_comments: list[str] = []
        prompt_suggestions: list[str] = []

        if clean_type == "prompt":
            report = analyze_prompt_quality(content)
            prompt_score = report.score
            prompt_risk_level = report.risk_level
            prompt_comments = report.comments
            prompt_suggestions = report.improvement_suggestions

        self.connection.execute(
            """
            INSERT INTO memories (
                id, content, memory_type, user_id, source, tags, metadata, search_text,
                prompt_score, prompt_risk_level, prompt_comments, prompt_suggestions,
                expires_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                content,
                clean_type,
                user_id,
                source,
                json_dumps(clean_tags),
                json_dumps(metadata or {}),
                " ".join([content, clean_type, source, " ".join(clean_tags)]),
                prompt_score,
                prompt_risk_level,
                json_dumps(prompt_comments),
                json_dumps(prompt_suggestions),
                expires_at,
                now,
                now,
            ),
        )
        self.connection.commit()
        item = self.get(item_id)
        if item is None:
            raise RuntimeError("failed to read inserted memory")
        return item

    def add_prompt(
        self,
        prompt: str,
        user_id: str | None = None,
        source: str = "manual",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryItem:
        """Add a prompt memory and attach prompt quality comments."""

        return self.add(
            prompt,
            memory_type="prompt",
            user_id=user_id,
            source=source,
            tags=tags,
            metadata=metadata,
        )

    def search(
        self,
        query: str,
        user_id: str | None = None,
        memory_type: str | None = None,
        tags: list[str] | None = None,
        limit: int = 10,
        mode: str = "hybrid",
    ) -> list[MemorySearchResult]:
        """Search local memories."""

        candidates = self.list(user_id=user_id, memory_type=memory_type, limit=1000)
        wanted_tags = set(normalize_tags(tags))
        if wanted_tags:
            candidates = [item for item in candidates if wanted_tags.intersection(item.tags)]
        return search_memories(candidates, query, limit=limit, mode=mode)

    def list(
        self,
        user_id: str | None = None,
        memory_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryItem]:
        """List memories."""

        where: list[str] = []
        params: list[Any] = []
        if user_id is not None:
            where.append("user_id = ?")
            params.append(user_id)
        if memory_type is not None:
            where.append("memory_type = ?")
            params.append(normalize_memory_type(memory_type))
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        rows = self.connection.execute(
            f"SELECT * FROM memories {clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def get(self, memory_id: str) -> MemoryItem | None:
        """Get a memory by id."""

        row = self.connection.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        return self._row_to_item(row) if row else None

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by id."""

        cursor = self.connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    def clear(self, confirm: bool = False) -> int:
        """Clear all memories when confirmed."""

        if not confirm:
            raise ValueError("clear requires confirm=True")
        cursor = self.connection.execute("DELETE FROM memories")
        self.connection.commit()
        return cursor.rowcount

    def stats(self) -> MemoryStats:
        """Return memory statistics."""

        rows = self.connection.execute("SELECT * FROM memories").fetchall()
        items = [self._row_to_item(row) for row in rows]
        by_type: dict[str, int] = {}
        by_source: dict[str, int] = {}
        prompt_scores: list[int] = []
        now = utc_now()
        recent = 0
        expired = 0
        for item in items:
            by_type[item.memory_type] = by_type.get(item.memory_type, 0) + 1
            by_source[item.source] = by_source.get(item.source, 0) + 1
            if item.prompt_score is not None:
                prompt_scores.append(item.prompt_score)
            if item.expires_at and item.expires_at < now:
                expired += 1
            if (now - item.created_at).days <= 7:
                recent += 1
        return MemoryStats(
            total_memories=len(items),
            memories_by_type=by_type,
            memories_by_source=by_source,
            total_prompts=by_type.get("prompt", 0),
            average_prompt_score=round(sum(prompt_scores) / len(prompt_scores), 2)
            if prompt_scores
            else None,
            low_quality_prompts=len([score for score in prompt_scores if score < 60]),
            total_documents=by_type.get("document", 0),
            expired_memories=expired,
            recent_memories=recent,
        )

    def close(self) -> None:
        """Close the database connection."""

        self.connection.close()

    def _row_to_item(self, row: sqlite3.Row) -> MemoryItem:
        return MemoryItem(
            id=row["id"],
            content=row["content"],
            memory_type=row["memory_type"],
            user_id=row["user_id"],
            source=row["source"],
            tags=json_loads(row["tags"], []),
            metadata=json_loads(row["metadata"], {}),
            prompt_score=row["prompt_score"],
            prompt_risk_level=row["prompt_risk_level"],
            prompt_comments=json_loads(row["prompt_comments"], []),
            prompt_suggestions=json_loads(row["prompt_suggestions"], []),
            expires_at=parse_datetime(row["expires_at"]),
            created_at=parse_datetime(row["created_at"]) or utc_now(),
            updated_at=parse_datetime(row["updated_at"]) or utc_now(),
        )

    def __enter__(self) -> MemoryStore:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
