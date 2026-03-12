"""Reusable premium UI primitives for the finance app."""

from __future__ import annotations

import html
from typing import Callable

import pandas as pd
import streamlit as st

from ui.ui_theme import apply_finance_theme


def render_page_header(title: str, subtitle: str, badges: list[tuple[str, str]] | None = None) -> None:
    """Render a premium page header with optional status badges."""
    apply_finance_theme()
    badge_html = ""
    if badges:
        parts = []
        for label, tone in badges:
            tone_class = {
                "positive": "finance-badge-positive",
                "warning": "finance-badge-warning",
                "negative": "finance-badge-negative",
                "info": "finance-badge-info",
                "neutral": "finance-badge-neutral",
            }.get(tone, "finance-badge-neutral")
            parts.append(f'<span class="finance-badge {tone_class}">{html.escape(label)}</span>')
        badge_html = f'<div class="finance-page-status-row">{"".join(parts)}</div>'

    st.markdown(
        f"""
        <div class="finance-page-header">
            <h1>{html.escape(title)}</h1>
            <div class="finance-page-subtitle">{html.escape(subtitle)}</div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, caption: str | None = None) -> None:
    """Render a section header."""
    apply_finance_theme()
    caption_html = f'<div class="finance-section-caption">{html.escape(caption)}</div>' if caption else ""
    st.markdown(
        f"""
        <div class="finance-section-header">
            <h3>{html.escape(title)}</h3>
            {caption_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(label: str, tone: str = "neutral") -> None:
    """Render a status badge."""
    apply_finance_theme()
    tone_class = {
        "positive": "finance-badge-positive",
        "warning": "finance-badge-warning",
        "negative": "finance-badge-negative",
        "info": "finance-badge-info",
        "neutral": "finance-badge-neutral",
    }.get(tone, "finance-badge-neutral")
    st.markdown(f'<span class="finance-badge {tone_class}">{html.escape(label)}</span>', unsafe_allow_html=True)


def render_kpi_card(title: str, value: str, delta_text: str | None = None, help_text: str | None = None) -> None:
    """Render one KPI card."""
    apply_finance_theme()
    st.markdown(
        f"""
        <div class="finance-card">
            <div class="finance-card-title">{html.escape(title)}</div>
            <div class="finance-card-value">{html.escape(value)}</div>
            {'<div class="finance-card-delta">' + html.escape(delta_text) + '</div>' if delta_text else ''}
            {'<div class="finance-card-help">' + html.escape(help_text) + '</div>' if help_text else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_row(cards: list[dict[str, str | None]]) -> None:
    """Render a row of KPI cards."""
    apply_finance_theme()
    columns = st.columns(len(cards))
    for column, card in zip(columns, cards):
        with column:
            render_kpi_card(
                title=str(card.get("title", "")),
                value=str(card.get("value", "NA")),
                delta_text=card.get("delta"),
                help_text=card.get("help"),
            )


def render_chart_card(title: str, render_chart: Callable[[], None], caption: str | None = None) -> None:
    """Render a chart inside a premium card."""
    apply_finance_theme()
    st.markdown('<div class="finance-chart-card">', unsafe_allow_html=True)
    render_section_header(title, caption)
    render_chart()
    st.markdown("</div>", unsafe_allow_html=True)


def render_insight_card(label: str, value: str, meta: str | None = None, tone: str = "neutral") -> None:
    """Render an insight mini-card."""
    apply_finance_theme()
    tone_class = {
        "positive": "finance-badge-positive",
        "warning": "finance-badge-warning",
        "negative": "finance-badge-negative",
        "info": "finance-badge-info",
        "neutral": "finance-badge-neutral",
    }.get(tone, "finance-badge-neutral")
    meta_html = f'<div class="finance-insight-meta">{html.escape(meta)}</div>' if meta else ""
    st.markdown(
        f"""
        <div class="finance-insight-card">
            <div class="finance-insight-label">{html.escape(label)}</div>
            <div class="finance-insight-value">{html.escape(value)}</div>
            <span class="finance-badge {tone_class}">{html.escape(tone.title())}</span>
            {meta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_action_bar(title: str, caption: str | None = None, badges: list[tuple[str, str]] | None = None) -> None:
    """Render an action bar container header."""
    apply_finance_theme()
    badge_html = ""
    if badges:
        badge_html = "".join(
            f'<span class="finance-badge finance-badge-{"info" if tone not in {"positive","warning","negative","neutral","info"} else tone}">{html.escape(label)}</span>'
            for label, tone in badges
        )
    st.markdown(
        f"""
        <div class="finance-action-bar">
            <div>
                <div class="finance-card-title">{html.escape(title)}</div>
                {'<div class="finance-card-help">' + html.escape(caption) + '</div>' if caption else ''}
            </div>
            <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_table_card(title: str, frame: pd.DataFrame, caption: str | None = None) -> None:
    """Render a dataframe inside a card wrapper."""
    apply_finance_theme()
    st.markdown('<div class="finance-table-card">', unsafe_allow_html=True)
    render_section_header(title, caption)
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_form_card_start(title: str, caption: str | None = None) -> None:
    """Open a form card wrapper."""
    apply_finance_theme()
    st.markdown('<div class="finance-form-card">', unsafe_allow_html=True)
    render_section_header(title, caption)


def render_card_end() -> None:
    """Close a previously opened card wrapper."""
    st.markdown("</div>", unsafe_allow_html=True)


def render_empty_state(title: str, message: str) -> None:
    """Render a reusable empty state block."""
    apply_finance_theme()
    st.markdown(
        f"""
        <div class="finance-empty-state">
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(message)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_currency(value: object) -> str:
    """Format a numeric value as finance-friendly currency text."""
    try:
        if value is None or pd.isna(value):
            return "NA"
        return f"Rs {float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def format_percentage(value: object) -> str:
    """Format a numeric value as finance-friendly percentage text."""
    try:
        if value is None or pd.isna(value):
            return "NA"
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return str(value)


def gain_loss_style(value: object) -> str:
    """Return gain or loss styling for numeric values."""
    try:
        if value is None or pd.isna(value):
            return ""
        numeric_value = float(value)
    except (TypeError, ValueError):
        return ""

    if numeric_value > 0:
        return "color: #16a34a; font-weight: 700;"
    if numeric_value < 0:
        return "color: #ef4444; font-weight: 700;"
    return "color: #94a3b8; font-weight: 700;"


def badge_style(value: object, palette: dict[str, str]) -> str:
    """Return inline badge styling for styled tables."""
    label = str(value or "Unknown")
    return palette.get(
        label,
        "background-color: rgba(148,163,184,0.16); color: #475569; border-radius: 999px; padding: 0.24rem 0.58rem; font-weight: 700;",
    )
