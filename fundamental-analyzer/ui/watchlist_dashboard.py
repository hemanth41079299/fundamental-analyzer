"""Professional watchlist dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from services.watchlist_intelligence_service import build_watchlist_intelligence
from ui.components.section_header import render_page_header, render_section_header
from ui.components.status_badge import render_status_badge
from ui.components.table_card import render_table_card
from ui.layout_helpers import create_columns
from ui.news_alerts_dashboard import render_news_alerts_dashboard, render_recent_news_table
from ui.theme import apply_theme_css


def _valuation_signal(summary: object) -> str:
    """Convert valuation summary text into a compact signal."""
    text = str(summary or "").lower()
    if "undervalued" in text or "fair" in text:
        return "Attractive"
    if "overvalued" in text or "expensive" in text or "rich" in text:
        return "Expensive"
    return "Neutral"


def render_watchlist_dashboard(user_id: int) -> None:
    """Render the watchlist dashboard."""
    apply_theme_css()
    try:
        intelligence = build_watchlist_intelligence(user_id)
    except Exception as exc:
        st.error(f"Unable to load watchlist intelligence: {exc}")
        return

    ranked_watchlist = list(intelligence.get("ranked_watchlist", []))
    alerts = list(intelligence.get("alerts", []))
    source_errors = list(intelligence.get("source_errors", []))

    render_page_header(
        "Watchlist Dashboard",
        "Rank watchlist names by current score, surface latest news, and review catalysts, valuation signals, and risk labels.",
    )

    if not ranked_watchlist:
        st.info("No watchlist intelligence yet. Add companies to the watchlist to populate this dashboard.")
        return

    ranking_frame = pd.DataFrame(ranked_watchlist)
    ranking_frame["Valuation Signal"] = ranking_frame["valuation_summary"].apply(_valuation_signal)
    ranking_frame["Latest News"] = ranking_frame["latest_news"].apply(
        lambda items: ", ".join(str(item.get("title")) for item in list(items)[:1]) if items else "NA"
    )
    ranking_frame = ranking_frame.rename(
        columns={
            "ticker": "Ticker",
            "company_name": "Company",
            "score_on_10": "Score",
            "suggestion": "Suggestion",
            "risk": "Risk",
        }
    )
    render_table_card(
        "Watchlist Ranking",
        ranking_frame[["Ticker", "Company", "Score", "Suggestion", "Risk", "Valuation Signal", "Latest News"]],
        "Current ranking across score, suggestion label, risk level, and latest headline context.",
    )

    top_left, top_right = create_columns([1, 1])
    with top_left:
        alert_frame = pd.DataFrame(alerts) if alerts else pd.DataFrame(columns=["ticker", "message"])
        render_table_card(
            "Watchlist Alerts",
            alert_frame.rename(columns={"ticker": "Ticker", "message": "Alert"}),
            "Detected changes in score, valuation, debt, or growth relative to previous reviews.",
        )
    with top_right:
        valuation_frame = pd.DataFrame(
            [
                {
                    "Ticker": item["ticker"],
                    "Company": item["company_name"],
                    "Valuation Signal": _valuation_signal(item.get("valuation_summary")),
                    "Summary": item.get("valuation_summary") or "NA",
                }
                for item in ranked_watchlist
            ]
        )
        render_table_card(
            "Valuation Signals",
            valuation_frame,
            "Quick valuation read across watchlist names using the existing valuation layer.",
        )

    news_col, catalyst_col = create_columns([1.05, 0.95])
    with news_col:
        recent_news_rows = []
        for item in ranked_watchlist[:6]:
            for news_item in list(item.get("latest_news", []))[:2]:
                recent_news_rows.append(
                    {
                        "Ticker": item["ticker"],
                        "Title": news_item.get("title"),
                        "Type": news_item.get("event_type"),
                        "Direction": news_item.get("direction"),
                        "Severity": news_item.get("severity"),
                    }
                )
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        render_recent_news_table(
            recent_news_rows,
            title="Latest News",
            caption="Most recent company headlines mapped into event types and directional impact.",
            empty_message="No recent watchlist headlines were classified.",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with catalyst_col:
        rows = []
        for item in ranked_watchlist[:8]:
            for catalyst in list(item.get("positive_catalysts", [])):
                rows.append({"Ticker": item["ticker"], "Signal": catalyst, "Type": "Catalyst"})
            for risk in list(item.get("negative_news_alerts", [])):
                rows.append({"Ticker": item["ticker"], "Signal": risk, "Type": "Risk"})
            for trigger in list(item.get("policy_macro_triggers", [])):
                rows.append({"Ticker": item["ticker"], "Signal": trigger, "Type": "Policy / Macro"})
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        render_news_alerts_dashboard(
            title="Catalysts and Triggers",
            alerts=rows,
            caption="Positive catalysts, policy triggers, and risk alerts for the current watchlist.",
            empty_message="No catalysts or policy triggers were generated.",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if source_errors:
        render_status_badge("Some news feeds were partially unavailable", "watch")
