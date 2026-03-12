"""Styled holdings table for the portfolio dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.design_system import badge_style, format_currency, format_percentage, gain_loss_style, render_empty_state
from ui.ui_theme import apply_finance_theme


def render_portfolio_holdings_table(holdings: pd.DataFrame) -> None:
    """Render the modern portfolio holdings table."""
    apply_finance_theme()
    if holdings.empty:
        render_empty_state("No active holdings", "Add positions to view a live holdings table with analytics and risk context.")
        return

    display_columns = [
        "Ticker",
        "Company",
        "Qty",
        "Avg Buy",
        "LTP",
        "Invested",
        "Current Value",
        "Unrealized P&L",
        "Return %",
        "Score",
        "Suggestion",
        "Risk",
    ]
    frame = holdings[[column for column in display_columns if column in holdings.columns]].copy()

    suggestion_palette = {
        "Strong Candidate": "background-color: #ecfdf3; color: #027a48; border-radius: 999px; padding: 0.2rem 0.5rem;",
        "Watchlist Candidate": "background-color: #eff8ff; color: #175cd3; border-radius: 999px; padding: 0.2rem 0.5rem;",
        "High Quality, Expensive": "background-color: #fff6ed; color: #b54708; border-radius: 999px; padding: 0.2rem 0.5rem;",
        "Caution Required": "background-color: #fef3f2; color: #b42318; border-radius: 999px; padding: 0.2rem 0.5rem;",
    }
    risk_palette = {
        "Low": "background-color: #ecfdf3; color: #027a48; border-radius: 999px; padding: 0.2rem 0.5rem;",
        "Moderate": "background-color: #fff6ed; color: #b54708; border-radius: 999px; padding: 0.2rem 0.5rem;",
        "Medium": "background-color: #fff6ed; color: #b54708; border-radius: 999px; padding: 0.2rem 0.5rem;",
        "High": "background-color: #fef3f2; color: #b42318; border-radius: 999px; padding: 0.2rem 0.5rem;",
    }

    styled = (
        frame.style.format(
            {
                "Avg Buy": format_currency,
                "LTP": format_currency,
                "Invested": format_currency,
                "Current Value": format_currency,
                "Unrealized P&L": format_currency,
                "Return %": format_percentage,
                "Score": lambda value: "NA" if value is None or pd.isna(value) else f"{float(value):.0f}",
            }
        )
        .map(gain_loss_style, subset=["Unrealized P&L", "Return %"])
        .map(lambda value: badge_style(value, suggestion_palette), subset=["Suggestion"])
        .map(lambda value: badge_style(value, risk_palette), subset=["Risk"])
        .set_properties(
            subset=["Ticker", "Company", "Qty", "Score"],
            **{"font-weight": "600", "color": "#101828"},
        )
        .hide(axis="index")
    )

    st.dataframe(styled, use_container_width=True)
