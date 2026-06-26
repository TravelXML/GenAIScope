"""Tests for the multi-provider live LLM gateway — adapters are mocked, no real API calls."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from genaiscope.core.errors import GatewayError
from genaiscope.gateway import GatewayClient
from genaiscope.memory.factory import MemoryStore
from genaiscope.tracing import LocalTracer


def _openai_response(reply: str = "hi from openai") -> SimpleNamespace:
    msg = SimpleNamespace(content=reply)
    choice = SimpleNamespace(message=msg)
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5)
    return SimpleNamespace(choices=[choice], usage=usage, model="gpt-4o-mini")


def _anthropic_response(reply: str = "hi from anthropic") -> SimpleNamespace:
    block = SimpleNamespace(text=reply)
    usage = SimpleNamespace(input_tokens=8, output_tokens=4)
    return SimpleNamespace(content=[block], usage=usage, model="claude-sonnet-4-6")


def _store(tmp_path: Path) -> MemoryStore:
    return MemoryStore(db_path=tmp_path / "m.db")


def test_complete_explicit_provider(tmp_path: Path) -> None:
    store = _store(tmp_path)
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    gw = GatewayClient(store, tracer)

    with patch("genaiscope.adapters.OpenAIAdapter") as mock_adapter:
        mock_adapter.return_value.chat.return_value = _openai_response("hello!")
        result = gw.complete("Write a poem", provider="openai")

    assert result.provider == "openai"
    assert result.text == "hello!"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.attempted_providers == ["openai"]
    assert result.context_health_score is not None
    assert len(tracer.list()) == 1
    store.close()
    tracer.close()


def test_complete_auto_routes_coding_prompt_to_openai(tmp_path: Path) -> None:
    store = _store(tmp_path)
    gw = GatewayClient(store, tracer=None)

    with patch("genaiscope.adapters.OpenAIAdapter") as mock_adapter:
        mock_adapter.return_value.chat.return_value = _openai_response()
        result = gw.complete("Refactor this Python function and fix the bug", provider="auto")

    assert result.provider == "openai"
    store.close()


def test_complete_falls_back_to_next_provider_on_failure(tmp_path: Path) -> None:
    store = _store(tmp_path)
    gw = GatewayClient(store, tracer=None)

    with (
        patch("genaiscope.adapters.OpenAIAdapter") as mock_openai,
        patch("genaiscope.adapters.AnthropicAdapter") as mock_anthropic,
    ):
        mock_openai.return_value.chat.side_effect = RuntimeError("rate limited")
        mock_anthropic.return_value.chat.return_value = _anthropic_response("fallback reply")
        result = gw.complete("Refactor this Python function and fix the bug", provider="auto")

    assert result.provider == "anthropic"
    assert result.text == "fallback reply"
    assert result.attempted_providers == ["openai", "anthropic"]
    store.close()


def test_complete_raises_gateway_error_when_all_candidates_fail(tmp_path: Path) -> None:
    store = _store(tmp_path)
    gw = GatewayClient(store, tracer=None)

    with (
        patch("genaiscope.adapters.OpenAIAdapter") as mock_openai,
        patch("genaiscope.adapters.AnthropicAdapter") as mock_anthropic,
    ):
        mock_openai.return_value.chat.side_effect = RuntimeError("down")
        mock_anthropic.return_value.chat.side_effect = RuntimeError("down")
        with pytest.raises(GatewayError):
            gw.complete("Refactor this Python function and fix the bug", provider="auto")

    store.close()


def test_complete_explicit_provider_no_adapter_raises(tmp_path: Path) -> None:
    store = _store(tmp_path)
    gw = GatewayClient(store, tracer=None)

    with pytest.raises(GatewayError):
        gw.complete("hello", provider="groq")

    store.close()
