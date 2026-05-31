"""Public GenAIScope exceptions."""


class GenAIScopeError(Exception):
    """Base package error."""


class ConfigurationError(GenAIScopeError):
    """Raised when configuration is invalid."""


class ProviderError(GenAIScopeError):
    """Raised when provider operations fail."""


class ValidationError(GenAIScopeError):
    """Raised when validation fails."""


class EvaluationError(GenAIScopeError):
    """Raised when evaluation fails."""


class InvalidBackendError(GenAIScopeError):
    """Raised for unsupported storage backends."""


class BackendNotAvailableError(GenAIScopeError):
    """Raised when a requested backend cannot be used."""


class RedisDependencyMissingError(BackendNotAvailableError):
    """Raised when redis-py is not installed."""


class RedisConnectionError(BackendNotAvailableError):
    """Raised when Redis cannot be reached."""


class MemoryNotFoundError(GenAIScopeError):
    """Raised when a requested memory does not exist."""
