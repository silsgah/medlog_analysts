"""
AI Freight Copilot — Financial KPI Calculator.

Calculates all financial metrics from the ERP database,
including period-over-period comparisons, currency parsing, and business health scores.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import structlog

from app.core.anomaly.detector import parse_float
from app.core.financial.metrics import METRIC_DEFINITIONS, MetricDefinition, TableMapping
from app.domain.entities import (
    BusinessHealthScore,
    FinancialSnapshot,
    MetricValue,
    TrendDirection,
)
from app.infrastructure.database import DatabaseManager

logger = structlog.get_logger(__name__)


class FinancialCalculator:
    """Calculates financial KPIs and health scores."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        table_mapping: TableMapping | None = None,
    ) -> None:
        self._db = db_manager
        self._mapping = table_mapping or TableMapping()

    async def calculate_snapshot(
        self,
        start_date: str,
        end_date: str,
        tenant_id: str | None = None,
    ) -> FinancialSnapshot:
        """
        Calculate a complete financial snapshot for the given period.
        
        Includes all KPIs with trend comparison against the previous period.
        """
        logger.info(
            "Calculating financial snapshot",
            start_date=start_date,
            end_date=end_date,
            tenant_id=tenant_id,
        )

        # Calculate previous period dates for comparison
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        period_days = (end - start).days
        prev_start = (start - timedelta(days=period_days)).strftime("%Y-%m-%d")
        prev_end = (start - timedelta(days=1)).strftime("%Y-%m-%d")

        snapshot = FinancialSnapshot(
            period=f"{start_date} to {end_date}",
        )

        # Calculate each metric
        for metric_name, metric_def in METRIC_DEFINITIONS.items():
            try:
                metric_value = await self._calculate_metric(
                    metric_def,
                    start_date=start_date,
                    end_date=end_date,
                    prev_start_date=prev_start,
                    prev_end_date=prev_end,
                    tenant_id=tenant_id,
                )

                # Map metric to snapshot field
                if hasattr(snapshot, metric_name):
                    setattr(snapshot, metric_name, metric_value)

            except Exception as e:
                logger.warning(
                    "Failed to calculate metric",
                    metric=metric_name,
                    error=str(e),
                )

        return snapshot

    async def _calculate_metric(
        self,
        metric_def: MetricDefinition,
        start_date: str,
        end_date: str,
        prev_start_date: str,
        prev_end_date: str,
        tenant_id: str | None = None,
    ) -> MetricValue:
        """Calculate a single metric with comparison."""
        # Apply table mapping to query
        query = self._mapping.apply_to_query(metric_def.query_template)

        # Execute current period query
        result = await self._db.execute_erp_query(
            query,
            params={"start_date": start_date, "end_date": end_date},
            tenant_id=tenant_id,
        )

        current_value = 0.0
        if result.rows and not result.error:
            current_value = parse_float(result.rows[0].get("value"))

        # Execute previous period query for comparison
        previous_value: float | None = None
        change_percent: float | None = None
        trend = TrendDirection.STABLE

        if metric_def.comparison_query_template:
            comp_query = self._mapping.apply_to_query(metric_def.comparison_query_template)
        else:
            comp_query = query

        prev_result = await self._db.execute_erp_query(
            comp_query,
            params={
                "start_date": prev_start_date,
                "end_date": prev_end_date,
                "prev_start_date": prev_start_date,
                "prev_end_date": prev_end_date,
            },
            tenant_id=tenant_id,
        )

        if prev_result.rows and not prev_result.error:
            previous_value = parse_float(prev_result.rows[0].get("value"))
            if previous_value and previous_value != 0:
                change_percent = ((current_value - previous_value) / abs(previous_value)) * 100
                if change_percent > 2:
                    trend = TrendDirection.UP
                elif change_percent < -2:
                    trend = TrendDirection.DOWN

        unit = "GHS" if metric_def.unit == "currency" else metric_def.unit

        return MetricValue(
            name=metric_def.display_name,
            value=round(current_value, 2),
            unit=unit,
            trend=trend,
            change_percent=round(change_percent, 1) if change_percent else None,
            previous_value=round(previous_value, 2) if previous_value else None,
        )

    async def calculate_health_score(
        self,
        start_date: str,
        end_date: str,
        tenant_id: str | None = None,
    ) -> BusinessHealthScore:
        """
        Calculate the composite Business Health Score (0-100).
        
        Weighted average of key financial metrics normalized to 0-100.
        """
        snapshot = await self.calculate_snapshot(start_date, end_date, tenant_id)
        components: dict[str, float] = {}
        total_weight = 0.0
        weighted_sum = 0.0

        for metric_name, metric_def in METRIC_DEFINITIONS.items():
            if metric_def.health_weight <= 0:
                continue

            metric_value = getattr(snapshot, metric_name, None)
            if metric_value is None:
                continue

            # Normalize the metric to a 0-100 score
            score = self._normalize_metric_score(metric_value, metric_def)
            components[metric_def.display_name] = round(score, 1)
            weighted_sum += score * metric_def.health_weight
            total_weight += metric_def.health_weight

        overall_score = int(weighted_sum / total_weight) if total_weight > 0 else 50

        return BusinessHealthScore(
            score=max(0, min(100, overall_score)),
            components=components,
        )

    def _normalize_metric_score(
        self, metric: MetricValue, definition: MetricDefinition
    ) -> float:
        """Normalize a metric value to a 0-100 health score."""
        if definition.unit == "percent":
            # For percentage metrics, use the value directly (capped at 100)
            score = min(100, max(0, metric.value))
            if not definition.higher_is_better:
                score = 100 - score
        elif definition.critical_threshold is not None:
            # Score based on distance from critical threshold
            if definition.higher_is_better:
                if metric.value <= definition.critical_threshold:
                    score = 20.0
                elif definition.warning_threshold and metric.value <= definition.warning_threshold:
                    score = 50.0
                else:
                    score = 80.0
            else:
                if metric.value >= definition.critical_threshold:
                    score = 20.0
                elif definition.warning_threshold and metric.value >= definition.warning_threshold:
                    score = 50.0
                else:
                    score = 80.0
        else:
            # Default: use trend direction
            if metric.trend == TrendDirection.UP:
                score = 75.0 if definition.higher_is_better else 35.0
            elif metric.trend == TrendDirection.DOWN:
                score = 35.0 if definition.higher_is_better else 75.0
            else:
                score = 55.0

        return score

    async def calculate_branch_profitability(
        self,
        start_date: str,
        end_date: str,
        tenant_id: str | None = None,
    ) -> dict[str, MetricValue]:
        """Calculate profitability per branch."""
        query = f"""
            SELECT 
                b.BranchName,
                ISNULL(SUM({self._mapping.safe_numeric_expr("i." + self._mapping.invoice_amount_col)}), 0) AS revenue,
                ISNULL((
                    SELECT SUM({self._mapping.safe_numeric_expr("e." + self._mapping.expense_amount_col)}) 
                    FROM {self._mapping.expense_table} e 
                    WHERE e.BranchID = b.BranchID 
                    AND e.{self._mapping.expense_date_column} BETWEEN :start_date AND :end_date
                ), 0) AS expenses
            FROM {self._mapping.branch_table} b
            LEFT JOIN {self._mapping.invoice_table} i 
                ON i.BranchID = b.BranchID 
                AND i.{self._mapping.date_column} BETWEEN :start_date AND :end_date
            GROUP BY b.BranchID, b.BranchName
            ORDER BY revenue DESC
        """

        result = await self._db.execute_erp_query(
            query,
            params={"start_date": start_date, "end_date": end_date},
            tenant_id=tenant_id,
        )

        branch_metrics: dict[str, MetricValue] = {}
        if result.rows and not result.error:
            for row in result.rows:
                branch_name = row.get("BranchName", "Unknown")
                revenue = parse_float(row.get("revenue"))
                expenses = parse_float(row.get("expenses"))
                profit = revenue - expenses

                branch_metrics[branch_name] = MetricValue(
                    name=f"{branch_name} Profit",
                    value=round(profit, 2),
                    unit="GHS",
                )

        return branch_metrics
