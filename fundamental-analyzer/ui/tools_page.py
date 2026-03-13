"""Top-level tools page."""

from __future__ import annotations

import streamlit as st

from config.settings import MARKET_CAP_CATEGORIES
from services.auth_service import get_current_user_id
from services.holdings_service import calculate_holdings
from services.portfolio_service import analyze_portfolio, load_portfolio_csv
from services.rule_service import RuleService
from ui.components.section_header import render_page_header
from ui.portfolio_section import render_portfolio_section
from ui.rules_editor import render_rules_editor


def render_tools_page() -> None:
    """Render the tools workspace with tabs."""
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access the tools workspace.")
        return

    render_page_header(
        "Tools",
        "Rule management, score review, and one-off portfolio scanning tools.",
    )
    tabs = st.tabs(["Rule Engine", "Scorecards", "Portfolio Scanner"])

    with tabs[0]:
        rule_service = RuleService()
        selected_bucket = st.selectbox(
            "Market-cap bucket",
            options=MARKET_CAP_CATEGORIES,
            format_func=lambda value: value.replace("_", " ").title(),
            key="tools_rule_engine_bucket",
        )
        _, rule_source = rule_service.get_rules_with_source(selected_bucket, user_id=user_id)
        render_rules_editor(rule_service, selected_bucket, rule_source=rule_source)

    with tabs[1]:
        holdings = calculate_holdings()
        if holdings.empty:
            st.info("Add holdings to view scorecards.")
        else:
            preferred_columns = [
                column
                for column in ["Ticker", "Company", "Score", "Suggestion", "Risk", "Red Flags", "Category"]
                if column in holdings.columns
            ]
            frame = holdings[preferred_columns].copy()
            if "Score" in frame.columns:
                frame = frame.sort_values(by="Score", ascending=False, na_position="last")
            st.dataframe(frame, use_container_width=True, hide_index=True)

    with tabs[2]:
        scanner_file = st.file_uploader("Upload Portfolio CSV", type=["csv"], key="tools_portfolio_scanner")
        if scanner_file is None:
            st.info("Upload a CSV file with stock and quantity columns to start the scanner.")
        else:
            try:
                portfolio_df = load_portfolio_csv(scanner_file)
                portfolio_results = analyze_portfolio(portfolio_df)
            except ValueError as exc:
                st.error(str(exc))
            else:
                render_portfolio_section(portfolio_results)
