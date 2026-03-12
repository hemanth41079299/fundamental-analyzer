"""Portfolio risk monitor page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from services.news_risk_service import scan_portfolio_news_risk
from services.portfolio_health_service import calculate_portfolio_health_score
from services.portfolio_intelligence_service import build_portfolio_intelligence
from ui.design_system import render_empty_state, render_section_header, render_status_badge
from ui.layout_helpers import create_columns
from ui.ui_theme import apply_finance_theme


def render_risk_monitor_page(
    user_id: int,
    holdings: pd.DataFrame,
    transactions: pd.DataFrame,
    cash_balance: float,
) -> None:
    """Render portfolio risk monitoring output."""
    apply_finance_theme()
    render_section_header(
        "Risk Monitor",
        "Concentration, company-level risk, red flags, and negative-news monitoring for the active portfolio.",
    )

    if holdings.empty:
        render_empty_state("No portfolio risks to monitor yet", "Add holdings to activate the risk monitor.")
        return

    try:
        portfolio_health = calculate_portfolio_health_score(holdings)
        intelligence = build_portfolio_intelligence(
            user_id=user_id,
            holdings=holdings,
            transaction_history=transactions,
            cash_balance=cash_balance,
        )
    except Exception as exc:
        st.error(f"Unable to build portfolio risk analytics: {exc}")
        return

    try:
        news_summary = scan_portfolio_news_risk(holdings, top_n=5)
    except Exception:
        news_summary = {"overall_risk_level": "low", "alerts": []}

    render_status_badge(f"Portfolio Health {portfolio_health['portfolio_score']:.1f}/10", tone="warning" if portfolio_health["portfolio_score"] < 6 else "positive")

    left_col, right_col = create_columns(2)
    with left_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_section_header("Portfolio Risk Alerts", "Concentration and position-size warnings generated from holdings data.")
        risk_warnings = list(intelligence.get("risk_warnings", []))
        if not risk_warnings:
            st.info("No deterministic concentration warnings were triggered.")
        else:
            for warning in risk_warnings:
                st.write(f"- {warning}")
        st.markdown("</div>", unsafe_allow_html=True)
    with right_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_section_header("Negative News Alerts", "Recent RSS-based adverse-news alerts for the largest holdings.")
        alerts = list(news_summary.get("alerts", []))
        if not alerts:
            st.info("No negative news signals were detected.")
        else:
            st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    risk_frame = holdings.copy()
    display_columns = [column for column in ["Ticker", "Company", "Risk", "Red Flags", "Suggestion", "Score"] if column in risk_frame.columns]
    if display_columns:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_section_header("Holding Risk Matrix", "Per-holding risk and red-flag snapshot from the research engine.")
        st.dataframe(risk_frame[display_columns], use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
