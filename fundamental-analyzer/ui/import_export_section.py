"""Import/export UI for portfolio data."""

from __future__ import annotations

import streamlit as st

from services.cash_service import export_cash_entries_csv
from services.holdings_service import calculate_holdings, export_holdings_csv
from services.portfolio_snapshot_service import export_portfolio_summary_csv
from services.transaction_service import export_transactions_csv, import_transactions_csv
from services.watchlist_service import export_watchlist_csv, import_watchlist_csv
from ui.design_system import render_section_header, render_status_badge
from ui.layout_helpers import create_columns
from ui.ui_theme import apply_finance_theme


def render_import_export_section() -> None:
    """Render import/export tools."""
    apply_finance_theme()
    render_section_header(
        "Import / Export",
        "Move ledger data in and out of the app with controlled CSV workflows.",
    )

    import_column, export_column = create_columns(2)
    holdings = calculate_holdings()
    with import_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("CSV Import", tone="info")
        render_section_header("Import Data", "Validate CSV schema before entries are added to the database.")

        transaction_file = st.file_uploader("Import Transactions CSV", type=["csv"], key="import_transactions")
        if transaction_file is not None and st.button("Import Transactions", use_container_width=True):
            try:
                count = import_transactions_csv(transaction_file)
                st.success(f"Imported {count} transactions.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

        watchlist_file = st.file_uploader("Import Watchlist CSV", type=["csv"], key="import_watchlist")
        if watchlist_file is not None and st.button("Import Watchlist", use_container_width=True):
            try:
                count = import_watchlist_csv(watchlist_file)
                st.success(f"Imported {count} watchlist items.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        st.markdown("</div>", unsafe_allow_html=True)

    with export_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Data Export", tone="neutral")
        render_section_header("Export Data", "Download current user-scoped records for backup or review.")
        st.download_button("Export Transactions CSV", export_transactions_csv(), file_name="transactions.csv", mime="text/csv", use_container_width=True)
        st.download_button("Export Watchlist CSV", export_watchlist_csv(), file_name="watchlist.csv", mime="text/csv", use_container_width=True)
        st.download_button("Export Holdings CSV", export_holdings_csv(holdings), file_name="holdings.csv", mime="text/csv", use_container_width=True)
        st.download_button("Export Portfolio Summary CSV", export_portfolio_summary_csv(), file_name="portfolio_snapshots.csv", mime="text/csv", use_container_width=True)
        st.download_button("Export Cash Ledger CSV", export_cash_entries_csv(), file_name="cash_ledger.csv", mime="text/csv", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
