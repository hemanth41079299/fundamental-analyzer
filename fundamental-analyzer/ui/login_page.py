"""Login page UI."""

from __future__ import annotations

import streamlit as st

from config.settings import AUTH_LOCKOUT_ATTEMPTS, AUTH_LOCKOUT_MINUTES
from services.auth_service import login_user
from ui.design_system import render_insight_card, render_page_header, render_status_badge
from ui.layout_helpers import centered_auth_columns
from ui.ui_theme import apply_finance_theme


def render_login_page() -> None:
    """Render the login form."""
    apply_finance_theme()
    left_column, right_column = centered_auth_columns()
    with left_column:
        st.markdown('<div class="finance-hero-panel">', unsafe_allow_html=True)
        render_page_header(
            "Research. Track. Move Fast.",
            "A premium multi-user investing workspace for company research, portfolio intelligence, and rule-driven monitoring.",
            badges=[("Gen-Z Premium UI", "info"), ("Secure Access", "neutral")],
        )
        render_insight_card("Portfolio", "Live dashboards", "Track holdings, watchlists, cash, and news impact in one place.", "positive")
        render_insight_card("Research", "Rule-based conviction", "Scorecards, valuation, risk layers, and thesis cards stay user-specific.", "info")
        render_insight_card("Security", "Session and audit controls", f"{AUTH_LOCKOUT_ATTEMPTS} failed attempts trigger a {AUTH_LOCKOUT_MINUTES}-minute lockout.", "warning")
        st.markdown("</div>", unsafe_allow_html=True)
    with right_column:
        st.markdown('<div class="finance-auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="finance-auth-kicker">Secure login</div>', unsafe_allow_html=True)
        render_page_header(
            "Welcome back",
            "Sign in to access portfolio dashboards, company research, watchlists, rules, and settings.",
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
