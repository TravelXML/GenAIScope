"""Anthropic provider adapter.

Requires: pip install "genaiscope[providers]"
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from genaiscope.adapters.base import MemoryAdapter
from genaiscope.analyzers import CostAnalyzer
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

        if self.tracer is None:
            response = self.client.messages.create(**kwargs)
        else:
            with self.tracer.trace(name="chat", model=model, provider="anthropic") as span:
                response = self.client.messages.create(**kwargs)
                resp_model = getattr(response, "model", None) or model
                usage = getattr(response, "usage", None)
                input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
                output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
                span.model = resp_model
                span.log_tokens(input_tokens=input_tokens or 0, output_tokens=output_tokens or 0)
                if resp_model:
                    cost = CostAnalyzer().estimate_cost(resp_model, input_tokens or 0, output_tokens or 0)
                    span.log_cost(cost["total_cost"])

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
