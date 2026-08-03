"""
AI Freight Copilot — Isolation Forest Anomaly Detection.

Uses scikit-learn's Isolation Forest for unsupervised anomaly detection
on numerical business metrics.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest as SKIsolationForest


class IsolationForestDetector:
    """Detects anomalies using the Isolation Forest algorithm."""

    def __init__(
        self,
        contamination: float = 0.05,
        n_estimators: int = 100,
        random_state: int = 42,
    ) -> None:
        self._contamination = contamination
        self._n_estimators = n_estimators
        self._random_state = random_state

    def detect(
        self,
        values: list[float],
        contamination: float | None = None,
    ) -> list[int]:
        """
        Detect anomalies in a list of values.
        
        Returns indices of anomalous values.
        """
        if len(values) < 10:
            return []

        arr = np.array(values).reshape(-1, 1)

        model = SKIsolationForest(
            contamination=contamination or self._contamination,
            n_estimators=self._n_estimators,
            random_state=self._random_state,
        )

        predictions = model.fit_predict(arr)

        # -1 = anomaly, 1 = normal
        anomaly_indices = [i for i, p in enumerate(predictions) if p == -1]
        return anomaly_indices

    def detect_multivariate(
        self,
        data: list[list[float]],
        contamination: float | None = None,
    ) -> list[int]:
        """
        Detect anomalies in multivariate data.
        
        Each inner list represents a feature vector.
        Returns indices of anomalous observations.
        """
        if len(data) < 10:
            return []

        arr = np.array(data)

        model = SKIsolationForest(
            contamination=contamination or self._contamination,
            n_estimators=self._n_estimators,
            random_state=self._random_state,
        )

        predictions = model.fit_predict(arr)
        return [i for i, p in enumerate(predictions) if p == -1]

    def anomaly_scores(self, values: list[float]) -> list[float]:
        """
        Get anomaly scores for each value.
        
        Lower (more negative) scores indicate more anomalous values.
        """
        if len(values) < 10:
            return [0.0] * len(values)

        arr = np.array(values).reshape(-1, 1)

        model = SKIsolationForest(
            contamination=self._contamination,
            n_estimators=self._n_estimators,
            random_state=self._random_state,
        )

        model.fit(arr)
        scores = model.score_samples(arr)
        return [round(float(s), 4) for s in scores]
