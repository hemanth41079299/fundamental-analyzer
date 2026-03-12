"""Session-based authentication helpers for Streamlit."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import streamlit as st

from config.settings import AUTH_LOCKOUT_ATTEMPTS, AUTH_LOCKOUT_MINUTES, AUTH_MIN_PASSWORD_LENGTH
from services.audit_service import log_audit_event
from services.email_service import send_admin_registration_email
from services.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    record_failed_login_attempt,
    reset_login_security_state,
    update_user_password,
)

try:  # pragma: no cover - depends on local environment
    from passlib.context import CryptContext
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    CryptContext = None  # type: ignore[assignment]

PASSWORD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto") if CryptContext is not None else None

AUTH_STATE_DEFAULTS: dict[str, Any] = {
    "auth_user_id": None,
    "auth_user_name": None,
    "auth_user_email": None,
    "is_authenticated": False,
    "auth_last_activity_at": None,
    "auth_login_at": None,
}


def _truncate_password(password: str) -> str:
    """Truncate a password to bcrypt's 72-byte limit."""
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")


def _require_password_context() -> None:
    """Ensure passlib is installed before using password functions."""
    if PASSWORD_CONTEXT is None:
        raise ValueError("passlib is not installed. Run: pip install -r requirements.txt")


def _utcnow() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def _parse_timestamp(value: object) -> datetime | None:
    """Parse an ISO timestamp into a timezone-aware datetime."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_lockout_message(locked_until: object) -> str:
    """Return a user-facing lockout message."""
    parsed = _parse_timestamp(locked_until)
    if parsed is None:
        return f"Too many failed login attempts. Try again in {AUTH_LOCKOUT_MINUTES} minutes."
    return f"Too many failed login attempts. Try again after {parsed.strftime('%Y-%m-%d %H:%M UTC')}."


def _active_lockout(user: dict[str, Any]) -> datetime | None:
    """Return the current lockout end timestamp if the account is locked."""
    parsed = _parse_timestamp(user.get("locked_until"))
    if parsed is None:
        return None
    if parsed <= _utcnow():
        return None
    return parsed


def initialize_auth_state() -> None:
    """Initialize Streamlit auth session keys."""
    for key, value in AUTH_STATE_DEFAULTS.items():
        st.session_state.setdefault(key, value)


def _set_authenticated_session(user: dict[str, Any]) -> None:
    """Persist authenticated user data in session state."""
    timestamp = _utcnow().isoformat(timespec="seconds")
    st.session_state["auth_user_id"] = int(user["id"])
    st.session_state["auth_user_name"] = str(user["name"])
    st.session_state["auth_user_email"] = str(user["email"])
    st.session_state["is_authenticated"] = True
    st.session_state["auth_login_at"] = timestamp
    st.session_state["auth_last_activity_at"] = timestamp


def clear_auth_session() -> None:
    """Clear auth-related session state."""
    for key, value in AUTH_STATE_DEFAULTS.items():
        st.session_state[key] = value


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    _require_password_context()
    return PASSWORD_CONTEXT.hash(_truncate_password(password))


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    _require_password_context()
    return bool(PASSWORD_CONTEXT.verify(_truncate_password(password), password_hash))


def _validate_registration_input(name: str, email: str, password: str, confirm_password: str) -> None:
    """Validate registration form inputs."""
    if not name.strip():
        raise ValueError("Name is required.")
    if not email.strip():
        raise ValueError("Email is required.")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValueError("Enter a valid email address.")
    if len(password) < AUTH_MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {AUTH_MIN_PASSWORD_LENGTH} characters long.")
    if _truncate_password(password) != _truncate_password(confirm_password):
        raise ValueError("Password and confirm password must match.")


def register_user(name: str, email: str, password: str, confirm_password: str) -> dict[str, Any]:
    """Register a new pending user."""
    _validate_registration_input(name, email, password, confirm_password)
    user = create_user(name=name, email=email, password_hash=hash_password(password))
    log_audit_event(
        "register",
        details={
            "email": user["email"],
            "name": user["name"],
            "approval_status": user.get("approval_status"),
            "is_active": user.get("is_active"),
        },
        user_id=int(user["id"]),
    )
    try:
        send_admin_registration_email(name=str(user["name"]), email=str(user["email"]))
        log_audit_event(
            "register_notification_sent",
            details={"email": user["email"], "admin_notified": True},
            user_id=int(user["id"]),
        )
    except Exception as exc:
        log_audit_event(
            "register_notification_failed",
            details={"email": user["email"], "error": str(exc)},
            user_id=int(user["id"]),
        )
    return user


def login_user(email: str, password: str) -> dict[str, Any]:
    """Authenticate a user by email and password."""
    normalized_email = email.strip().lower()
    if not normalized_email:
        raise ValueError("Email is required.")
    if not password:
        raise ValueError("Password is required.")

    user = get_user_by_email(normalized_email)
    if user is not None:
        locked_until = _active_lockout(user)
        if locked_until is not None:
            log_audit_event(
                "login_failure",
                details={"email": normalized_email, "reason": "account_locked", "locked_until": locked_until.isoformat(timespec="seconds")},
                user_id=int(user["id"]),
            )
            raise ValueError(_format_lockout_message(locked_until))

    if user is None or not verify_password(password, str(user["password_hash"])):
        attempt_state = record_failed_login_attempt(normalized_email)
        log_audit_event(
            "login_failure",
            details={
                "email": normalized_email,
                "reason": "invalid_credentials",
                "failed_attempts": None if attempt_state is None else attempt_state.get("failed_login_attempts"),
                "lock_threshold": AUTH_LOCKOUT_ATTEMPTS,
            },
            user_id=None if attempt_state is None else int(attempt_state["id"]),
        )
        if attempt_state is not None and attempt_state.get("locked_until"):
            raise ValueError(_format_lockout_message(attempt_state["locked_until"]))
        raise ValueError("Invalid email or password.")
    if str(user.get("approval_status", "")).lower() != "approved" or int(user.get("is_active", 0) or 0) != 1:
        log_audit_event(
            "login_failure",
            details={"email": normalized_email, "reason": "not_approved_or_inactive"},
            user_id=int(user["id"]),
        )
        raise ValueError("Your account is pending approval. Please contact the administrator.")

    reset_login_security_state(int(user["id"]))
    log_audit_event("login_success", details={"email": user["email"]}, user_id=int(user["id"]))
    _set_authenticated_session(user)
    return user


def logout_user() -> None:
    """Log out the current user."""
    user_id = get_current_user_id()
    user_email = st.session_state.get("auth_user_email")
    if user_id is not None:
        log_audit_event("logout", details={"email": user_email}, user_id=int(user_id))
    clear_auth_session()


def get_current_user() -> dict[str, Any] | None:
    """Return the authenticated user from session state."""
    initialize_auth_state()
    user_id = st.session_state.get("auth_user_id")
    if not st.session_state.get("is_authenticated") or user_id is None:
        return None
    return get_user_by_id(int(user_id))


def get_current_user_id() -> int | None:
    """Return the authenticated user id from session state."""
    user = get_current_user()
    if user is None:
        return None
    return int(user["id"])


def require_current_user_id() -> int:
    """Return the authenticated user id or raise a clear error."""
    user_id = get_current_user_id()
    if user_id is None:
        raise ValueError("You must be logged in to access user data.")
    return user_id


def is_authenticated() -> bool:
    """Return whether the current session is authenticated."""
    initialize_auth_state()
    return bool(st.session_state.get("is_authenticated"))


def is_admin_user() -> bool:
    """Return whether the current session belongs to the configured admin."""
    user = get_current_user()
    if user is None:
        return False
    admin_email = os.getenv("ADMIN_APPROVAL_EMAIL", "").strip().lower()
    if not admin_email:
        return False
    return str(user.get("email", "")).strip().lower() == admin_email


def require_admin() -> None:
    """Raise if the current user is not the configured admin."""
    if not is_authenticated():
        raise ValueError("You must be logged in to access the admin page.")
    if not is_admin_user():
        raise ValueError("You do not have permission to access this admin page.")


def change_password(user_id: int, current_password: str, new_password: str, confirm_password: str) -> None:
    """Change a user's password after verifying the current password."""
    if len(new_password) < AUTH_MIN_PASSWORD_LENGTH:
        raise ValueError(f"New password must be at least {AUTH_MIN_PASSWORD_LENGTH} characters long.")
    if _truncate_password(new_password) != _truncate_password(confirm_password):
        raise ValueError("New password and confirm password must match.")

    user = get_user_by_id(user_id)
    if user is None:
        raise ValueError("User not found.")
    if not verify_password(current_password, str(user["password_hash"])):
        raise ValueError("Current password is incorrect.")

    update_user_password(user_id, hash_password(new_password))
