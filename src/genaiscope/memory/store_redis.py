"""Optional Redis production memory backend."""

from __future__ import annotations

import uuid
from typing import Any

from genaiscope.core.errors import RedisConnectionError, RedisDependencyMissingError
from genaiscope.memory.base import BaseMemoryStore
from genaiscope.memory.models import MemoryItem, MemorySearchResult, MemoryStats
from genaiscope.memory.namespaces import normalize_namespace
from genaiscope.memory.prompt_quality import analyze_prompt_quality
from genaiscope.memory.search import search_memories
from genaiscope.memory.ttl import calculate_expiry, is_expired
from genaiscope.memory.utils import normalize_memory_type, normalize_tags, parse_datetime, utc_now

SCOPES = ("user_id", "workspace_id", "project_id", "agent_id", "session_id")


def _redis_client(redis_url: str) -> Any:
    try:
        import redis
    except ImportError as exc:
        raise RedisDependencyMissingError(
            'Redis backend requires optional dependency. Install with:\npip install "genaiscope[redis]"'
        ) from exc
    try:
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except redis.RedisError as exc:
        raise RedisConnectionError(f"Unable to connect to Redis at {redis_url}: {exc}") from exc


class RedisMemoryStore(BaseMemoryStore):
    """Redis-backed memory store using JSON values and set indexes."""

    backend = "redis"

    def __init__(self, redis_url: str = "redis://localhost:6379", namespace: str = "genaiscope", **_kwargs: Any):
        self.redis_url = redis_url
        self.namespace = normalize_namespace(namespace)
        self.client = _redis_client(redis_url)

    def _key(self, memory_id: str) -> str:
        return f"{self.namespace}:memory:{memory_id}"

    def _index_keys(self, item: MemoryItem) -> list[str]:
        keys = [f"{self.namespace}:memories", f"{self.namespace}:type:{item.memory_type}:memories"]
        for scope in SCOPES:
            value = getattr(item, scope)
            if value:
                keys.append(f"{self.namespace}:{scope.removesuffix('_id')}:{value}:memories")
        keys.extend(f"{self.namespace}:tag:{tag}:memories" for tag in item.tags)
        return keys

    def add(self, content: str, memory_type: str = "general", tags: list[str] | None = None, ttl_seconds: int | None = None, ttl_days: int | None = None, memory_id: str | None = None, created_at: Any = None, updated_at: Any = None, importance: int = 5, visibility: str = "private", source: str = "manual", metadata: dict[str, Any] | None = None, **scopes: Any) -> MemoryItem:
        if not content.strip():
            raise ValueError("content must not be empty")
        if not 1 <= importance <= 10:
            raise ValueError("importance must be between 1 and 10")
        ttl_seconds, expires_at = calculate_expiry(ttl_seconds, ttl_days)
        now = utc_now()
        clean_type = normalize_memory_type(memory_type)
        quality = analyze_prompt_quality(content) if clean_type == "prompt" else None
        item = MemoryItem(
            id=memory_id or str(uuid.uuid4()), content=content, memory_type=clean_type,
            source=source, tags=normalize_tags(tags), metadata=metadata or {}, importance=importance,
            visibility=visibility, ttl_seconds=ttl_seconds, expires_at=expires_at,
            prompt_score=quality.score if quality else None,
            prompt_risk_level=quality.risk_level if quality else None,
            prompt_comments=quality.comments if quality else [],
            prompt_suggestions=quality.improvement_suggestions if quality else [],
            created_at=parse_datetime(created_at) if isinstance(created_at, str) else created_at or now,
            updated_at=parse_datetime(updated_at) if isinstance(updated_at, str) else updated_at or now,
            **{scope: scopes.get(scope) for scope in SCOPES},
        )
        pipe = self.client.pipeline()
        pipe.set(self._key(item.id), item.model_dump_json(), ex=ttl_seconds)
        for index in self._index_keys(item):
            pipe.sadd(index, item.id)
        pipe.execute()
        return item

    def get(self, memory_id: str, include_expired: bool = False) -> MemoryItem | None:
        value = self.client.get(self._key(memory_id))
        item = MemoryItem.model_validate_json(value) if value else None
        return item if item and (include_expired or not is_expired(item.expires_at)) else None

    def list(self, limit: int = 50, offset: int = 0, tags: list[str] | None = None, visibility: str | None = None, include_expired: bool = False, **filters: Any) -> list[MemoryItem]:
        index_keys = [f"{self.namespace}:memories"]
        for field in (*SCOPES, "memory_type"):
            value = filters.get(field)
            if value:
                name = "type" if field == "memory_type" else field.removesuffix("_id")
                index_keys.append(f"{self.namespace}:{name}:{value}:memories")
        index_keys.extend(f"{self.namespace}:tag:{tag}:memories" for tag in normalize_tags(tags))
        ids = self.client.sinter(index_keys) if len(index_keys) > 1 else self.client.smembers(index_keys[0])
        items: list[MemoryItem] = []
        stale: list[str] = []
        for memory_id in ids:
            item = self.get(memory_id, include_expired=include_expired)
            if item is None:
                stale.append(memory_id)
            elif visibility is None or item.visibility == visibility:
                items.append(item)
        if stale:
            for index in index_keys:
                self.client.srem(index, *stale)
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[offset : offset + limit]

    def search(self, query: str, limit: int = 10, mode: str = "hybrid", **filters: Any) -> list[MemorySearchResult]:
        return search_memories(
            self.list(limit=1000, **filters), query, limit=limit, mode=mode,
            memory_type=filters.get("memory_type"),
            requested_scopes={scope: filters.get(scope) for scope in SCOPES},
        )

    def delete(self, memory_id: str) -> bool:
        item = self.get(memory_id, include_expired=True)
        if item is None:
            return False
        pipe = self.client.pipeline()
        pipe.delete(self._key(memory_id))
        for index in self._index_keys(item):
            pipe.srem(index, memory_id)
        pipe.execute()
        return True

    def clear(self, confirm: bool = False, **filters: Any) -> int:
        if not confirm:
            raise ValueError("clear requires confirm=True")
        items = self.list(limit=100000, include_expired=True, **filters)
        for item in items:
            self.delete(item.id)
        return len(items)

    def cleanup_expired(self) -> int:
        before = self.client.scard(f"{self.namespace}:memories")
        self.list(limit=100000, include_expired=True)
        return before - self.client.scard(f"{self.namespace}:memories")

    def stats(self) -> MemoryStats:
        items = self.list(limit=100000)
        def counts(field: str) -> dict[str, int]:
            result: dict[str, int] = {}
            for item in items:
                value = getattr(item, field)
                if value:
                    result[value] = result.get(value, 0) + 1
            return result
        by_type = counts("memory_type")
        scores = [item.prompt_score for item in items if item.prompt_score is not None]
        return MemoryStats(
            total_memories=len(items), memories_by_type=by_type, memories_by_source=counts("source"),
            memories_by_user=counts("user_id"), memories_by_workspace=counts("workspace_id"),
            memories_by_project=counts("project_id"), total_prompts=by_type.get("prompt", 0),
            average_prompt_score=round(sum(scores) / len(scores), 2) if scores else None,
            low_quality_prompts=len([score for score in scores if score < 60]),
            total_documents=by_type.get("document", 0),
            recent_memories=len([item for item in items if (utc_now() - item.created_at).days <= 7]),
        )

    def close(self) -> None:
        self.client.close()
