"""
AI Freight Copilot — Alerts API.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.dependencies import get_container

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
async def get_alerts():
    """
    Get active alerts and anomalies.
    """
    container = get_container()
    active_alerts = container.alert_engine.get_active_alerts()
    return [a.model_dump() for a in active_alerts]


@router.post("/scan")
async def trigger_anomaly_scan(lookback_days: int = 30):
    """
    Trigger immediate anomaly scan across all methods.
    """
    container = get_container()
    try:
        anomalies = await container.anomaly_detector.scan_all(
            lookback_days=lookback_days
        )
        new_alerts = container.alert_engine.evaluate_anomalies(anomalies)
        container.alert_engine.add_alerts(new_alerts)

        return {
            "anomalies_found": len(anomalies),
            "alerts_created": len(new_alerts),
            "anomalies": [a.model_dump() for a in anomalies],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """
    Acknowledge an alert.
    """
    container = get_container()
    success = container.alert_engine.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged"}


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """
    Resolve an alert.
    """
    container = get_container()
    success = container.alert_engine.resolve_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "resolved"}
