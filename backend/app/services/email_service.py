"""
AI Freight Copilot — Email Service.

Sends transactional emails using Resend API.
Handles report delivery, alert notifications, and formatted HTML emails.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


class EmailService:
    """Sends emails via Resend API."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client: Any = None

    def initialize(self) -> None:
        """Initialize the Resend client."""
        api_key = self._settings.resend_api_key.get_secret_value()
        if not api_key:
            logger.warning("Resend API key not configured — email will be disabled")
            return

        try:
            import resend
            resend.api_key = api_key
            self._client = resend
            logger.info("Email service initialized via Resend")
        except ImportError:
            logger.warning("Resend package not installed")

    async def send_report_email(
        self,
        subject: str,
        html_content: str,
        recipients: list[str] | None = None,
    ) -> bool:
        """Send a report email to configured recipients."""
        to = recipients or self._settings.report_recipients
        if not to:
            logger.warning("No email recipients configured")
            return False

        return await self._send(
            to=to,
            subject=subject,
            html=html_content,
        )

    async def send_alert_email(
        self,
        subject: str,
        html_content: str,
        recipients: list[str] | None = None,
    ) -> bool:
        """Send an alert notification email."""
        to = recipients or self._settings.report_recipients
        if not to:
            return False

        return await self._send(
            to=to,
            subject=f"🚨 ALERT: {subject}",
            html=html_content,
        )

    async def _send(
        self,
        to: list[str],
        subject: str,
        html: str,
    ) -> bool:
        """Send an email via Resend."""
        if not self._client:
            logger.warning("Email service not initialized — skipping send")
            return False

        try:
            params = {
                "from": self._settings.resend_from_email,
                "to": to,
                "subject": subject,
                "html": html,
            }

            response = self._client.Emails.send(params)

            logger.info(
                "Email sent",
                to=to,
                subject=subject,
                response_id=getattr(response, "id", None),
            )
            return True

        except Exception as e:
            logger.error("Email send failed", error=str(e), to=to, subject=subject)
            return False
