"""Top-level research page."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from config.settings import OUTPUTS_DIR
from core.extractor import FundamentalExtractor
from core.validators import validate_pdf_file
from models.company_data import CompanyData
from services.auth_service import get_current_user_id
from services.pdf_service import extract_pdf_text, save_uploaded_file
from services.portfolio_service import analyze_portfolio, load_portfolio_csv, web_payload_to_company_data
from services.web_data_service import fetch_company_data
from ui.bulk_analysis_section import render_bulk_analysis_section
from ui.ai_research_page import render_ai_research_page
from ui.company_analysis_view import render_company_analysis_view
from ui.company_workspace_page import render_company_workspace_page
from ui.components.section_header import render_page_header
from ui.market_discovery_page import render_market_discovery_page
from ui.portfolio_section import render_portfolio_section
from ui.watchlist_dashboard import render_watchlist_dashboard
from ui.watchlist_section import render_watchlist_section


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


def render_research_page() -> None:
    """Render the research workspace with tabs."""
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access the research workspace.")
        return

    render_page_header(
        "Research",
        "Company research, market discovery, and watchlist workflows in one workspace.",
    )
    tabs = st.tabs(["Company Analysis", "Company Workspace", "Market Discovery", "Watchlist", "Watchlist Dashboard", "AI Research"])

    with tabs[0]:
        controls = st.columns([1.1, 1.1, 0.8, 0.9, 0.9])
        with controls[0]:
            uploaded_file = st.file_uploader("Upload company PDF", type=["pdf"], key="research_pdf_upload")
        with controls[1]:
            ticker = st.text_input("Company ticker", placeholder="INFY.NS", key="research_company_ticker")
            fetch_company_clicked = st.button("Fetch Company Data", key="research_fetch_company")
        with controls[2]:
            narration_style = st.selectbox(
                "Narration style",
                options=["simple", "investor", "professional"],
                index=0,
                key="research_narration_style",
            )
        with controls[3]:
            portfolio_file = st.file_uploader("Portfolio CSV", type=["csv"], key="research_portfolio_csv")
        with controls[4]:
            bulk_file = st.file_uploader("Screener CSV", type=["csv"], key="research_screener_csv")

        company_data: CompanyData | None = None
        source_label: str | None = None

        if fetch_company_clicked:
            try:
                company_data = _extract_company_data_from_web(ticker)
                source_label = f"Web Search: {ticker.upper().strip()}"
            except ValueError as exc:
                st.error(str(exc))
                company_data = None
        elif portfolio_file is not None:
            try:
                portfolio_df = load_portfolio_csv(portfolio_file)
                portfolio_results = analyze_portfolio(portfolio_df)
            except ValueError as exc:
                st.error(str(exc))
            else:
                render_portfolio_section(portfolio_results)
            company_data = None
        elif bulk_file is not None:
            from services.bulk_analysis_service import analyze_bulk_companies

            try:
                bulk_results = analyze_bulk_companies(bulk_file)
            except ValueError as exc:
                st.error(str(exc))
            else:
                render_bulk_analysis_section(bulk_results)
            company_data = None
        elif uploaded_file is not None:
            try:
                company_data = _extract_company_data_from_pdf(uploaded_file)
                source_label = f"PDF Upload: {uploaded_file.name}"
            except ValueError as exc:
                st.error(str(exc))
                company_data = None

        if company_data is None or source_label is None:
            st.info("Upload a PDF, search by ticker, or run a portfolio/Screener scan from this tab.")
        else:
            render_company_analysis_view(
                company_data=company_data,
                narration_style=narration_style,
                source_label=source_label,
                output_dir=Path(OUTPUTS_DIR),
            )

    with tabs[1]:
        render_company_workspace_page()
    with tabs[2]:
        render_market_discovery_page(user_id)
    with tabs[3]:
        render_watchlist_section()
    with tabs[4]:
        render_watchlist_dashboard(user_id)
    with tabs[5]:
        render_ai_research_page(user_id)
