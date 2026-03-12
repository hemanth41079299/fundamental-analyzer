"""Professional login page UI."""

from __future__ import annotations

import streamlit as st

from config.settings import AUTH_LOCKOUT_ATTEMPTS, AUTH_LOCKOUT_MINUTES
from services.auth_service import login_user
from ui.components.section_header import render_page_header, render_section_header
from ui.components.status_badge import render_status_badge
from ui.layout_helpers import centered_auth_columns
from ui.theme import apply_theme_css


def render_login_page() -> None:
    """Render the login screen."""
    apply_theme_css()
    left_column, right_column = centered_auth_columns()

    with left_column:
        st.markdown('<div class="ui-panel ui-auth-hero">', unsafe_allow_html=True)
        render_status_badge("Professional Research Workspace", "info")
        render_page_header(
            "Institutional-grade investing workflow",
            "Track portfolios, evaluate companies, monitor rules, and surface risks through a clean multi-user dashboard.",
        )
        st.markdown(
            """
            <div class="ui-card">
                <div class="ui-card-title">Why this workspace</div>
                <div class="ui-caption">Portfolio tracking, company research, watchlist intelligence, news monitoring, and audit-backed account controls are available under one secure login.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right_column:
        st.markdown('<div class="ui-auth-card">', unsafe_allow_html=True)
        render_status_badge("Secure Login", "info")
        render_section_header(
            "Sign in",
            "Approved users can access research, portfolio dashboards, watchlists, rules, and account settings.",
        )
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login", use_container_width=True)
        st.caption(
            f"Security policy: after {AUTH_LOCKOUT_ATTEMPTS} failed attempts, access is locked for {AUTH_LOCKOUT_MINUTES} minutes."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        try:
            login_user(email=email, password=password)
            st.success("Login successful.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
