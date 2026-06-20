"""OpenAI provider adapter.

Requires: pip install "genaiscope[providers]"
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from genaiscope.adapters.base import MemoryAdapter
from genaiscope.analyzers import CostAnalyzer
from genaiscope.core.errors import ProviderDependencyMissingError

if TYPE_CHECKING:
    from genaiscope.memory.base import BaseMemoryStore


class OpenAIAdapter(MemoryAdapter):
    """Wraps the OpenAI client with automatic memory injection and persistence."""

    def __init__(self, memory: BaseMemoryStore, client: Any = None, **kwargs: Any) -> None:
        if client is None:
            try:
                from openai import OpenAI

                client = OpenAI()
            except ImportError as exc:
                raise ProviderDependencyMissingError(
                    'openai is not installed. Run: pip install "genaiscope[providers]"'
                ) from exc
        super().__init__(memory, client, **kwargs)

    def with_memory(self, messages: list[dict]) -> list[dict]:
        query = self._last_user_content(messages)
        block = self._build_context_block(query) if query else ""
        result: list[dict] = []
        injected = False
        for msg in messages:
            if msg.get("role") == "system" and not injected:
                content = msg.get("content", "")
                result.append({**msg, "content": content + block})
                injected = True
            else:
                result.append(msg)
        if not injected and block:
            result = [{"role": "system", "content": block.strip()}, *result]
        return result

    def chat(self, messages: list[dict], **provider_kwargs: Any) -> Any:
        query = self._last_user_content(messages)
        augmented = self.with_memory(messages)

        if self.store_user_turns and query:
            self.memory.add(
                query, memory_type="conversation", source="openai_adapter",
                user_id=self.user_id, project_id=self.project_id,
            )

        model_name = provider_kwargs.get("model")
        if self.tracer is None:
            response = self.client.chat.completions.create(messages=augmented, **provider_kwargs)
        else:
            with self.tracer.trace(name="chat", model=model_name, provider="openai") as span:
                response = self.client.chat.completions.create(messages=augmented, **provider_kwargs)
                resp_model = getattr(response, "model", None) or model_name
                usage = getattr(response, "usage", None)
                input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
                output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
                span.model = resp_model
                span.log_tokens(input_tokens=input_tokens or 0, output_tokens=output_tokens or 0)
                if resp_model:
                    cost = CostAnalyzer().estimate_cost(resp_model, input_tokens or 0, output_tokens or 0)
                    span.log_cost(cost["total_cost"])

        if self.store_assistant_turns:
            try:
                reply = response.choices[0].message.content or ""
                if reply:
                    self.memory.add(
                        reply, memory_type="conversation", source="openai_adapter_reply",
                        user_id=self.user_id, project_id=self.project_id,
                    )
            except Exception:
                pass

        return response
