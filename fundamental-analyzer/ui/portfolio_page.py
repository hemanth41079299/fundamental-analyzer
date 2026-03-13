"""Top-level portfolio page."""

from __future__ import annotations

import streamlit as st

from services.auth_service import get_current_user_id
from services.cash_service import get_cash_balance
from services.holdings_service import build_portfolio_summary, calculate_holdings
from services.portfolio_snapshot_service import get_snapshots, save_snapshot_if_missing_today
from services.transaction_service import get_transactions
from services.watchlist_service import get_watchlist
from ui.cash_ledger_section import render_cash_ledger_section
from ui.components.section_header import render_page_header
from ui.import_export_section import render_import_export_section
from ui.portfolio_allocation_section import render_portfolio_allocation_section
from ui.portfolio_dashboard import render_portfolio_dashboard
from ui.portfolio_history_section import render_portfolio_history_section
from ui.portfolio_holdings_table import render_portfolio_holdings_table
from ui.transaction_form import render_transaction_form


def render_portfolio_page() -> None:
    """Render the portfolio workspace with page tabs."""
    save_snapshot_if_missing_today()
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access the portfolio workspace.")
        return

    holdings = calculate_holdings()
    cash_balance = get_cash_balance()
    summary = build_portfolio_summary(holdings, cash_balance)
    snapshots = get_snapshots()
    transactions = get_transactions()
    watchlist = get_watchlist()

    import_feedback = st.session_state.pop("portfolio_import_completed", None)
    if import_feedback:
        st.success(
            f"Imported {int(import_feedback.get('rows_imported', 0))} holdings rows from {import_feedback.get('file_name', 'the file')}. Holdings and portfolio analytics were refreshed."
        )

    render_page_header(
        "Portfolio",
        "Portfolio operations, position analytics, transaction ledger, imports, cash tracking, allocation, and history.",
    )
    tabs = st.tabs(["Overview", "Holdings", "Transactions", "Import Portfolio", "Cash", "Allocation", "History"])

    with tabs[0]:
        render_portfolio_dashboard(
            user_id=user_id,
            summary=summary,
            holdings=holdings,
            snapshot_df=snapshots,
            transaction_history=transactions,
            watchlist=watchlist,
        )
    with tabs[1]:
        render_portfolio_holdings_table(holdings)
    with tabs[2]:
        render_transaction_form()
        st.subheader("Transaction History")
        if transactions.empty:
            st.info("No transactions recorded yet.")
        else:
            st.dataframe(transactions, use_container_width=True, hide_index=True)
    with tabs[3]:
        render_import_export_section()
    with tabs[4]:
        render_cash_ledger_section()
    with tabs[5]:
        render_portfolio_allocation_section(summary, holdings, cash_balance)
    with tabs[6]:
        render_portfolio_history_section()
