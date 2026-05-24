"""Error definitions for GenAIScope."""


class GenAIScopeError(Exception):
    """Base exception for all GenAIScope errors."""

    pass


class ConfigurationError(GenAIScopeError):
    """Raised when configuration is invalid."""

    pass


class ProviderError(GenAIScopeError):
    """Raised when provider operations fail."""

    pass


class ValidationError(GenAIScopeError):
    """Raised when validation fails."""

    pass


class EvaluationError(GenAIScopeError):
    """Raised when evaluation fails."""

    pass
