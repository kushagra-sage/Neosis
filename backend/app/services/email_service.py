"""Email abstraction.

In development (no SMTP configured) emails are logged instead of sent, and
``email_available()`` returns ``False`` so the password-reset endpoint can tell
the UI the feature is temporarily unavailable. When SMTP settings are present,
messages are delivered over a standard TLS connection.
"""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from app.config import settings
from app.core.logging import get_logger

logger = get_logger("noesis.email")


def email_available() -> bool:
    """True when a real email transport is configured."""
    return bool(settings.smtp_host and settings.smtp_user)


async def _send(to: str, subject: str, body: str) -> None:
    if not email_available():
        logger.info("email_skipped_no_smtp", to=to, subject=subject)
        return

    def _deliver() -> None:
        msg = EmailMessage()
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password.get_secret_value())
            server.send_message(msg)

    try:
        await asyncio.to_thread(_deliver)
        logger.info("email_sent", to=to, subject=subject)
    except Exception as exc:  # pragma: no cover - network dependent
        logger.error("email_send_failed", to=to, error=str(exc))


async def send_password_reset_email(to: str, reset_link: str) -> None:
    subject = "Reset your Noesis password"
    body = (
        "You requested a password reset for your Noesis account.\n\n"
        f"Reset your password using the link below (valid for "
        f"{settings.reset_token_expiry_minutes} minutes):\n\n"
        f"{reset_link}\n\n"
        "If you did not request this, you can safely ignore this email.\n"
    )
    await _send(to, subject, body)
