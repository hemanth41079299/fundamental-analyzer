"""Authenticated user settings UI."""

from __future__ import annotations

from typing import Any

import streamlit as st

from services.auth_service import change_password
from ui.design_system import render_page_header, render_section_header, render_status_badge
from ui.ui_theme import apply_finance_theme, render_theme_toggle


def render_settings_page(current_user: dict[str, Any]) -> None:
    """Render user account settings."""
    apply_finance_theme()
    render_page_header(
        "Settings",
        "Manage profile details, appearance preferences, security controls, and account status from one place.",
        badges=[
            ("Authenticated", "positive"),
            (str(current_user.get("approval_status", "approved")).title(), "info"),
        ],
    )

    profile_column, controls_column = st.columns([0.95, 1.35])

    with profile_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Profile", tone="info")
        render_section_header("Account Profile", "Current signed-in account and data-isolation context.")
        st.metric("Name", str(current_user["name"]))
        st.metric("Email", str(current_user["email"]))
        st.metric("Approval Status", str(current_user.get("approval_status", "approved")).title())
        st.metric("Account State", "Active" if bool(current_user.get("is_active", True)) else "Inactive")
        st.caption("Portfolio data, history, uploads, and custom rules are isolated per user.")
        st.markdown("</div>", unsafe_allow_html=True)

    with controls_column:
        top_row, bottom_row = st.columns([0.9, 1.3])
        with top_row:
            st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
            render_status_badge("Appearance", tone="info")
            render_section_header("Interface Mode", "Switch between light and dark themes while keeping the interface restrained and professional.")
            render_theme_toggle(location="main", key="settings_theme_mode")
            st.caption("Theme preference is stored in session state for the current session.")
            st.markdown("</div>", unsafe_allow_html=True)
        with bottom_row:
            st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
            render_status_badge("Security", tone="info")
            render_section_header(
                "Workspace Security",
                "Password authentication, audit logging, approval workflow, and session timeout protections are active.",
            )
            st.write("- Passwords are hashed before storage")
            st.write("- Login failures are tracked and temporarily locked after repeated failures")
            st.write("- Session timeout is enforced on protected views")
            st.write("- Important account actions are written to the audit log")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Password", tone="warning")
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
