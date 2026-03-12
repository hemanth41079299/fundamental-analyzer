"""Professional registration page UI."""

from __future__ import annotations

import streamlit as st

from config.settings import AUTH_MIN_PASSWORD_LENGTH
from services.auth_service import register_user
from ui.components.section_header import render_page_header, render_section_header
from ui.components.status_badge import render_status_badge
from ui.layout_helpers import centered_auth_columns
from ui.theme import apply_theme_css


def render_register_page() -> None:
    """Render the registration screen."""
    apply_theme_css()
    left_column, right_column = centered_auth_columns()

    with left_column:
        st.markdown('<div class="ui-panel ui-auth-hero">', unsafe_allow_html=True)
        render_status_badge("Private Account Setup", "watch")
        render_page_header(
            "Create your analysis workspace",
            "Open a private account for portfolio tracking, company research, watchlist monitoring, and user-specific rule profiles.",
        )
        st.markdown(
            """
            <div class="ui-card">
                <div class="ui-card-title">Approval-based access</div>
                <div class="ui-caption">New accounts are created in pending state. An administrator must approve the account before protected views become available.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right_column:
        st.markdown('<div class="ui-auth-card">', unsafe_allow_html=True)
        render_status_badge("Register", "info")
        render_section_header(
            "Create account",
            "Use your name, email, and password to register a local user account.",
        )
        with st.form("register_form", clear_on_submit=False):
            name = st.text_input("Full Name", placeholder="Your name")
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder=f"At least {AUTH_MIN_PASSWORD_LENGTH} characters")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Repeat the password")
            submitted = st.form_submit_button("Create Account", use_container_width=True)
        st.caption(
            f"Minimum password length: {AUTH_MIN_PASSWORD_LENGTH} characters. Access remains pending until admin approval."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        try:
            register_user(
                name=name,
                email=email,
                password=password,
                confirm_password=confirm_password,
            )
            st.success("Account created. Your access is pending approval.")
        except ValueError as exc:
            st.error(str(exc))
