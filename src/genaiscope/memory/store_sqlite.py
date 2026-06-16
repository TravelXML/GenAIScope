"""SQLite-backed default memory store."""

from __future__ import annotations

import contextlib
import sqlite3
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

from genaiscope.memory.base import BaseMemoryStore
from genaiscope.memory.context import ContextResult
from genaiscope.memory.models import MemoryItem, MemorySearchResult, MemoryStats
from genaiscope.memory.namespaces import normalize_namespace
from genaiscope.memory.prompt_quality import analyze_prompt_quality
from genaiscope.memory.search import search_memories
from genaiscope.memory.ttl import calculate_expiry, is_expired
from genaiscope.memory.utils import (
    default_db_path,
    ensure_parent,
    json_dumps,
    json_loads,
    normalize_memory_type,
    normalize_tags,
    parse_datetime,
    utc_now,
)

if TYPE_CHECKING:
    from genaiscope.embeddings.base import BaseEmbedder
    from genaiscope.vector.base import BaseVectorStore

SCOPES = ("user_id", "workspace_id", "project_id", "agent_id", "session_id")


class SQLiteMemoryStore(BaseMemoryStore):
    """Local SQLite memory store with production-oriented scopes and TTL."""

    backend = "sqlite"

    def __init__(
        self,
        db_path: str | Path | None = None,
        auto_create: bool = True,
        namespace: str = "genaiscope",
        embedder: BaseEmbedder | None = None,
        vector_store: BaseVectorStore | None = None,
        **_kwargs: Any,
    ):
        self.db_path = Path(db_path) if db_path else default_db_path()
        self.namespace = normalize_namespace(namespace)
        ensure_parent(self.db_path)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._embedder = embedder
        self._vector_store = vector_store

        if auto_create:
            self._create_schema()

        # lazy-init local vector store sidecar when no store was provided but embedder exists
        if self._embedder and not self._vector_store:
            try:
                from genaiscope.vector.local_vector import LocalVectorStore

                self._vector_store = LocalVectorStore(
                    db_path=self.db_path.with_suffix(".vectors.db")
                )
            except Exception:
                pass

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY, content TEXT NOT NULL,
                memory_type TEXT NOT NULL DEFAULT 'general', user_id TEXT,
                workspace_id TEXT, project_id TEXT, agent_id TEXT, session_id TEXT,
                source TEXT DEFAULT 'manual', tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}', search_text TEXT,
                importance INTEGER DEFAULT 5, visibility TEXT DEFAULT 'private',
                ttl_seconds INTEGER, prompt_score INTEGER, prompt_risk_level TEXT,
                prompt_comments TEXT DEFAULT '[]', prompt_suggestions TEXT DEFAULT '[]',
                expires_at TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
            CREATE INDEX IF NOT EXISTS idx_memories_memory_type ON memories(memory_type);
            CREATE INDEX IF NOT EXISTS idx_memories_expires_at ON memories(expires_at);
            """
        )
        existing = {row["name"] for row in self.connection.execute("PRAGMA table_info(memories)")}
        migrations = {
            "workspace_id": "TEXT",
            "project_id": "TEXT",
            "agent_id": "TEXT",
            "session_id": "TEXT",
            "importance": "INTEGER DEFAULT 5",
            "visibility": "TEXT DEFAULT 'private'",
            "ttl_seconds": "INTEGER",
        }
        for column, sql_type in migrations.items():
            if column not in existing:
                self.connection.execute(f"ALTER TABLE memories ADD COLUMN {column} {sql_type}")
        for scope in SCOPES[1:]:
            self.connection.execute(
                f"CREATE INDEX IF NOT EXISTS idx_memories_{scope} ON memories({scope})"
            )
        self.connection.commit()

    def add(
        self,
        content: str,
        memory_type: str = "general",
        user_id: str | None = None,
        workspace_id: str | None = None,
        project_id: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        source: str = "manual",
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        importance: int = 5,
        visibility: str = "private",
        ttl_seconds: int | None = None,
        ttl_days: int | None = None,
        memory_id: str | None = None,
        created_at: Any = None,
        updated_at: Any = None,
        **_kwargs: Any,
    ) -> MemoryItem:
        """Add one memory."""

        if not content.strip():
            raise ValueError("content must not be empty")
        if not 1 <= importance <= 10:
            raise ValueError("importance must be between 1 and 10")
        ttl_seconds, expires_at = calculate_expiry(ttl_seconds, ttl_days)
        now = utc_now()
        clean_type = normalize_memory_type(memory_type)
        clean_tags = normalize_tags(tags)
        quality = analyze_prompt_quality(content) if clean_type == "prompt" else None
        mid = memory_id or str(uuid.uuid4())
        values = {
            "id": mid,
            "content": content,
            "memory_type": clean_type,
            "user_id": user_id,
            "workspace_id": workspace_id,
            "project_id": project_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "source": source,
            "tags": json_dumps(clean_tags),
            "metadata": json_dumps(metadata or {}),
            "search_text": " ".join([content, clean_type, source, *clean_tags]),
            "importance": importance,
            "visibility": visibility,
            "ttl_seconds": ttl_seconds,
            "prompt_score": quality.score if quality else None,
            "prompt_risk_level": quality.risk_level if quality else None,
            "prompt_comments": json_dumps(quality.comments if quality else []),
            "prompt_suggestions": json_dumps(quality.improvement_suggestions if quality else []),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "created_at": (parse_datetime(created_at) if isinstance(created_at, str) else created_at or now).isoformat(),
            "updated_at": (parse_datetime(updated_at) if isinstance(updated_at, str) else updated_at or now).isoformat(),
        }
        columns = ", ".join(values)
        placeholders = ", ".join("?" for _ in values)
        self.connection.execute(
            f"INSERT OR REPLACE INTO memories ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )
        self.connection.commit()

        # store embedding vector if embedder is configured
        if self._embedder and self._vector_store:
            try:
                vec = self._embedder.embed(content)
                vec_meta = {
                    "user_id": user_id,
                    "workspace_id": workspace_id,
                    "project_id": project_id,
                    "agent_id": agent_id,
                    "session_id": session_id,
                    "memory_type": clean_type,
                    "importance": importance,
                }
                self._vector_store.upsert(mid, vec, vec_meta)
            except Exception:
                pass

        return self.get(mid, include_expired=True)  # type: ignore[return-value]

    def search(
        self,
        query: str,
        limit: int = 10,
        mode: str = "hybrid",
        **filters: Any,
    ) -> list[MemorySearchResult]:
        """Search non-expired memories."""

        memory_type = filters.get("memory_type")
        candidates = self.list(limit=1000, **filters)
        return search_memories(
            candidates,
            query,
            limit=limit,
            mode=mode,
            memory_type=memory_type,
            requested_scopes={scope: filters.get(scope) for scope in SCOPES},
            embedder=self._embedder,
            vector_store=self._vector_store,
        )

    def context(
        self,
        query: str,
        user_id: str | None = None,
        project_id: str | None = None,
        workspace_id: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        limit: int = 10,
        mode: str = "hybrid",
        max_chars: int | None = None,
    ) -> ContextResult:
        """Return a ready-to-inject context block from the top memories."""

        results = self.search(
            query,
            limit=limit,
            mode=mode,
            user_id=user_id,
            project_id=project_id,
            workspace_id=workspace_id,
            agent_id=agent_id,
            session_id=session_id,
        )

        lines: list[str] = []
        selected: list[dict] = []
        char_count = 0
        for result in results:
            line = f"- [{result.item.memory_type}] {result.item.content}"
            if max_chars and char_count + len(line) > max_chars:
                break
            lines.append(line)
            char_count += len(line)
            selected.append({"id": result.item.id, "content": result.item.content, "score": result.score})

        text = "\n".join(lines)
        return ContextResult(
            query=query,
            memories=selected,
            text=text,
            char_count=char_count,
            memory_count=len(selected),
            embedder_used=self._embedder.name if self._embedder else "none",
            mode=mode,
        )

    def reindex_embeddings(self) -> int:
        """Recompute and store embeddings for all memories. Returns count reindexed."""
        if not self._embedder or not self._vector_store:
            return 0
        items = self.list(limit=100000, include_expired=True)
        count = 0
        for item in items:
            try:
                vec = self._embedder.embed(item.content)
                meta: dict[str, Any] = {
                    "user_id": item.user_id,
                    "workspace_id": item.workspace_id,
                    "project_id": item.project_id,
                    "memory_type": item.memory_type,
                    "importance": item.importance,
                }
                self._vector_store.upsert(item.id, vec, meta)
                count += 1
            except Exception:
                pass
        return count

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        tags: list[str] | None = None,
        visibility: str | None = None,
        include_expired: bool = False,
        **filters: Any,
    ) -> list[MemoryItem]:
        """List memories with optional scope filters."""

        where: list[str] = []
        params: list[Any] = []
        for field in (*SCOPES, "memory_type"):
            value = filters.get(field)
            if value is not None:
                where.append(f"{field} = ?")
                params.append(normalize_memory_type(value) if field == "memory_type" else value)
        if visibility is not None:
            where.append("visibility = ?")
            params.append(visibility)
        if not include_expired:
            where.append("(expires_at IS NULL OR expires_at > ?)")
            params.append(utc_now().isoformat())
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        rows = self.connection.execute(
            f"SELECT * FROM memories {clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()
        items = [self._row_to_item(row) for row in rows]
        wanted_tags = set(normalize_tags(tags))
        return [item for item in items if not wanted_tags or wanted_tags.intersection(item.tags)]

    def get(self, memory_id: str, include_expired: bool = False) -> MemoryItem | None:
        row = self.connection.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        item = self._row_to_item(row) if row else None
        return item if item and (include_expired or not is_expired(item.expires_at)) else None

    def delete(self, memory_id: str) -> bool:
        cursor = self.connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self.connection.commit()
        if self._vector_store:
            with contextlib.suppress(Exception):
                self._vector_store.delete(memory_id)
        return cursor.rowcount > 0

    def clear(self, confirm: bool = False, **filters: Any) -> int:
        if not confirm:
            raise ValueError("clear requires confirm=True")
        items = self.list(limit=100000, include_expired=True, **filters)
        for item in items:
            self.delete(item.id)
        return len(items)

    def cleanup_expired(self) -> int:
        cursor = self.connection.execute(
            "DELETE FROM memories WHERE expires_at IS NOT NULL AND expires_at <= ?",
            (utc_now().isoformat(),),
        )
        self.connection.commit()
        return cursor.rowcount

    def stats(self) -> MemoryStats:
        items = self.list(limit=100000, include_expired=True)
        active = [item for item in items if not is_expired(item.expires_at)]
        now = utc_now()

        def counts(field: str) -> dict[str, int]:
            result: dict[str, int] = {}
            for item in active:
                value = getattr(item, field)
                if value:
                    result[value] = result.get(value, 0) + 1
            return result

        prompt_scores = [item.prompt_score for item in active if item.prompt_score is not None]
        by_type = counts("memory_type")
        vec_count = self._vector_store.count() if self._vector_store else 0
        return MemoryStats(
            total_memories=len(active),
            memories_by_type=by_type,
            memories_by_source=counts("source"),
            memories_by_user=counts("user_id"),
            memories_by_workspace=counts("workspace_id"),
            memories_by_project=counts("project_id"),
            total_prompts=by_type.get("prompt", 0),
            average_prompt_score=round(sum(prompt_scores) / len(prompt_scores), 2) if prompt_scores else None,
            low_quality_prompts=len([s for s in prompt_scores if s < 60]),
            total_documents=by_type.get("document", 0),
            expired_memories=len(items) - len(active),
            recent_memories=len([item for item in active if (now - item.created_at).days <= 7]),
            duplicate_memories=vec_count,
        )

    def close(self) -> None:
        self.connection.close()

    def _row_to_item(self, row: sqlite3.Row) -> MemoryItem:
        data = dict(row)
        for key, fallback in (("tags", []), ("metadata", {}), ("prompt_comments", []), ("prompt_suggestions", [])):
            data[key] = json_loads(data.get(key), fallback)
        data.pop("search_text", None)
        for key in ("expires_at", "created_at", "updated_at"):
            data[key] = parse_datetime(data.get(key))
        return MemoryItem(**data)
