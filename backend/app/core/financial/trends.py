"""
AI Freight Copilot — Trend Analysis.

Analyzes financial trends over time using moving averages,
linear regression, and change point detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import structlog

from app.domain.entities import MetricValue, TrendDirection

logger = structlog.get_logger(__name__)


@dataclass
class TrendAnalysis:
    """Result of a trend analysis."""
    direction: TrendDirection
    slope: float
    r_squared: float
    change_points: list[int]  # Indices where trend changes
    forecast_next: float | None = None
    moving_average: list[float] | None = None
    is_significant: bool = False
    description: str = ""


class TrendAnalyzer:
    """Analyzes time series data for trends and patterns."""

    def analyze(
        self,
        values: list[float],
        periods: list[str] | None = None,
        window_size: int = 3,
    ) -> TrendAnalysis:
        """
        Analyze a time series for trends.
        
        Uses linear regression for overall direction and
        moving averages for smoothing.
        """
        if len(values) < 2:
            return TrendAnalysis(
                direction=TrendDirection.STABLE,
                slope=0.0,
                r_squared=0.0,
                change_points=[],
                description="Insufficient data for trend analysis.",
            )

        arr = np.array(values, dtype=float)
        x = np.arange(len(arr))

        # Linear regression
        coefficients = np.polyfit(x, arr, 1)
        slope = float(coefficients[0])

        # R-squared
        predicted = np.polyval(coefficients, x)
        ss_res = np.sum((arr - predicted) ** 2)
        ss_tot = np.sum((arr - np.mean(arr)) ** 2)
        r_squared = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

        # Moving average
        ma = self._moving_average(values, window_size)

        # Determine direction
        mean_val = float(np.mean(arr))
        relative_slope = (slope / abs(mean_val)) * 100 if mean_val != 0 else 0

        if relative_slope > 2:
            direction = TrendDirection.UP
        elif relative_slope < -2:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.STABLE

        # Change point detection (simple method)
        change_points = self._detect_change_points(values, window_size)

        # Forecast next value
        forecast = float(np.polyval(coefficients, len(arr)))

        # Significance
        is_significant = abs(r_squared) > 0.5 and abs(relative_slope) > 5

        # Generate description
        description = self._generate_description(
            direction, slope, r_squared, relative_slope, change_points
        )

        return TrendAnalysis(
            direction=direction,
            slope=round(slope, 4),
            r_squared=round(r_squared, 4),
            change_points=change_points,
            forecast_next=round(forecast, 2),
            moving_average=ma,
            is_significant=is_significant,
            description=description,
        )

    def _moving_average(self, values: list[float], window: int) -> list[float]:
        """Calculate simple moving average."""
        if len(values) < window:
            return values.copy()

        arr = np.array(values)
        cumsum = np.cumsum(arr)
        cumsum = np.insert(cumsum, 0, 0)
        ma = (cumsum[window:] - cumsum[:-window]) / window
        # Pad the beginning with the original values
        padded = list(values[:window - 1]) + [round(float(v), 2) for v in ma]
        return padded

    def _detect_change_points(self, values: list[float], window: int) -> list[int]:
        """Detect points where the trend direction changes significantly."""
        if len(values) < window * 2:
            return []

        change_points = []
        arr = np.array(values)

        for i in range(window, len(arr) - window):
            left_mean = float(np.mean(arr[i - window:i]))
            right_mean = float(np.mean(arr[i:i + window]))

            if left_mean != 0:
                change_pct = abs((right_mean - left_mean) / left_mean) * 100
                if change_pct > 15:  # 15% change threshold
                    change_points.append(i)

        return change_points

    def _generate_description(
        self,
        direction: TrendDirection,
        slope: float,
        r_squared: float,
        relative_slope: float,
        change_points: list[int],
    ) -> str:
        """Generate a human-readable trend description."""
        parts = []

        if direction == TrendDirection.UP:
            parts.append(f"Upward trend detected (relative change: +{relative_slope:.1f}% per period)")
        elif direction == TrendDirection.DOWN:
            parts.append(f"Downward trend detected (relative change: {relative_slope:.1f}% per period)")
        else:
            parts.append("Trend is stable with no significant directional movement")

        if r_squared > 0.8:
            parts.append("with high confidence (strong linear fit)")
        elif r_squared > 0.5:
            parts.append("with moderate confidence")
        else:
            parts.append("with low confidence (high variability)")

        if change_points:
            parts.append(f". {len(change_points)} trend change(s) detected")

        return ". ".join(parts) + "."

    def compare_periods(
        self,
        current: list[float],
        previous: list[float],
    ) -> dict[str, Any]:
        """Compare two periods and return the analysis."""
        curr_sum = sum(current)
        prev_sum = sum(previous)
        change = curr_sum - prev_sum
        change_pct = (change / abs(prev_sum) * 100) if prev_sum != 0 else 0

        return {
            "current_total": round(curr_sum, 2),
            "previous_total": round(prev_sum, 2),
            "absolute_change": round(change, 2),
            "percent_change": round(change_pct, 1),
            "direction": "up" if change > 0 else "down" if change < 0 else "stable",
        }
