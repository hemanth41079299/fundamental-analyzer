"""Insight widgets for the portfolio dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.portfolio_kpi_cards import render_insight_card

RISK_RANK = {"Low": 1, "Moderate": 2, "Medium": 2, "High": 3, "Unknown": 0}


def _empty_if_missing(frame: pd.DataFrame, column: str) -> pd.Series:
    """Return a numeric column with null-safe fallback."""
    return pd.to_numeric(frame.get(column), errors="coerce")


def render_portfolio_insights_cards(holdings: pd.DataFrame, summary: dict[str, float]) -> None:
    """Render core portfolio insight cards."""
    st.subheader("Portfolio Insights")
    if holdings.empty:
        st.info("Insights will appear after you add holdings.")
        return

    frame = holdings.copy()
    frame["Return %"] = _empty_if_missing(frame, "Return %")
    frame["Current Value"] = _empty_if_missing(frame, "Current Value").fillna(0.0)
    frame["Score"] = _empty_if_missing(frame, "Score")
    frame["risk_rank"] = frame["Risk"].map(RISK_RANK).fillna(0)

    best_row = frame.loc[frame["Return %"].fillna(float("-inf")).idxmax()]
    worst_row = frame.loc[frame["Return %"].fillna(float("inf")).idxmin()]
    concentrated_row = frame.loc[frame["Current Value"].idxmax()]
    risk_row = frame.loc[frame["risk_rank"].idxmax()]

    total_net_worth = summary.get("total_net_worth", 0.0) or 1.0
    cash_weight = (summary.get("cash_balance", 0.0) / total_net_worth) * 100
    average_score = frame["Score"].dropna().mean()

    cols = st.columns(3)
    with cols[0]:
        render_insight_card("Best Performer", str(best_row["Ticker"]), f"Return {best_row['Return %']:.2f}%", "positive")
    with cols[1]:
        render_insight_card("Worst Performer", str(worst_row["Ticker"]), f"Return {worst_row['Return %']:.2f}%", "negative")
    with cols[2]:
        render_insight_card("Most Concentrated", str(concentrated_row["Ticker"]), f"Value Rs {float(concentrated_row['Current Value']):,.2f}", "warning")

    cols = st.columns(3)
    with cols[0]:
        render_insight_card("Highest Risk Holding", str(risk_row["Ticker"]), f"Risk {risk_row['Risk']}", "warning" if str(risk_row["Risk"]) != "Low" else "neutral")
    with cols[1]:
        render_insight_card("Average Portfolio Score", "NA" if pd.isna(average_score) else f"{average_score:.1f}/100", "Across current holdings", "neutral")
    with cols[2]:
        render_insight_card("Cash Weight", f"{cash_weight:.2f}%", "Cash as a share of net worth", "neutral")


def render_research_widgets(holdings: pd.DataFrame) -> None:
    """Render research-oriented widgets derived from holding analysis."""
    st.subheader("Research Widgets")
    if holdings.empty:
        st.info("Research widgets will appear after holdings are analyzed.")
        return

    frame = holdings.copy()
    frame["Score"] = _empty_if_missing(frame, "Score")
    frame["Red Flags"] = _empty_if_missing(frame, "Red Flags").fillna(0.0)

    top_score_row = frame.loc[frame["Score"].fillna(float("-inf")).idxmax()]
    watchlist_candidates = frame[frame["Suggestion"].eq("Watchlist Candidate")]
    expensive_candidates = frame[frame["Suggestion"].eq("High Quality, Expensive")]
    red_flag_total = int(frame["Red Flags"].sum())

    cols = st.columns(4)
    with cols[0]:
        render_insight_card("Top Scoring Holding", str(top_score_row["Ticker"]), f"Score {float(top_score_row['Score']):.0f}", "positive")
    with cols[1]:
        watchlist_value = watchlist_candidates.iloc[0]["Ticker"] if not watchlist_candidates.empty else "None"
        render_insight_card("Watchlist Candidate", str(watchlist_value), "From current holdings", "neutral")
    with cols[2]:
        expensive_value = expensive_candidates.iloc[0]["Ticker"] if not expensive_candidates.empty else "None"
        render_insight_card("High Quality, Expensive", str(expensive_value), "Valuation-led caution", "warning")
    with cols[3]:
        tone = "negative" if red_flag_total > 0 else "positive"
        render_insight_card("Red Flag Alerts", str(red_flag_total), "Total across holdings", tone)
