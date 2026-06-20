"""Tests for tracing wired into MCP tool dispatch — no live transport needed."""

from pathlib import Path

from genaiscope.mcp.server import _dispatch
from genaiscope.memory.factory import MemoryStore
from genaiscope.tracing import LocalTracer


def test_dispatch_records_trace_when_tracer_provided(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "traces.db")

    result = _dispatch(store, "memory_remember", {"content": "hello"}, tracer)

    assert "id" in result
    traces = tracer.list()
    assert len(traces) == 1
    assert traces[0].name == "mcp.memory_remember"
    assert traces[0].provider == "mcp"
    assert traces[0].status == "success"
    store.close()
    tracer.close()


def test_dispatch_no_trace_when_tracer_none(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")

    result = _dispatch(store, "memory_remember", {"content": "hello"}, None)

    assert "id" in result
    store.close()
