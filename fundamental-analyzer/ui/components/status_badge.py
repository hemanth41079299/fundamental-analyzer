"""Status badge component."""

from __future__ import annotations

import html

import streamlit as st

from ui.theme import apply_theme_css


def render_status_badge(label: str, tone: str = "info") -> None:
    """Render a themed status badge."""
    apply_theme_css()
    tone_class = {
        "positive": "ui-badge-positive",
        "risk": "ui-badge-risk",
        "watch": "ui-badge-watch",
        "info": "ui-badge-info",
    }.get(tone, "ui-badge-info")
    st.markdown(f'<span class="ui-badge {tone_class}">{html.escape(label)}</span>', unsafe_allow_html=True)
