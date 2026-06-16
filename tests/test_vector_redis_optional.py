"""Tests for RedisVectorStore — skips if redis not installed or not running."""

import pytest


def _redis_available() -> bool:
    try:
        import redis

        r = redis.Redis()
        r.ping()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _redis_available(), reason="Redis not available")
def test_redis_vector_store_basic(tmp_path) -> None:
    from genaiscope.vector.redis_vector import RedisVectorStore

    store = RedisVectorStore(namespace="test_vec_" + str(id(tmp_path)))
    vec = [1.0, 0.0, 0.0, 0.0]
    store.upsert("r1", vec, {"user_id": "alice"})
    assert store.count() >= 1
    results = store.query(vec, top_k=5)
    ids = [r.vector_id for r in results]
    assert "r1" in ids
    store.delete("r1")
