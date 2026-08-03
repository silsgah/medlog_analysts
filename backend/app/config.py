"""
AI Freight Copilot — Application Configuration.

All settings are loaded from environment variables with sensible defaults.
Uses Pydantic Settings for validation and type safety.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    VLLM = "vllm"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = "AI Freight Copilot"
    app_env: Environment = Environment.DEVELOPMENT
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_secret_key: SecretStr = SecretStr("change-me-in-production")
    app_cors_origins: list[str] = Field(default=["http://localhost:3000"])

    # ── SQL Server (ERP Database — READ ONLY) ────────────────────────────
    sqlserver_host: str = "localhost"
    sqlserver_port: int = 1433
    sqlserver_database: str = "FreightERP"
    sqlserver_user: str = "readonly_user"
    sqlserver_password: SecretStr = SecretStr("")
    sqlserver_driver: str = "ODBC Driver 18 for SQL Server"
    sqlserver_encrypt: bool = True
    sqlserver_trust_server_certificate: bool = True
    sqlserver_pool_size: int = 5
    sqlserver_max_overflow: int = 10
    sqlserver_pool_timeout: int = 30

    # ── PostgreSQL (Application State) ───────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "freight_copilot"
    postgres_user: str = "copilot"
    postgres_password: SecretStr = SecretStr("")
    postgres_pool_size: int = 10
    postgres_max_overflow: int = 20

    # ── Redis ────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Qdrant ───────────────────────────────────────────────────────────
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "business_knowledge"

    # ── AI Providers ─────────────────────────────────────────────────────
    ai_default_provider: AIProvider = AIProvider.OPENAI

    # OpenAI
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.1

    # Anthropic
    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_max_tokens: int = 4096
    anthropic_temperature: float = 0.1

    # Gemini
    gemini_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-2.0-flash"
    gemini_max_tokens: int = 4096
    gemini_temperature: float = 0.1

    # vLLM
    vllm_base_url: str = "http://localhost:8001/v1"
    vllm_model: str = "meta-llama/Llama-3-8b-chat-hf"
    vllm_max_tokens: int = 4096
    vllm_temperature: float = 0.1

    # ── Email (Resend) ───────────────────────────────────────────────────
    resend_api_key: SecretStr = SecretStr("")
    resend_from_email: str = "copilot@yourdomain.com"
    report_recipients: list[str] = Field(default=[])

    # ── Scheduler ────────────────────────────────────────────────────────
    daily_report_cron: str = "0 6 * * *"
    weekly_report_cron: str = "0 7 * * 1"
    monthly_report_cron: str = "0 7 1 * *"
    anomaly_scan_interval_minutes: int = 60

    # ── Logging ──────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "json"

    # ── Computed Properties ──────────────────────────────────────────────
    @property
    def sqlserver_connection_string(self) -> str:
        """Build the SQL Server connection string for pyodbc/aioodbc."""
        password = self.sqlserver_password.get_secret_value()
        return (
            f"DRIVER={{{self.sqlserver_driver}}};"
            f"SERVER={self.sqlserver_host},{self.sqlserver_port};"
            f"DATABASE={self.sqlserver_database};"
            f"UID={self.sqlserver_user};"
            f"PWD={password};"
            f"Encrypt={'yes' if self.sqlserver_encrypt else 'no'};"
            f"TrustServerCertificate={'yes' if self.sqlserver_trust_server_certificate else 'no'};"
        )

    @property
    def sqlserver_async_url(self) -> str:
        """SQLAlchemy async URL for SQL Server via aioodbc."""
        password = self.sqlserver_password.get_secret_value()
        return (
            f"mssql+aioodbc://{self.sqlserver_user}:{password}"
            f"@{self.sqlserver_host}:{self.sqlserver_port}"
            f"/{self.sqlserver_database}"
            f"?driver={self.sqlserver_driver.replace(' ', '+')}"
            f"&Encrypt={'yes' if self.sqlserver_encrypt else 'no'}"
            f"&TrustServerCertificate={'yes' if self.sqlserver_trust_server_certificate else 'no'}"
        )

    @property
    def postgres_async_url(self) -> str:
        """SQLAlchemy async URL for PostgreSQL."""
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_database}"
        )

    @property
    def is_production(self) -> bool:
        return self.app_env == Environment.PRODUCTION

    @field_validator("app_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("report_recipients", mode="before")
    @classmethod
    def parse_recipients(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [r.strip() for r in v.split(",") if r.strip()]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()
