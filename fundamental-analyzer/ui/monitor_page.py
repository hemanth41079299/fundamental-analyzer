"""Top-level News & Macro Monitor page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from services.auth_service import get_current_user_id
from services.google_news_service import (
    clear_google_news_cache,
    fetch_business_news,
    fetch_geopolitical_news,
    fetch_india_policy_news,
)
from services.geopolitical_impact_service import load_holding_sensitivity_map
from services.holdings_service import calculate_holdings
from services.monitor_news_classifier import classify_monitor_news_items
from services.monitor_portfolio_mapping_service import map_monitor_news_to_portfolio
from services.news_summary_service import summarize_monitor_page
from services.portfolio_impact_summary_service import build_portfolio_impact_summary
from ui.design_system import render_empty_state, render_section_header
from ui.news_monitor_section import render_news_monitor_section
from ui.news_summary_cards import render_monitor_overview


def _collect_news_bundle(limit: int = 10) -> dict[str, object]:
    """Fetch and classify the three monitor news buckets."""
    geopolitical_raw = fetch_geopolitical_news(limit=limit)
    india_policy_raw = fetch_india_policy_news(limit=limit)
    business_raw = fetch_business_news(limit=limit)

    geopolitical = classify_monitor_news_items(list(geopolitical_raw.get("items", [])))
    india_policy = classify_monitor_news_items(list(india_policy_raw.get("items", [])))
    business = classify_monitor_news_items(list(business_raw.get("items", [])))

    errors: list[str] = []
    for error in list(geopolitical_raw.get("errors", [])) + list(india_policy_raw.get("errors", [])) + list(business_raw.get("errors", [])):
        if str(error) not in errors:
            errors.append(str(error))

    return {
        "geopolitical": geopolitical,
        "india_policy": india_policy,
        "business": business,
        "errors": errors,
    }


def _portfolio_impact_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Convert mapped holding rows into one display dataframe."""
    if not rows:
        return pd.DataFrame(
        columns=["Ticker", "Event", "Category", "Direction", "Severity", "Why it matters", "Date", "Article"]
        )
    frame = pd.DataFrame(rows).rename(
        columns={
            "ticker": "Ticker",
            "news_title": "Event",
            "news_category": "Category",
            "impact_direction": "Direction",
            "severity": "Severity",
            "reason": "Why it matters",
            "published_at": "Date",
            "url": "Article",
        }
    )
    preferred_columns = ["Ticker", "Event", "Category", "Direction", "Severity", "Why it matters", "Date", "Article"]
    available_columns = [column for column in preferred_columns if column in frame.columns]
    return frame[available_columns]


def render_monitor_page() -> None:
    """Render the News & Macro Monitor workspace."""
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access the monitor workspace.")
        return

    header_left, header_right = st.columns([0.82, 0.18], gap="large")
    with header_left:
        from ui.components.section_header import render_page_header

        render_page_header(
            "News & Macro Monitor",
            "Track geopolitical, India policy, and business headlines, then map the most relevant developments to current holdings.",
        )
    with header_right:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("Refresh News", use_container_width=True, key="monitor_refresh_news"):
            clear_google_news_cache()
            st.rerun()

    with st.spinner("Loading monitor news..."):
        news_bundle = _collect_news_bundle(limit=10)

    geopolitical_news = list(news_bundle.get("geopolitical", []))
    india_policy_news = list(news_bundle.get("india_policy", []))
    business_news = list(news_bundle.get("business", []))
    all_news_items = geopolitical_news + india_policy_news + business_news

    holdings = calculate_holdings()
    holding_sensitivity_map = load_holding_sensitivity_map()
    impact_rows = map_monitor_news_to_portfolio(
        user_id=user_id,
        holdings=holdings,
        news_items=all_news_items,
        holding_sensitivity_map=holding_sensitivity_map,
    )
    impact_summary = build_portfolio_impact_summary(impact_rows)
    summary_data = summarize_monitor_page(geopolitical_news, india_policy_news, business_news)
    high_impact_alerts = [item for item in all_news_items if str(item.get("severity")) == "High"][:8]

    source_errors = list(news_bundle.get("errors", []))
    if source_errors:
        st.info("Some Google News feeds were partially unavailable. Available headlines are still shown.")

    tabs = st.tabs(["Overview", "Geopolitics", "India Policy", "Business", "Portfolio Impact"])

    with tabs[0]:
        render_monitor_overview(summary_data, impact_summary, high_impact_alerts, impact_rows)

    with tabs[1]:
        render_news_monitor_section(
            "Geopolitical Headlines",
            "War, sanctions, border tension, energy shocks, and global conflict developments.",
            geopolitical_news,
            "No recent geopolitical headlines found.",
        )

    with tabs[2]:
        render_news_monitor_section(
            "India Policy Headlines",
            "RBI, budget, ministry, tax, and regulation developments relevant to Indian markets.",
            india_policy_news,
            "No recent India policy headlines found.",
        )

    with tabs[3]:
        render_news_monitor_section(
            "Business & Market Headlines",
            "Business, earnings, sector, and market sentiment developments relevant to current research workflows.",
            business_news,
            "No recent business or market headlines found.",
        )

    with tabs[4]:
        render_section_header(
            "Portfolio Impact",
            "Holding-level impact mapping from the latest monitor headlines.",
        )
        if holdings.empty:
            render_empty_state("No holdings to map", "Add holdings to activate portfolio impact monitoring.")
        elif not impact_rows:
            render_empty_state(
                "No mapped portfolio impacts",
                "Current headlines did not map to holdings through direct mentions, sector relevance, or sensitivity tags.",
            )
        else:
            st.dataframe(
                _portfolio_impact_frame(impact_rows),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Article": st.column_config.LinkColumn("Article", display_text="Open"),
                },
            )
