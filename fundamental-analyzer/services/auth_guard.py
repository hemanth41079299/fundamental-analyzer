"""Session timeout guard for authenticated Streamlit requests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import streamlit as st

from config.settings import AUTH_SESSION_TIMEOUT_MINUTES
from services.audit_service import log_audit_event
from services.auth_service import clear_auth_session, get_current_user_id, initialize_auth_state


def _utcnow() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def _parse_timestamp(value: object) -> datetime | None:
    """Parse an ISO timestamp from session state."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def touch_session_activity() -> None:
    """Refresh the authenticated session activity timestamp."""
    initialize_auth_state()
    st.session_state["auth_last_activity_at"] = _utcnow().isoformat(timespec="seconds")


def enforce_session_timeout() -> bool:
    """Expire authenticated sessions that have been idle for too long."""
    initialize_auth_state()
    if not st.session_state.get("is_authenticated"):
        return False

    last_activity = _parse_timestamp(st.session_state.get("auth_last_activity_at"))
    if last_activity is None:
        touch_session_activity()
        return False

    timeout_window = timedelta(minutes=AUTH_SESSION_TIMEOUT_MINUTES)
    if _utcnow() - last_activity <= timeout_window:
        return False

    user_id = get_current_user_id()
    log_audit_event(
        "session_timeout",
        details={"timeout_minutes": AUTH_SESSION_TIMEOUT_MINUTES},
        user_id=user_id,
    )
    clear_auth_session()
    return True
