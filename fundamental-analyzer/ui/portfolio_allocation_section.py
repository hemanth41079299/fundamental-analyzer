"""Portfolio allocation visuals and account overview widgets."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.portfolio_charts import render_top_holdings_bar_chart
from ui.portfolio_kpi_cards import inject_portfolio_dashboard_css


def _format_currency(value: float | int | None) -> str:
    """Format numeric values as currency-like text."""
    if value is None:
        return "NA"
    return f"Rs {float(value):,.2f}"


def render_account_overview(summary: dict[str, float], holdings: pd.DataFrame) -> None:
    """Render account overview items."""
    inject_portfolio_dashboard_css()
    equity_value = float(holdings["Current Value"].fillna(0).sum()) if not holdings.empty else 0.0
    account_items = [
        ("Equity Holdings", _format_currency(equity_value)),
        ("ETFs", _format_currency(0.0)),
        ("Mutual Funds", _format_currency(0.0)),
        ("Cash Balance", _format_currency(summary.get("cash_balance", 0.0))),
        ("Total Account Value", _format_currency(summary.get("total_net_worth", 0.0))),
    ]

    st.markdown('<div class="portfolio-side-card">', unsafe_allow_html=True)
    st.markdown("#### Account Overview")
    for label, value in account_items:
        left, right = st.columns([1.4, 1])
        left.caption(label)
        right.markdown(f"**{value}**")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_donut_chart(frame: pd.DataFrame, names: str, values: str, title: str) -> None:
    """Render a donut chart from a dataframe."""
    try:
        import plotly.express as px
    except ModuleNotFoundError:
        st.info("Install plotly to view allocation charts: pip install plotly")
        return

    if frame.empty:
        st.info(f"No data available for {title.lower()}.")
        return

    fig = px.pie(frame, names=names, values=values, hole=0.62)
    fig.update_traces(textposition="inside", textinfo="percent")
    fig.update_layout(
        title=title,
        height=320,
        margin={"l": 10, "r": 10, "t": 45, "b": 10},
        paper_bgcolor="#ffffff",
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_allocation_visuals(holdings: pd.DataFrame, cash_balance: float) -> None:
    """Render asset and sector allocation visuals."""
    if holdings.empty:
        st.info("No holdings available for allocation analysis.")
        return

    holdings_frame = holdings.copy()
    holdings_frame["Current Value"] = pd.to_numeric(holdings_frame["Current Value"], errors="coerce").fillna(0.0)

    asset_frame = pd.DataFrame(
        [
            {"Asset": "Equity", "Value": holdings_frame["Current Value"].sum()},
            {"Asset": "Cash", "Value": cash_balance},
        ]
    )
    sector_frame = (
        holdings_frame[["Sector", "Current Value"]]
        .fillna({"Sector": "Unknown"})
        .groupby("Sector", as_index=False)["Current Value"]
        .sum()
        .sort_values("Current Value", ascending=False)
    )

    col_1, col_2 = st.columns(2)
    with col_1:
        _render_donut_chart(asset_frame, "Asset", "Value", "Asset Allocation")
    with col_2:
        _render_donut_chart(sector_frame, "Sector", "Current Value", "Sector Allocation")


def render_portfolio_allocation_section(summary: dict[str, float], holdings: pd.DataFrame, cash_balance: float) -> None:
    """Render the standalone allocation page."""
    st.subheader("Allocation")
    left_column, right_column = st.columns([1, 1.25])
    with left_column:
        render_account_overview(summary, holdings)
    with right_column:
        render_allocation_visuals(holdings, cash_balance)
    st.write("")
    render_top_holdings_bar_chart(holdings)
