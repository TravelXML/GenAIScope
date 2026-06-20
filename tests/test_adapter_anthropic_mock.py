"""Anthropic adapter tests using a mock client."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from genaiscope.adapters.anthropic_adapter import AnthropicAdapter
from genaiscope.memory.factory import MemoryStore
from genaiscope.tracing import LocalTracer


def _mock_anthropic_client(reply: str = "mock response"):
    content_block = SimpleNamespace(text=reply)
    msg = SimpleNamespace(content=[content_block])
    client = MagicMock()
    client.messages.create.return_value = msg
    return client


def test_anthropic_adapter_injects_system(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    store.add("User prefers concise answers and clear style", memory_type="preference", user_id="u1")

    mock_client = _mock_anthropic_client()
    adapter = AnthropicAdapter(store, mock_client, user_id="u1", store_user_turns=False)

    messages = [{"role": "user", "content": "concise answers style preference"}]
    adapter.chat(messages=messages)

    call_kwargs = mock_client.messages.create.call_args.kwargs
    system_param = call_kwargs.get("system", "")
    assert "preference" in system_param.lower() or "concise" in system_param.lower()
    store.close()


def test_anthropic_adapter_stores_user_turn(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    adapter = AnthropicAdapter(
        store, _mock_anthropic_client(), user_id="u1", store_user_turns=True
    )
    adapter.chat(messages=[{"role": "user", "content": "Remember I like bullets"}])

    items = store.list(user_id="u1", memory_type="conversation")
    assert len(items) >= 1
    store.close()


def test_anthropic_adapter_chat_records_trace(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "traces.db")
    adapter = AnthropicAdapter(
        store, _mock_anthropic_client("Hello!"), user_id="u1", store_user_turns=False, tracer=tracer
    )

    adapter.chat(messages=[{"role": "user", "content": "Say hello"}])

    traces = tracer.list()
    assert len(traces) == 1
    assert traces[0].provider == "anthropic"
    assert traces[0].status == "success"
    # the mock response has no .usage, so extraction must degrade to zero, not crash
    assert traces[0].input_tokens == 0
    assert traces[0].output_tokens == 0
    assert traces[0].estimated_cost == 0.0
    store.close()
    tracer.close()


def test_anthropic_adapter_chat_trace_records_error_and_propagates(tmp_path: Path) -> None:
    store = MemoryStore(db_path=tmp_path / "m.db")
    tracer = LocalTracer(db_path=tmp_path / "traces.db")
    mock_client = _mock_anthropic_client()
    mock_client.messages.create.side_effect = RuntimeError("boom")
    adapter = AnthropicAdapter(store, mock_client, user_id="u1", store_user_turns=False, tracer=tracer)

    with pytest.raises(RuntimeError, match="boom"):
        adapter.chat(messages=[{"role": "user", "content": "hi"}])

    traces = tracer.list()
    assert len(traces) == 1
    assert traces[0].status == "error"
    assert "boom" in (traces[0].error or "")
    store.close()
    tracer.close()
