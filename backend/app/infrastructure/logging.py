"""
AI Freight Copilot — Structured Logging.

Configures structlog for JSON-formatted, production-ready logging
with context binding, request correlation IDs, and performance tracking.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from app.config import get_settings


def add_app_context(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add application-level context to all log entries."""
    settings = get_settings()
    event_dict["app"] = settings.app_name
    event_dict["env"] = settings.app_env.value
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    # Shared processors for all log output
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.ExtraAdder(),
        add_app_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.format_exc_info,
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to route through structlog
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Quieten noisy libraries
    for noisy_logger in ["uvicorn.access", "sqlalchemy.engine", "httpx"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
