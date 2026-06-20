"""Gemini adapter tests using a mock client."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from genaiscope.adapters.gemini_adapter import GeminiAdapter
from genaiscope.memory.factory import MemoryStore
from genaiscope.tracing import LocalTracer


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


def test_gemini_adapter_chat_records_trace(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "traces.db")
    adapter = GeminiAdapter(store, _mock_genai("Hello!"), user_id="u1", store_user_turns=False, tracer=tracer)

    adapter.chat(messages=[{"role": "user", "content": "hello"}])

    traces = tracer.list()
    assert len(traces) == 1
    assert traces[0].provider == "gemini"
    assert traces[0].status == "success"
    # the mock response has no .usage_metadata, so extraction must degrade to zero, not crash
    assert traces[0].input_tokens == 0
    assert traces[0].output_tokens == 0
    assert traces[0].estimated_cost == 0.0
    store.close()
    tracer.close()


def test_gemini_adapter_chat_trace_records_error_and_propagates(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "traces.db")
    mock_client = _mock_genai()
    mock_client.GenerativeModel.return_value.generate_content.side_effect = RuntimeError("boom")
    adapter = GeminiAdapter(store, mock_client, user_id="u1", store_user_turns=False, tracer=tracer)

    with pytest.raises(RuntimeError, match="boom"):
        adapter.chat(messages=[{"role": "user", "content": "hi"}])

    traces = tracer.list()
    assert len(traces) == 1
    assert traces[0].status == "error"
    assert "boom" in (traces[0].error or "")
    store.close()
    tracer.close()
