"""Tests for the LlamaIndex memory adapter -- against the real installed ABC."""

from pathlib import Path

import pytest

pytest.importorskip("llama_index.core")

from llama_index.core.llms import ChatMessage, MessageRole

from genaiscope.integrations.llamaindex import GenAIScopeMemory
from genaiscope.memory.factory import MemoryStore


def test_put_and_get_all_messages_in_order(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    memory = GenAIScopeMemory.from_defaults(store=store, session_id="s1")

    memory.put(ChatMessage(role=MessageRole.USER, content="hello"))
    memory.put(ChatMessage(role=MessageRole.ASSISTANT, content="hi there"))

    messages = memory.get_all()
    assert len(messages) == 2
    assert messages[0].role == MessageRole.USER
    assert messages[0].content == "hello"
    assert messages[1].role == MessageRole.ASSISTANT
    assert messages[1].content == "hi there"
    store.close()


def test_get_delegates_to_get_all(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    memory = GenAIScopeMemory.from_defaults(store=store, session_id="s1")
    memory.put(ChatMessage(role=MessageRole.USER, content="hello"))

    assert memory.get() == memory.get_all()
    store.close()


def test_set_replaces_history(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    memory = GenAIScopeMemory.from_defaults(store=store, session_id="s1")
    memory.put(ChatMessage(role=MessageRole.USER, content="old message"))

    memory.set([ChatMessage(role=MessageRole.USER, content="new message")])

    messages = memory.get_all()
    assert len(messages) == 1
    assert messages[0].content == "new message"
    store.close()


def test_reset_clears_history(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    memory = GenAIScopeMemory.from_defaults(store=store, session_id="s1")
    memory.put(ChatMessage(role=MessageRole.USER, content="hello"))

    memory.reset()

    assert memory.get_all() == []
    store.close()


def test_from_defaults_requires_store() -> None:
    with pytest.raises(ValueError, match="store is required"):
        GenAIScopeMemory.from_defaults()
