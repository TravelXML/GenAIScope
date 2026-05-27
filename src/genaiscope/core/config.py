"""Configuration management."""

import os
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel


class Config(BaseModel):
    """Global configuration."""

    # Provider settings
    provider: str = os.getenv("GENAISCOPE_PROVIDER", "openai")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")

    # Model settings
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    google_model: str = os.getenv("GOOGLE_MODEL", "gemini-pro")

    # Execution settings
    max_tokens: int = int(os.getenv("GENAISCOPE_MAX_TOKENS", "2048"))
    temperature: float = float(os.getenv("GENAISCOPE_TEMPERATURE", "0.7"))
    timeout: int = int(os.getenv("GENAISCOPE_TIMEOUT", "30"))
    retries: int = int(os.getenv("GENAISCOPE_RETRIES", "3"))

    # Logging settings
    log_level: str = os.getenv("GENAISCOPE_LOG_LEVEL", "INFO")
    log_file: str | None = os.getenv("GENAISCOPE_LOG_FILE")

    class Config:
        """Pydantic config."""

        extra = "allow"

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment."""
        load_dotenv()
        return cls()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump(exclude_none=True)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration."""
    global _config
    _config = config
