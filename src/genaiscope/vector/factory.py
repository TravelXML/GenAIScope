"""Vector store factory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from genaiscope.core.errors import VectorBackendError
from genaiscope.vector.base import BaseVectorStore


def get_vector_store(
    backend: str = "local",
    *,
    db_path: str | Path | None = None,
    redis_url: str = "redis://localhost:6379",
    namespace: str = "genaiscope",
    dimensions: int = 256,
    **_kwargs: Any,
) -> BaseVectorStore:
    """Return a configured vector store."""

    b = backend.lower()
    if b in ("local", "sqlite"):
        from genaiscope.vector.local_vector import LocalVectorStore

        return LocalVectorStore(db_path=db_path)

    if b == "redis":
        from genaiscope.vector.redis_vector import RedisVectorStore

        return RedisVectorStore(
            redis_url=redis_url, namespace=namespace, dimensions=dimensions
        )

    raise VectorBackendError(
        f"Unknown vector store backend: {backend!r}. Use 'local' or 'redis'."
    )
