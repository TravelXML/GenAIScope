"""ContextBuilder -- retrieves relevant memory and builds an improved prompt."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from genaiscope.context.models import ContextBuildResult
from genaiscope.doctor.prompt_improver import build_recommended_prompt, detect_missing_context
from genaiscope.doctor.scoring import context_completeness_score

if TYPE_CHECKING:
    from genaiscope.memory.base import BaseMemoryStore

_INCLUDABLE_TYPES = {
    "profile_memory": "include_profile",
    "project_memory": "include_projects",
    "preference_memory": "include_preferences",
}


def _estimate_tokens(text: str) -> int:
    """Zero-dependency chars/4 token estimate."""
    return max(0, len(text) // 4)


class ContextBuilder:
    """Builds an injectable context block and an improved prompt from memory."""

    def __init__(self, memory_store: BaseMemoryStore) -> None:
        self._memory = memory_store

    def build(
        self,
        user_prompt: str,
        top_k: int = 5,
        include_profile: bool = True,
        include_projects: bool = True,
        include_preferences: bool = True,
        user_id: str | None = None,
        project_id: str | None = None,
        workspace_id: str | None = None,
        max_chars: int | None = None,
    ) -> ContextBuildResult:
        """Retrieve relevant memory and build context_text/improved_prompt."""

        flags = {
            "profile_memory": include_profile,
            "project_memory": include_projects,
            "preference_memory": include_preferences,
        }

        results = self._memory.search(
            user_prompt,
            limit=top_k,
            user_id=user_id,
            project_id=project_id,
            workspace_id=workspace_id,
        )

        retrieved: list[dict[str, Any]] = []
        for result in results:
            memory_type = result.item.memory_type
            if memory_type in flags and not flags[memory_type]:
                continue
            retrieved.append(
                {
                    "id": result.item.id,
                    "content": result.item.content,
                    "memory_type": memory_type,
                    "tags": result.item.tags,
                    "score": result.score,
                }
            )

        context_text = "\n".join(f"- [{m['memory_type']}] {m['content']}" for m in retrieved)
        if max_chars:
            context_text = context_text[:max_chars]

        missing = detect_missing_context(user_prompt, retrieved, check_memory_references=False)
        improved_prompt = build_recommended_prompt(user_prompt, retrieved, missing)
        # Deliberately omits missing_context here: that signal measures
        # prompt specificity (prompt_clarity_score's job), not retrieval
        # completeness, which is what context_quality_score represents.
        quality_score = context_completeness_score(retrieved, requested_top_k=top_k)

        return ContextBuildResult(
            original_prompt=user_prompt,
            retrieved_memories=retrieved,
            context_text=context_text,
            improved_prompt=improved_prompt,
            token_estimate=_estimate_tokens(context_text) + _estimate_tokens(improved_prompt),
            memory_ids_used=[m["id"] for m in retrieved],
            context_quality_score=quality_score,
        )
