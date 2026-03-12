"""Session-based authentication helpers for Streamlit."""

from __future__ import annotations

from typing import Any

import streamlit as st

from services.audit_service import log_audit_event
from services.user_service import create_user, get_user_by_email, get_user_by_id, update_user_password

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
}


def _truncate_password(password: str) -> str:
    """Truncate a password to bcrypt's 72-byte limit."""
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")


def _require_password_context() -> None:
    """Ensure passlib is installed before using password functions."""
    if PASSWORD_CONTEXT is None:
        raise ValueError("passlib is not installed. Run: pip install -r requirements.txt")


def initialize_auth_state() -> None:
    """Initialize Streamlit auth session keys."""
    for key, value in AUTH_STATE_DEFAULTS.items():
        st.session_state.setdefault(key, value)


def _set_authenticated_session(user: dict[str, Any]) -> None:
    """Persist authenticated user data in session state."""
    st.session_state["auth_user_id"] = int(user["id"])
    st.session_state["auth_user_name"] = str(user["name"])
    st.session_state["auth_user_email"] = str(user["email"])
    st.session_state["is_authenticated"] = True


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
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if _truncate_password(password) != _truncate_password(confirm_password):
        raise ValueError("Password and confirm password must match.")


def register_user(name: str, email: str, password: str, confirm_password: str) -> dict[str, Any]:
    """Register a new user and log them in."""
    _validate_registration_input(name, email, password, confirm_password)
    user = create_user(name=name, email=email, password_hash=hash_password(password))
    log_audit_event("register", details={"email": user["email"], "name": user["name"]}, user_id=int(user["id"]))
    _set_authenticated_session(user)
    return user


def login_user(email: str, password: str) -> dict[str, Any]:
    """Authenticate a user by email and password."""
    if not email.strip():
        raise ValueError("Email is required.")
    if not password:
        raise ValueError("Password is required.")

    user = get_user_by_email(email)
    if user is None or not verify_password(password, str(user["password_hash"])):
        raise ValueError("Invalid email or password.")

    log_audit_event("login", details={"email": user["email"]}, user_id=int(user["id"]))
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


def change_password(user_id: int, current_password: str, new_password: str, confirm_password: str) -> None:
    """Change a user's password after verifying the current password."""
    if len(new_password) < 8:
        raise ValueError("New password must be at least 8 characters long.")
    if _truncate_password(new_password) != _truncate_password(confirm_password):
        raise ValueError("New password and confirm password must match.")

    user = get_user_by_id(user_id)
    if user is None:
        raise ValueError("User not found.")
    if not verify_password(current_password, str(user["password_hash"])):
        raise ValueError("Current password is incorrect.")

    update_user_password(user_id, hash_password(new_password))
