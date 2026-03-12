"""Broker-style portfolio dashboard layout."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from services.holdings_service import export_holdings_csv
from services.portfolio_snapshot_service import save_snapshot
from ui.design_system import render_empty_state, render_section_header, render_status_badge
from ui.layout_helpers import create_columns, render_spacer
from ui.portfolio_allocation_section import render_account_overview, render_allocation_visuals
from ui.portfolio_charts import render_portfolio_performance_chart
from ui.portfolio_holdings_table import render_portfolio_holdings_table
from ui.portfolio_insights_cards import render_portfolio_insights_cards, render_research_widgets
from ui.portfolio_kpi_cards import inject_portfolio_dashboard_css, render_kpi_row


def _format_currency(value: float | int | None) -> str:
    """Format numeric values as dashboard currency text."""
    if value is None:
        return "NA"
    return f"Rs {float(value):,.2f}"


def _build_status_text(summary: dict[str, float]) -> str:
    """Build a high-level portfolio status line."""
    total_return = summary.get("total_return_pct", 0.0)
    if total_return > 15:
        return "Portfolio momentum is constructive with positive mark-to-market performance."
    if total_return > 0:
        return "Portfolio is above cost with moderate positive performance."
    if total_return < 0:
        return "Portfolio is below cost and needs closer review on position sizing and quality."
    return "Portfolio is flat. Add more snapshots to build a stronger performance history."


def _render_header(summary: dict[str, float]) -> None:
    """Render the dashboard header."""
    inject_portfolio_dashboard_css()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.markdown(
        f"""
        <div class="portfolio-header">
            <h2>Portfolio Dashboard</h2>
            <div class="portfolio-subtitle">Updated on: {updated_at}</div>
            <div class="portfolio-status">{_build_status_text(summary)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_status_badge("Analytics Console", tone="info")


def _render_toolbar(holdings: pd.DataFrame) -> None:
    """Render dashboard actions."""
    render_section_header("Actions", "Refresh live values, store a snapshot, or export the current holdings.")
    action_col_1, action_col_2, action_col_3, _ = create_columns([0.14, 0.14, 0.2, 0.52])
    with action_col_1:
        if st.button("Refresh Prices", use_container_width=True):
            st.rerun()
    with action_col_2:
        if st.button("Save Snapshot", use_container_width=True):
            save_snapshot()
            st.success("Portfolio snapshot saved.")
            st.rerun()
    with action_col_3:
        st.download_button(
            "Download Holdings CSV",
            export_holdings_csv(holdings),
            file_name="portfolio_holdings.csv",
            mime="text/csv",
            use_container_width=True,
        )


def _render_empty_state() -> None:
    """Render a dashboard empty state with quick navigation actions."""
    render_empty_state(
        "No holdings yet",
        "Start by adding a transaction, importing historical trades, or building a watchlist.",
    )

    col_1, col_2, col_3 = st.columns(3)
    with col_1:
        if st.button("Add Transaction", use_container_width=True):
            st.session_state["portfolio_section"] = "Transactions"
            st.rerun()
    with col_2:
        if st.button("Import Transactions", use_container_width=True):
            st.session_state["portfolio_section"] = "Import / Export"
            st.rerun()
    with col_3:
        if st.button("Add to Watchlist", use_container_width=True):
            st.session_state["portfolio_section"] = "Watchlist"
            st.rerun()


def _render_kpis(summary: dict[str, float]) -> None:
    """Render the top KPI row."""
    total_return_pct = summary.get("total_return_pct", 0.0)
    cards = [
        {"title": "Total Invested", "value": _format_currency(summary.get("invested_amount")), "delta": None},
        {"title": "Current Value", "value": _format_currency(summary.get("portfolio_value")), "delta": f"{total_return_pct:.2f}% total return"},
        {"title": "Unrealized P&L", "value": _format_currency(summary.get("unrealized_pnl")), "delta": "Live mark-to-market"},
        {"title": "Realized P&L", "value": _format_currency(summary.get("realized_pnl")), "delta": "Booked from sells"},
        {"title": "Cash Balance", "value": _format_currency(summary.get("cash_balance")), "delta": "Manual ledger balance"},
        {"title": "Total Net Worth", "value": _format_currency(summary.get("total_net_worth")), "delta": "Portfolio plus cash"},
    ]
    render_kpi_row(cards)


def _render_selected_holding_widget(holdings: pd.DataFrame) -> None:
    """Render a research panel for one selected holding."""
    if holdings.empty:
        return

    render_section_header("Holding Research", "Open a position-level research panel beside the holdings table.")
    selected_ticker = st.selectbox("Select holding", options=holdings["Ticker"].tolist(), key="selected_holding")
    selected_row = holdings.loc[holdings["Ticker"] == selected_ticker].iloc[0]

    st.markdown('<div class="portfolio-side-card">', unsafe_allow_html=True)
    render_status_badge(str(selected_row.get("Suggestion") or "Unlabeled"), tone="neutral")
    st.markdown(f"#### {selected_row['Ticker']}")
    st.caption(str(selected_row.get("Company", "Unknown Company")))
    left, right = st.columns(2)
    left.metric("Current Value", _format_currency(selected_row.get("Current Value")))
    right.metric("Return %", "NA" if pd.isna(selected_row.get("Return %")) else f"{float(selected_row['Return %']):.2f}%")
    left.metric("Score", "NA" if pd.isna(selected_row.get("Score")) else f"{float(selected_row['Score']):.0f}/100")
    right.metric("Risk Level", str(selected_row.get("Risk", "NA")))

    st.write("")
    badge_col_1, badge_col_2 = st.columns(2)
    with badge_col_1:
        st.caption("Suggestion Label")
        st.markdown(f"**{selected_row.get('Suggestion', 'NA')}**")
    with badge_col_2:
        red_flags = selected_row.get("Red Flags")
        st.caption("Red Flag Count")
        st.markdown("**NA**" if pd.isna(red_flags) else f"**{float(red_flags):.0f}**")

    st.write("")
    st.caption(f"Sector: {selected_row.get('Sector', 'Unknown')}")
    st.caption(f"Category: {selected_row.get('Category', 'Unknown')}")

    st.divider()
    render_section_header("Valuation", None)
    st.write(str(selected_row.get("Valuation Summary") or "Valuation summary is not available."))

    render_section_header("Earnings Quality", None)
    st.write(str(selected_row.get("Earnings Quality Summary") or "Earnings quality summary is not available."))

    render_section_header("Thesis Summary", None)
    st.write(str(selected_row.get("Thesis Summary") or "Thesis summary is not available."))
    st.markdown("</div>", unsafe_allow_html=True)


def render_portfolio_dashboard(summary: dict[str, float], holdings: pd.DataFrame, snapshot_df: pd.DataFrame) -> None:
    """Render the full broker-style dashboard."""
    _render_header(summary)
    render_spacer()
    _render_toolbar(holdings)
    render_spacer()
    render_section_header("Account Overview", "Track capital deployed, current value, and realized versus unrealized outcomes.")
    _render_kpis(summary)

    if holdings.empty:
        render_spacer()
        _render_empty_state()
        render_spacer()
        render_portfolio_performance_chart(snapshot_df)
        return

    render_spacer()
    render_section_header("Performance", "Monitor invested capital, portfolio value, and total net worth over time.")
    render_portfolio_performance_chart(snapshot_df)

    render_spacer()
    render_section_header("Allocation And Overview", "Balance high-level account values with current stock and sector concentration.")
    left_column, right_column = create_columns([1, 1.35])
    with left_column:
        render_account_overview(summary, holdings)
    with right_column:
        render_allocation_visuals(holdings, summary.get("cash_balance", 0.0))

    render_spacer()
    render_section_header("Holdings And Position Research", "Review live positions and inspect one selected holding without leaving the dashboard.")
    table_column, detail_column = create_columns([2.2, 1])
    with table_column:
        render_portfolio_holdings_table(holdings)
    with detail_column:
        _render_selected_holding_widget(holdings)

    render_spacer()
    render_portfolio_insights_cards(holdings, summary)
    render_spacer()
    render_research_widgets(holdings)
