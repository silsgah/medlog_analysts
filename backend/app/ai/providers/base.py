"""
AI Freight Copilot — Abstract LLM Provider.

Base protocol and types for all AI provider implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """A chat message."""
    role: MessageRole
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    """Response from an embedding provider."""
    embeddings: list[list[float]]
    model: str
    provider: str
    total_tokens: int = 0
    dimensions: int = 0


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        ...

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        ...

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM."""
        ...

    async def health_check(self) -> bool:
        """Check if the provider is available."""
        try:
            response = await self.generate(
                [Message(role=MessageRole.USER, content="ping")],
                max_tokens=5,
            )
            return bool(response.content)
        except Exception:
            return False


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        ...

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        **kwargs: Any,
    ) -> EmbeddingResponse:
        """Generate embeddings for the given texts."""
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        ...
