"""Conventional memory_type string constants for the v0.6.0 memory layer.

MemoryItem.memory_type is (and remains) a free string -- these are typo-safe
constants, not an enforced enum, so existing/custom memory types keep working.
"""

from __future__ import annotations

PROFILE_MEMORY = "profile_memory"
PROJECT_MEMORY = "project_memory"
PREFERENCE_MEMORY = "preference_memory"
CONVERSATION_MEMORY = "conversation_memory"
DOCUMENT_MEMORY = "document_memory"
ENTITY_MEMORY = "entity_memory"
DECISION_MEMORY = "decision_memory"
LEARNING_MEMORY = "learning_memory"
PROMPT_PATTERN_MEMORY = "prompt_pattern_memory"

ALL_MEMORY_TYPES = (
    PROFILE_MEMORY,
    PROJECT_MEMORY,
    PREFERENCE_MEMORY,
    CONVERSATION_MEMORY,
    DOCUMENT_MEMORY,
    ENTITY_MEMORY,
    DECISION_MEMORY,
    LEARNING_MEMORY,
    PROMPT_PATTERN_MEMORY,
)
