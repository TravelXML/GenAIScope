"""REST API tests — skips without server extra (fastapi)."""

import pytest

try:
    from fastapi.testclient import TestClient

    _fastapi_available = True
except ImportError:
    _fastapi_available = False


@pytest.mark.skipif(not _fastapi_available, reason="fastapi not installed")
def test_health(tmp_path) -> None:
    from genaiscope.memory.factory import MemoryStore
    from genaiscope.server.app import create_app

    store = MemoryStore(db_path=tmp_path / "m.db")
    client = TestClient(create_app(store))
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    store.close()


@pytest.mark.skipif(not _fastapi_available, reason="fastapi not installed")
def test_remember_and_search(tmp_path) -> None:
    from genaiscope.memory.factory import MemoryStore
    from genaiscope.server.app import create_app

    store = MemoryStore(db_path=tmp_path / "m.db")
    client = TestClient(create_app(store))

    resp = client.post(
        "/v1/memory/remember",
        json={"content": "User prefers concise answers", "memory_type": "preference"},
    )
    assert resp.status_code == 200
    mid = resp.json()["id"]

    resp = client.post("/v1/memory/search", json={"query": "concise", "limit": 5})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert any(r["id"] == mid for r in results)

    store.close()


@pytest.mark.skipif(not _fastapi_available, reason="fastapi not installed")
def test_context_endpoint(tmp_path) -> None:
    from genaiscope.memory.factory import MemoryStore
    from genaiscope.server.app import create_app

    store = MemoryStore(db_path=tmp_path / "m.db")
    client = TestClient(create_app(store))

    client.post(
        "/v1/memory/remember",
        json={"content": "Sapan is building GenAIScope", "memory_type": "project"},
    )

    resp = client.post(
        "/v1/memory/context",
        json={"query": "what is GenAIScope", "limit": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "text" in data
    assert "memory_count" in data
    store.close()


@pytest.mark.skipif(not _fastapi_available, reason="fastapi not installed")
def test_get_delete(tmp_path) -> None:
    from genaiscope.memory.factory import MemoryStore
    from genaiscope.server.app import create_app

    store = MemoryStore(db_path=tmp_path / "m.db")
    client = TestClient(create_app(store))

    resp = client.post("/v1/memory/remember", json={"content": "test memory"})
    mid = resp.json()["id"]

    resp = client.get(f"/v1/memory/{mid}")
    assert resp.status_code == 200

    resp = client.delete(f"/v1/memory/{mid}")
    assert resp.status_code == 200

    resp = client.get(f"/v1/memory/{mid}")
    assert resp.status_code == 404

    store.close()


@pytest.mark.skipif(not _fastapi_available, reason="fastapi not installed")
def test_middleware_records_trace_on_success(tmp_path) -> None:
    from genaiscope.memory.factory import MemoryStore
    from genaiscope.server.app import create_app
    from genaiscope.tracing import LocalTracer

    store = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "traces.db")
    client = TestClient(create_app(store, tracer=tracer))

    resp = client.get("/health")
    assert resp.status_code == 200

    traces = tracer.list()
    assert len(traces) == 1
    assert traces[0].provider == "rest"
    assert traces[0].status == "success"
    assert traces[0].metadata.get("status_code") == 200
    store.close()
    tracer.close()


@pytest.mark.skipif(not _fastapi_available, reason="fastapi not installed")
def test_middleware_records_trace_on_404(tmp_path) -> None:
    from genaiscope.memory.factory import MemoryStore
    from genaiscope.server.app import create_app
    from genaiscope.tracing import LocalTracer

    store = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "traces.db")
    client = TestClient(create_app(store, tracer=tracer))

    resp = client.get("/v1/memory/does-not-exist")
    assert resp.status_code == 404

    traces = tracer.list()
    assert len(traces) == 1
    assert traces[0].status == "error"
    assert traces[0].metadata.get("status_code") == 404
    store.close()
    tracer.close()


@pytest.mark.skipif(not _fastapi_available, reason="fastapi not installed")
def test_auth_rejected(tmp_path) -> None:
    import os

    os.environ["GENAISCOPE_API_TOKEN"] = "secret123"
    try:
        from genaiscope.memory.factory import MemoryStore
        from genaiscope.server.app import create_app

        store = MemoryStore(db_path=tmp_path / "m.db")
        client = TestClient(create_app(store, auth_enabled=True))

        resp = client.get("/health")
        assert resp.status_code == 200

        resp = client.get("/v1/memory/stats")
        assert resp.status_code == 401

        resp = client.get(
            "/v1/memory/stats",
            headers={"Authorization": "Bearer secret123"},
        )
        assert resp.status_code == 200
        store.close()
    finally:
        os.environ.pop("GENAISCOPE_API_TOKEN", None)


@pytest.mark.skipif(not _fastapi_available, reason="fastapi not installed")
def test_gateway_ask_success(tmp_path) -> None:
    from types import SimpleNamespace
    from unittest.mock import patch

    from genaiscope.memory.factory import MemoryStore
    from genaiscope.server.app import create_app
    from genaiscope.tracing import LocalTracer

    store = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "traces.db")
    client = TestClient(create_app(store, tracer=tracer))

    msg = SimpleNamespace(content="hello from the gateway")
    choice = SimpleNamespace(message=msg)
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5)
    openai_response = SimpleNamespace(choices=[choice], usage=usage, model="gpt-4o-mini")

    with patch("genaiscope.adapters.OpenAIAdapter") as mock_adapter:
        mock_adapter.return_value.chat.return_value = openai_response
        resp = client.post(
            "/v1/gateway/ask",
            json={"prompt": "Refactor this Python function", "provider": "openai"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["text"] == "hello from the gateway"
    assert data["provider"] == "openai"
    assert data["context_health_score"] is not None

    # One "rest" middleware trace for the request, one detailed "gateway.complete" trace.
    traces = tracer.list()
    assert any(t.name == "gateway.complete" for t in traces)
    store.close()
    tracer.close()


@pytest.mark.skipif(not _fastapi_available, reason="fastapi not installed")
def test_gateway_ask_returns_502_when_all_providers_fail(tmp_path) -> None:
    from unittest.mock import patch

    from genaiscope.memory.factory import MemoryStore
    from genaiscope.server.app import create_app

    store = MemoryStore(db_path=tmp_path / "m.db")
    client = TestClient(create_app(store))

    with (
        patch("genaiscope.adapters.OpenAIAdapter") as mock_openai,
        patch("genaiscope.adapters.AnthropicAdapter") as mock_anthropic,
    ):
        mock_openai.return_value.chat.side_effect = RuntimeError("down")
        mock_anthropic.return_value.chat.side_effect = RuntimeError("down")
        resp = client.post(
            "/v1/gateway/ask",
            json={"prompt": "Refactor this Python function and fix the bug", "provider": "auto"},
        )

    assert resp.status_code == 502
    store.close()
