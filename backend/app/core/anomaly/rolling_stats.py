"""
AI Freight Copilot — Rolling Statistics Anomaly Detection.

Detects anomalies using rolling window statistics: moving average,
rolling standard deviation, and deviation from rolling mean.
"""

from __future__ import annotations

import numpy as np


class RollingStatsDetector:
    """Detects anomalies using rolling window statistics."""

    def detect(
        self,
        values: list[float],
        window: int = 7,
        threshold: float = 2.0,
    ) -> list[int]:
        """
        Detect values that deviate significantly from the rolling mean.
        
        Returns indices where the value exceeds threshold * rolling_std
        from the rolling mean.
        """
        if len(values) < window + 1:
            return []

        arr = np.array(values)
        anomalies = []

        for i in range(window, len(arr)):
            window_data = arr[i - window:i]
            rolling_mean = float(np.mean(window_data))
            rolling_std = float(np.std(window_data))

            if rolling_std == 0:
                continue

            deviation = abs(arr[i] - rolling_mean) / rolling_std
            if deviation > threshold:
                anomalies.append(i)

        return anomalies

    def detect_drops(
        self,
        values: list[float],
        window: int = 7,
        threshold: float = 0.3,
    ) -> list[int]:
        """
        Detect significant drops relative to the rolling mean.
        
        threshold: fraction drop (0.3 = 30% drop from rolling mean).
        """
        if len(values) < window + 1:
            return []

        arr = np.array(values)
        drops = []

        for i in range(window, len(arr)):
            rolling_mean = float(np.mean(arr[i - window:i]))
            if rolling_mean > 0:
                drop_fraction = (rolling_mean - arr[i]) / rolling_mean
                if drop_fraction > threshold:
                    drops.append(i)

        return drops

    def detect_spikes(
        self,
        values: list[float],
        window: int = 7,
        threshold: float = 0.5,
    ) -> list[int]:
        """
        Detect significant spikes relative to the rolling mean.
        
        threshold: fraction increase (0.5 = 50% spike above rolling mean).
        """
        if len(values) < window + 1:
            return []

        arr = np.array(values)
        spikes = []

        for i in range(window, len(arr)):
            rolling_mean = float(np.mean(arr[i - window:i]))
            if rolling_mean > 0:
                spike_fraction = (arr[i] - rolling_mean) / rolling_mean
                if spike_fraction > threshold:
                    spikes.append(i)

        return spikes

    def rolling_mean_at(
        self, values: list[float], index: int, window: int
    ) -> float:
        """Get rolling mean at a specific index."""
        if index < window:
            return float(np.mean(values[:index + 1])) if values else 0.0
        return float(np.mean(values[index - window:index]))

    def rolling_statistics(
        self, values: list[float], window: int = 7
    ) -> dict[str, list[float]]:
        """Calculate rolling mean and std for the entire series."""
        if not values:
            return {"mean": [], "std": [], "upper": [], "lower": []}

        arr = np.array(values)
        means = []
        stds = []

        for i in range(len(arr)):
            start = max(0, i - window + 1)
            window_data = arr[start:i + 1]
            m = float(np.mean(window_data))
            s = float(np.std(window_data))
            means.append(round(m, 2))
            stds.append(round(s, 2))

        return {
            "mean": means,
            "std": stds,
            "upper": [round(m + 2 * s, 2) for m, s in zip(means, stds)],
            "lower": [round(m - 2 * s, 2) for m, s in zip(means, stds)],
        }
