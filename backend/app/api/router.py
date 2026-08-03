"""
AI Freight Copilot — API Router Registry.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.alerts import router as alerts_router
from app.api.v1.chat import router as chat_router
from app.api.v1.discovery import router as discovery_router
from app.api.v1.financial import router as financial_router
from app.api.v1.health import router as health_router
from app.api.v1.reports import router as reports_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(discovery_router)
api_router.include_router(chat_router)
api_router.include_router(financial_router)
api_router.include_router(reports_router)
api_router.include_router(alerts_router)
