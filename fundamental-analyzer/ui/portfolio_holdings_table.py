"""Styled holdings table for the portfolio dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.design_system import badge_style, format_currency, format_percentage, gain_loss_style, render_empty_state
from ui.theme import apply_theme_css, get_theme


def render_portfolio_holdings_table(holdings: pd.DataFrame) -> None:
    """Render the modern portfolio holdings table."""
    apply_theme_css()
    if holdings.empty:
        render_empty_state("No active holdings", "Add positions to view a live holdings table with analytics and risk context.")
        return
    theme = get_theme()

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
        "Strong Candidate": f"background-color: {theme['positive_background']}; color: {theme['positive']}; border: 1px solid {theme['border']}; border-radius: 999px; padding: 0.2rem 0.5rem;",
        "Watchlist Candidate": f"background-color: {theme['info_background']}; color: {theme['accent']}; border: 1px solid {theme['border']}; border-radius: 999px; padding: 0.2rem 0.5rem;",
        "High Quality, Expensive": f"background-color: {theme['warning_background']}; color: {theme['watch']}; border: 1px solid {theme['border']}; border-radius: 999px; padding: 0.2rem 0.5rem;",
        "Caution Required": f"background-color: {theme['negative_background']}; color: {theme['risk']}; border: 1px solid {theme['border']}; border-radius: 999px; padding: 0.2rem 0.5rem;",
    }
    risk_palette = {
        "Low": f"background-color: {theme['positive_background']}; color: {theme['positive']}; border: 1px solid {theme['border']}; border-radius: 999px; padding: 0.2rem 0.5rem;",
        "Moderate": f"background-color: {theme['warning_background']}; color: {theme['watch']}; border: 1px solid {theme['border']}; border-radius: 999px; padding: 0.2rem 0.5rem;",
        "Medium": f"background-color: {theme['warning_background']}; color: {theme['watch']}; border: 1px solid {theme['border']}; border-radius: 999px; padding: 0.2rem 0.5rem;",
        "High": f"background-color: {theme['negative_background']}; color: {theme['risk']}; border: 1px solid {theme['border']}; border-radius: 999px; padding: 0.2rem 0.5rem;",
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
            **{"font-weight": "600", "color": theme["text_primary"]},
        )
        .hide(axis="index")
    )

    st.dataframe(styled, use_container_width=True)
