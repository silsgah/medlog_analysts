"""
AI Freight Copilot — Alert Engine.

Evaluates alert rules against current metrics and anomalies,
produces alerts, and dispatches notifications.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog

from app.domain.entities import (
    Alert,
    AlertSeverity,
    AlertStatus,
    Anomaly,
    Insight,
    MetricValue,
)
from app.domain.value_objects import ThresholdRule

logger = structlog.get_logger(__name__)


# ── Default Alert Rules ─────────────────────────────────────────────────────

DEFAULT_ALERT_RULES: list[ThresholdRule] = [
    ThresholdRule(
        metric_name="revenue",
        operator="pct_change_lt",
        value=15.0,
        description="Revenue dropped by more than 15%",
    ),
    ThresholdRule(
        metric_name="cash_flow",
        operator="lt",
        value=0,
        description="Cash flow has become negative",
    ),
    ThresholdRule(
        metric_name="collection_rate",
        operator="lt",
        value=60.0,
        description="Collection rate fell below 60%",
    ),
    ThresholdRule(
        metric_name="expense_ratio",
        operator="gt",
        value=90.0,
        description="Expense ratio exceeds 90% of revenue",
    ),
    ThresholdRule(
        metric_name="avg_payment_delay",
        operator="gt",
        value=60.0,
        description="Average payment delay exceeds 60 days",
    ),
]


class AlertEngine:
    """Evaluates conditions and generates business alerts."""

    def __init__(
        self,
        rules: list[ThresholdRule] | None = None,
    ) -> None:
        self._rules = rules or DEFAULT_ALERT_RULES
        self._active_alerts: list[Alert] = []

    def evaluate_metrics(
        self,
        metrics: dict[str, MetricValue],
        tenant_id: str | None = None,
    ) -> list[Alert]:
        """
        Evaluate all alert rules against current metrics.
        
        Returns newly triggered alerts.
        """
        new_alerts: list[Alert] = []

        for rule in self._rules:
            metric = metrics.get(rule.metric_name)
            if metric is None:
                continue

            breached = rule.evaluate(
                metric.value,
                metric.previous_value,
            )

            if breached:
                severity = self._determine_severity(rule, metric)
                alert = Alert(
                    severity=severity,
                    title=rule.description,
                    description=(
                        f"{metric.name}: current value is {metric.value} {metric.unit}. "
                        f"Rule threshold: {rule.operator} {rule.value}."
                    ),
                    tenant_id=tenant_id,
                )
                new_alerts.append(alert)

                logger.warning(
                    "Alert triggered",
                    rule=rule.description,
                    metric=rule.metric_name,
                    value=metric.value,
                    severity=severity.value,
                )

        return new_alerts

    def evaluate_anomalies(
        self,
        anomalies: list[Anomaly],
        tenant_id: str | None = None,
    ) -> list[Alert]:
        """Convert high-severity anomalies into alerts."""
        alerts = []
        for anomaly in anomalies:
            if anomaly.severity in (AlertSeverity.CRITICAL, AlertSeverity.HIGH):
                alert = Alert(
                    severity=anomaly.severity,
                    title=f"Anomaly: {anomaly.anomaly_type.value.replace('_', ' ').title()}",
                    description=(
                        f"{anomaly.metric_name}: {anomaly.current_value} "
                        f"(expected: {anomaly.expected_value}, "
                        f"detected by: {anomaly.detection_method})"
                    ),
                    anomaly=anomaly,
                    tenant_id=tenant_id,
                )
                alerts.append(alert)

        return alerts

    def get_active_alerts(self) -> list[Alert]:
        """Get all active (unresolved) alerts."""
        return [a for a in self._active_alerts if a.status == AlertStatus.ACTIVE]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        for alert in self._active_alerts:
            if alert.id == alert_id:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        for alert in self._active_alerts:
            if alert.id == alert_id:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                return True
        return False

    def add_alerts(self, alerts: list[Alert]) -> None:
        """Add new alerts to the active list."""
        self._active_alerts.extend(alerts)

    def _determine_severity(
        self, rule: ThresholdRule, metric: MetricValue
    ) -> AlertSeverity:
        """Determine alert severity based on how far the metric exceeds threshold."""
        if metric.change_percent is not None:
            if abs(metric.change_percent) > 30:
                return AlertSeverity.CRITICAL
            elif abs(metric.change_percent) > 20:
                return AlertSeverity.HIGH
        return AlertSeverity.MEDIUM
