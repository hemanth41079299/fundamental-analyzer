"""Portfolio news impact UI section."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.design_system import render_empty_state, render_kpi_row, render_section_header, render_status_badge


def _render_event_table(rows: list[dict[str, object]], title: str, empty_message: str) -> None:
    """Render a compact event table."""
    render_section_header(title, None)
    if not rows:
        st.info(empty_message)
        return

    frame = pd.DataFrame(rows).rename(
        columns={
            "ticker": "Ticker",
            "company_name": "Company",
            "event_title": "Event",
            "event_type": "Type",
            "impact_direction": "Direction",
            "severity": "Severity",
            "why_it_matters": "Why it matters",
            "event_date": "Date",
        }
    )
    preferred_columns = [column for column in ["Ticker", "Company", "Event", "Type", "Direction", "Severity", "Why it matters", "Date"] if column in frame.columns]
    st.dataframe(frame[preferred_columns], use_container_width=True, hide_index=True)


def render_portfolio_news_section(news_output: dict[str, object], impact_summary: dict[str, object]) -> None:
    """Render portfolio news impact summary, tailwinds, headwinds, and holding-level mapping."""
    render_section_header(
        "Portfolio News Impact Summary",
        "Company, sector, macro, and geopolitical events mapped to current holdings.",
    )

    impact_rows = list(news_output.get("impact_rows", []))
    if not impact_rows:
        render_empty_state("No mapped portfolio news", "No company, sector, or macro events were mapped to current holdings in the latest scan.")
        return

    summary = dict(news_output.get("portfolio_summary", {}))
    render_kpi_row(
        [
            {"title": "Impacted Holdings", "value": str(summary.get("impacted_holdings", 0)), "delta": None},
            {"title": "Positive Tailwinds", "value": str(summary.get("positive_events", 0)), "delta": None},
            {"title": "Negative Headwinds", "value": str(summary.get("negative_events", 0)), "delta": None},
            {"title": "Monitor Events", "value": str(summary.get("monitor_events", 0)), "delta": None},
        ]
    )

    st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
    render_status_badge("Portfolio View", tone="info")
    st.write(str(impact_summary.get("summary_text") or ""))
    st.markdown("</div>", unsafe_allow_html=True)

    left_column, right_column = st.columns(2)
    with left_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Positive Tailwinds", tone="positive")
        _render_event_table(
            list(news_output.get("top_positive_tailwinds", [])),
            "Top Positive Tailwinds",
            "No positive portfolio tailwinds were identified.",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with right_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Negative Headwinds", tone="warning")
        _render_event_table(
            list(news_output.get("top_negative_headwinds", [])),
            "Top Negative Headwinds",
            "No negative portfolio headwinds were identified.",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
    render_status_badge("Holding-Level Impact Table", tone="neutral")
    _render_event_table(impact_rows, "Holding-Level News Impact", "No holding-level news impact rows were generated.")
    source_errors = list(news_output.get("source_errors", []))
    if source_errors:
        st.caption("Some news feeds were partially unavailable during the scan.")
    st.markdown("</div>", unsafe_allow_html=True)
