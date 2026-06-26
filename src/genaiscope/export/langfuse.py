"""Batch export of local traces to Langfuse's documented ingestion event shape.

Writes a JSON file matching the `POST /api/public/ingestion` batch body
(`{"batch": [event, ...]}`) -- no network call, no `langfuse` package
dependency. Pipe the output file through Langfuse's own ingestion endpoint
(or the official SDK) to actually load it; this module only produces the file.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from genaiscope.tracing import LocalTracer


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


def export_langfuse(tracer: LocalTracer, out: str | Path, limit: int = 1000) -> Path:
    """Export recent local traces as a Langfuse batch-ingestion JSON file. One
    `trace-create` event per `TraceItem`, plus a paired `generation-create`
    event when the trace carries a model/provider."""

    batch: list[dict[str, Any]] = []
    for item in tracer.list(limit=limit):
        batch.append(
            {
                "id": f"{item.id}-trace",
                "type": "trace-create",
                "timestamp": _iso(item.created_at),
                "body": {
                    "id": item.id,
                    "name": item.name,
                    "input": item.input_text,
                    "output": item.output_text,
                    "metadata": item.metadata,
                    "timestamp": _iso(item.created_at),
                },
            }
        )
        if item.model or item.provider:
            batch.append(
                {
                    "id": f"{item.id}-generation",
                    "type": "generation-create",
                    "timestamp": _iso(item.created_at),
                    "body": {
                        "id": f"{item.id}-generation",
                        "traceId": item.id,
                        "name": item.name,
                        "startTime": _iso(item.created_at),
                        "endTime": _iso(item.updated_at),
                        "model": item.model,
                        "input": item.input_text,
                        "output": item.output_text,
                        "usage": {
                            "promptTokens": item.input_tokens,
                            "completionTokens": item.output_tokens,
                            "totalTokens": item.input_tokens + item.output_tokens,
                        },
                        "metadata": {"provider": item.provider, "estimated_cost": item.estimated_cost},
                        "level": "ERROR" if item.status == "error" else "DEFAULT",
                        "statusMessage": item.error,
                    },
                }
            )

    path = Path(out)
    path.write_text(json.dumps({"batch": batch}, indent=2), encoding="utf-8")
    return path
