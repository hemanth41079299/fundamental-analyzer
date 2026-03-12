"""Section header components."""

from __future__ import annotations

import html

import streamlit as st

from ui.theme import apply_theme_css


def render_page_header(title: str, subtitle: str) -> None:
    """Render a page-level header."""
    apply_theme_css()
    st.markdown(
        f"""
        <div class="ui-page-header">
            <h1 class="ui-page-title">{html.escape(title)}</h1>
            <div class="ui-page-subtitle">{html.escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: str | None = None) -> None:
    """Render a section header."""
    apply_theme_css()
    subtitle_html = f'<div class="ui-section-caption">{html.escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div style="margin-bottom: 12px;">
            <div class="ui-section-title">{html.escape(title)}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
