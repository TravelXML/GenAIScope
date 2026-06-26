"""Tests for MCP tool functions — no live transport needed."""

from pathlib import Path

from genaiscope.mcp.tools import (
    tool_analytics_prompt_patterns,
    tool_analytics_usage_summary,
    tool_doctor_diagnose,
    tool_memory_add_prompt,
    tool_memory_context,
    tool_memory_list,
    tool_memory_remember,
    tool_memory_search,
    tool_memory_stats,
    tool_report_generate,
)
from genaiscope.memory.factory import MemoryStore
from genaiscope.tracing import LocalTracer


def _store(tmp_path: Path):
    return MemoryStore(db_path=tmp_path / "m.db")


def test_tool_remember(tmp_path: Path) -> None:
    store = _store(tmp_path)
    result = tool_memory_remember(store, content="User prefers bullets", memory_type="preference")
    assert "id" in result
    assert result["memory_type"] == "preference"
    store.close()


def test_tool_search(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add("concise CTO answers", memory_type="preference")
    result = tool_memory_search(store, query="concise", limit=5)
    assert "results" in result
    assert len(result["results"]) >= 1
    store.close()


def test_tool_context(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add("Sapan likes bullets", memory_type="preference")
    result = tool_memory_context(store, query="answer style", limit=5)
    assert "text" in result
    assert "memory_count" in result
    store.close()


def test_tool_add_prompt(tmp_path: Path) -> None:
    store = _store(tmp_path)
    result = tool_memory_add_prompt(store, prompt="Translate this text to French.")
    assert "id" in result
    assert "prompt_score" in result
    store.close()


def test_tool_list(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add("memory one")
    store.add("memory two")
    result = tool_memory_list(store, limit=10)
    assert "memories" in result
    assert len(result["memories"]) == 2
    store.close()


def test_tool_stats(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.add("something")
    result = tool_memory_stats(store)
    assert "total_memories" in result
    assert result["total_memories"] >= 1
    store.close()


def test_tool_doctor_diagnose(tmp_path: Path) -> None:
    store = _store(tmp_path)
    result = tool_doctor_diagnose(store, prompt="Write answer for feature velocity.")
    assert "context_health_score" in result
    assert "recommended_prompt" in result
    store.close()


def test_tool_analytics_usage_summary_without_tracer() -> None:
    result = tool_analytics_usage_summary(None, days=7)
    assert result == {
        "error": "Tracing is not enabled on this server. Restart with --trace to use this tool."
    }


def test_tool_analytics_usage_summary_with_tracer(tmp_path: Path) -> None:
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    tracer.log(name="chat", input_tokens=10, output_tokens=5)
    result = tool_analytics_usage_summary(tracer, days=7)
    assert result["total_requests"] >= 1
    tracer.close()


def test_tool_analytics_prompt_patterns_with_tracer(tmp_path: Path) -> None:
    store = _store(tmp_path)
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    result = tool_analytics_prompt_patterns(store, tracer, days=30)
    assert "top_topics" in result
    store.close()
    tracer.close()


def test_tool_report_generate_with_tracer(tmp_path: Path) -> None:
    store = _store(tmp_path)
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    out = tmp_path / "report.html"
    result = tool_report_generate(store, tracer, out=str(out), days=30)
    assert result["path"] == str(out)
    assert out.exists()
    store.close()
    tracer.close()
