"""Streamlit entry point for the Fundamental Analyzer platform."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from config.settings import APP_TITLE, MARKET_CAP_CATEGORIES, OUTPUTS_DIR
from core.extractor import FundamentalExtractor
from core.validators import validate_pdf_file
from services.bulk_analysis_service import analyze_bulk_companies
from models.company_data import CompanyData
from services.auth_service import get_current_user, initialize_auth_state, is_admin_user, is_authenticated, logout_user
from services.auth_guard import enforce_session_timeout, touch_session_activity
from services.auth_service import get_current_user_id
from services.cash_service import get_cash_balance
from services.holdings_service import build_portfolio_summary, calculate_holdings
from services.portfolio_impact_summary_service import build_portfolio_impact_summary
from services.portfolio_news_service import build_portfolio_news_monitor
from services.db import init_db
from services.pdf_service import extract_pdf_text, save_uploaded_file
from services.portfolio_snapshot_service import get_snapshots, save_snapshot_if_missing_today
from services.portfolio_service import analyze_portfolio, load_portfolio_csv, web_payload_to_company_data
from services.transaction_service import get_transactions
from services.watchlist_service import get_watchlist
from services.web_data_service import fetch_company_data
from services.rule_service import RuleService
from ui.bulk_analysis_section import render_bulk_analysis_section
from ui.cash_ledger_section import render_cash_ledger_section
from ui.admin_user_approvals_page import render_admin_user_approvals_page
from ui.account_page import render_account_page
from ui.company_analysis_view import render_company_analysis_view
from ui.components.section_header import render_page_header
from ui.components.status_badge import render_status_badge
from ui.dashboard_page import render_dashboard_page
from ui.geopolitical_risk_section import render_geopolitical_risk_section
from ui.import_export_section import render_import_export_section
from ui.login_page import render_login_page
from ui.monitor_page import render_monitor_page
from ui.narration_section import render_narration
from ui.portfolio_page import render_portfolio_page
from ui.portfolio_allocation_section import render_portfolio_allocation_section
from ui.portfolio_dashboard import render_portfolio_dashboard
from ui.portfolio_holdings_table import render_portfolio_holdings_table
from ui.portfolio_history_section import render_portfolio_history_section
from ui.portfolio_news_section import render_portfolio_news_section
from ui.market_discovery_page import render_market_discovery_page
from ui.portfolio_section import render_portfolio_section
from ui.register_page import render_register_page
from ui.research_page import render_research_page
from ui.risk_monitor_page import render_risk_monitor_page
from ui.rules_editor import render_rules_editor
from ui.settings_page import render_settings_page
from ui.tools_page import render_tools_page
from ui.transaction_form import render_transaction_form
from ui.watchlist_dashboard import render_watchlist_dashboard
from ui.watchlist_section import render_watchlist_section
from ui.theme import apply_theme_css, render_theme_toggle


NAVIGATION_SECTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    ("Dashboard", [("dashboard", "Dashboard")]),
    (
        "Portfolio",
        [
            ("overview", "Overview"),
            ("holdings", "Holdings"),
            ("transactions", "Transactions"),
            ("import_export", "Import / Export"),
            ("cash", "Cash"),
            ("allocation", "Allocation"),
            ("history", "History"),
        ],
    ),
    (
        "Research",
        [
            ("company_analysis", "Company Analysis"),
            ("market_discovery", "Market Discovery"),
            ("watchlist", "Watchlist"),
            ("watchlist_dashboard", "Watchlist Dashboard"),
        ],
    ),
    (
        "Monitoring",
        [
            ("risk_monitor", "Risk Monitor"),
            ("news_impact", "News Impact"),
            ("geo_political_alerts", "Geo-Political Alerts"),
        ],
    ),
    (
        "Tools",
        [
            ("rule_engine", "Rule Engine"),
            ("scorecards", "Scorecards"),
            ("portfolio_scanner", "Portfolio Scanner"),
        ],
    ),
    ("Account", [("settings", "Settings")]),
]

PORTFOLIO_ROUTE_MAP: dict[str, str] = {
    "dashboard": "Dashboard",
    "overview": "Dashboard",
    "holdings": "Holdings",
    "transactions": "Transactions",
    "import_export": "Import / Export",
    "cash": "Cash",
    "allocation": "Allocation",
    "history": "History",
    "watchlist": "Watchlist",
    "watchlist_dashboard": "Watchlist Dashboard",
    "market_discovery": "Market Discovery",
    "risk_monitor": "Risk Monitor",
}

MAIN_NAVIGATION = ["Dashboard", "Portfolio", "Research", "Monitor", "Tools", "Account"]


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


def _render_sidebar_navigation(current_route: str, is_admin: bool) -> str:
    """Render grouped sidebar navigation and return the selected route."""
    for section_title, items in NAVIGATION_SECTIONS:
        st.markdown(f'<div class="ui-sidebar-group-label">{section_title}</div>', unsafe_allow_html=True)
        for route_key, label in items:
            button_label = label if section_title == "Dashboard" else f"\u2022 {label}"
            if st.button(
                button_label,
                key=f"nav_{route_key}",
                use_container_width=True,
                type="primary" if current_route == route_key else "secondary",
            ):
                st.session_state["app_route"] = route_key
                current_route = route_key
    if is_admin:
        st.markdown('<div class="ui-sidebar-group-label">Admin</div>', unsafe_allow_html=True)
        if st.button(
            "\u2022 User Approvals",
            key="nav_admin_approvals",
            use_container_width=True,
            type="primary" if current_route == "admin_approvals" else "secondary",
        ):
            st.session_state["app_route"] = "admin_approvals"
            current_route = "admin_approvals"
    return current_route


def _render_portfolio_manager(show_sidebar_selector: bool = True) -> None:
    """Render the persistent portfolio management workspace."""
    save_snapshot_if_missing_today()
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access the portfolio manager.")
        return

    portfolio_section = st.session_state.get("portfolio_section", "Dashboard")
    if show_sidebar_selector:
        with st.sidebar:
            st.markdown("### Portfolio")
            portfolio_section = st.radio(
                "Portfolio section",
                options=[
                    "Dashboard",
                    "Holdings",
                    "Transactions",
                    "Import / Export",
                    "Cash",
                    "Watchlist",
                    "Watchlist Dashboard",
                    "Market Discovery",
                    "Risk Monitor",
                    "Allocation",
                    "History",
                ],
                index=0,
                key="portfolio_section",
            )

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

    try:
        if portfolio_section == "Dashboard":
            render_portfolio_dashboard(
                user_id=user_id,
                summary=summary,
                holdings=holdings,
                snapshot_df=snapshots,
                transaction_history=transactions,
                watchlist=watchlist,
            )
            return

        if portfolio_section == "Transactions":
            render_transaction_form()
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

        if portfolio_section == "Watchlist Dashboard":
            render_watchlist_dashboard(user_id)
            return

        if portfolio_section == "Market Discovery":
            render_market_discovery_page(user_id)
            return

        if portfolio_section == "Risk Monitor":
            render_risk_monitor_page(
                user_id=user_id,
                holdings=holdings,
                transactions=transactions,
                cash_balance=cash_balance,
            )
            return

        if portfolio_section == "Allocation":
            render_portfolio_allocation_section(summary, holdings, cash_balance)
            return

        if portfolio_section == "History":
            render_portfolio_history_section()
            return

        render_import_export_section()
    except ValueError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Unable to load the selected portfolio page right now: {exc}")


def _render_news_impact_page(user_id: int) -> None:
    """Render a standalone portfolio news-impact page."""
    holdings = calculate_holdings()
    watchlist = get_watchlist()
    render_page_header(
        "News Impact",
        "Company, sector, and macro events mapped to the current portfolio using the existing news-monitoring layer.",
    )
    if holdings.empty:
        st.info("Add holdings to activate the portfolio news impact view.")
        return
    news_output = build_portfolio_news_monitor(user_id=user_id, holdings=holdings, watchlist=watchlist)
    impact_summary = build_portfolio_impact_summary(
        impact_rows=list(news_output.get("impact_rows", [])),
        macro_events=list(news_output.get("macro_events", [])),
    )
    render_portfolio_news_section(news_output, impact_summary)


def _render_geopolitical_alerts_page(user_id: int) -> None:
    """Render a standalone macro and geopolitical alerts page."""
    holdings = calculate_holdings()
    watchlist = get_watchlist()
    render_page_header(
        "Geo-Political Alerts",
        "Macro, policy, and geopolitical exposure mapped to holdings using the portfolio news and sensitivity engine.",
    )
    if holdings.empty:
        st.info("Add holdings to activate geopolitical and macro exposure alerts.")
        return
    news_output = build_portfolio_news_monitor(user_id=user_id, holdings=holdings, watchlist=watchlist)
    impact_summary = build_portfolio_impact_summary(
        impact_rows=list(news_output.get("impact_rows", [])),
        macro_events=list(news_output.get("macro_events", [])),
    )
    render_geopolitical_risk_section(news_output, impact_summary)


def _render_rule_engine_page(user_id: int) -> None:
    """Render a standalone rules-management page."""
    del user_id
    render_page_header(
        "Rule Engine",
        "Manage the bucket-based rule framework used by the existing company analysis and scorecard engine.",
    )
    rule_service = RuleService()
    selected_bucket = st.selectbox(
        "Market-cap bucket",
        options=MARKET_CAP_CATEGORIES,
        format_func=lambda value: value.replace("_", " ").title(),
        key="rule_engine_bucket",
    )
    _, rule_source = rule_service.get_rules_with_source(selected_bucket)
    render_rules_editor(rule_service, selected_bucket, rule_source=rule_source)


def _render_scorecards_page() -> None:
    """Render a scorecard-oriented view over the current holdings."""
    holdings = calculate_holdings()
    render_page_header(
        "Scorecards",
        "Current holdings ranked by score, suggestion, and risk using the existing analysis output attached to each position.",
    )
    if holdings.empty:
        st.info("Add holdings to view portfolio scorecards.")
        return
    preferred_columns = [
        column
        for column in ["Ticker", "Company", "Score", "Suggestion", "Risk", "Red Flags", "Category"]
        if column in holdings.columns
    ]
    score_frame = holdings[preferred_columns].copy()
    if "Score" in score_frame.columns:
        score_frame = score_frame.sort_values(by="Score", ascending=False, na_position="last")
        average_score = float(score_frame["Score"].dropna().mean()) if not score_frame["Score"].dropna().empty else 0.0
        high_risk_count = int(score_frame["Risk"].astype(str).isin(["High"]).sum()) if "Risk" in score_frame.columns else 0
        st.metric("Average Score", f"{average_score:.1f}")
        st.metric("High Risk Holdings", high_risk_count)
    st.dataframe(score_frame, use_container_width=True, hide_index=True)


def _render_portfolio_scanner_page() -> None:
    """Render the existing one-off portfolio CSV scanner as a standalone tool page."""
    render_page_header(
        "Portfolio Scanner",
        "Upload a portfolio CSV for a one-time rule-based scan across score, verdict, suggestion, and risk.",
    )
    scanner_file = st.file_uploader("Upload Portfolio CSV", type=["csv"], key="tool_portfolio_scanner")
    if scanner_file is None:
        st.info("Upload a CSV file with stock and quantity columns to start the scan.")
        return
    try:
        portfolio_df = load_portfolio_csv(scanner_file)
        portfolio_results = analyze_portfolio(portfolio_df)
    except ValueError as exc:
        st.error(str(exc))
        return
    render_portfolio_section(portfolio_results)


def _load_portfolio_context() -> tuple[int, dict[str, float], object, object, object, object]:
    """Load the current user's portfolio data once for page-level tabs."""
    save_snapshot_if_missing_today()
    user_id = get_current_user_id()
    if user_id is None:
        raise ValueError("You must be logged in to access the portfolio workspace.")
    holdings = calculate_holdings()
    cash_balance = get_cash_balance()
    summary = build_portfolio_summary(holdings, cash_balance)
    snapshots = get_snapshots()
    transactions = get_transactions()
    watchlist = get_watchlist()
    return user_id, summary, holdings, snapshots, transactions, watchlist


