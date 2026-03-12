"""Allocation analysis UI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.design_system import render_chart_card, render_empty_state, render_section_header
from ui.layout_helpers import create_columns
from ui.ui_theme import apply_finance_theme


def render_allocation_section(holdings: pd.DataFrame, cash_balance: float) -> None:
    """Render stock, sector, and asset allocation charts."""
    apply_finance_theme()
    render_section_header(
        "Allocation Analysis",
        "Review concentration across stocks, sectors, and core asset buckets.",
    )
    if holdings.empty:
        render_empty_state("No allocation data yet", "Add holdings to analyze stock, sector, and asset concentration.")
        return

    try:
        import plotly.express as px
    except ModuleNotFoundError:
        st.info("Install plotly to view allocation charts: pip install plotly")
        return

    stock_frame = holdings[["Ticker", "Current Value"]].dropna()
    sector_frame = holdings[["Sector", "Current Value"]].fillna({"Sector": "Unknown"}).groupby("Sector", as_index=False)["Current Value"].sum()
    asset_frame = pd.DataFrame(
        [
            {"Asset": "Equity", "Value": holdings["Current Value"].fillna(0).sum()},
            {"Asset": "Cash", "Value": cash_balance},
        ]
    )

    col_1, col_2 = create_columns(2)
    if not stock_frame.empty:
        with col_1:
            render_chart_card(
                "Stock Allocation",
                lambda: st.plotly_chart(
                    px.pie(stock_frame, values="Current Value", names="Ticker", hole=0.55),
                    use_container_width=True,
                ),
                "Weight by current market value.",
            )
    if not sector_frame.empty:
        with col_2:
            render_chart_card(
                "Sector Allocation",
                lambda: st.plotly_chart(
                    px.bar(sector_frame, x="Sector", y="Current Value", color="Current Value", color_continuous_scale=["#d1e9ff", "#155eef"]),
                    use_container_width=True,
                ),
                "Sector concentration by portfolio value.",
            )

    render_chart_card(
        "Asset Allocation",
        lambda: st.plotly_chart(
            px.pie(asset_frame, values="Value", names="Asset", hole=0.6),
            use_container_width=True,
        ),
        "Current split between equity and cash.",
    )
