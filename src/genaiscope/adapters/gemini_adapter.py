"""Gemini provider adapter.

Requires: pip install "genaiscope[providers]"  (google-genai)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from genaiscope.adapters.base import MemoryAdapter
from genaiscope.core.errors import ProviderDependencyMissingError

if TYPE_CHECKING:
    from genaiscope.memory.base import BaseMemoryStore


class GeminiAdapter(MemoryAdapter):
    """Wraps the google-genai client with automatic memory injection and persistence."""

    def __init__(
        self,
        memory: BaseMemoryStore,
        client: Any = None,
        model: str = "gemini-1.5-flash",
        **kwargs: Any,
    ) -> None:
        if client is None:
            try:
                import google.generativeai as genai  # type: ignore[import-not-found]

                client = genai
            except ImportError as exc:
                raise ProviderDependencyMissingError(
                    'google-genai is not installed. Run: pip install "genaiscope[providers]"'
                ) from exc
        super().__init__(memory, client, **kwargs)
        self._model_name = model

    def with_memory(self, messages: list[dict]) -> list[dict]:
        """Return messages unchanged; system_instruction handled separately in chat()."""
        return list(messages)

    def chat(self, messages: list[dict], **provider_kwargs: Any) -> Any:
        query = self._last_user_content(messages)
        block = self._build_context_block(query) if query else ""

        if self.store_user_turns and query:
            self.memory.add(
                query, memory_type="conversation", source="gemini_adapter",
                user_id=self.user_id, project_id=self.project_id,
            )

        # Combine memory block with any existing system_instruction
        existing_si = provider_kwargs.pop("system_instruction", "")
        system_instruction = (existing_si + block).strip() or None

        # Convert OpenAI-style messages to Gemini content list
        contents = []
        for msg in messages:
            role = "user" if msg.get("role") in ("user", "system") else "model"
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    p.get("text", "") for p in content if isinstance(p, dict)
                )
            contents.append({"role": role, "parts": [{"text": content}]})

        model = self.client.GenerativeModel(
            self._model_name,
            system_instruction=system_instruction,
        )
        response = model.generate_content(contents, **provider_kwargs)

        if self.store_assistant_turns:
            try:
                reply = response.text if hasattr(response, "text") else ""
                if reply:
                    self.memory.add(
                        reply, memory_type="conversation", source="gemini_adapter_reply",
                        user_id=self.user_id, project_id=self.project_id,
                    )
            except Exception:
                pass

        return response
