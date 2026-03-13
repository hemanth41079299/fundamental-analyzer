"""Overview cards for the News & Macro Monitor page."""

from __future__ import annotations

import html

import streamlit as st

from ui.design_system import render_empty_state, render_kpi_row, render_section_header


def _headline_link(title: str, url: str) -> str:
    """Build one linked headline for overview lists."""
    cleaned_url = str(url or "").strip()
    if not cleaned_url:
        return html.escape(title)
    return (
        f'<a href="{html.escape(cleaned_url, quote=True)}" '
        'target="_blank" style="color: var(--ui-heading-text); text-decoration: none;">'
        f"{html.escape(title)}</a>"
    )


def render_monitor_overview(
    summary_data: dict[str, object],
    impact_summary: dict[str, object],
    high_impact_alerts: list[dict[str, object]],
    impact_rows: list[dict[str, object]],
) -> None:
    """Render daily summary, themes, alerts, and portfolio impact snapshot."""
    render_section_header(
        "Daily Summary",
        "Structured view of today's geopolitical, policy, and business developments.",
    )
    st.markdown(
        f"""
        <div class="ui-card">
            <div class="ui-card-title">Today's monitor summary</div>
            <div class="ui-section-caption">{html.escape(str(summary_data.get("summary_text") or "No monitor summary is available right now."))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_column, right_column = st.columns(2, gap="large")
    with left_column:
        top_themes = list(summary_data.get("top_themes", []))
        if not top_themes:
            render_empty_state("No recurring themes", "No dominant themes were detected across the latest news buckets.")
        else:
            theme_items = "".join(f"<li>{html.escape(str(theme))}</li>" for theme in top_themes)
            st.markdown(
                f"""
                <div class="ui-card">
                    <div class="ui-card-title">Top themes</div>
                    <div class="ui-section-caption">
                        <ul style="margin: 0; padding-left: 18px;">{theme_items}</ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right_column:
        if not high_impact_alerts:
            render_empty_state("No high impact alerts", "No high-severity developments were identified in the latest scan.")
        else:
            alert_items = "".join(
                f"<li>{_headline_link(str(item.get('title') or 'Untitled headline'), str(item.get('url') or ''))}</li>"
                for item in high_impact_alerts[:5]
            )
            st.markdown(
                f"""
                <div class="ui-card">
                    <div class="ui-card-title">High impact alerts</div>
                    <div class="ui-section-caption">
                        <ul style="margin: 0; padding-left: 18px;">{alert_items}</ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    positive_count = sum(1 for row in impact_rows if row.get("impact_direction") == "Positive Tailwind")
    negative_count = sum(1 for row in impact_rows if row.get("impact_direction") == "Negative Headwind")
    render_kpi_row(
        [
            {"title": "Affected Holdings", "value": str(len({str(row.get('ticker')) for row in impact_rows if row.get('ticker')}))},
            {"title": "Positive Tailwinds", "value": str(positive_count)},
            {"title": "Negative Headwinds", "value": str(negative_count)},
            {"title": "High Impact Events", "value": str(len(high_impact_alerts))},
        ]
    )

    st.markdown(
        f"""
        <div class="ui-card">
            <div class="ui-card-title">Portfolio impact snapshot</div>
            <div class="ui-section-caption">{html.escape(str(impact_summary.get("summary_text") or "No holding-level portfolio impact summary is available."))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
