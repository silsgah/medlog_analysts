"""
AI Freight Copilot — Seasonality Detection.

Detects seasonal patterns and trend changes in time series data
using decomposition and autocorrelation analysis.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SeasonalityResult:
    """Result of seasonality analysis."""
    has_seasonality: bool
    period: int | None  # Detected period length
    seasonal_strength: float  # 0-1
    trend_component: list[float]
    seasonal_component: list[float]
    residual_component: list[float]
    description: str


class SeasonalityDetector:
    """Detects seasonal patterns and trend changes."""

    def analyze(
        self,
        values: list[float],
        max_period: int = 30,
    ) -> SeasonalityResult:
        """
        Analyze a time series for seasonal patterns.
        
        Uses autocorrelation to detect periodicity and
        simple decomposition for trend/seasonal/residual components.
        """
        if len(values) < max_period * 2:
            return SeasonalityResult(
                has_seasonality=False,
                period=None,
                seasonal_strength=0.0,
                trend_component=values.copy(),
                seasonal_component=[0.0] * len(values),
                residual_component=[0.0] * len(values),
                description="Insufficient data for seasonality detection.",
            )

        arr = np.array(values)

        # Detect period using autocorrelation
        period = self._detect_period(arr, max_period)

        if period is None or period < 2:
            return SeasonalityResult(
                has_seasonality=False,
                period=None,
                seasonal_strength=0.0,
                trend_component=values.copy(),
                seasonal_component=[0.0] * len(values),
                residual_component=[0.0] * len(values),
                description="No significant seasonal pattern detected.",
            )

        # Decompose the series
        trend, seasonal, residual = self._decompose(arr, period)

        # Calculate seasonal strength
        var_residual = float(np.var(residual))
        var_detrended = float(np.var(arr - trend))
        strength = max(0, 1 - var_residual / var_detrended) if var_detrended > 0 else 0

        has_seasonality = strength > 0.3

        description = (
            f"Seasonal pattern detected with period of {period} "
            f"(strength: {strength:.0%})"
            if has_seasonality
            else "No significant seasonal pattern detected."
        )

        return SeasonalityResult(
            has_seasonality=has_seasonality,
            period=period if has_seasonality else None,
            seasonal_strength=round(strength, 4),
            trend_component=[round(float(v), 2) for v in trend],
            seasonal_component=[round(float(v), 2) for v in seasonal],
            residual_component=[round(float(v), 2) for v in residual],
            description=description,
        )

    def _detect_period(self, arr: np.ndarray, max_period: int) -> int | None:
        """Detect the dominant period using autocorrelation."""
        n = len(arr)
        mean = np.mean(arr)
        var = np.var(arr)

        if var == 0:
            return None

        # Calculate autocorrelation for different lags
        autocorrs = []
        for lag in range(1, min(max_period + 1, n // 2)):
            c = np.sum((arr[:n - lag] - mean) * (arr[lag:] - mean)) / (n * var)
            autocorrs.append((lag, float(c)))

        if not autocorrs:
            return None

        # Find the first significant peak
        best_lag = None
        best_corr = 0.3  # Minimum threshold

        for i in range(1, len(autocorrs) - 1):
            lag, corr = autocorrs[i]
            prev_corr = autocorrs[i - 1][1]
            next_corr = autocorrs[i + 1][1]

            # Is this a local maximum above threshold?
            if corr > prev_corr and corr > next_corr and corr > best_corr:
                best_lag = lag
                best_corr = corr

        return best_lag

    def _decompose(
        self, arr: np.ndarray, period: int
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Simple additive decomposition: trend + seasonal + residual."""
        n = len(arr)

        # Trend: moving average with the period length
        trend = np.copy(arr)
        half = period // 2
        for i in range(half, n - half):
            trend[i] = np.mean(arr[i - half:i + half + 1])

        # Pad edges
        trend[:half] = trend[half]
        trend[n - half:] = trend[n - half - 1]

        # Detrended
        detrended = arr - trend

        # Seasonal: average of detrended values at same position in cycle
        seasonal = np.zeros(n)
        for i in range(period):
            indices = list(range(i, n, period))
            avg = np.mean(detrended[indices])
            for idx in indices:
                seasonal[idx] = avg

        # Residual
        residual = arr - trend - seasonal

        return trend, seasonal, residual

    def detect_trend_changes(
        self,
        values: list[float],
        window: int = 7,
        min_change: float = 0.15,
    ) -> list[dict]:
        """
        Detect points where the trend direction changes significantly.
        
        Returns list of change points with direction info.
        """
        if len(values) < window * 3:
            return []

        arr = np.array(values)
        changes = []

        for i in range(window, len(arr) - window):
            left_slope = np.polyfit(range(window), arr[i - window:i], 1)[0]
            right_slope = np.polyfit(range(window), arr[i:i + window], 1)[0]

            # Check if slopes have different signs (trend reversal)
            if left_slope * right_slope < 0:
                left_mean = float(np.mean(arr[i - window:i]))
                right_mean = float(np.mean(arr[i:i + window]))

                if left_mean != 0:
                    change_pct = abs(right_mean - left_mean) / abs(left_mean)
                    if change_pct > min_change:
                        direction = "up_to_down" if left_slope > 0 else "down_to_up"
                        changes.append({
                            "index": i,
                            "direction": direction,
                            "change_percent": round(change_pct * 100, 1),
                            "left_slope": round(float(left_slope), 4),
                            "right_slope": round(float(right_slope), 4),
                        })

        return changes
