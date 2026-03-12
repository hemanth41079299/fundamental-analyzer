"""Streamlit entry point for the Fundamental Analyzer platform."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from config.settings import APP_TITLE, OUTPUTS_DIR
from core.extractor import FundamentalExtractor
from core.validators import validate_pdf_file
from services.bulk_analysis_service import analyze_bulk_companies
from models.company_data import CompanyData
from services.auth_service import get_current_user, initialize_auth_state, is_authenticated, logout_user
from services.cash_service import get_cash_balance
from services.holdings_service import build_portfolio_summary, calculate_holdings
from services.pdf_service import extract_pdf_text, save_uploaded_file
from services.portfolio_db import init_portfolio_db
from services.portfolio_snapshot_service import get_snapshots, save_snapshot_if_missing_today
from services.portfolio_service import analyze_portfolio, load_portfolio_csv, web_payload_to_company_data
from services.transaction_service import get_transactions
from services.watchlist_service import get_watchlist
from services.web_data_service import fetch_company_data
from ui.bulk_analysis_section import render_bulk_analysis_section
from ui.cash_ledger_section import render_cash_ledger_section
from ui.company_analysis_view import render_company_analysis_view
from ui.import_export_section import render_import_export_section
from ui.login_page import render_login_page
from ui.narration_section import render_narration
from ui.portfolio_allocation_section import render_portfolio_allocation_section
from ui.portfolio_dashboard import render_portfolio_dashboard
from ui.portfolio_holdings_table import render_portfolio_holdings_table
from ui.portfolio_history_section import render_portfolio_history_section
from ui.portfolio_section import render_portfolio_section
from ui.register_page import render_register_page
from ui.settings_page import render_settings_page
from ui.transaction_form import render_transaction_form
from ui.watchlist_section import render_watchlist_section
from ui.upload_section import (
    render_bulk_analysis_upload_section,
    render_company_search_section,
    render_portfolio_upload_section,
    render_upload_section,
)


def _extract_company_data_from_pdf(uploaded_file) -> CompanyData:
    """Extract company data from an uploaded PDF file."""
    is_valid, validation_message = validate_pdf_file(uploaded_file.name)
    if not is_valid:
        raise ValueError(validation_message)

    saved_pdf_path = save_uploaded_file(uploaded_file)
    pdf_text = extract_pdf_text(saved_pdf_path)
    extractor = FundamentalExtractor()
    return extractor.extract(pdf_text, source_file=saved_pdf_path.name)


def _extract_company_data_from_web(ticker: str) -> CompanyData:
    """Fetch and normalize company data from the web."""
    payload = fetch_company_data(ticker)
    return web_payload_to_company_data(payload, source_file=f"web:{ticker.upper().strip()}")


def _render_analysis(company_data: CompanyData, narration_style: str, source_label: str) -> None:
    """Run rules, analysis, and render the main page sections."""
    render_company_analysis_view(
        company_data=company_data,
        narration_style=narration_style,
        source_label=source_label,
        output_dir=Path(OUTPUTS_DIR),
    )


def _render_portfolio_manager() -> None:
    """Render the persistent portfolio management workspace."""
    save_snapshot_if_missing_today()

    with st.sidebar:
        st.markdown("### Portfolio Manager")
        portfolio_section = st.radio(
            "Portfolio section",
            options=[
                "Dashboard",
                "Transactions",
                "Holdings",
                "Cash",
                "Watchlist",
                "Allocation",
                "History",
                "Import / Export",
            ],
            index=0,
            key="portfolio_section",
        )

    holdings = calculate_holdings()
    cash_balance = get_cash_balance()
    summary = build_portfolio_summary(holdings, cash_balance)
    snapshots = get_snapshots()

    if portfolio_section == "Dashboard":
        render_portfolio_dashboard(summary, holdings, snapshots)
        return

    if portfolio_section == "Transactions":
        render_transaction_form()
        transactions = get_transactions()
        st.subheader("Transaction History")
        if transactions.empty:
            st.info("No transactions recorded yet.")
        else:
            st.dataframe(transactions, use_container_width=True, hide_index=True)
        return

    if portfolio_section == "Holdings":
        render_portfolio_holdings_table(holdings)
        return

    if portfolio_section == "Cash":
        render_cash_ledger_section()
        return

    if portfolio_section == "Watchlist":
        watchlist = get_watchlist()
        st.caption(f"Tracked watchlist items: {len(watchlist)}")
        render_watchlist_section()
        return

    if portfolio_section == "Allocation":
        render_portfolio_allocation_section(summary, holdings, cash_balance)
        return

    if portfolio_section == "History":
        render_portfolio_history_section()
        return

    render_import_export_section()


def _render_auth_screen() -> None:
    """Render login and registration tabs for unauthenticated users."""
    st.subheader("Secure Access")
    st.caption("Public pages: Login and Register. All research, portfolio, rules, history, and settings pages require authentication.")
    login_tab, register_tab = st.tabs(["Login", "Register"])
    with login_tab:
        render_login_page()
    with register_tab:
        render_register_page()


def main() -> None:
    """Run the Streamlit UI workflow."""
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_portfolio_db()
    initialize_auth_state()
    st.title(APP_TITLE)
    st.caption("Modular equity research platform for company analysis and persistent portfolio tracking.")

    if not is_authenticated():
        _render_auth_screen()
        return

    current_user = get_current_user()
    if current_user is None:
        logout_user()
        st.warning("Your session is no longer valid. Please log in again.")
        _render_auth_screen()
        return

    with st.sidebar:
        st.markdown("### Account")
        st.caption(str(current_user["name"]))
        st.caption(str(current_user["email"]))
        if st.button("Logout", use_container_width=True):
            logout_user()
            st.rerun()
        workspace = st.radio(
            "Workspace",
            options=["Company Analysis", "Portfolio Manager", "Settings"],
            index=0,
        )

    if workspace == "Settings":
        render_settings_page(current_user)
        return

    if workspace == "Portfolio Manager":
        _render_portfolio_manager()
        return

    with st.sidebar:
        uploaded_file = render_upload_section()
        ticker, fetch_company_clicked = render_company_search_section()
        portfolio_file = render_portfolio_upload_section()
        bulk_file = render_bulk_analysis_upload_section()
        narration_style = st.selectbox(
            "Narration style",
            options=["simple", "investor", "professional"],
            index=0,
        )

    company_data: CompanyData | None = None
    source_label: str | None = None

    if fetch_company_clicked:
        try:
            company_data = _extract_company_data_from_web(ticker)
            source_label = f"Web Search: {ticker.upper().strip()}"
        except ValueError as exc:
            st.error(str(exc))
            return
    elif portfolio_file is not None:
        try:
            portfolio_df = load_portfolio_csv(portfolio_file)
            portfolio_results = analyze_portfolio(portfolio_df)
        except ValueError as exc:
            st.error(str(exc))
            return

        render_portfolio_section(portfolio_results)
        return
    elif bulk_file is not None:
        try:
            bulk_results = analyze_bulk_companies(bulk_file)
        except ValueError as exc:
            st.error(str(exc))
            return

        render_bulk_analysis_section(bulk_results)
        return
    elif uploaded_file is not None:
        try:
            company_data = _extract_company_data_from_pdf(uploaded_file)
            source_label = f"PDF Upload: {uploaded_file.name}"
        except ValueError as exc:
            st.error(str(exc))
            return

    if company_data is None or source_label is None:
        st.info("Upload a PDF report or search by company ticker to start the analysis.")
        return

    _render_analysis(company_data, narration_style, source_label)


if __name__ == "__main__":
    main()
