"""
AI Freight Copilot — Google Gemini Provider.

Implementation of the LLM provider for Google's Gemini API.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

import structlog
import google.generativeai as genai

from app.ai.providers.base import LLMProvider, LLMResponse, Message, MessageRole
from app.config import get_settings

logger = structlog.get_logger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        api_key = api_key or settings.gemini_api_key.get_secret_value()
        genai.configure(api_key=api_key)
        self._model_name = model or settings.gemini_model
        self._model = genai.GenerativeModel(self._model_name)
        self._default_max_tokens = settings.gemini_max_tokens
        self._default_temperature = settings.gemini_temperature

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _convert_messages(
        self, messages: list[Message]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert standard messages to Gemini format."""
        system_instruction = None
        gemini_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_instruction = msg.content
            else:
                role = "user" if msg.role == MessageRole.USER else "model"
                gemini_messages.append({"role": role, "parts": [msg.content]})

        return system_instruction, gemini_messages

    async def generate(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response using Google Gemini."""
        system_instruction, gemini_messages = self._convert_messages(messages)

        generation_config = genai.types.GenerationConfig(
            temperature=temperature if temperature is not None else self._default_temperature,
            max_output_tokens=max_tokens or self._default_max_tokens,
        )

        if json_mode:
            generation_config.response_mime_type = "application/json"

        # Re-create model with system instruction if provided
        model = self._model
        if system_instruction:
            model = genai.GenerativeModel(
                self._model_name,
                system_instruction=system_instruction,
            )

        response = await model.generate_content_async(
            gemini_messages,
            generation_config=generation_config,
        )

        # Extract token usage
        usage_meta = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage_meta, "prompt_token_count", 0) if usage_meta else 0
        output_tokens = getattr(usage_meta, "candidates_token_count", 0) if usage_meta else 0

        return LLMResponse(
            content=response.text or "",
            model=self._model_name,
            provider=self.provider_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            finish_reason="stop",
        )

    async def generate_stream(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate a streaming response using Google Gemini."""
        system_instruction, gemini_messages = self._convert_messages(messages)

        generation_config = genai.types.GenerationConfig(
            temperature=temperature if temperature is not None else self._default_temperature,
            max_output_tokens=max_tokens or self._default_max_tokens,
        )

        model = self._model
        if system_instruction:
            model = genai.GenerativeModel(
                self._model_name,
                system_instruction=system_instruction,
            )

        response = await model.generate_content_async(
            gemini_messages,
            generation_config=generation_config,
            stream=True,
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text
