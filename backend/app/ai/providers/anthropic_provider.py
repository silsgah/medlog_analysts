"""
AI Freight Copilot — Anthropic Provider.

Implementation of the LLM provider for Anthropic's Claude API.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

import structlog
from anthropic import AsyncAnthropic

from app.ai.providers.base import LLMProvider, LLMResponse, Message, MessageRole
from app.config import get_settings

logger = structlog.get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(
            api_key=api_key or settings.anthropic_api_key.get_secret_value()
        )
        self._model = model or settings.anthropic_model
        self._default_max_tokens = settings.anthropic_max_tokens
        self._default_temperature = settings.anthropic_temperature

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response using Anthropic's messages API."""
        # Extract system message if present
        system_message = ""
        chat_messages = []
        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system_message = m.content
            else:
                chat_messages.append({"role": m.role.value, "content": m.content})

        request_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": chat_messages,
            "max_tokens": max_tokens or self._default_max_tokens,
            "temperature": temperature if temperature is not None else self._default_temperature,
        }

        if system_message:
            request_kwargs["system"] = system_message

        response = await self._client.messages.create(**request_kwargs)

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        return LLMResponse(
            content=content,
            model=response.model,
            provider=self.provider_name,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason or "",
        )

    async def generate_stream(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate a streaming response using Anthropic."""
        system_message = ""
        chat_messages = []
        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system_message = m.content
            else:
                chat_messages.append({"role": m.role.value, "content": m.content})

        request_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": chat_messages,
            "max_tokens": max_tokens or self._default_max_tokens,
            "temperature": temperature if temperature is not None else self._default_temperature,
        }

        if system_message:
            request_kwargs["system"] = system_message

        async with self._client.messages.stream(**request_kwargs) as stream:
            async for text in stream.text_stream:
                yield text
