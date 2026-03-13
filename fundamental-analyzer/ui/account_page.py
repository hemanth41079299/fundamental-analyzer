"""Top-level account page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from services.auth_service import logout_user
from ui.admin_user_approvals_page import render_admin_user_approvals_page
from ui.components.section_header import render_page_header
from ui.settings_page import render_settings_page


def render_account_page(current_user: dict[str, Any], is_admin: bool) -> None:
    """Render the account workspace with tabs."""
    render_page_header(
        "Account",
        "User settings, administration, and session controls.",
    )
    tabs = st.tabs(["Settings", "User Management", "Logout"])
    with tabs[0]:
        render_settings_page(current_user)
    with tabs[1]:
        if is_admin:
            render_admin_user_approvals_page()
        else:
            st.info("User management is available only for approved admin accounts.")
    with tabs[2]:
        st.write("End the current authenticated session for this browser workspace.")
        if st.button("Logout", key="account_logout_button", use_container_width=True):
            logout_user()
            st.rerun()
