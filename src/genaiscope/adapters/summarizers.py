"""Provider-agnostic summarizer factories for LLM-assisted memory compaction.

Each factory returns a ``Callable[[list[str]], str]`` that merges a cluster
of near-duplicate memory contents into one sentence preserving all facts.
Requires: pip install "genaiscope[providers]"
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from genaiscope.core.errors import ProviderDependencyMissingError

Summarizer = Callable[[list[str]], str]

_PROMPT_PREFIX = "Merge these near-duplicate notes into one concise sentence that preserves all facts:\n"


def _build_prompt(texts: list[str]) -> str:
    return _PROMPT_PREFIX + "\n".join(f"- {text}" for text in texts)


def openai_summarizer(client: Any = None, model: str = "gpt-4o-mini") -> Summarizer:
    """Build a summarizer backed by the OpenAI chat completions API."""

    if client is None:
        try:
            from openai import OpenAI

            client = OpenAI()
        except ImportError as exc:
            raise ProviderDependencyMissingError(
                'openai is not installed. Run: pip install "genaiscope[providers]"'
            ) from exc

    def _summarize(texts: list[str]) -> str:
        response = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": _build_prompt(texts)}]
        )
        return response.choices[0].message.content or ""

    return _summarize


def anthropic_summarizer(client: Any = None, model: str = "claude-3-5-haiku-20241022") -> Summarizer:
    """Build a summarizer backed by the Anthropic messages API."""

    if client is None:
        try:
            from anthropic import Anthropic

            client = Anthropic()
        except ImportError as exc:
            raise ProviderDependencyMissingError(
                'anthropic is not installed. Run: pip install "genaiscope[providers]"'
            ) from exc

    def _summarize(texts: list[str]) -> str:
        response = client.messages.create(
            model=model, max_tokens=256, messages=[{"role": "user", "content": _build_prompt(texts)}]
        )
        return response.content[0].text if response.content else ""

    return _summarize


def gemini_summarizer(client: Any = None, model: str = "gemini-1.5-flash") -> Summarizer:
    """Build a summarizer backed by the google-generativeai API."""

    if client is None:
        try:
            import google.generativeai as genai  # type: ignore[import-not-found]

            client = genai
        except ImportError as exc:
            raise ProviderDependencyMissingError(
                'google-genai is not installed. Run: pip install "genaiscope[providers]"'
            ) from exc

    def _summarize(texts: list[str]) -> str:
        generative_model = client.GenerativeModel(model)
        response = generative_model.generate_content(_build_prompt(texts))
        return response.text if hasattr(response, "text") else ""

    return _summarize
