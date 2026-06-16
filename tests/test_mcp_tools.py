"""Tests for MCP tool functions — no live transport needed."""

import tempfile
from pathlib import Path

import pytest

from genaiscope.memory.factory import MemoryStore
from genaiscope.mcp.tools import (
    tool_memory_add_prompt,
    tool_memory_context,
    tool_memory_list,
    tool_memory_remember,
    tool_memory_search,
    tool_memory_stats,
)


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
