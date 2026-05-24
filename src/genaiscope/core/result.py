"""Result type for operations."""

from enum import Enum
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


class ResultStatus(str, Enum):
    """Status of an operation."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class Result(Generic[T]):
    """Generic result wrapper."""

    def __init__(
        self,
        status: ResultStatus,
        data: Optional[T] = None,
        error: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """Initialize a result."""
        self.status = status
        self.data = data
        self.error = error
        self.message = message

    @property
    def is_success(self) -> bool:
        """Check if result is successful."""
        return self.status == ResultStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Check if result is a failure."""
        return self.status == ResultStatus.FAILURE

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Result(status={self.status}, data={self.data}, error={self.error})"

    def __bool__(self) -> bool:
        """Return truthiness based on status."""
        return self.is_success
