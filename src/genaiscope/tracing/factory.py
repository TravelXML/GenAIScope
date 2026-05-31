"""Trace backend factory."""

from __future__ import annotations

from typing import Any

from genaiscope.core.errors import InvalidBackendError
from genaiscope.tracing.base import BaseTraceStore
from genaiscope.tracing.store import SQLiteTraceStore
from genaiscope.tracing.store_redis import RedisTraceStore


def create_trace_store(backend: str = "sqlite", **kwargs: Any) -> BaseTraceStore:
    """Create the requested trace backend."""

    if backend == "sqlite":
        return SQLiteTraceStore(**kwargs)
    if backend == "redis":
        return RedisTraceStore(**kwargs)
    raise InvalidBackendError(f"Unsupported trace backend: {backend}. Use 'sqlite' or 'redis'.")
