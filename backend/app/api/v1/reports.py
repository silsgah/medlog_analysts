"""
AI Freight Copilot — Executive Reports API.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.dependencies import get_container
from app.domain.entities import ReportType

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportRequest(BaseModel):
    report_type: ReportType = ReportType.DAILY_EXECUTIVE
    start_date: str | None = None
    end_date: str | None = None
    send_email: bool = False


@router.post("/generate")
async def generate_report(request: ReportRequest):
    """
    Generate an executive report.
    """
    container = get_container()
    try:
        if request.report_type == ReportType.DAILY_EXECUTIVE:
            report = await container.report_service.generate_daily_report(
                send_email=request.send_email
            )
        else:
            if not request.start_date or not request.end_date:
                raise HTTPException(
                    status_code=400,
                    detail="start_date and end_date required for custom reports",
                )
            report = await container.report_service.generate_report(
                report_type=request.report_type,
                start_date=request.start_date,
                end_date=request.end_date,
            )

        return report.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
