"""KPI card component."""

from __future__ import annotations

import html

import streamlit as st

from ui.theme import apply_theme_css


def render_kpi_card(title: str, value: str, change: str | None = None) -> None:
    """Render a clean KPI card."""
    apply_theme_css()
    change_html = f'<div class="ui-kpi-change">{html.escape(change)}</div>' if change else ""
    st.markdown(
        f"""
        <div class="ui-card">
            <div class="ui-kpi-label">{html.escape(title)}</div>
            <div class="ui-kpi-value">{html.escape(value)}</div>
            {change_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
