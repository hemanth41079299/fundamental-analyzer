"""Chart card wrapper."""

from __future__ import annotations

import streamlit as st

from ui.components.section_header import render_section_header
from ui.theme import apply_theme_css


def render_chart_card(title: str, subtitle: str | None = None) -> None:
    """Open a chart card wrapper."""
    apply_theme_css()
    st.markdown('<div class="ui-chart-card">', unsafe_allow_html=True)
    render_section_header(title, subtitle)


def close_chart_card() -> None:
    """Close a chart card wrapper."""
    st.markdown("</div>", unsafe_allow_html=True)
