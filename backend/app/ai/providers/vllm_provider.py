"""
AI Freight Copilot — vLLM Provider.

Implementation of the LLM provider for local vLLM instances
using the OpenAI-compatible API endpoint.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

import structlog
from openai import AsyncOpenAI

from app.ai.providers.base import LLMProvider, LLMResponse, Message
from app.config import get_settings

logger = structlog.get_logger(__name__)


class VLLMProvider(LLMProvider):
    """vLLM local inference provider (OpenAI-compatible API)."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key="not-needed",
            base_url=base_url or settings.vllm_base_url,
        )
        self._model = model or settings.vllm_model
        self._default_max_tokens = settings.vllm_max_tokens
        self._default_temperature = settings.vllm_temperature

    @property
    def provider_name(self) -> str:
        return "vllm"

    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response using a local vLLM instance."""
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
            request_kwargs["extra_body"] = {"guided_json": True}

        response = await self._client.chat.completions.create(**request_kwargs)

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model or self._model,
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
        """Generate a streaming response using a local vLLM instance."""
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
