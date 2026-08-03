"""
AI Freight Copilot — OpenAI Provider.

Implementation of the LLM and Embedding provider for OpenAI's API.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

import structlog
from openai import AsyncOpenAI

from app.ai.providers.base import (
    EmbeddingProvider,
    EmbeddingResponse,
    LLMProvider,
    LLMResponse,
    Message,
    MessageRole,
)
from app.config import get_settings

logger = structlog.get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=api_key or settings.openai_api_key.get_secret_value()
        )
        self._model = model or settings.openai_model
        self._default_max_tokens = settings.openai_max_tokens
        self._default_temperature = settings.openai_temperature

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response using OpenAI's chat completion API."""
        openai_messages = [
            {"role": m.role.value, "content": m.content} for m in messages
        ]

        request_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": openai_messages,
            "temperature": temperature if temperature is not None else self._default_temperature,
            "max_tokens": max_tokens or self._default_max_tokens,
        }

        if json_mode:
            request_kwargs["response_format"] = {"type": "json_object"}

        response = await self._client.chat.completions.create(**request_kwargs)

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            provider=self.provider_name,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            finish_reason=choice.finish_reason or "",
        )

    async def generate_stream(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate a streaming response using OpenAI."""
        openai_messages = [
            {"role": m.role.value, "content": m.content} for m in messages
        ]

        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=openai_messages,
            temperature=temperature if temperature is not None else self._default_temperature,
            max_tokens=max_tokens or self._default_max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    DIMENSIONS_MAP = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self, api_key: str | None = None, model: str | None = None
    ) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=api_key or settings.openai_api_key.get_secret_value()
        )
        self._model = model or settings.openai_embedding_model

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def dimensions(self) -> int:
        return self.DIMENSIONS_MAP.get(self._model, 1536)

    async def embed(
        self,
        texts: list[str],
        **kwargs: Any,
    ) -> EmbeddingResponse:
        """Generate embeddings using OpenAI's embedding API."""
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
        )

        embeddings = [item.embedding for item in response.data]

        return EmbeddingResponse(
            embeddings=embeddings,
            model=response.model,
            provider=self.provider_name,
            total_tokens=response.usage.total_tokens,
            dimensions=len(embeddings[0]) if embeddings else 0,
        )
