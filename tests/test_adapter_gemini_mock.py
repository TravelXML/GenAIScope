"""Gemini adapter tests using a mock client."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from genaiscope.adapters.gemini_adapter import GeminiAdapter
from genaiscope.memory.factory import MemoryStore


def _mock_genai(reply: str = "mock gemini response"):
    model_instance = MagicMock()
    model_instance.generate_content.return_value = SimpleNamespace(text=reply)
    client = MagicMock()
    client.GenerativeModel.return_value = model_instance
    return client


def test_gemini_adapter_chat(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    store.add("User prefers concise answers", memory_type="preference", user_id="u1")
    mock_client = _mock_genai()

    adapter = GeminiAdapter(store, mock_client, user_id="u1", store_user_turns=False)
    response = adapter.chat(messages=[{"role": "user", "content": "hello"}])
    assert response.text == "mock gemini response"
    store.close()


def test_gemini_adapter_stores_turn(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    adapter = GeminiAdapter(
        store, _mock_genai(), user_id="u1", store_user_turns=True
    )
    adapter.chat(messages=[{"role": "user", "content": "some question"}])
    items = store.list(user_id="u1", memory_type="conversation")
    assert len(items) >= 1
    store.close()
