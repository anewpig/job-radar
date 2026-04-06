"""Notification helpers for email channel."""

from __future__ import annotations

from email.message import EmailMessage
import smtplib

from ..settings import Settings


def send_email_message(
    settings: Settings,
    subject: str,
    body: str,
    recipients: list[str],
) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=20,
        ) as smtp:
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        return

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=20,
    ) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
