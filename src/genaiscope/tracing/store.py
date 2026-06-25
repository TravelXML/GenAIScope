"""SQLite store for local traces."""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any

from genaiscope.memory.namespaces import normalize_namespace
from genaiscope.memory.utils import (
    default_db_path,
    ensure_parent,
    iso_now,
    json_dumps,
    json_loads,
    parse_datetime,
    utc_now,
)
from genaiscope.tracing.base import BaseTraceStore
from genaiscope.tracing.models import TraceItem, TraceStats


class SQLiteTraceStore(BaseTraceStore):
    """SQLite-backed trace store."""

    backend = "sqlite"

    def __init__(self, db_path: str | Path | None = None, namespace: str = "genaiscope", **_kwargs: Any):
        self.db_path = Path(db_path) if db_path else default_db_path()
        self.namespace = normalize_namespace(namespace)
        ensure_parent(self.db_path)
        # check_same_thread=False: this store is shared by the REST API/MCP
        # server tracer middleware, which may dispatch across threads (and
        # their test clients do too). See store_sqlite.py for the same fix.
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS traces (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                input_text TEXT,
                output_text TEXT,
                model TEXT,
                provider TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                estimated_cost REAL DEFAULT 0,
                latency_ms REAL,
                status TEXT DEFAULT 'success',
                error TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_traces_name ON traces(name);
            CREATE INDEX IF NOT EXISTS idx_traces_model ON traces(model);
            CREATE INDEX IF NOT EXISTS idx_traces_provider ON traces(provider);
            CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
            CREATE INDEX IF NOT EXISTS idx_traces_created_at ON traces(created_at);
            """
        )
        self.connection.commit()

    def log(
        self,
        name: str,
        input_text: str | None = None,
        output_text: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        estimated_cost: float = 0.0,
        latency_ms: float | None = None,
        status: str = "success",
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceItem:
        """Log one trace."""

        trace_id = str(uuid.uuid4())
        now = iso_now()
        self.connection.execute(
            """
            INSERT INTO traces (
                id, name, input_text, output_text, model, provider, input_tokens,
                output_tokens, estimated_cost, latency_ms, status, error, metadata,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_id,
                name,
                input_text,
                output_text,
                model,
                provider,
                input_tokens,
                output_tokens,
                estimated_cost,
                latency_ms,
                status,
                error,
                json_dumps(metadata or {}),
                now,
                now,
            ),
        )
        self.connection.commit()
        item = self.get(trace_id)
        if item is None:
            raise RuntimeError("failed to read inserted trace")
        return item

    def list(self, limit: int = 50, offset: int = 0) -> list[TraceItem]:
        """List traces."""

        rows = self.connection.execute(
            "SELECT * FROM traces ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def get(self, trace_id: str) -> TraceItem | None:
        """Get one trace by id."""

        row = self.connection.execute("SELECT * FROM traces WHERE id = ?", (trace_id,)).fetchone()
        return self._row_to_item(row) if row else None

    def clear(self, confirm: bool = False) -> int:
        """Clear traces when confirmed."""

        if not confirm:
            raise ValueError("clear requires confirm=True")
        cursor = self.connection.execute("DELETE FROM traces")
        self.connection.commit()
        return cursor.rowcount

    def stats(self) -> TraceStats:
        """Return trace statistics."""

        traces = self.list(limit=1000)
        latencies = [trace.latency_ms for trace in traces if trace.latency_ms is not None]
        by_model: dict[str, int] = {}
        by_provider: dict[str, int] = {}
        for trace in traces:
            if trace.model:
                by_model[trace.model] = by_model.get(trace.model, 0) + 1
            if trace.provider:
                by_provider[trace.provider] = by_provider.get(trace.provider, 0) + 1
        return TraceStats(
            total_traces=len(traces),
            success_count=len([trace for trace in traces if trace.status == "success"]),
            error_count=len([trace for trace in traces if trace.status != "success"]),
            total_estimated_cost=round(sum(trace.estimated_cost for trace in traces), 6),
            average_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else None,
            total_input_tokens=sum(trace.input_tokens for trace in traces),
            total_output_tokens=sum(trace.output_tokens for trace in traces),
            traces_by_model=by_model,
            traces_by_provider=by_provider,
        )

    def close(self) -> None:
        """Close the database connection."""

        self.connection.close()

    def _row_to_item(self, row: sqlite3.Row) -> TraceItem:
        return TraceItem(
            id=row["id"],
            name=row["name"],
            input_text=row["input_text"],
            output_text=row["output_text"],
            model=row["model"],
            provider=row["provider"],
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            estimated_cost=row["estimated_cost"],
            latency_ms=row["latency_ms"],
            status=row["status"],
            error=row["error"],
            metadata=json_loads(row["metadata"], {}),
            created_at=parse_datetime(row["created_at"]) or utc_now(),
            updated_at=parse_datetime(row["updated_at"]) or utc_now(),
        )


TraceStore = SQLiteTraceStore
