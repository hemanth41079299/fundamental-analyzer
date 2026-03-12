"""Login page UI."""

from __future__ import annotations

import streamlit as st

from config.settings import AUTH_LOCKOUT_ATTEMPTS, AUTH_LOCKOUT_MINUTES
from services.auth_service import login_user
from ui.design_system import render_section_header, render_status_badge
from ui.ui_theme import apply_finance_theme


def render_login_page() -> None:
    """Render the login form."""
    apply_finance_theme()
    _, center_column, _ = st.columns([1, 1.15, 1])
    with center_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Secure Login", tone="info")
        render_section_header(
            "Welcome Back",
            "Access research, portfolio analytics, watchlists, and custom rules from one workspace.",
        )
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        st.caption(
            f"Only approved and active accounts can sign in. After {AUTH_LOCKOUT_ATTEMPTS} failed attempts, access is locked for {AUTH_LOCKOUT_MINUTES} minutes."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        try:
            login_user(email=email, password=password)
            st.success("Login successful.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
