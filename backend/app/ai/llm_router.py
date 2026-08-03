"""
AI Freight Copilot — LLM Router.

Multi-provider LLM routing with automatic fallback, token tracking,
and cost monitoring. Provides a unified interface for all AI operations.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

import structlog

from app.ai.providers.base import (
    EmbeddingProvider,
    EmbeddingResponse,
    LLMProvider,
    LLMResponse,
    Message,
)
from app.ai.providers.openai_provider import OpenAIEmbeddingProvider, OpenAIProvider
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.vllm_provider import VLLMProvider
from app.config import AIProvider, get_settings

logger = structlog.get_logger(__name__)


class LLMRouter:
    """
    Routes LLM requests to the appropriate provider with automatic fallback.
    
    Supports OpenAI, Anthropic, Gemini, and local vLLM.
    Tracks token usage and supports provider-specific overrides.
    """

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}
        self._embedding_provider: EmbeddingProvider | None = None
        self._fallback_order: list[str] = []
        self._total_tokens: dict[str, int] = {}
        self._request_count: dict[str, int] = {}

    def initialize(self) -> None:
        """Initialize available providers based on configuration."""
        settings = get_settings()

        # Register providers based on available API keys
        if settings.openai_api_key.get_secret_value():
            self._providers["openai"] = OpenAIProvider()
            self._embedding_provider = OpenAIEmbeddingProvider()
            logger.info("OpenAI provider registered")

        if settings.anthropic_api_key.get_secret_value():
            self._providers["anthropic"] = AnthropicProvider()
            logger.info("Anthropic provider registered")

        if settings.gemini_api_key.get_secret_value():
            self._providers["gemini"] = GeminiProvider()
            logger.info("Gemini provider registered")

        # vLLM is always available if configured (no API key needed)
        if settings.vllm_base_url:
            self._providers["vllm"] = VLLMProvider()
            logger.info("vLLM provider registered")

        # Set fallback order: default provider first, then others
        default = settings.ai_default_provider.value
        self._fallback_order = [default] + [
            p for p in self._providers if p != default
        ]

        if not self._providers:
            logger.warning("No AI providers configured — AI features will be unavailable")

    def _get_provider(self, provider_name: str | None = None) -> LLMProvider:
        """Get a specific provider or the default."""
        if provider_name and provider_name in self._providers:
            return self._providers[provider_name]

        for name in self._fallback_order:
            if name in self._providers:
                return self._providers[name]

        raise RuntimeError(
            "No AI providers available. Configure at least one provider's API key."
        )

    def _track_usage(self, response: LLMResponse) -> None:
        """Track token usage per provider."""
        provider = response.provider
        self._total_tokens[provider] = (
            self._total_tokens.get(provider, 0) + response.total_tokens
        )
        self._request_count[provider] = (
            self._request_count.get(provider, 0) + 1
        )

    async def generate(
        self,
        messages: list[Message],
        *,
        provider: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a response with automatic fallback.
        
        Tries the specified/default provider first, then falls back
        to other available providers on failure.
        """
        errors: list[str] = []

        # Build provider order: specified first, then fallback
        provider_order = self._fallback_order.copy()
        if provider:
            provider_order = [provider] + [p for p in provider_order if p != provider]

        for provider_name in provider_order:
            if provider_name not in self._providers:
                continue

            try:
                llm = self._providers[provider_name]
                response = await llm.generate(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                    **kwargs,
                )
                self._track_usage(response)

                logger.info(
                    "LLM generation complete",
                    provider=provider_name,
                    model=response.model,
                    tokens=response.total_tokens,
                )

                return response

            except Exception as e:
                errors.append(f"{provider_name}: {str(e)}")
                logger.warning(
                    "Provider failed, trying fallback",
                    provider=provider_name,
                    error=str(e),
                )
                continue

        raise RuntimeError(
            f"All AI providers failed. Errors: {'; '.join(errors)}"
        )

    async def generate_stream(
        self,
        messages: list[Message],
        *,
        provider: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Generate a streaming response with fallback."""
        llm = self._get_provider(provider)

        async for chunk in llm.generate_stream(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield chunk

    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        """Generate embeddings using the configured embedding provider."""
        if not self._embedding_provider:
            raise RuntimeError("No embedding provider configured.")

        return await self._embedding_provider.embed(texts)

    @property
    def embedding_dimensions(self) -> int:
        """Get the embedding dimensions."""
        if not self._embedding_provider:
            return 1536  # Default
        return self._embedding_provider.dimensions

    def get_usage_stats(self) -> dict[str, Any]:
        """Get token usage statistics per provider."""
        return {
            "total_tokens": dict(self._total_tokens),
            "request_count": dict(self._request_count),
            "available_providers": list(self._providers.keys()),
            "fallback_order": self._fallback_order,
        }

    async def health_check(self) -> dict[str, bool]:
        """Check health of all configured providers."""
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception:
                results[name] = False
        return results
