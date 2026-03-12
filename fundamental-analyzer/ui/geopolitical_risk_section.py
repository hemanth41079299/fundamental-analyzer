"""Macro and geopolitical exposure UI section."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.design_system import format_percentage, render_empty_state, render_kpi_row, render_section_header, render_status_badge


def _render_exposure_chart(exposure_map: dict[str, float]) -> None:
    """Render a simple exposure bar chart."""
    if not exposure_map:
        st.info("Exposure map will appear after holdings are classified with sensitivity tags.")
        return
    try:
        import plotly.express as px
    except ModuleNotFoundError:
        st.bar_chart(pd.DataFrame({"Exposure": exposure_map}).T)
        return

    frame = pd.DataFrame(
        [{"Exposure": key.replace("_", " ").title(), "Percent": value} for key, value in exposure_map.items()]
    )
    fig = px.bar(frame, x="Exposure", y="Percent", color="Percent", color_continuous_scale="Blues")
    fig.update_layout(height=320, margin={"l": 10, "r": 10, "t": 20, "b": 10}, paper_bgcolor="#ffffff")
    st.plotly_chart(fig, use_container_width=True)


def render_geopolitical_risk_section(news_output: dict[str, object], impact_summary: dict[str, object]) -> None:
    """Render macro and geopolitical exposure summary."""
    render_section_header(
        "Macro / Geopolitical Exposure Summary",
        "Sensitivity-map driven exposure and theme mapping across the current portfolio.",
    )
    exposure_map = dict(news_output.get("exposure_map", {}))
    macro_events = list(news_output.get("macro_events", []))

    if not exposure_map and not macro_events:
        render_empty_state("No exposure mapping yet", "No macro or geopolitical events were mapped to the current portfolio in the latest scan.")
        return

    render_kpi_row(
        [
            {"title": "Most Affected Stock", "value": str(impact_summary.get("most_affected_stock") or "NA"), "delta": None},
            {"title": "Most Vulnerable Sector", "value": str(impact_summary.get("most_vulnerable_sector") or "NA"), "delta": None},
            {"title": "Macro Themes", "value": str(len(impact_summary.get("macro_themes_affecting_portfolio", []))), "delta": None},
            {"title": "Geopolitical Themes", "value": str(len(impact_summary.get("geopolitical_themes_affecting_portfolio", []))), "delta": None},
        ]
    )

    exposure_cards = []
    for key in ["rate_sensitive", "export_sensitive", "policy_sensitive", "commodity_sensitive", "geopolitical_sensitive"]:
        if key in exposure_map:
            exposure_cards.append(
                {
                    "title": key.replace("_", " ").title(),
                    "value": format_percentage(exposure_map.get(key)),
                    "delta": "Portfolio exposure",
                }
            )
    if exposure_cards:
        render_kpi_row(exposure_cards[:5])

    left_column, right_column = st.columns([1.1, 1])
    with left_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Exposure Map", tone="info")
        _render_exposure_chart(exposure_map)
        st.markdown("</div>", unsafe_allow_html=True)
    with right_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Macro Events", tone="warning" if macro_events else "positive")
        if not macro_events:
            st.info("No mapped macro or geopolitical events were detected.")
        else:
            event_rows = []
            for event in macro_events:
                affected = list(event.get("affected_holdings", []))
                event_rows.append(
                    {
                        "Theme": event.get("theme"),
                        "Event": event.get("event_title"),
                        "Type": event.get("event_type"),
                        "Affected Holdings": ", ".join(str(item.get("ticker")) for item in affected[:4]),
                        "Date": event.get("event_date"),
                    }
                )
            st.dataframe(pd.DataFrame(event_rows), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
