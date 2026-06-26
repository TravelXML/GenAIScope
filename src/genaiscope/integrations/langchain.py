"""LangChain chat message history backed by a GenAIScope MemoryStore.

Implements `langchain_core.chat_history.BaseChatMessageHistory` -- verified
against the installed `langchain-core` ABC (1.4.x): `messages` is a property,
`add_messages`/`clear` are the two methods to override (the base class's
default `add_message` delegates to `add_messages`). `messages` is read-only
here (it's computed from the store on every access, not cached), which is why
it needs `# type: ignore[override]` -- the base class declares it as a
mutable attribute, but the ABC's own example implementations show overriding
it as a property is an intended usage pattern, just one mypy can't model.

Requires: pip install "genaiscope[langchain]"
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from genaiscope.core.errors import LangChainDependencyMissingError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from genaiscope.memory.base import BaseMemoryStore

try:
    from langchain_core.chat_history import BaseChatMessageHistory
    from langchain_core.messages import BaseMessage
except ImportError as exc:
    raise LangChainDependencyMissingError(
        'langchain-core is not installed. Run: pip install "genaiscope[langchain]"'
    ) from exc


class GenAIScopeChatMessageHistory(BaseChatMessageHistory):
    """Drop-in LangChain memory backend: `MemoryStore.add(memory_type="conversation")`
    per message, role tracked in the existing `metadata` dict -- no schema change."""

    def __init__(
        self,
        store: BaseMemoryStore,
        session_id: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        limit: int = 50,
    ) -> None:
        self._store = store
        self.session_id = session_id
        self.user_id = user_id
        self.project_id = project_id
        self.limit = limit

    @property
    def messages(self) -> list[BaseMessage]:  # type: ignore[override]  # read-only by design, see module docstring
        from langchain_core.messages import AIMessage, HumanMessage

        items = self._store.list(
            memory_type="conversation",
            user_id=self.user_id,
            project_id=self.project_id,
            session_id=self.session_id,
            limit=self.limit,
        )
        # store.list() returns newest-first; chat history must read chronologically.
        ordered = list(reversed(items))
        result: list[BaseMessage] = []
        for item in ordered:
            role = item.metadata.get("role", "human")
            cls = AIMessage if role == "ai" else HumanMessage
            result.append(cls(content=item.content))
        return result

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        from langchain_core.messages import AIMessage

        for message in messages:
            role = "ai" if isinstance(message, AIMessage) else "human"
            self._store.add(
                str(message.content),
                memory_type="conversation",
                user_id=self.user_id,
                project_id=self.project_id,
                session_id=self.session_id,
                metadata={"role": role},
            )

    def clear(self) -> None:
        items = self._store.list(
            memory_type="conversation",
            user_id=self.user_id,
            project_id=self.project_id,
            session_id=self.session_id,
            limit=100_000,
        )
        for item in items:
            self._store.delete(item.id)
