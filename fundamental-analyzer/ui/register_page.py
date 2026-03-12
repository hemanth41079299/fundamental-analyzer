"""Registration page UI."""

from __future__ import annotations

import streamlit as st

from config.settings import AUTH_MIN_PASSWORD_LENGTH
from services.auth_service import register_user
from ui.design_system import render_insight_card, render_page_header, render_status_badge
from ui.layout_helpers import centered_auth_columns
from ui.ui_theme import apply_finance_theme


def render_register_page() -> None:
    """Render the registration form."""
    apply_finance_theme()
    left_column, right_column = centered_auth_columns()
    with left_column:
        st.markdown('<div class="finance-hero-panel">', unsafe_allow_html=True)
        render_page_header(
            "Build your private investing workspace",
            "Create a user-scoped account for portfolio tracking, saved research history, custom rules, and watchlist intelligence.",
            badges=[("Approval Flow", "warning"), ("Multi-user", "info")],
        )
        render_insight_card("Workspace", "User-isolated data", "Portfolio, uploads, history, and custom rules are stored per account.", "positive")
        render_insight_card("Rules", "Customizable framework", "Default rules can be overridden with your own market-cap profiles.", "info")
        render_insight_card("Access", "Manual approval", "New registrations stay pending until approved by the administrator.", "warning")
        st.markdown("</div>", unsafe_allow_html=True)
    with right_column:
        st.markdown('<div class="finance-auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="finance-auth-kicker">Create account</div>', unsafe_allow_html=True)
        render_page_header(
            "Open your account",
            "Register to unlock portfolio dashboards, research pages, watchlists, and private rule management.",
        )
        with st.form("register_form", clear_on_submit=False):
            name = st.text_input("Full Name", placeholder="Your name")
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder=f"At least {AUTH_MIN_PASSWORD_LENGTH} characters")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Repeat the password")
            submitted = st.form_submit_button("Create Account", use_container_width=True)

        st.caption(
            f"New accounts are created in pending status and must be approved before login is allowed. Minimum password length: {AUTH_MIN_PASSWORD_LENGTH} characters."
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
