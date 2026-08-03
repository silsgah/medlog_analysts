"""
AI Freight Copilot — Anomaly Detection Orchestrator.

Runs all detection algorithms against business data and
produces structured anomaly reports. Includes safe numeric parsing for currency strings.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import structlog

from app.core.anomaly.isolation_forest import IsolationForestDetector
from app.core.anomaly.z_score import ZScoreDetector
from app.core.anomaly.rolling_stats import RollingStatsDetector
from app.core.anomaly.seasonality import SeasonalityDetector
from app.domain.entities import AlertSeverity, Anomaly, AnomalyType
from app.infrastructure.database import DatabaseManager

logger = structlog.get_logger(__name__)


def parse_float(val: Any) -> float:
    """Safely convert any value (including currency strings like 'GHS 1,500.00', '$250') to float."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    clean_s = re.sub(r"[^\d.-]", "", s.replace(",", ""))
    try:
        return float(clean_s) if clean_s else 0.0
    except (ValueError, TypeError):
        return 0.0


class AnomalyDetector:
    """Orchestrates anomaly detection across all methods and data types."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager
        self._isolation_forest = IsolationForestDetector()
        self._z_score = ZScoreDetector()
        self._rolling_stats = RollingStatsDetector()
        self._seasonality = SeasonalityDetector()

    async def scan_all(
        self,
        tenant_id: str | None = None,
        lookback_days: int = 90,
    ) -> list[Anomaly]:
        """
        Run all anomaly detection algorithms across all data types.
        
        Returns a consolidated list of detected anomalies sorted by severity.
        """
        logger.info("Starting full anomaly scan", tenant_id=tenant_id)

        anomalies: list[Anomaly] = []

        # Run each detection type
        detectors = [
            ("withdrawal_anomalies", self._detect_withdrawal_anomalies),
            ("expense_anomalies", self._detect_expense_anomalies),
            ("revenue_anomalies", self._detect_revenue_anomalies),
            ("collection_anomalies", self._detect_collection_anomalies),
            ("duplicate_payments", self._detect_duplicate_payments),
        ]

        for name, detector in detectors:
            try:
                detected = await detector(tenant_id=tenant_id, lookback_days=lookback_days)
                anomalies.extend(detected)
                logger.info(f"Detection complete: {name}", count=len(detected))
            except Exception as e:
                logger.warning(f"Detection failed: {name}", error=str(e))

        # Sort by severity
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.HIGH: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 3,
            AlertSeverity.INFO: 4,
        }
        anomalies.sort(key=lambda a: severity_order.get(a.severity, 5))

        logger.info("Full anomaly scan complete", total_anomalies=len(anomalies))
        return anomalies

    async def _detect_withdrawal_anomalies(
        self, tenant_id: str | None, lookback_days: int
    ) -> list[Anomaly]:
        """Detect suspicious withdrawal patterns."""
        query = """
            SELECT 
                Amount,
                CAST(WithdrawalDate AS DATE) AS date,
                Description,
                BranchID
            FROM tblWithdrawal
            WHERE WithdrawalDate >= DATEADD(day, -:lookback_days, GETDATE())
            ORDER BY WithdrawalDate
        """
        result = await self._db.execute_erp_query(
            query, params={"lookback_days": lookback_days}, tenant_id=tenant_id
        )

        if result.error or not result.rows:
            return []

        amounts = [parse_float(r.get("Amount")) for r in result.rows]
        anomalies = []

        # Z-Score detection on amounts
        z_anomalies = self._z_score.detect(amounts, threshold=2.5)
        for idx in z_anomalies:
            row = result.rows[idx]
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.SUSPICIOUS_WITHDRAWAL,
                severity=AlertSeverity.HIGH if amounts[idx] > self._z_score.mean(amounts) * 3 else AlertSeverity.MEDIUM,
                metric_name="Withdrawal Amount",
                current_value=amounts[idx],
                expected_value=round(self._z_score.mean(amounts), 2),
                deviation=round(self._z_score.z_score_at(amounts, idx), 2),
                detection_method="z_score",
                details={"description": row.get("Description", ""), "date": str(row.get("date", ""))},
            ))

        # Isolation Forest on amounts
        if len(amounts) >= 10:
            iso_anomalies = self._isolation_forest.detect(amounts)
            for idx in iso_anomalies:
                if idx not in z_anomalies:  # Avoid duplicates
                    row = result.rows[idx]
                    anomalies.append(Anomaly(
                        anomaly_type=AnomalyType.SUSPICIOUS_WITHDRAWAL,
                        severity=AlertSeverity.MEDIUM,
                        metric_name="Withdrawal Amount",
                        current_value=amounts[idx],
                        expected_value=round(self._z_score.mean(amounts), 2),
                        deviation=0,
                        detection_method="isolation_forest",
                        details={"description": row.get("Description", ""), "date": str(row.get("date", ""))},
                    ))

        return anomalies

    async def _detect_expense_anomalies(
        self, tenant_id: str | None, lookback_days: int
    ) -> list[Anomaly]:
        """Detect expense spikes and unusual patterns."""
        query = """
            SELECT 
                Amount,
                CAST(ExpenseDate AS DATE) AS date,
                Category,
                Description
            FROM tblExpense
            WHERE ExpenseDate >= DATEADD(day, -:lookback_days, GETDATE())
            ORDER BY ExpenseDate
        """
        result = await self._db.execute_erp_query(
            query, params={"lookback_days": lookback_days}, tenant_id=tenant_id
        )

        if result.error or not result.rows:
            return []

        amounts = [parse_float(r.get("Amount")) for r in result.rows]
        anomalies = []

        # Rolling statistics detection
        rolling_anomalies = self._rolling_stats.detect(amounts, window=14, threshold=2.0)
        for idx in rolling_anomalies:
            row = result.rows[idx]
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.EXPENSE_SPIKE,
                severity=AlertSeverity.MEDIUM,
                metric_name="Expense Amount",
                current_value=amounts[idx],
                expected_value=round(self._rolling_stats.rolling_mean_at(amounts, idx, 14), 2),
                deviation=round(amounts[idx] - self._rolling_stats.rolling_mean_at(amounts, idx, 14), 2),
                detection_method="rolling_stats",
                details={
                    "category": row.get("Category", ""),
                    "description": row.get("Description", ""),
                    "date": str(row.get("date", "")),
                },
            ))

        return anomalies

    async def _detect_revenue_anomalies(
        self, tenant_id: str | None, lookback_days: int
    ) -> list[Anomaly]:
        """Detect unusual revenue drops."""
        query = """
            SELECT 
                CAST(InvoiceDate AS DATE) AS date,
                SUM(TotalAmount) AS daily_revenue
            FROM tblInvoice
            WHERE InvoiceDate >= DATEADD(day, -:lookback_days, GETDATE())
            GROUP BY CAST(InvoiceDate AS DATE)
            ORDER BY date
        """
        result = await self._db.execute_erp_query(
            query, params={"lookback_days": lookback_days}, tenant_id=tenant_id
        )

        if result.error or not result.rows or len(result.rows) < 7:
            return []

        revenues = [parse_float(r.get("daily_revenue")) for r in result.rows]
        anomalies = []

        # Check for significant drops using rolling stats
        drop_indices = self._rolling_stats.detect_drops(revenues, window=7, threshold=0.3)
        for idx in drop_indices:
            row = result.rows[idx]
            expected = self._rolling_stats.rolling_mean_at(revenues, idx, 7)
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.REVENUE_DROP,
                severity=AlertSeverity.HIGH,
                metric_name="Daily Revenue",
                current_value=revenues[idx],
                expected_value=round(expected, 2),
                deviation=round(((revenues[idx] - expected) / expected) * 100 if expected else 0, 1),
                detection_method="rolling_stats",
                details={"date": str(row.get("date", ""))},
            ))

        return anomalies

    async def _detect_collection_anomalies(
        self, tenant_id: str | None, lookback_days: int
    ) -> list[Anomaly]:
        """Detect delayed collection patterns."""
        query = """
            SELECT 
                i.InvoiceNo,
                i.CustomerID,
                i.TotalAmount,
                i.InvoiceDate,
                DATEDIFF(day, i.InvoiceDate, GETDATE()) AS days_outstanding,
                i.BalanceDue
            FROM tblInvoice i
            WHERE i.BalanceDue > 0
            AND DATEDIFF(day, i.InvoiceDate, GETDATE()) > 60
            ORDER BY days_outstanding DESC
        """
        result = await self._db.execute_erp_query(query, tenant_id=tenant_id)

        if result.error or not result.rows:
            return []

        anomalies = []
        for row in result.rows[:20]:  # Top 20 overdue
            days = parse_float(row.get("days_outstanding"))
            severity = AlertSeverity.CRITICAL if days > 90 else AlertSeverity.HIGH
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.DELAYED_COLLECTION,
                severity=severity,
                metric_name="Days Outstanding",
                current_value=days,
                expected_value=30.0,  # Standard payment terms
                deviation=days - 30.0,
                detection_method="threshold",
                details={
                    "invoice_no": row.get("InvoiceNo", ""),
                    "balance_due": parse_float(row.get("BalanceDue")),
                    "total_amount": parse_float(row.get("TotalAmount")),
                },
            ))

        return anomalies

    async def _detect_duplicate_payments(
        self, tenant_id: str | None, lookback_days: int
    ) -> list[Anomaly]:
        """Detect potential duplicate payments."""
        query = """
            SELECT 
                Amount,
                CustomerID,
                CAST(ReceiptDate AS DATE) AS date,
                COUNT(*) AS occurrence_count
            FROM tblReceipt
            WHERE ReceiptDate >= DATEADD(day, -:lookback_days, GETDATE())
            GROUP BY Amount, CustomerID, CAST(ReceiptDate AS DATE)
            HAVING COUNT(*) > 1
            ORDER BY occurrence_count DESC
        """
        result = await self._db.execute_erp_query(
            query, params={"lookback_days": lookback_days}, tenant_id=tenant_id
        )

        if result.error or not result.rows:
            return []

        anomalies = []
        for row in result.rows:
            count = parse_float(row.get("occurrence_count"))
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.DUPLICATE_PAYMENT,
                severity=AlertSeverity.HIGH,
                metric_name="Duplicate Payment Count",
                current_value=count,
                expected_value=1.0,
                deviation=count - 1.0,
                detection_method="exact_match",
                details={
                    "amount": parse_float(row.get("Amount")),
                    "customer_id": str(row.get("CustomerID", "")),
                    "date": str(row.get("date", "")),
                },
            ))

        return anomalies
