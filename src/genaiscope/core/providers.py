"""Provider interfaces and implementations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import aiohttp
import httpx

from genaiscope.core.errors import ProviderError


class BaseProvider(ABC):
    """Base class for all providers."""

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize provider."""
        self.api_key = api_key
        self.kwargs = kwargs

    @abstractmethod
    async def call(self, prompt: str, **kwargs: Any) -> str:
        """Call the provider's API."""
        pass

    @abstractmethod
    def validate(self) -> None:
        """Validate provider configuration."""
        pass


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4", **kwargs: Any) -> None:
        """Initialize OpenAI provider."""
        super().__init__(api_key, **kwargs)
        self.model = model
        self.base_url = "https://api.openai.com/v1"

    def validate(self) -> None:
        """Validate OpenAI API key."""
        if not self.api_key:
            raise ProviderError("OpenAI API key is required")

    async def call(self, prompt: str, **kwargs: Any) -> str:
        """Call OpenAI API."""
        self.validate()

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                data = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": kwargs.get("max_tokens", 2048),
                    "temperature": kwargs.get("temperature", 0.7),
                }
                async with session.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=data
                ) as response:
                    if response.status != 200:
                        raise ProviderError(f"OpenAI API error: {response.status}")
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except aiohttp.ClientError as e:
            raise ProviderError(f"OpenAI API call failed: {e}")


class AnthropicProvider(BaseProvider):
    """Anthropic provider implementation."""

    def __init__(
        self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229", **kwargs: Any
    ) -> None:
        """Initialize Anthropic provider."""
        super().__init__(api_key, **kwargs)
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"

    def validate(self) -> None:
        """Validate Anthropic API key."""
        if not self.api_key:
            raise ProviderError("Anthropic API key is required")

    async def call(self, prompt: str, **kwargs: Any) -> str:
        """Call Anthropic API."""
        self.validate()

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                }
                data = {
                    "model": self.model,
                    "max_tokens": kwargs.get("max_tokens", 2048),
                    "messages": [{"role": "user", "content": prompt}],
                }
                async with session.post(
                    f"{self.base_url}/messages", headers=headers, json=data
                ) as response:
                    if response.status != 200:
                        raise ProviderError(f"Anthropic API error: {response.status}")
                    result = await response.json()
                    return result["content"][0]["text"]
        except aiohttp.ClientError as e:
            raise ProviderError(f"Anthropic API call failed: {e}")


class GoogleProvider(BaseProvider):
    """Google GenAI provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro", **kwargs: Any) -> None:
        """Initialize Google provider."""
        super().__init__(api_key, **kwargs)
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def validate(self) -> None:
        """Validate Google API key."""
        if not self.api_key:
            raise ProviderError("Google API key is required")

    async def call(self, prompt: str, **kwargs: Any) -> str:
        """Call Google GenAI API."""
        self.validate()

        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": kwargs.get("max_tokens", 2048),
                        "temperature": kwargs.get("temperature", 0.7),
                    },
                }
                async with session.post(
                    f"{self.base_url}/{self.model}:generateContent?key={self.api_key}",
                    json=data,
                ) as response:
                    if response.status != 200:
                        raise ProviderError(f"Google API error: {response.status}")
                    result = await response.json()
                    return result["candidates"][0]["content"]["parts"][0]["text"]
        except aiohttp.ClientError as e:
            raise ProviderError(f"Google API call failed: {e}")


class LocalProvider(BaseProvider):
    """Local/custom provider for testing and offline use."""

    def __init__(self, model_callable: Optional[Any] = None, **kwargs: Any) -> None:
        """Initialize local provider."""
        super().__init__(**kwargs)
        self.model_callable = model_callable

    def validate(self) -> None:
        """Validate local provider."""
        if not self.model_callable:
            raise ProviderError("Local provider requires a model_callable")

    async def call(self, prompt: str, **kwargs: Any) -> str:
        """Call local model."""
        self.validate()
        if callable(self.model_callable):
            return self.model_callable(prompt, **kwargs)
        raise ProviderError("Model callable is not callable")


def get_provider(provider_type: str, api_key: Optional[str] = None, **kwargs: Any) -> BaseProvider:
    """Get a provider instance by type."""
    providers: Dict[str, type] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "local": LocalProvider,
    }

    if provider_type not in providers:
        raise ProviderError(f"Unknown provider type: {provider_type}")

    provider_class = providers[provider_type]
    return provider_class(api_key=api_key, **kwargs)
