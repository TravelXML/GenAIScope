"""LlamaIndex memory backed by a GenAIScope MemoryStore.

Implements `llama_index.core.memory.types.BaseMemory` -- verified against the
installed `llama-index-core` ABC (0.14.x). Unlike LangChain's ABC, LlamaIndex's
`BaseMemory` extends `BaseComponent` (a pydantic model), so the store and scope
fields are declared as pydantic fields with `arbitrary_types_allowed=True`
rather than set in a plain `__init__`. Abstract methods to implement:
`from_defaults`, `get`, `get_all`, `put`, `set`, `reset`.

Requires: pip install "genaiscope[llamaindex]"
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import ConfigDict

from genaiscope.core.errors import LlamaIndexDependencyMissingError

if TYPE_CHECKING:
    from genaiscope.memory.base import BaseMemoryStore

try:
    from llama_index.core.llms import ChatMessage
    from llama_index.core.memory.types import BaseMemory
except ImportError as exc:
    raise LlamaIndexDependencyMissingError(
        'llama-index-core is not installed. Run: pip install "genaiscope[llamaindex]"'
    ) from exc


class GenAIScopeMemory(BaseMemory):
    """Drop-in LlamaIndex memory backend: `MemoryStore.add(memory_type="conversation")`
    per message, role tracked in the existing `metadata` dict -- no schema change."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    store: Any
    session_id: str | None = None
    user_id: str | None = None
    project_id: str | None = None
    limit: int = 50

    @classmethod
    def class_name(cls) -> str:
        return "GenAIScopeMemory"

    @classmethod
    def from_defaults(
        cls,
        store: BaseMemoryStore | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        limit: int = 50,
        **kwargs: Any,
    ) -> GenAIScopeMemory:
        if store is None:
            raise ValueError("store is required")
        return cls(store=store, session_id=session_id, user_id=user_id, project_id=project_id, limit=limit)

    def get(self, input: str | None = None, **kwargs: Any) -> list[ChatMessage]:
        return self.get_all()

    def get_all(self) -> list[ChatMessage]:
        from llama_index.core.llms import MessageRole

        items = self.store.list(
            memory_type="conversation",
            user_id=self.user_id,
            project_id=self.project_id,
            session_id=self.session_id,
            limit=self.limit,
        )
        # store.list() returns newest-first; chat history must read chronologically.
        ordered = list(reversed(items))
        result: list[ChatMessage] = []
        for item in ordered:
            role = item.metadata.get("role", "user")
            message_role = MessageRole.ASSISTANT if role == "assistant" else MessageRole.USER
            result.append(ChatMessage(role=message_role, content=item.content))
        return result

    def put(self, message: ChatMessage) -> None:
        from llama_index.core.llms import MessageRole

        role = "assistant" if message.role == MessageRole.ASSISTANT else "user"
        self.store.add(
            str(message.content),
            memory_type="conversation",
            user_id=self.user_id,
            project_id=self.project_id,
            session_id=self.session_id,
            metadata={"role": role},
        )

    def set(self, messages: list[ChatMessage]) -> None:
        self.reset()
        for message in messages:
            self.put(message)

    def reset(self) -> None:
        items = self.store.list(
            memory_type="conversation",
            user_id=self.user_id,
            project_id=self.project_id,
            session_id=self.session_id,
            limit=100_000,
        )
        for item in items:
            self.store.delete(item.id)
