"""User persistence helpers for local authentication."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from config.settings import AUTH_LOCKOUT_ATTEMPTS, AUTH_LOCKOUT_MINUTES
from services.db import get_connection


def _normalize_email(email: str) -> str:
    """Normalize an email address for storage and lookup."""
    return email.strip().lower()


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    """Convert a database row into a plain dictionary."""
    if row is None:
        return None
    return dict(row)


def _utcnow() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def _isoformat(timestamp: datetime) -> str:
    """Return a timezone-aware ISO timestamp."""
    return timestamp.isoformat(timespec="seconds")


def get_user_by_email(email: str) -> dict[str, Any] | None:
    """Return one user by email."""
    normalized_email = _normalize_email(email)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = %s",
            (normalized_email,),
        ).fetchone()
    return _row_to_dict(row)


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    """Return one user by id."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE id = %s",
            (int(user_id),),
        ).fetchone()
    return _row_to_dict(row)


def create_user(name: str, email: str, password_hash: str) -> dict[str, Any]:
    """Create a new user record."""
    cleaned_name = name.strip()
    normalized_email = _normalize_email(email)
    if not cleaned_name:
        raise ValueError("Name is required.")
    if not normalized_email:
        raise ValueError("Email is required.")
    if get_user_by_email(normalized_email) is not None:
        raise ValueError("An account with this email already exists.")

    timestamp = _isoformat(_utcnow())
    with get_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO users (
                name, email, password_hash, approval_status, is_active, approval_note,
                failed_login_attempts, locked_until, last_login_at, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                cleaned_name,
                normalized_email,
                password_hash,
                "pending",
                False,
                None,
                0,
                None,
                None,
                timestamp,
                timestamp,
            ),
        ).fetchone()
        connection.commit()

    user = get_user_by_id(int(row["id"])) if row is not None else None
    if user is None:
        raise ValueError("Unable to create user.")
    return user


def update_user_password(user_id: int, password_hash: str) -> None:
    """Update a user's password hash."""
    timestamp = _isoformat(_utcnow())
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET password_hash = %s, updated_at = %s
            WHERE id = %s
            """,
            (password_hash, timestamp, int(user_id)),
        )
        connection.commit()


def record_failed_login_attempt(email: str) -> dict[str, Any] | None:
    """Increment failed login attempts and apply a temporary lockout if needed."""
    normalized_email = _normalize_email(email)
    timestamp = _utcnow()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, failed_login_attempts, locked_until
            FROM users
            WHERE email = %s
            FOR UPDATE
            """,
            (normalized_email,),
        ).fetchone()
        if row is None:
            connection.commit()
            return None

        failed_attempts = int(row.get("failed_login_attempts") or 0) + 1
        locked_until = None
        if failed_attempts >= AUTH_LOCKOUT_ATTEMPTS:
            locked_until = _isoformat(timestamp + timedelta(minutes=AUTH_LOCKOUT_MINUTES))

        connection.execute(
            """
            UPDATE users
            SET failed_login_attempts = %s, locked_until = %s, updated_at = %s
            WHERE id = %s
            """,
            (failed_attempts, locked_until, _isoformat(timestamp), int(row["id"])),
        )
        connection.commit()
        return {
            "id": int(row["id"]),
            "failed_login_attempts": failed_attempts,
            "locked_until": locked_until,
        }


def reset_login_security_state(user_id: int) -> None:
    """Clear failed login counters after a successful login."""
    timestamp = _isoformat(_utcnow())
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET failed_login_attempts = 0, locked_until = NULL, last_login_at = %s, updated_at = %s
            WHERE id = %s
            """,
            (timestamp, timestamp, int(user_id)),
        )
        connection.commit()


def list_pending_users() -> list[dict[str, Any]]:
    """Return all users waiting for admin approval."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, email, approval_status, is_active, approval_note, created_at, updated_at
            FROM users
            WHERE approval_status = 'pending'
            ORDER BY created_at ASC, id ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def update_user_approval_status(user_id: int, approval_status: str, is_active: bool, approval_note: str | None = None) -> None:
    """Update approval fields for a user."""
    cleaned_status = approval_status.strip().lower()
    if cleaned_status not in {"pending", "approved", "rejected"}:
        raise ValueError("Unsupported approval status.")

    timestamp = _isoformat(_utcnow())
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET approval_status = %s, is_active = %s, approval_note = %s, updated_at = %s
            WHERE id = %s
            """,
            (cleaned_status, bool(is_active), (approval_note or "").strip() or None, timestamp, int(user_id)),
        )
        connection.commit()
