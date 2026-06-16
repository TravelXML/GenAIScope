"""OpenAI adapter tests using a mock client — no API key needed."""

import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from genaiscope.adapters.openai_adapter import OpenAIAdapter
from genaiscope.memory.factory import MemoryStore


def _mock_openai_client(reply: str = "mock response"):
    """Build a mock that mimics openai.OpenAI chat completions."""
    msg = SimpleNamespace(content=reply)
    choice = SimpleNamespace(message=msg)
    completion = SimpleNamespace(choices=[choice])
    client = MagicMock()
    client.chat.completions.create.return_value = completion
    return client


def test_adapter_injects_context(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    store.add("User prefers concise answers and clear style", memory_type="preference", user_id="u1")

    adapter = OpenAIAdapter(
        store, _mock_openai_client(), user_id="u1", store_user_turns=False
    )
    messages = [{"role": "user", "content": "concise answers style preference"}]
    augmented = adapter.with_memory(messages)

    # A system message with memory context should have been prepended or injected
    system_messages = [m for m in augmented if m.get("role") == "system"]
    assert system_messages, "No system message injected"
    assert "preference" in system_messages[0]["content"].lower() or "concise" in system_messages[0]["content"].lower()
    store.close()


def test_adapter_stores_user_turn(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    adapter = OpenAIAdapter(
        store, _mock_openai_client(), user_id="u1", store_user_turns=True
    )
    messages = [{"role": "user", "content": "Remember that I like bullets"}]
    adapter.chat(messages=messages, model="gpt-4o-mini")

    items = store.list(user_id="u1", memory_type="conversation")
    assert len(items) >= 1
    assert "bullets" in items[0].content
    store.close()


def test_adapter_chat_calls_provider(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    mock_client = _mock_openai_client("Hello!")
    adapter = OpenAIAdapter(store, mock_client, user_id="u1", store_user_turns=False)

    response = adapter.chat(
        messages=[{"role": "user", "content": "Say hello"}],
        model="gpt-4o-mini",
    )
    assert mock_client.chat.completions.create.called
    assert response.choices[0].message.content == "Hello!"
    store.close()


def test_adapter_missing_sdk_raises(tmp_path: Path) -> None:
    """If no client is passed and openai not installed, raise ProviderDependencyMissingError."""
    try:
        import openai  # noqa: F401

        pytest.skip("openai is installed")
    except ImportError:
        pass

    from genaiscope.core.errors import ProviderDependencyMissingError
    from genaiscope.memory.factory import MemoryStore

    store = MemoryStore(db_path=tmp_path / "m.db")
    with pytest.raises(ProviderDependencyMissingError):
        OpenAIAdapter(store)
    store.close()
