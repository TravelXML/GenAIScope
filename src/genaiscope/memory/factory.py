"""Memory backend factory."""

from __future__ import annotations

from typing import Any

from genaiscope.core.errors import InvalidBackendError
from genaiscope.memory.base import BaseMemoryStore
from genaiscope.memory.store_redis import RedisMemoryStore
from genaiscope.memory.store_sqlite import SQLiteMemoryStore


def MemoryStore(backend: str = "sqlite", **kwargs: Any) -> BaseMemoryStore:  # noqa: N802
    """Create a configured memory backend."""

    if backend == "sqlite":
        return SQLiteMemoryStore(**kwargs)
    if backend == "redis":
        return RedisMemoryStore(**kwargs)
    raise InvalidBackendError(f"Unsupported memory backend: {backend}. Use 'sqlite' or 'redis'.")
