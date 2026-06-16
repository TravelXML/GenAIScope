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


class EmbeddingBackendError(BackendNotAvailableError):
    """Raised when an embedding backend is unavailable or misconfigured."""


class VectorBackendError(BackendNotAvailableError):
    """Raised when the vector store backend is unavailable."""


class MCPDependencyMissingError(BackendNotAvailableError):
    """Raised when the mcp extra is not installed."""


class ServerDependencyMissingError(BackendNotAvailableError):
    """Raised when the server extra (FastAPI/uvicorn) is not installed."""


class ProviderDependencyMissingError(BackendNotAvailableError):
    """Raised when a provider SDK (openai/anthropic/google-genai) is not installed."""


class AdapterError(GenAIScopeError):
    """Raised when a provider adapter encounters an unrecoverable error."""
