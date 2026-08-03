"""
AI Freight Copilot — Observability.

Metrics collection, health checking, and application instrumentation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class HealthStatus:
    """Application health check result."""
    status: str = "healthy"  # healthy, degraded, unhealthy
    checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_check(self, name: str, healthy: bool, details: str = "") -> None:
        self.checks[name] = {
            "status": "healthy" if healthy else "unhealthy",
            "details": details,
        }
        if not healthy:
            self.status = "degraded" if self.status == "healthy" else "unhealthy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "checks": self.checks,
            "timestamp": self.timestamp,
        }


class MetricsCollector:
    """Simple in-memory metrics collector for observability."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}

    def increment(self, name: str, value: int = 1) -> None:
        self._counters[name] = self._counters.get(name, 0) + value

    def gauge(self, name: str, value: float) -> None:
        self._gauges[name] = value

    def observe(self, name: str, value: float) -> None:
        if name not in self._histograms:
            self._histograms[name] = []
        self._histograms[name].append(value)
        # Keep only last 1000 observations
        if len(self._histograms[name]) > 1000:
            self._histograms[name] = self._histograms[name][-1000:]

    def get_metrics(self) -> dict[str, Any]:
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: {
                    "count": len(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                }
                for name, values in self._histograms.items()
            },
        }


# Module-level singleton
metrics = MetricsCollector()


class Timer:
    """Context manager for timing operations."""

    def __init__(self, metric_name: str) -> None:
        self.metric_name = metric_name
        self._start: float = 0

    def __enter__(self) -> Timer:
        self._start = time.monotonic()
        return self

    def __exit__(self, *args: Any) -> None:
        elapsed = (time.monotonic() - self._start) * 1000
        metrics.observe(self.metric_name, elapsed)
