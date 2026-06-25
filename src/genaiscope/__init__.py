"""GenAIScope: Inspect, test, secure, optimize, and operationalize GenAI applications."""

__version__ = "0.6.0"
__author__ = "GenAIScope Contributors"
__license__ = "MIT"

# v0.6.0 Context Doctor -- imported after the above so genaiscope.core's own
# (lazy) GenAIScope export never risks a circular import during bootstrap.
from genaiscope.context import ContextBuilder
from genaiscope.core.models import (
    EvaluationResult,
    InspectionReport,
    Provider,
    ScopeConfig,
)
from genaiscope.core.result import Result, ResultStatus
from genaiscope.core.scope import GenAIScope
from genaiscope.cost import CostEstimator
from genaiscope.dashboard import generate_dashboard
from genaiscope.doctor import ContextDoctor
from genaiscope.files import FileMemory
from genaiscope.inspect import Inspector
from genaiscope.memory import MemoryStore
from genaiscope.scoring import ScoringEngine
from genaiscope.tracing import LocalTracer

__all__ = [
    "ContextBuilder",
    "ContextDoctor",
    "CostEstimator",
    "EvaluationResult",
    "FileMemory",
    "GenAIScope",
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
