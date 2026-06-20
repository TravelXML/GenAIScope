"""Tests for provider-agnostic compaction summarizer factories — mocked clients."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from genaiscope.adapters.summarizers import (
    anthropic_summarizer,
    gemini_summarizer,
    openai_summarizer,
)
from genaiscope.core.errors import ProviderDependencyMissingError


def _mock_openai_client(reply: str = "merged note") -> MagicMock:
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=reply))]
    )
    return client


def test_openai_summarizer_merges_texts() -> None:
    client = _mock_openai_client()
    summarize = openai_summarizer(client=client, model="gpt-4o-mini")
    result = summarize(["fact one", "fact two"])
    assert result == "merged note"
    call_kwargs = client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o-mini"
    assert "fact one" in call_kwargs["messages"][0]["content"]
    assert "fact two" in call_kwargs["messages"][0]["content"]


def _mock_anthropic_client(reply: str = "merged note") -> MagicMock:
    client = MagicMock()
    client.messages.create.return_value = SimpleNamespace(content=[SimpleNamespace(text=reply)])
    return client


def test_anthropic_summarizer_merges_texts() -> None:
    client = _mock_anthropic_client()
    summarize = anthropic_summarizer(client=client, model="claude-3-5-haiku-20241022")
    result = summarize(["fact one", "fact two"])
    assert result == "merged note"
    call_kwargs = client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-3-5-haiku-20241022"


def _mock_gemini_client(reply: str = "merged note") -> MagicMock:
    model_instance = MagicMock()
    model_instance.generate_content.return_value = SimpleNamespace(text=reply)
    client = MagicMock()
    client.GenerativeModel.return_value = model_instance
    return client


def test_gemini_summarizer_merges_texts() -> None:
    client = _mock_gemini_client()
    summarize = gemini_summarizer(client=client, model="gemini-1.5-flash")
    result = summarize(["fact one", "fact two"])
    assert result == "merged note"
    client.GenerativeModel.assert_called_with("gemini-1.5-flash")


def test_openai_summarizer_missing_sdk_raises() -> None:
    try:
        import openai  # noqa: F401

        pytest.skip("openai is installed")
    except ImportError:
        pass
    with pytest.raises(ProviderDependencyMissingError):
        openai_summarizer()


def test_anthropic_summarizer_missing_sdk_raises() -> None:
    try:
        import anthropic  # noqa: F401

        pytest.skip("anthropic is installed")
    except ImportError:
        pass
    with pytest.raises(ProviderDependencyMissingError):
        anthropic_summarizer()


def test_gemini_summarizer_missing_sdk_raises() -> None:
    try:
        import google.generativeai  # noqa: F401

        pytest.skip("google-generativeai is installed")
    except ImportError:
        pass
    with pytest.raises(ProviderDependencyMissingError):
        gemini_summarizer()
