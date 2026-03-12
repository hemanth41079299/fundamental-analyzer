"""Compatibility design helpers backed by the new component system."""

from __future__ import annotations

import html
from typing import Callable

import pandas as pd
import streamlit as st

from ui.components.kpi_card import render_kpi_card as component_kpi_card
from ui.components.section_header import render_page_header as component_page_header
from ui.components.section_header import render_section_header as component_section_header
from ui.components.status_badge import render_status_badge as component_status_badge
from ui.theme import apply_theme_css, get_theme


def render_page_header(title: str, subtitle: str, badges: list[tuple[str, str]] | None = None) -> None:
    """Render a page header and optional badges."""
    apply_theme_css()
    component_page_header(title, subtitle)
    if badges:
        badge_columns = st.columns(len(badges))
        for column, (label, tone) in zip(badge_columns, badges):
            with column:
                component_status_badge(label, tone="risk" if tone == "negative" else "watch" if tone == "warning" else tone)


def render_section_header(title: str, caption: str | None = None) -> None:
    """Render a section header."""
    component_section_header(title, caption)


def render_status_badge(label: str, tone: str = "neutral") -> None:
    """Render a status badge."""
    tone_map = {
        "positive": "positive",
        "warning": "watch",
        "negative": "risk",
        "info": "info",
        "neutral": "info",
        "watch": "watch",
        "risk": "risk",
    }
    component_status_badge(label, tone=tone_map.get(tone, "info"))


def render_kpi_card(title: str, value: str, delta_text: str | None = None, help_text: str | None = None) -> None:
    """Render a KPI card."""
    component_kpi_card(title, value, change=delta_text or help_text)


def render_kpi_row(cards: list[dict[str, str | None]]) -> None:
    """Render a row of KPI cards."""
    columns = st.columns(len(cards))
    for column, card in zip(columns, cards):
        with column:
            component_kpi_card(
                str(card.get("title", "")),
                str(card.get("value", "NA")),
                change=card.get("delta") or card.get("help"),
            )


def render_chart_card(title: str, render_chart: Callable[[], None], caption: str | None = None) -> None:
    """Render a chart card wrapper."""
    apply_theme_css()
    st.markdown('<div class="ui-chart-card">', unsafe_allow_html=True)
    component_section_header(title, caption)
    render_chart()
    st.markdown("</div>", unsafe_allow_html=True)


def render_insight_card(label: str, value: str, meta: str | None = None, tone: str = "info") -> None:
    """Render an insight card."""
    apply_theme_css()
    tone_class = {
        "positive": "ui-badge-positive",
        "warning": "ui-badge-watch",
        "negative": "ui-badge-risk",
        "risk": "ui-badge-risk",
        "watch": "ui-badge-watch",
        "info": "ui-badge-info",
        "neutral": "ui-badge-info",
    }.get(tone, "ui-badge-info")
    meta_html = f'<div class="ui-caption">{html.escape(meta)}</div>' if meta else ""
    st.markdown(
        f"""
        <div class="ui-card">
            <div class="ui-kpi-label">{html.escape(label)}</div>
            <div class="ui-card-title" style="font-size:18px; margin-bottom:8px;">{html.escape(value)}</div>
            <div style="margin-bottom:10px;"><span class="ui-badge {tone_class}">{html.escape(tone.title())}</span></div>
            {meta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_action_bar(title: str, caption: str | None = None, badges: list[tuple[str, str]] | None = None) -> None:
    """Render an action bar."""
    apply_theme_css()
    badges_html = ""
    if badges:
        parts = []
        for label, tone in badges:
            tone_class = {
                "positive": "ui-badge-positive",
                "warning": "ui-badge-watch",
                "negative": "ui-badge-risk",
                "info": "ui-badge-info",
                "neutral": "ui-badge-info",
            }.get(tone, "ui-badge-info")
            parts.append(f'<span class="ui-badge {tone_class}">{html.escape(label)}</span>')
        badges_html = "".join(parts)
    st.markdown(
        f"""
        <div class="ui-card" style="padding:16px; margin-bottom:16px;">
            <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;">
                <div>
                    <div class="ui-card-title">{html.escape(title)}</div>
                    {'<div class="ui-caption">' + html.escape(caption) + '</div>' if caption else ''}
                </div>
                <div style="display:flex; gap:8px; flex-wrap:wrap;">{badges_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_table_card(title: str, frame: pd.DataFrame, caption: str | None = None) -> None:
    """Render a dataframe inside a card."""
    apply_theme_css()
    st.markdown('<div class="ui-table-card">', unsafe_allow_html=True)
    component_section_header(title, caption)
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_form_card_start(title: str, caption: str | None = None) -> None:
    """Open a form card."""
    apply_theme_css()
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    component_section_header(title, caption)


def render_card_end() -> None:
    """Close a form or generic card."""
    st.markdown("</div>", unsafe_allow_html=True)


def render_empty_state(title: str, message: str) -> None:
    """Render an empty state."""
    apply_theme_css()
    st.markdown(
        f"""
        <div class="ui-card" style="text-align:center; border-style:dashed;">
            <div class="ui-card-title" style="font-size:18px;">{html.escape(title)}</div>
            <div class="ui-caption">{html.escape(message)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_currency(value: object) -> str:
    """Format currency."""
    try:
        if value is None or pd.isna(value):
            return "NA"
        return f"Rs {float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def format_percentage(value: object) -> str:
    """Format percent."""
    try:
        if value is None or pd.isna(value):
            return "NA"
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return str(value)


def gain_loss_style(value: object) -> str:
    """Return positive/negative numeric style."""
    theme = get_theme()
    try:
        if value is None or pd.isna(value):
            return ""
        numeric = float(value)
    except (TypeError, ValueError):
        return ""
    if numeric > 0:
        return f"color: {theme['positive_text']}; font-weight: 700;"
    if numeric < 0:
        return f"color: {theme['negative_text']}; font-weight: 700;"
    return f"color: {theme['caption_text']}; font-weight: 600;"


def badge_style(value: object, palette: dict[str, str]) -> str:
    """Return inline badge style."""
    theme = get_theme()
    default_style = (
        f"background-color: {theme['info_background']}; "
        f"color: {theme['info_text']}; "
        f"border: 1px solid {theme['border']}; "
        "border-radius: 999px; padding: 0.2rem 0.5rem;"
    )
    return palette.get(str(value or "Unknown"), default_style)
