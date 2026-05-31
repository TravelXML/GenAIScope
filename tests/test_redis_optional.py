"""Optional live Redis backend tests."""

from __future__ import annotations

from uuid import uuid4

import pytest

from genaiscope.cache import SemanticCache
from genaiscope.memory import MemoryStore
from genaiscope.tracing import LocalTracer


def test_live_redis_memory_trace_and_cache() -> None:
    """Exercise Redis when redis-py and a local server are available."""

    redis = pytest.importorskip("redis")
    redis_url = "redis://localhost:6379"
    try:
        redis.Redis.from_url(redis_url, socket_connect_timeout=1).ping()
    except redis.RedisError:
        pytest.skip("local Redis server is unavailable")

    namespace = f"genaiscope-test-{uuid4()}"
    memory = MemoryStore(backend="redis", redis_url=redis_url, namespace=namespace)
    tracer = LocalTracer(backend="redis", redis_url=redis_url, namespace=namespace)
    try:
        item = memory.add(
            "User prefers concise answers",
            memory_type="preference",
            user_id="sapan",
            project_id="memovo",
        )
        assert memory.list(memory_type="preference") == [item]
        assert memory.search("concise answers", user_id="sapan")[0].item == item

        cache = SemanticCache(memory_store=memory)
        cache.set("Summarize refund policy", "Refund summary", user_id="sapan")
        assert cache.get("Summarize refund policy", user_id="sapan").response == "Refund summary"

        tracer.log(name="redis-test", model="local", provider="test")
        assert tracer.stats().total_traces == 1
    finally:
        memory.clear(confirm=True)
        tracer.clear(confirm=True)
        memory.close()
        tracer.close()
