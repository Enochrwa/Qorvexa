"""Outgoing email. Dev uses Mailpit over SMTP; tests replace the sender with a fake."""

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

from app.core.config import get_settings

log = logging.getLogger(__name__)


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


class SmtpEmailSender:
    async def send(self, to: str, subject: str, body: str) -> None:
        settings = get_settings()
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = settings.email_from, to, subject
        msg.set_content(body)

        def _send() -> None:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=5) as smtp:
                smtp.send_message(msg)

        try:
            await asyncio.to_thread(_send)
        except OSError:
            # Never fail a request because mail is down; never log the body (contains a token).
            log.error("email delivery failed")


def get_email_sender() -> EmailSender:
    return SmtpEmailSender()
