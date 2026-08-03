"""
AI Freight Copilot — Report Service.

Generates all report types with financial data, anomaly detection,
and AI-powered executive summaries.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import structlog

from app.ai.llm_router import LLMRouter
from app.ai.providers.base import Message, MessageRole
from app.ai.prompts.templates import DAILY_REPORT_PROMPT, EMAIL_REPORT_HTML, SYSTEM_PROMPT
from app.core.alerts.engine import AlertEngine
from app.core.anomaly.detector import AnomalyDetector
from app.core.financial.calculator import FinancialCalculator
from app.domain.entities import (
    ExecutiveReport,
    ReportType,
)
from app.services.email_service import EmailService

logger = structlog.get_logger(__name__)


class ReportService:
    """Generates and distributes executive reports."""

    def __init__(
        self,
        financial_calculator: FinancialCalculator,
        anomaly_detector: AnomalyDetector,
        alert_engine: AlertEngine,
        llm_router: LLMRouter,
        email_service: EmailService,
    ) -> None:
        self._financial = financial_calculator
        self._anomaly = anomaly_detector
        self._alerts = alert_engine
        self._llm = llm_router
        self._email = email_service

    async def generate_daily_report(
        self,
        tenant_id: str | None = None,
        send_email: bool = True,
        recipients: list[str] | None = None,
    ) -> ExecutiveReport:
        """Generate the Daily Executive Intelligence Report."""
        logger.info("Generating daily executive report", tenant_id=tenant_id)

        today = datetime.utcnow()
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        # Calculate financial metrics
        snapshot = await self._financial.calculate_snapshot(
            start_date, end_date, tenant_id
        )

        # Calculate health score
        health = await self._financial.calculate_health_score(
            start_date, end_date, tenant_id
        )

        # Run anomaly detection
        anomalies = await self._anomaly.scan_all(tenant_id=tenant_id, lookback_days=30)

        # Generate alerts from anomalies
        anomaly_alerts = self._alerts.evaluate_anomalies(anomalies, tenant_id)
        self._alerts.add_alerts(anomaly_alerts)

        # Use AI to generate executive summary
        report_data = await self._generate_ai_summary(
            snapshot, anomalies, anomaly_alerts, today
        )

        report = ExecutiveReport(
            report_type=ReportType.DAILY_EXECUTIVE,
            title=f"Daily Executive Intelligence — {today.strftime('%B %d, %Y')}",
            period=f"{start_date} to {end_date}",
            health_score=health,
            financial_snapshot=snapshot,
            anomalies=anomalies[:10],  # Top 10
            tenant_id=tenant_id,
        )

        # Send email if configured
        if send_email:
            html = self._render_email(report, report_data)
            await self._email.send_report_email(
                subject=f"📊 Daily Executive Intelligence — Health Score: {health.score}/100",
                html_content=html,
                recipients=recipients,
            )

        logger.info(
            "Daily report generated",
            health_score=health.score,
            anomalies=len(anomalies),
            alerts=len(anomaly_alerts),
        )

        return report

    async def generate_report(
        self,
        report_type: ReportType,
        start_date: str,
        end_date: str,
        tenant_id: str | None = None,
    ) -> ExecutiveReport:
        """Generate any type of report for a custom period."""
        snapshot = await self._financial.calculate_snapshot(
            start_date, end_date, tenant_id
        )
        health = await self._financial.calculate_health_score(
            start_date, end_date, tenant_id
        )

        return ExecutiveReport(
            report_type=report_type,
            title=f"{report_type.value.replace('_', ' ').title()} Report",
            period=f"{start_date} to {end_date}",
            health_score=health,
            financial_snapshot=snapshot,
            tenant_id=tenant_id,
        )

    async def _generate_ai_summary(
        self, snapshot: Any, anomalies: list, alerts: list, report_date: datetime
    ) -> dict[str, Any]:
        """Use AI to generate the executive summary."""
        try:
            prompt = DAILY_REPORT_PROMPT.format(
                company_name="Freight Company",
                report_date=report_date.strftime("%B %d, %Y"),
                financial_data=json.dumps(snapshot.model_dump(), default=str, indent=2),
                anomalies_data=json.dumps(
                    [a.model_dump() for a in anomalies[:10]], default=str, indent=2
                ),
                alerts_data=json.dumps(
                    [a.model_dump() for a in alerts[:10]], default=str, indent=2
                ),
            )

            messages = [
                Message(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT),
                Message(role=MessageRole.USER, content=prompt),
            ]

            response = await self._llm.generate(messages, json_mode=True)
            return json.loads(response.content)

        except Exception as e:
            logger.warning("AI summary generation failed", error=str(e))
            return {}

    def _render_email(self, report: ExecutiveReport, ai_data: dict) -> str:
        """Render the HTML email template."""
        score = report.health_score.score if report.health_score else 50
        score_color = "#10b981" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"

        # Build metrics HTML
        metrics_html = ""
        if report.financial_snapshot:
            snapshot = report.financial_snapshot
            for field_name in ["revenue", "cash_flow", "collection_rate", "outstanding_receivables"]:
                metric = getattr(snapshot, field_name, None)
                if metric:
                    trend_class = f"trend-{metric.trend.value}"
                    trend_arrow = "↑" if metric.trend.value == "up" else "↓" if metric.trend.value == "down" else "→"
                    change_text = f"{trend_arrow} {abs(metric.change_percent or 0):.1f}%" if metric.change_percent else ""
                    metrics_html += f"""
                    <div class="metric">
                        <div class="name">{metric.name}</div>
                        <div class="value">{metric.unit} {metric.value:,.0f}</div>
                        <div class="trend {trend_class}">{change_text}</div>
                    </div>"""

        # Build alerts HTML
        alerts_html = ""
        for anomaly in (report.anomalies or [])[:5]:
            severity_class = f"alert-{anomaly.severity.value}"
            alerts_html += f"""
            <div class="alert {severity_class}">
                <strong>{anomaly.anomaly_type.value.replace('_', ' ').title()}</strong>:
                {anomaly.metric_name} — current: {anomaly.current_value:,.2f}, expected: {anomaly.expected_value:,.2f}
            </div>"""

        # Build actions HTML
        actions_html = ""
        ai_actions = ai_data.get("recommended_actions", [])
        for i, action in enumerate(ai_actions[:5], 1):
            action_text = action.get("action", str(action)) if isinstance(action, dict) else str(action)
            actions_html += f"""
            <div class="action">
                <span class="number">{i}.</span> {action_text}
            </div>"""

        return EMAIL_REPORT_HTML.format(
            report_date=report.title,
            health_score=f"{score} / 100",
            score_color=score_color,
            metrics_html=metrics_html or "<p>No metrics available</p>",
            alerts_html=alerts_html or "<p>No alerts</p>",
            actions_html=actions_html or "<p>No actions required</p>",
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        )