def _render_dashboard_page() -> None:
    """Render the main dashboard page."""
    user_id, summary, holdings, snapshots, transactions, watchlist = _load_portfolio_context()
    import_feedback = st.session_state.pop("portfolio_import_completed", None)
    if import_feedback:
        st.success(
            f"Imported {int(import_feedback.get('rows_imported', 0))} holdings rows from {import_feedback.get('file_name', 'the file')}. Holdings and portfolio analytics were refreshed."
        )
    render_portfolio_dashboard(
        user_id=user_id,
        summary=summary,
        holdings=holdings,
        snapshot_df=snapshots,
        transaction_history=transactions,
        watchlist=watchlist,
    )


def _render_portfolio_page() -> None:
    """Render the portfolio workspace with top tabs."""
    user_id, summary, holdings, snapshots, transactions, watchlist = _load_portfolio_context()
    render_page_header(
        "Portfolio",
        "Operational portfolio workspace for positions, transactions, imports, cash, allocation, and historical tracking.",
    )
    tabs = st.tabs(["Overview", "Holdings", "Transactions", "Import", "Cash", "Allocation", "History"])

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
        render_portfolio_allocation_section(summary, holdings, get_cash_balance())
    with tabs[6]:
        render_portfolio_history_section()


def _render_company_analysis_tab() -> None:
    """Render the company analysis workflow inside the Research page."""
    render_page_header(
        "Company Analysis",
        "Upload a company report or search by ticker to run the existing rule-based research workflow.",
    )
    controls = st.columns([1.1, 1.1, 0.8])
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

    company_data: CompanyData | None = None
    source_label: str | None = None
    if fetch_company_clicked:
        try:
            company_data = _extract_company_data_from_web(ticker)
            source_label = f"Web Search: {ticker.upper().strip()}"
        except ValueError as exc:
            st.error(str(exc))
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


