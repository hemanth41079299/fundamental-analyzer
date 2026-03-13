"""Reusable news briefing rendering for the Monitor page."""

from __future__ import annotations

import html

import streamlit as st

from ui.design_system import render_empty_state, render_section_header


def _tone_class(label: str) -> str:
    """Map one label to the shared badge palette."""
    lowered = str(label or "").strip().lower()
    if lowered in {"high", "negative headwind", "regulation"}:
        return "ui-badge-risk"
    if lowered in {"moderate", "india policy", "macro", "markets"}:
        return "ui-badge-watch"
    if lowered in {"positive tailwind"}:
        return "ui-badge-positive"
    return "ui-badge-info"


def _link_html(label: str, url: str) -> str:
    """Build one safe clickable link."""
    cleaned_url = str(url or "").strip()
    if not cleaned_url:
        return html.escape(label)
    return (
        f'<a href="{html.escape(cleaned_url, quote=True)}" '
        'target="_blank" style="color: var(--ui-heading-text); text-decoration: none;">'
        f"{html.escape(label)}</a>"
    )


def _render_featured_story(item: dict[str, object]) -> None:
    """Render one featured story card."""
    category = str(item.get("category") or "News")
    severity = str(item.get("severity") or "Low")
    direction = str(item.get("impact_direction") or "Neutral / Monitor")
    source = str(item.get("source") or "Google News")
    published_at = str(item.get("published_at") or "Unknown date")
    title = str(item.get("title") or "Untitled headline")
    summary = str(item.get("summary") or title)
    url = str(item.get("url") or "").strip()
    title_link = _link_html(title, url)
    action_link = (
        f'<a href="{html.escape(url, quote=True)}" target="_blank" style="color: var(--ui-accent); font-weight: 600; text-decoration: none;">Open article</a>'
        if url
        else '<span class="ui-caption">Article link unavailable</span>'
    )
    st.markdown(
        f"""
        <div class="ui-card" style="height: 100%;">
            <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px;">
                <span class="ui-badge ui-badge-info">{html.escape(category)}</span>
                <span class="ui-badge {_tone_class(severity)}">{html.escape(severity)}</span>
                <span class="ui-badge {_tone_class(direction)}">{html.escape(direction)}</span>
            </div>
            <div class="ui-card-title" style="line-height: 1.4; margin-bottom: 10px; font-size: 22px;">{title_link}</div>
            <div class="ui-caption" style="margin-bottom: 10px;">{html.escape(source)} | {html.escape(published_at)}</div>
            <div class="ui-section-caption" style="margin-bottom: 14px;">{html.escape(summary)}</div>
            <div>{action_link}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_supporting_story(item: dict[str, object]) -> None:
    """Render one compact supporting headline row."""
    severity = str(item.get("severity") or "Low")
    source = str(item.get("source") or "Google News")
    published_at = str(item.get("published_at") or "Unknown date")
    title = str(item.get("title") or "Untitled headline")
    summary = str(item.get("summary") or title)
    url = str(item.get("url") or "").strip()
    st.markdown(
        f"""
        <div class="ui-card" style="padding: 16px;">
            <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom: 8px;">
                <div class="ui-card-title" style="font-size: 16px; line-height: 1.45; margin: 0;">{_link_html(title, url)}</div>
                <span class="ui-badge {_tone_class(severity)}">{html.escape(severity)}</span>
            </div>
            <div class="ui-caption" style="margin-bottom: 8px;">{html.escape(source)} | {html.escape(published_at)}</div>
            <div class="ui-section-caption">{html.escape(summary)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_news_monitor_section(
    title: str,
    caption: str,
    items: list[dict[str, object]],
    empty_message: str,
) -> None:
    """Render one news briefing section with clickable links."""
    render_section_header(title, caption)
    if not items:
        render_empty_state(f"No {title.lower()}", empty_message)
        return

    featured = items[0]
    supporting = items[1:]

    left_column, right_column = st.columns([1.15, 0.85], gap="large")
    with left_column:
        _render_featured_story(featured)
    with right_column:
        if not supporting:
            st.markdown(
                """
                <div class="ui-card">
                    <div class="ui-card-title">No additional headlines</div>
                    <div class="ui-section-caption">Only one headline was available in this bucket.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for item in supporting[:5]:
                _render_supporting_story(item)
