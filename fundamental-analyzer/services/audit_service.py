"""Audit logging helpers for important user actions."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from services.portfolio_db import get_connection


def log_audit_event(
    action: str,
    details: dict[str, Any] | None = None,
    user_id: int | None = None,
) -> None:
    """Persist an audit event without interrupting the main workflow."""
    if not action.strip():
        return

    resolved_user_id = user_id
    if resolved_user_id is None:
        try:
            from services.auth_service import get_current_user_id

            resolved_user_id = get_current_user_id()
        except Exception:
            resolved_user_id = None
    payload = json.dumps(details or {}, default=str)
    created_at = datetime.utcnow().isoformat(timespec="seconds")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO audit_logs (user_id, action, details_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (resolved_user_id, action.strip(), payload, created_at),
        )
        connection.commit()
