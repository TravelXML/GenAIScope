"""GenAIScope: Inspect, test, secure, optimize, and operationalize GenAI applications."""

__version__ = "0.1.0"
__author__ = "GenAIScope Contributors"
__license__ = "MIT"

from genaiscope.core.models import (
    EvaluationResult,
    InspectionReport,
    Provider,
    ScopeConfig,
)
from genaiscope.core.result import Result, ResultStatus
from genaiscope.inspect import Inspector
from genaiscope.scoring import ScoringEngine

__all__ = [
    "EvaluationResult",
    "InspectionReport",
    "Inspector",
    "Provider",
    "Result",
    "ResultStatus",
    "ScopeConfig",
    "ScoringEngine",
]
