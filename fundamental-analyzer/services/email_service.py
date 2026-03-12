"""SMTP email helpers for administrative notifications."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def _get_env(name: str, default: str = "") -> str:
    """Read and trim an environment variable."""
    return os.getenv(name, default).strip()


def send_admin_registration_email(name: str, email: str) -> None:
    """Send a new-user registration email to the admin approval inbox.

    Required environment variables:
    - SMTP_HOST
    - SMTP_PORT
    - SMTP_USERNAME
    - SMTP_PASSWORD
    - SMTP_FROM_EMAIL
    - ADMIN_APPROVAL_EMAIL

    Optional:
    - SMTP_USE_TLS=true|false
    """
    smtp_host = _get_env("SMTP_HOST")
    smtp_port_raw = _get_env("SMTP_PORT")
    smtp_username = _get_env("SMTP_USERNAME")
    smtp_password = _get_env("SMTP_PASSWORD")
    smtp_from_email = _get_env("SMTP_FROM_EMAIL")
    admin_email = _get_env("ADMIN_APPROVAL_EMAIL")
    use_tls = _get_env("SMTP_USE_TLS", "true").lower() != "false"

    missing = [
        key
        for key, value in {
            "SMTP_HOST": smtp_host,
            "SMTP_PORT": smtp_port_raw,
            "SMTP_USERNAME": smtp_username,
            "SMTP_PASSWORD": smtp_password,
            "SMTP_FROM_EMAIL": smtp_from_email,
            "ADMIN_APPROVAL_EMAIL": admin_email,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(f"Missing email configuration: {', '.join(missing)}")

    try:
        smtp_port = int(smtp_port_raw)
    except ValueError as exc:
        raise ValueError("SMTP_PORT must be a valid integer.") from exc

    message = EmailMessage()
    message["Subject"] = "New user pending approval"
    message["From"] = smtp_from_email
    message["To"] = admin_email
    message.set_content(
        "\n".join(
            [
                "A new user has registered and is pending approval.",
                "",
                f"Name: {name}",
                f"Email: {email}",
            ]
        )
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
        if use_tls:
            server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(message)
