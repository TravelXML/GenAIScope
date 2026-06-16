"""GenAIScope: Inspect, test, secure, optimize, and operationalize GenAI applications."""

__version__ = "0.4.0"
__author__ = "GenAIScope Contributors"
__license__ = "MIT"

from genaiscope.core.models import (
    EvaluationResult,
    InspectionReport,
    Provider,
    ScopeConfig,
)
from genaiscope.core.result import Result, ResultStatus
from genaiscope.dashboard import generate_dashboard
from genaiscope.files import FileMemory
from genaiscope.inspect import Inspector
from genaiscope.memory import MemoryStore
from genaiscope.scoring import ScoringEngine
from genaiscope.tracing import LocalTracer

__all__ = [
    "EvaluationResult",
    "FileMemory",
    "InspectionReport",
    "Inspector",
    "LocalTracer",
    "MemoryStore",
    "Provider",
    "Result",
    "ResultStatus",
    "ScopeConfig",
    "ScoringEngine",
    "generate_dashboard",
]
