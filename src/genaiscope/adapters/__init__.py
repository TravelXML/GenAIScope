"""Provider adapters for OpenAI, Anthropic, and Gemini with memory auto-injection."""

from genaiscope.adapters.anthropic_adapter import AnthropicAdapter
from genaiscope.adapters.base import MemoryAdapter
from genaiscope.adapters.gemini_adapter import GeminiAdapter
from genaiscope.adapters.openai_adapter import OpenAIAdapter
from genaiscope.adapters.summarizers import (
    anthropic_summarizer,
    gemini_summarizer,
    openai_summarizer,
)

__all__ = [
    "AnthropicAdapter",
    "GeminiAdapter",
    "MemoryAdapter",
    "OpenAIAdapter",
    "anthropic_summarizer",
    "gemini_summarizer",
    "openai_summarizer",
]
