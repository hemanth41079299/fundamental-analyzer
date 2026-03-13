"""Professional login page UI."""

from __future__ import annotations

import streamlit as st

from config.settings import AUTH_LOCKOUT_ATTEMPTS, AUTH_LOCKOUT_MINUTES
from services.auth_service import login_user
from ui.components.section_header import render_section_header
from ui.layout_helpers import centered_auth_columns
from ui.theme import apply_theme_css


def render_login_page() -> None:
    """Render the login screen."""
    apply_theme_css()
    left_column, right_column = centered_auth_columns()

    with left_column:
        st.markdown(
            """
            <div class="ui-auth-hero">
                <div class="ui-auth-brand-panel">
                    <div class="ui-auth-product-title">Fundamental Analyzer</div>
                    <div class="ui-auth-product-subtitle">Professional investment research platform</div>
                    <div class="ui-auth-brand-headline">Institutional-grade research and portfolio oversight</div>
                    <div class="ui-auth-brand-copy">
                        Track portfolios, analyze companies, monitor risk, and manage watchlists through a secure research workspace.
                    </div>
                    <div class="ui-auth-feature-list">
                        <div class="ui-auth-feature-item">
                            <div class="ui-auth-feature-title">Portfolio oversight</div>
                            <div class="ui-auth-feature-copy">Track holdings, transactions, cash, allocation, and portfolio health from one dashboard.</div>
                        </div>
                        <div class="ui-auth-feature-item">
                            <div class="ui-auth-feature-title">Research workflow</div>
                            <div class="ui-auth-feature-copy">Run company analysis, compare rule scorecards, and monitor valuation, earnings quality, and news signals.</div>
                        </div>
                        <div class="ui-auth-feature-item">
                            <div class="ui-auth-feature-title">Controlled access</div>
                            <div class="ui-auth-feature-copy">Accounts require administrator approval and all protected actions operate inside an authenticated workspace.</div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_column:
        render_section_header(
            "Sign in",
            "Use your approved account to access dashboards, company research, watchlists, rule management, and monitoring.",
        )
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            st.markdown(
                """
                <div class="ui-auth-inline-note">
                    <span class="ui-auth-link">Forgot password?</span> Contact the administrator to reset access.
                </div>
                """,
                unsafe_allow_html=True,
            )
            submitted = st.form_submit_button("Login", use_container_width=True)
        st.markdown(
            f"""
            <div class="ui-auth-security-note">
                Security note: credentials are verified inside the authenticated workspace. After {AUTH_LOCKOUT_ATTEMPTS} failed attempts, sign-in is locked for {AUTH_LOCKOUT_MINUTES} minutes.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if submitted:
        try:
            login_user(email=email, password=password)
            st.success("Login successful.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
