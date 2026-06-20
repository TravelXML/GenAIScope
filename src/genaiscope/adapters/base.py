"""Base provider adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from genaiscope.tracing import LocalTracer

if TYPE_CHECKING:
    from genaiscope.memory.base import BaseMemoryStore


class MemoryAdapter:
    """Wraps a provider client to inject memory context and persist turns."""

    def __init__(
        self,
        memory: BaseMemoryStore,
        client: Any = None,
        *,
        user_id: str | None = None,
        project_id: str | None = None,
        inject_limit: int = 10,
        max_context_chars: int = 2000,
        store_user_turns: bool = True,
        store_assistant_turns: bool = False,
        context_mode: str = "hybrid",
        tracer: LocalTracer | None = None,
    ) -> None:
        self.memory = memory
        self.client = client
        self.user_id = user_id
        self.project_id = project_id
        self.inject_limit = inject_limit
        self.max_context_chars = max_context_chars
        self.store_user_turns = store_user_turns
        self.store_assistant_turns = store_assistant_turns
        self.context_mode = context_mode
        self.tracer = tracer

    def _build_context_block(self, query: str) -> str:
        ctx = self.memory.context(
            query,
            user_id=self.user_id,
            project_id=self.project_id,
            limit=self.inject_limit,
            max_chars=self.max_context_chars,
            mode=self.context_mode,
        )
        if not ctx.text:
            return ""
        return f"\n\n[Memory context]\n{ctx.text}\n[End of memory context]"

    def _last_user_content(self, messages: list[dict]) -> str:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, list):
                    return " ".join(
                        part.get("text", "") for part in content if isinstance(part, dict)
                    )
                return str(content)
        return ""

    def with_memory(self, messages: list[dict]) -> list[dict]:
        """Return a copy of messages with memory context injected into the system message."""
        raise NotImplementedError

    def chat(self, messages: list[dict], **provider_kwargs: Any) -> Any:
        """Call the provider with memory-injected messages and optionally persist turns."""
        raise NotImplementedError
