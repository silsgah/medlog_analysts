"""
AI Freight Copilot — Z-Score Anomaly Detection.

Statistical anomaly detection using Z-scores (standard deviations from mean).
"""

from __future__ import annotations

import numpy as np


class ZScoreDetector:
    """Detects anomalies using Z-score (standard deviation from mean)."""

    def detect(
        self,
        values: list[float],
        threshold: float = 2.5,
    ) -> list[int]:
        """
        Detect anomalies where Z-score exceeds the threshold.
        
        Returns indices of anomalous values.
        """
        if len(values) < 3:
            return []

        arr = np.array(values)
        mean = float(np.mean(arr))
        std = float(np.std(arr))

        if std == 0:
            return []

        z_scores = np.abs((arr - mean) / std)
        return [i for i, z in enumerate(z_scores) if z > threshold]

    def z_scores(self, values: list[float]) -> list[float]:
        """Calculate Z-scores for all values."""
        if len(values) < 2:
            return [0.0] * len(values)

        arr = np.array(values)
        mean = float(np.mean(arr))
        std = float(np.std(arr))

        if std == 0:
            return [0.0] * len(values)

        return [round(float((v - mean) / std), 4) for v in arr]

    def z_score_at(self, values: list[float], index: int) -> float:
        """Get the Z-score for a specific index."""
        scores = self.z_scores(values)
        if 0 <= index < len(scores):
            return scores[index]
        return 0.0

    def mean(self, values: list[float]) -> float:
        """Calculate mean of values."""
        return float(np.mean(values)) if values else 0.0

    def std(self, values: list[float]) -> float:
        """Calculate standard deviation of values."""
        return float(np.std(values)) if values else 0.0

    def modified_z_score(self, values: list[float], threshold: float = 3.5) -> list[int]:
        """
        Detect anomalies using Modified Z-Score (MAD-based).
        
        More robust to outliers than standard Z-score.
        Uses median and median absolute deviation instead of mean/std.
        """
        if len(values) < 3:
            return []

        arr = np.array(values)
        median = float(np.median(arr))
        mad = float(np.median(np.abs(arr - median)))

        if mad == 0:
            return []

        modified_z = 0.6745 * (arr - median) / mad
        return [i for i, z in enumerate(np.abs(modified_z)) if z > threshold]
