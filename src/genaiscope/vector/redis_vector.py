"""Redis/RedisVL vector store backend.

Requires: pip install "genaiscope[redis]"  (redis + redisvl)
"""

from __future__ import annotations

from typing import Any

from genaiscope.core.errors import VectorBackendError
from genaiscope.vector.base import BaseVectorStore
from genaiscope.vector.models import VectorMatch


class RedisVectorStore(BaseVectorStore):
    """RedisVL/RediSearch vector backend with metadata filters."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        namespace: str = "genaiscope",
        dimensions: int = 256,
    ) -> None:
        try:
            import redis as redis_lib
        except ImportError as exc:
            raise VectorBackendError(
                "redis is not installed. Run: pip install \"genaiscope[redis]\""
            ) from exc

        try:
            import redis as redis_lib

            self._client = redis_lib.from_url(redis_url, decode_responses=False)
            self._client.ping()
        except Exception as exc:
            raise VectorBackendError(f"Cannot connect to Redis at {redis_url}: {exc}") from exc

        self._namespace = namespace
        self._dimensions = dimensions
        self._prefix = f"{namespace}:vec:"

    def _key(self, vector_id: str) -> str:
        return f"{self._prefix}{vector_id}"

    def upsert(self, vector_id: str, vector: list[float], metadata: dict) -> None:
        import json
        import struct

        packed = struct.pack(f"{len(vector)}f", *vector)
        data: dict[bytes, bytes] = {
            b"__vec__": packed,
            b"__meta__": json.dumps(metadata).encode(),
        }
        for k, v in metadata.items():
            if isinstance(v, str):
                data[k.encode()] = v.encode()
        self._client.hset(self._key(vector_id), mapping=data)

    def query(
        self,
        vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorMatch]:
        """Brute-force scan with cosine similarity (redisvl optional)."""
        import json
        import math
        import struct

        keys = self._client.keys(f"{self._prefix}*")
        results: list[VectorMatch] = []

        for key in keys:
            raw = self._client.hgetall(key)
            if b"__vec__" not in raw:
                continue
            meta_raw = raw.get(b"__meta__", b"{}")
            meta: dict[str, Any] = json.loads(meta_raw)
            if filters and not all(meta.get(k) == v for k, v in filters.items() if v is not None):
                continue
            stored_bytes = raw[b"__vec__"]
            n = len(stored_bytes) // 4
            stored = list(struct.unpack(f"{n}f", stored_bytes))
            dot = sum(a * b for a, b in zip(vector, stored, strict=False))
            na = math.sqrt(sum(x * x for x in vector)) or 1.0
            nb = math.sqrt(sum(x * x for x in stored)) or 1.0
            score = dot / (na * nb)
            vid = key.decode().removeprefix(self._prefix)
            results.append(VectorMatch(vector_id=vid, score=score, metadata=meta))

        return sorted(results, key=lambda m: m.score, reverse=True)[:top_k]

    def delete(self, vector_id: str) -> bool:
        return bool(self._client.delete(self._key(vector_id)))

    def count(self) -> int:
        keys = self._client.keys(f"{self._prefix}*")
        return len(keys)
