"""Table card wrapper."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.components.section_header import render_section_header
from ui.theme import apply_theme_css


def render_table_card(title: str, data: pd.DataFrame, subtitle: str | None = None) -> None:
    """Render a dataframe inside a card container."""
    apply_theme_css()
    st.markdown('<div class="ui-table-card">', unsafe_allow_html=True)
    render_section_header(title, subtitle)
    st.dataframe(data, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
