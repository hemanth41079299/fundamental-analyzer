"""Top-level dashboard page."""

from __future__ import annotations

import streamlit as st

from services.auth_service import get_current_user_id
from services.cash_service import get_cash_balance
from services.holdings_service import build_portfolio_summary, calculate_holdings
from services.portfolio_snapshot_service import get_snapshots, save_snapshot_if_missing_today
from services.transaction_service import get_transactions
from services.watchlist_service import get_watchlist
from ui.components.section_header import render_page_header
from ui.design_system import render_kpi_row, render_section_header, render_status_badge
from ui.portfolio_dashboard import render_portfolio_dashboard


def render_dashboard_page() -> None:
    """Render the top-level dashboard overview."""
    save_snapshot_if_missing_today()
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access the dashboard.")
        return

    holdings = calculate_holdings()
    cash_balance = get_cash_balance()
    summary = build_portfolio_summary(holdings, cash_balance)
    snapshots = get_snapshots()
    transactions = get_transactions()
    watchlist = get_watchlist()

    render_page_header(
        "Dashboard",
        "High-level overview of portfolio value, health, active alerts, and recent research signals.",
    )

    render_kpi_row(
        [
            {"title": "Portfolio Value", "value": f"Rs {float(summary.get('portfolio_value', 0.0)):,.2f}", "delta": None},
            {"title": "Net Worth", "value": f"Rs {float(summary.get('total_net_worth', 0.0)):,.2f}", "delta": None},
            {"title": "Watchlist", "value": str(len(watchlist)), "delta": "Tracked companies"},
            {"title": "Transactions", "value": str(len(transactions)), "delta": "Ledger entries"},
        ]
    )

    insight_col, action_col = st.columns([1.2, 0.8])
    with insight_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Portfolio Health", tone="info")
        render_section_header("Summary", "Current portfolio overview driven by the existing analytics engine.")
        st.write(
            "Use the portfolio workspace for holdings, ledger updates, cash tracking, imports, and historical review."
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with action_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Quick Actions", tone="neutral")
        render_section_header("Jump To", "Primary workflows available from the top-level pages.")
        st.write("- Portfolio: positions, transactions, imports, and cash")
        st.write("- Research: company analysis, discovery, and watchlist")
        st.write("- Monitor: risk, news impact, and geopolitical exposure")
        st.write("- Tools: rules, scorecards, and one-off scanners")
        st.markdown("</div>", unsafe_allow_html=True)

    render_portfolio_dashboard(
        user_id=user_id,
        summary=summary,
        holdings=holdings,
        snapshot_df=snapshots,
        transaction_history=transactions,
        watchlist=watchlist,
    )
