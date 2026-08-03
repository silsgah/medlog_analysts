"""
AI Freight Copilot — FastAPI Application Entry Point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config import get_settings
from app.dependencies import get_container
from app.infrastructure.logging import setup_logging
from app.infrastructure.middleware import setup_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    setup_logging()
    container = get_container()
    await container.initialize()

    yield

    await container.shutdown()


def create_app() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="AI Freight Operations & Financial Intelligence Copilot",
        version="0.1.0",
        lifespan=lifespan,
    )

    setup_middleware(app)
    app.include_router(api_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
