"""User persistence helpers for local authentication."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from services.portfolio_db import get_connection


def _normalize_email(email: str) -> str:
    """Normalize an email address for storage and lookup."""
    return email.strip().lower()


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    """Convert a SQLite row into a plain dictionary."""
    if row is None:
        return None
    return dict(row)


def get_user_by_email(email: str) -> dict[str, Any] | None:
    """Return one user by email."""
    normalized_email = _normalize_email(email)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (normalized_email,),
        ).fetchone()
    return _row_to_dict(row)


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    """Return one user by id."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE id = ?",
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

    timestamp = datetime.utcnow().isoformat(timespec="seconds")
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (name, email, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (cleaned_name, normalized_email, password_hash, timestamp, timestamp),
        )
        connection.commit()

    user = get_user_by_id(int(cursor.lastrowid))
    if user is None:
        raise ValueError("Unable to create user.")
    return user


def update_user_password(user_id: int, password_hash: str) -> None:
    """Update a user's password hash."""
    timestamp = datetime.utcnow().isoformat(timespec="seconds")
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET password_hash = ?, updated_at = ?
            WHERE id = ?
            """,
            (password_hash, timestamp, int(user_id)),
        )
        connection.commit()
