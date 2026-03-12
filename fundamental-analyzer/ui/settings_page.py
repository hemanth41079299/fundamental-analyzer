"""Authenticated user settings UI."""

from __future__ import annotations

from typing import Any

import streamlit as st

from services.auth_service import change_password
from ui.design_system import render_section_header, render_status_badge
from ui.ui_theme import apply_finance_theme


def render_settings_page(current_user: dict[str, Any]) -> None:
    """Render user account settings."""
    apply_finance_theme()
    render_section_header(
        "Account Settings",
        "Manage your authentication details and keep your research workspace secure.",
    )

    profile_column, password_column = st.columns([0.95, 1.35])

    with profile_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Authenticated", tone="positive")
        st.markdown("#### Profile")
        st.caption("Current signed-in account")
        st.metric("Name", str(current_user["name"]))
        st.metric("Email", str(current_user["email"]))
        st.caption("Portfolio data, history, uploads, and custom rules are isolated per user.")
        st.markdown("</div>", unsafe_allow_html=True)

    with password_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Security", tone="info")
        render_section_header(
            "Change Password",
            "Use your current password to rotate credentials for this local account.",
        )
        with st.form("change_password_form", clear_on_submit=True):
            current_password = st.text_input("Current Password", type="password", placeholder="Enter current password")
            new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
            confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Repeat new password")
            submitted = st.form_submit_button("Update Password", use_container_width=True)
        st.caption("Passwords are hashed with bcrypt and never stored in plain text.")
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        try:
            change_password(
                user_id=int(current_user["id"]),
                current_password=current_password,
                new_password=new_password,
                confirm_password=confirm_password,
            )
            st.success("Password updated successfully.")
        except ValueError as exc:
            st.error(str(exc))
