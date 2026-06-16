"""Adapter response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AdapterResponse(BaseModel):
    """Wraps provider response with memory context metadata."""

    raw: Any
    context_injected: bool = False
    memory_count: int = 0
    user_turn_stored: bool = False
    assistant_turn_stored: bool = False