def _render_research_page() -> None:
    """Render the research workspace with top tabs."""
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access the research workspace.")
        return
    tabs = st.tabs(["Company Analysis", "Market Discovery", "Watchlist", "Watchlist Dashboard"])
    with tabs[0]:
        _render_company_analysis_tab()
    with tabs[1]:
        render_market_discovery_page(user_id)
    with tabs[2]:
        render_watchlist_section()
    with tabs[3]:
        render_watchlist_dashboard(user_id)


def _render_monitor_page() -> None:
    """Render the monitoring workspace with top tabs."""
    user_id, _, holdings, _, transactions, _ = _load_portfolio_context()
    tabs = st.tabs(["Risk Monitor", "News Impact", "Geo-Political Risk"])
    with tabs[0]:
        render_risk_monitor_page(
            user_id=user_id,
            holdings=holdings,
            transactions=transactions,
            cash_balance=get_cash_balance(),
        )
    with tabs[1]:
        _render_news_impact_page(user_id)
    with tabs[2]:
        _render_geopolitical_alerts_page(user_id)


def _render_tools_page() -> None:
    """Render the tools workspace with top tabs."""
    user_id = get_current_user_id()
    if user_id is None:
        st.error("You must be logged in to access the tools workspace.")
        return
    tabs = st.tabs(["Rule Engine", "Scorecards", "Portfolio Scanner"])
    with tabs[0]:
        _render_rule_engine_page(user_id)
    with tabs[1]:
        _render_scorecards_page()
    with tabs[2]:
        _render_portfolio_scanner_page()


