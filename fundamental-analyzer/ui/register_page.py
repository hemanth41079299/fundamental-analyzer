"""Registration page UI."""

from __future__ import annotations

import streamlit as st

from config.settings import AUTH_MIN_PASSWORD_LENGTH
from services.auth_service import register_user
from ui.design_system import render_section_header, render_status_badge
from ui.ui_theme import apply_finance_theme


def render_register_page() -> None:
    """Render the registration form."""
    apply_finance_theme()
    _, center_column, _ = st.columns([1, 1.2, 1])
    with center_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("New Account", tone="neutral")
        render_section_header(
            "Create Your Workspace",
            "Set up a private account to manage research history, portfolio tracking, and custom rule profiles.",
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
