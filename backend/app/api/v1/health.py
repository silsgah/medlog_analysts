"""
AI Freight Copilot — Health Check API.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import get_container
from app.infrastructure.observability import HealthStatus, metrics

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Application health check."""
    health = HealthStatus()
    container = get_container()

    # Check database
    try:
        result = await container.db_manager.execute_erp_query("SELECT 1 AS ok")
        health.add_check("erp_database", not bool(result.error), result.error or "Connected")
    except Exception as e:
        health.add_check("erp_database", False, str(e))

    # Check AI providers
    try:
        ai_health = await container.llm_router.health_check()
        for provider, is_healthy in ai_health.items():
            health.add_check(f"ai_{provider}", is_healthy)
    except Exception as e:
        health.add_check("ai_providers", False, str(e))

    return health.to_dict()


@router.get("/health/ready")
async def readiness_check() -> dict:
    """Readiness probe for container orchestration."""
    return {"status": "ready"}


@router.get("/metrics")
async def get_metrics() -> dict:
    """Get application metrics."""
    container = get_container()
    return {
        "app_metrics": metrics.get_metrics(),
        "ai_usage": container.llm_router.get_usage_stats(),
    }