def _render_account_page(current_user: dict[str, object]) -> None:
    """Render the account workspace with top tabs."""
    tabs = st.tabs(["Settings", "User Management", "Logout"])
    with tabs[0]:
        render_settings_page(current_user)
    with tabs[1]:
        if is_admin_user():
            render_admin_user_approvals_page()
        else:
            st.info("User management is available only for approved admin accounts.")
    with tabs[2]:
        render_page_header(
            "Logout",
            "End the current authenticated session for this browser workspace.",
        )
        if st.button("Logout", key="account_logout_button", use_container_width=True):
            logout_user()
            st.rerun()


def _render_auth_screen() -> None:
    """Render login and registration tabs for unauthenticated users."""
    apply_theme_css()
    render_page_header(
        APP_TITLE,
        "Professional multi-user investing workspace. Public access is limited to login and access requests.",
    )
    login_tab, register_tab = st.tabs(["Login", "Request Access"])
    with login_tab:
        render_login_page()
    with register_tab:
        render_register_page()


def main() -> None:
    """Run the Streamlit UI workflow."""
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    apply_theme_css()
    try:
        init_db()
    except ValueError as exc:
        st.error(str(exc))
        return
    initialize_auth_state()

    if enforce_session_timeout():
        st.warning("Your session expired due to inactivity. Please log in again.")
        _render_auth_screen()
        return

    if not is_authenticated():
        _render_auth_screen()
        return

    current_user = get_current_user()
    if current_user is None:
        logout_user()
        st.warning("Your session is no longer valid. Please log in again.")
        _render_auth_screen()
        return

    touch_session_activity()

    with st.sidebar:
        st.markdown("## Fundamental Analyzer")
        st.markdown(
            '<div class="ui-sidebar-profile-email">Professional equity research and portfolio intelligence</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="ui-sidebar-profile-name">{current_user["name"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ui-sidebar-profile-email">{current_user["email"]}</div>', unsafe_allow_html=True)
        render_status_badge(str(current_user.get("approval_status", "approved")).title(), tone="info")
        st.markdown("---")
        main_section = st.radio(
            "Navigation",
            options=MAIN_NAVIGATION,
            index=0,
            key="main_navigation_section",
        )
        st.markdown("---")
        render_theme_toggle(location="sidebar", key="sidebar_theme_mode")

    try:
        if main_section == "Dashboard":
            render_dashboard_page()
            return
        if main_section == "Portfolio":
            render_portfolio_page()
            return
        if main_section == "Research":
            render_research_page()
            return
        if main_section == "Monitor":
            render_monitor_page()
            return
        if main_section == "Tools":
            render_tools_page()
            return
        render_account_page(current_user, is_admin=is_admin_user())
    except ValueError as exc:
        st.error(str(exc))


if __name__ == "__main__":
    main()
