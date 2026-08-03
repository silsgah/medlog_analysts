"""
AI Freight Copilot — Financial Intelligence API.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.dependencies import get_container

router = APIRouter(prefix="/financial", tags=["financial"])


@router.get("/snapshot")
async def get_financial_snapshot(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """
    Get a complete financial snapshot for the period.
    """
    container = get_container()
    snapshot = await container.financial_calculator.calculate_snapshot(
        start_date=start_date,
        end_date=end_date,
    )
    return snapshot.model_dump()


@router.get("/health-score")
async def get_health_score(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """
    Get composite Business Health Score (0-100).
    """
    container = get_container()
    health = await container.financial_calculator.calculate_health_score(
        start_date=start_date,
        end_date=end_date,
    )
    return health.model_dump()


@router.get("/branch-profitability")
async def get_branch_profitability(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """
    Get profitability by branch.
    """
    container = get_container()
    profitability = await container.financial_calculator.calculate_branch_profitability(
        start_date=start_date,
        end_date=end_date,
    )
    return {k: v.model_dump() for k, v in profitability.items()}
