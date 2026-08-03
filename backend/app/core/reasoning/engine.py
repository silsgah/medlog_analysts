"""
AI Freight Copilot — Executive Reasoning Engine.

Produces structured insights following the executive template:
Finding → Confidence → Evidence → Business Impact → Recommended Actions.
Every conclusion must be backed by actual data.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from app.ai.llm_router import LLMRouter
from app.ai.providers.base import Message, MessageRole
from app.ai.prompts.templates import ANALYSIS_PROMPT, SYSTEM_PROMPT
from app.domain.entities import Anomaly, ConfidenceLevel, Evidence, Insight
from app.domain.value_objects import SQLResult

logger = structlog.get_logger(__name__)


class ReasoningEngine:
    """
    Generates executive-grade insights backed by evidence.
    
    Every insight follows the structured template and traces back
    to actual business data. Never invents facts.
    """

    def __init__(self, llm_router: LLMRouter) -> None:
        self._llm = llm_router

    async def analyze_query_result(
        self,
        question: str,
        sql_result: SQLResult,
    ) -> Insight:
        """
        Analyze SQL query results and produce a structured insight.
        
        Used by the conversational AI to structure responses.
        """
        if sql_result.error:
            return Insight(
                finding=f"Query execution failed: {sql_result.error}",
                confidence=ConfidenceLevel.INSUFFICIENT,
                evidence=[Evidence(
                    description="Query failed to execute",
                    sql_query=sql_result.query,
                )],
                business_impact="Unable to determine — data retrieval failed.",
                recommended_actions=["Review the query and try again", "Check data availability"],
                source_query=question,
            )

        if not sql_result.rows:
            return Insight(
                finding="No data found matching the query criteria.",
                confidence=ConfidenceLevel.INSUFFICIENT,
                evidence=[Evidence(
                    description="Query returned zero results",
                    sql_query=sql_result.query,
                )],
                business_impact="Insufficient evidence to assess impact.",
                recommended_actions=["Broaden the search criteria", "Verify data exists for the period"],
                source_query=question,
            )

        # Use AI to analyze the data
        data_preview = json.dumps(sql_result.rows[:50], default=str, indent=2)
        prompt = ANALYSIS_PROMPT.format(
            question=question,
            data_json=data_preview,
            sql_query=sql_result.query,
        )

        messages = [
            Message(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT),
            Message(role=MessageRole.USER, content=prompt),
        ]

        try:
            response = await self._llm.generate(messages, json_mode=True)
            analysis = json.loads(response.content)

            return Insight(
                finding=analysis.get("finding", "Analysis complete."),
                confidence=self._parse_confidence(analysis.get("confidence", "medium")),
                evidence=[
                    Evidence(
                        description=e.get("description", ""),
                        sql_query=sql_result.query,
                        data_points=sql_result.rows[:10],
                    )
                    for e in analysis.get("evidence", [])
                ],
                business_impact=analysis.get("business_impact", ""),
                recommended_actions=analysis.get("recommended_actions", []),
                source_query=question,
            )

        except Exception as e:
            logger.error("AI analysis failed", error=str(e))
            # Fallback to basic analysis without AI
            return self._basic_analysis(question, sql_result)

    async def explain_anomaly(self, anomaly: Anomaly) -> Insight:
        """Generate an executive explanation for a detected anomaly."""
        evidence = Evidence(
            description=(
                f"{anomaly.metric_name}: current value {anomaly.current_value}, "
                f"expected {anomaly.expected_value} "
                f"(deviation: {anomaly.deviation})"
            ),
            data_points=[anomaly.details] if anomaly.details else [],
        )

        # Determine confidence based on detection method
        confidence = ConfidenceLevel.HIGH
        if anomaly.detection_method == "isolation_forest":
            confidence = ConfidenceLevel.MEDIUM
        elif anomaly.detection_method == "threshold":
            confidence = ConfidenceLevel.HIGH

        finding = self._generate_anomaly_finding(anomaly)
        impact = self._generate_anomaly_impact(anomaly)
        actions = self._generate_anomaly_actions(anomaly)

        return Insight(
            finding=finding,
            confidence=confidence,
            evidence=[evidence],
            business_impact=impact,
            recommended_actions=actions,
        )

    def _basic_analysis(self, question: str, result: SQLResult) -> Insight:
        """Fallback basic analysis when AI is unavailable."""
        row_count = len(result.rows)
        columns = result.columns

        # Try to summarize numeric columns
        numeric_summaries = []
        for col in columns:
            values = []
            for row in result.rows:
                try:
                    values.append(float(row.get(col, 0)))
                except (ValueError, TypeError):
                    break
            if values:
                total = sum(values)
                avg = total / len(values)
                numeric_summaries.append(f"{col}: total={total:,.2f}, avg={avg:,.2f}")

        finding = f"Query returned {row_count} record(s)."
        if numeric_summaries:
            finding += " " + "; ".join(numeric_summaries[:3])

        return Insight(
            finding=finding,
            confidence=ConfidenceLevel.MEDIUM,
            evidence=[Evidence(
                description=f"Raw data: {row_count} rows across {len(columns)} columns",
                sql_query=result.query,
                data_points=result.rows[:5],
            )],
            business_impact="Review the data to determine business implications.",
            recommended_actions=["Analyze the detailed data for actionable insights"],
            source_query=question,
        )

    def _parse_confidence(self, value: str) -> ConfidenceLevel:
        """Parse confidence level from string."""
        mapping = {
            "high": ConfidenceLevel.HIGH,
            "medium": ConfidenceLevel.MEDIUM,
            "low": ConfidenceLevel.LOW,
            "insufficient": ConfidenceLevel.INSUFFICIENT,
        }
        return mapping.get(value.lower(), ConfidenceLevel.MEDIUM)

    def _generate_anomaly_finding(self, anomaly: Anomaly) -> str:
        """Generate a business-language finding for an anomaly."""
        type_descriptions = {
            "suspicious_withdrawal": f"Unusual withdrawal of {anomaly.current_value:,.2f} detected — significantly above the expected average of {anomaly.expected_value:,.2f}.",
            "duplicate_payment": f"Potential duplicate payment detected: {int(anomaly.current_value)} identical payments found where only 1 was expected.",
            "expense_spike": f"Expense spike detected: {anomaly.current_value:,.2f} vs rolling average of {anomaly.expected_value:,.2f}.",
            "revenue_drop": f"Revenue drop detected: {anomaly.current_value:,.2f} vs expected {anomaly.expected_value:,.2f} ({anomaly.deviation:.1f}% below average).",
            "delayed_collection": f"Invoice overdue by {int(anomaly.current_value)} days — balance of {anomaly.details.get('balance_due', 0):,.2f} outstanding.",
            "inactive_customer": f"Customer inactive for {int(anomaly.current_value)} days.",
            "branch_outlier": f"Branch performance anomaly detected.",
            "payment_irregularity": f"Payment irregularity detected: {anomaly.current_value:,.2f}.",
        }
        return type_descriptions.get(
            anomaly.anomaly_type.value,
            f"Anomaly detected in {anomaly.metric_name}: {anomaly.current_value} vs expected {anomaly.expected_value}."
        )

    def _generate_anomaly_impact(self, anomaly: Anomaly) -> str:
        """Generate business impact statement for an anomaly."""
        impact_map = {
            "suspicious_withdrawal": "Possible cash leakage or unreconciled withdrawal requiring immediate review.",
            "duplicate_payment": "Potential financial loss from duplicate payments; requires reconciliation.",
            "expense_spike": "Unexpected cost increase may affect profitability if sustained.",
            "revenue_drop": "Revenue decline impacts cash flow and may signal operational issues.",
            "delayed_collection": "Cash flow risk from overdue receivables; potential bad debt.",
            "inactive_customer": "Revenue risk from customer churn.",
            "branch_outlier": "Branch performance deviation requires investigation.",
            "payment_irregularity": "Payment irregularity may indicate process or data issues.",
        }
        return impact_map.get(anomaly.anomaly_type.value, "Requires investigation.")

    def _generate_anomaly_actions(self, anomaly: Anomaly) -> list[str]:
        """Generate recommended actions for an anomaly."""
        actions_map = {
            "suspicious_withdrawal": [
                "Review the withdrawal details and authorization",
                "Verify linked customer payments",
                "Audit the affected branch",
            ],
            "duplicate_payment": [
                "Verify both payment records",
                "Confirm with the customer",
                "Reverse if confirmed duplicate",
            ],
            "expense_spike": [
                "Review the expense category for unusual items",
                "Compare with historical monthly averages",
                "Verify vendor invoices",
            ],
            "revenue_drop": [
                "Analyze revenue by customer and product",
                "Check for operational disruptions",
                "Review sales pipeline",
            ],
            "delayed_collection": [
                "Contact the customer for payment status",
                "Escalate to management if overdue > 90 days",
                "Consider payment plan or collection action",
            ],
        }
        return actions_map.get(anomaly.anomaly_type.value, ["Investigate and report findings"])
