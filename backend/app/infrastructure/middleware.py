"""
AI Freight Copilot — Middleware.

HTTP middleware for CORS, request correlation, error handling,
tenant identification, and request logging.
"""

from __future__ import annotations

import time
import uuid

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import get_settings

logger = structlog.get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Adds correlation ID, tenant context, and request logging."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        tenant_id = request.headers.get("X-Tenant-ID", "default")

        # Bind context for structured logging
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = time.monotonic()

        try:
            response = await call_next(request)
            elapsed = (time.monotonic() - start_time) * 1000

            # Add correlation ID to response
            response.headers["X-Correlation-ID"] = correlation_id

            logger.info(
                "Request completed",
                status_code=response.status_code,
                elapsed_ms=round(elapsed, 2),
            )

            return response

        except Exception as exc:
            elapsed = (time.monotonic() - start_time) * 1000
            logger.error(
                "Request failed",
                error=str(exc),
                elapsed_ms=round(elapsed, 2),
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "correlation_id": correlation_id,
                },
            )


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handler that returns structured error responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except PermissionError as e:
            return JSONResponse(
                status_code=403,
                content={"error": "Permission denied", "detail": str(e)},
            )
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={"error": "Bad request", "detail": str(e)},
            )
        except Exception as e:
            logger.error("Unhandled exception", error=str(e), exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"},
            )


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the FastAPI application."""
    settings = get_settings()

    # CORS — allow frontend origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )

    # Custom middleware (order matters — outermost first)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestContextMiddleware)
