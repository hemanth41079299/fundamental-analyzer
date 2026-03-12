"""Reusable news alert dashboard helpers."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.design_system import render_empty_state, render_section_header, render_status_badge


def render_news_alerts_dashboard(
    title: str,
    alerts: list[dict[str, object]],
    caption: str,
    empty_message: str,
) -> None:
    """Render a compact news alert dashboard block."""
    render_section_header(title, caption)
    if not alerts:
        render_empty_state("No alerts", empty_message)
        return

    render_status_badge(f"{len(alerts)} alerts", tone="warning")
    st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)


def render_recent_news_table(
    items: list[dict[str, object]],
    title: str,
    caption: str,
    empty_message: str,
) -> None:
    """Render recent normalized news items."""
    render_section_header(title, caption)
    if not items:
        render_empty_state("No news items", empty_message)
        return

    st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
