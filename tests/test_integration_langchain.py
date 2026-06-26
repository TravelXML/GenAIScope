"""Tests for the LangChain chat history adapter -- against the real installed ABC."""

from pathlib import Path

import pytest

pytest.importorskip("langchain_core")

from langchain_core.messages import AIMessage, HumanMessage

from genaiscope.integrations.langchain import GenAIScopeChatMessageHistory
from genaiscope.memory.factory import MemoryStore


def test_add_and_read_messages_in_order(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    history = GenAIScopeChatMessageHistory(store, session_id="s1")

    history.add_user_message("hello")
    history.add_ai_message("hi there")

    messages = history.messages
    assert len(messages) == 2
    assert isinstance(messages[0], HumanMessage)
    assert messages[0].content == "hello"
    assert isinstance(messages[1], AIMessage)
    assert messages[1].content == "hi there"
    store.close()


def test_messages_scoped_by_session_id(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    history_a = GenAIScopeChatMessageHistory(store, session_id="a")
    history_b = GenAIScopeChatMessageHistory(store, session_id="b")

    history_a.add_user_message("for a")
    history_b.add_user_message("for b")

    assert [m.content for m in history_a.messages] == ["for a"]
    assert [m.content for m in history_b.messages] == ["for b"]
    store.close()


def test_clear_removes_messages(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    history = GenAIScopeChatMessageHistory(store, session_id="s1")
    history.add_user_message("hello")

    history.clear()

    assert history.messages == []
    store.close()
