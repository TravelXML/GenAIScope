"""Anthropic provider adapter.

Requires: pip install "genaiscope[providers]"
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from genaiscope.adapters.base import MemoryAdapter
from genaiscope.core.errors import ProviderDependencyMissingError

if TYPE_CHECKING:
    from genaiscope.memory.base import BaseMemoryStore


class AnthropicAdapter(MemoryAdapter):
    """Wraps the Anthropic client with automatic memory injection and persistence."""

    def __init__(self, memory: BaseMemoryStore, client: Any = None, **kwargs: Any) -> None:
        if client is None:
            try:
                from anthropic import Anthropic

                client = Anthropic()
            except ImportError as exc:
                raise ProviderDependencyMissingError(
                    'anthropic is not installed. Run: pip install "genaiscope[providers]"'
                ) from exc
        super().__init__(memory, client, **kwargs)

    def with_memory(self, messages: list[dict]) -> list[dict]:
        """Return messages unchanged; system param handled separately in chat()."""
        return list(messages)

    def chat(self, messages: list[dict], model: str = "claude-sonnet-4-6", **provider_kwargs: Any) -> Any:
        query = self._last_user_content(messages)
        block = self._build_context_block(query) if query else ""

        existing_system = provider_kwargs.pop("system", "")
        system_content = (existing_system + block).strip()

        if self.store_user_turns and query:
            self.memory.add(
                query, memory_type="conversation", source="anthropic_adapter",
                user_id=self.user_id, project_id=self.project_id,
            )

        kwargs: dict[str, Any] = {"model": model, "messages": messages, **provider_kwargs}
        if system_content:
            kwargs["system"] = system_content

        response = self.client.messages.create(**kwargs)

        if self.store_assistant_turns:
            try:
                reply = response.content[0].text if response.content else ""
                if reply:
                    self.memory.add(
                        reply, memory_type="conversation", source="anthropic_adapter_reply",
                        user_id=self.user_id, project_id=self.project_id,
                    )
            except Exception:
                pass

        return response
