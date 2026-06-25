"""AnalyticsEngine -- `scope.analytics` facade over usage_summary/prompt_patterns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from genaiscope.analytics.models import PromptPatterns, UsageSummary
from genaiscope.analytics.patterns import prompt_patterns
from genaiscope.analytics.usage import usage_summary

if TYPE_CHECKING:
    from genaiscope.memory import BaseMemoryStore
    from genaiscope.tracing import LocalTracer


class AnalyticsEngine:
    """`scope.analytics.usage_summary(...)` / `scope.analytics.prompt_patterns(...)`."""

    def __init__(self, memory: BaseMemoryStore, tracer: LocalTracer) -> None:
        self._memory = memory
        self._tracer = tracer

    def usage_summary(self, days: int = 7) -> UsageSummary:
        return usage_summary(self._tracer, days=days)

    def prompt_patterns(self, days: int = 30) -> PromptPatterns:
        return prompt_patterns(self._memory, self._tracer, days=days)
