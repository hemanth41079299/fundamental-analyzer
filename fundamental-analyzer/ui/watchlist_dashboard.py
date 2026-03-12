"""Watchlist dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from services.watchlist_intelligence_service import build_watchlist_intelligence
from ui.design_system import render_empty_state, render_section_header, render_status_badge
from ui.layout_helpers import create_columns
from ui.news_alerts_dashboard import render_news_alerts_dashboard, render_recent_news_table
from ui.ui_theme import apply_finance_theme


def _valuation_signal(summary: object) -> str:
    """Convert valuation summary text into a compact signal."""
    text = str(summary or "").lower()
    if "undervalued" in text or "fair" in text:
        return "Attractive"
    if "overvalued" in text or "expensive" in text or "rich" in text:
        return "Expensive"
    return "Neutral"


def render_watchlist_dashboard(user_id: int) -> None:
    """Render the watchlist intelligence dashboard."""
    apply_finance_theme()
    try:
        intelligence = build_watchlist_intelligence(user_id)
    except Exception as exc:
        st.error(f"Unable to load watchlist intelligence: {exc}")
        return
    ranked_watchlist = list(intelligence.get("ranked_watchlist", []))
    alerts = list(intelligence.get("alerts", []))
    source_errors = list(intelligence.get("source_errors", []))

    render_section_header(
        "Watchlist Dashboard",
        "Ranked watchlist names, alert tracking, and valuation changes from the latest saved company research.",
    )

    if not ranked_watchlist:
        render_empty_state("No watchlist intelligence yet", "Add companies to the watchlist to rank candidates and generate alerts.")
        return

    ranking_col, alerts_col = create_columns([1.4, 1])
    with ranking_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Watchlist Ranking", tone="info")
        ranking_frame = pd.DataFrame(ranked_watchlist)
        ranking_frame["valuation_signal"] = ranking_frame["valuation_summary"].apply(_valuation_signal)
        ranking_frame = ranking_frame.rename(
            columns={
                "ticker": "Ticker",
                "company_name": "Company",
                "score_on_10": "Score",
                "suggestion": "Suggestion",
                "risk": "Risk",
                "valuation_signal": "Valuation Signal",
            }
        )
        st.dataframe(
            ranking_frame[["Ticker", "Company", "Score", "Suggestion", "Risk", "Valuation Signal"]],
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with alerts_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Watchlist Alerts", tone="warning" if alerts else "positive")
        render_section_header("Alerts", "Score, valuation, debt, and growth changes detected from the latest analysis history.")
        if not alerts:
            st.info("No watchlist alerts were generated.")
        else:
            st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
    render_status_badge("Valuation Signals", tone="neutral")
    valuation_frame = pd.DataFrame(
        [
            {
                "Ticker": item["ticker"],
                "Company": item["company_name"],
                "Valuation Signal": _valuation_signal(item.get("valuation_summary")),
                "Valuation Summary": item.get("valuation_summary"),
            }
            for item in ranked_watchlist
        ]
    )
    st.dataframe(valuation_frame, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    news_col, catalysts_col = create_columns([1.2, 1])
    with news_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        recent_news_rows = []
        for item in ranked_watchlist[:6]:
            for news_item in list(item.get("latest_news", []))[:2]:
                recent_news_rows.append(
                    {
                        "Ticker": item["ticker"],
                        "Title": news_item.get("title"),
                        "Direction": news_item.get("direction"),
                        "Severity": news_item.get("severity"),
                        "Type": news_item.get("event_type"),
                    }
                )
        render_recent_news_table(
            recent_news_rows,
            title="Latest Watchlist News",
            caption="Recent company-specific headlines classified into catalysts, risks, and monitor signals.",
            empty_message="No recent watchlist news items were classified.",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with catalysts_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        catalyst_rows = []
        for item in ranked_watchlist[:8]:
            for catalyst in list(item.get("positive_catalysts", [])):
                catalyst_rows.append({"Ticker": item["ticker"], "Signal": catalyst, "Label": "Positive Tailwind"})
            for risk in list(item.get("negative_news_alerts", [])):
                catalyst_rows.append({"Ticker": item["ticker"], "Signal": risk, "Label": "Negative Headwind"})
            for trigger in list(item.get("policy_macro_triggers", [])):
                catalyst_rows.append({"Ticker": item["ticker"], "Signal": trigger, "Label": "Policy Risk"})
        render_news_alerts_dashboard(
            title="Catalysts and Risks",
            alerts=catalyst_rows,
            caption="Policy triggers, positive catalysts, and negative alerts for current watchlist names.",
            empty_message="No watchlist catalysts or risk triggers were generated.",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if source_errors:
        st.caption("Some macro news sources were partially unavailable during the watchlist scan.")
