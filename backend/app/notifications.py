
import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def send_incident_email(
    subject: str,
    body: str,
) -> bool:
    """Send an incident notification email using SMTP environment settings."""

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("ALERT_FROM_EMAIL")
    recipient = os.getenv("ALERT_TO_EMAIL")

    required_settings = {
        "SMTP_HOST": smtp_host,
        "SMTP_USERNAME": smtp_username,
        "SMTP_PASSWORD": smtp_password,
        "ALERT_FROM_EMAIL": sender,
        "ALERT_TO_EMAIL": recipient,
    }

    missing = [
        name for name, value in required_settings.items() if not value
    ]

    if missing:
        logger.warning(
            "Incident email not sent; missing settings: %s",
            ", ".join(missing),
        )
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)

        logger.info("Incident notification email sent")
        return True

    except (OSError, smtplib.SMTPException):
        logger.exception("Failed to send incident notification email")
        return False
