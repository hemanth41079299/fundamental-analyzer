"""Market discovery page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.analysis_engine import build_analysis
from core.classifier import classify_market_cap
from services.portfolio_service import web_payload_to_company_data
from services.rule_service import RuleService
from services.watchlist_service import WatchlistInput, add_watchlist_item
from services.web_data_service import fetch_company_data
from ui.design_system import render_empty_state, render_section_header, render_status_badge
from ui.layout_helpers import create_columns
from ui.ui_theme import apply_finance_theme

DEFAULT_DISCOVERY_TICKERS = [
    "INFY.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "ITC.NS",
    "BEL.NS",
    "LT.NS",
    "RELIANCE.NS",
]


def _parse_ticker_input(raw_text: str) -> list[str]:
    """Parse comma or newline separated tickers."""
    candidates = [item.strip().upper() for item in raw_text.replace("\n", ",").split(",")]
    seen: set[str] = set()
    tickers: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            tickers.append(candidate)
    return tickers


def _run_market_discovery(tickers: list[str], user_id: int) -> list[dict[str, object]]:
    """Analyze a ticker universe and return ranked candidates."""
    rule_service = RuleService()
    discoveries: list[dict[str, object]] = []

    for ticker in tickers:
        try:
            payload = fetch_company_data(ticker)
            company_data = web_payload_to_company_data(payload, source_file=f"web:{ticker}")
            category = classify_market_cap(company_data.market_cap_cr)
            rules = rule_service.get_rules(category, user_id=user_id)
            analysis = build_analysis(company_data, category, rules)
            discoveries.append(
                {
                    "Ticker": ticker,
                    "Company": company_data.company_name or ticker,
                    "Category": category.replace("_", " ").title(),
                    "Score": analysis.scorecard.total_score,
                    "Score %": analysis.score.percentage,
                    "Suggestion": analysis.suggestion.label,
                    "Risk": analysis.risk_scan.overall_risk_level,
                    "Verdict": analysis.final_verdict,
                    "Rule Matched": analysis.score.percentage >= 70,
                }
            )
        except Exception as exc:
            discoveries.append(
                {
                    "Ticker": ticker,
                    "Company": ticker,
                    "Category": "Unknown",
                    "Score": None,
                    "Score %": None,
                    "Suggestion": "Unavailable",
                    "Risk": "Unknown",
                    "Verdict": str(exc),
                    "Rule Matched": False,
                }
            )

    return sorted(discoveries, key=lambda item: (item["Score"] is None, -(item["Score"] or 0)))


def render_market_discovery_page(user_id: int) -> None:
    """Render the market discovery workflow."""
    apply_finance_theme()
    if not user_id:
        st.error("A valid user context is required for market discovery.")
        return
    render_section_header(
        "Market Discovery",
        "Analyze a ticker universe, surface rule-matched companies, and move promising names into the watchlist.",
    )

    st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
    render_status_badge("Opportunity Scanner", tone="info")
    ticker_text = st.text_area(
        "Ticker Universe",
        value=", ".join(DEFAULT_DISCOVERY_TICKERS),
        placeholder="INFY.NS, TCS.NS, BEL.NS",
        key="market_discovery_ticker_text",
    )
    if st.button("Scan Opportunities", use_container_width=True):
        try:
            st.session_state[f"market_discovery_results_{user_id}"] = _run_market_discovery(_parse_ticker_input(ticker_text), user_id=user_id)
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Unable to complete market discovery right now: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

    results = st.session_state.get(f"market_discovery_results_{user_id}", [])
    if not results:
        render_empty_state("No opportunities scanned yet", "Run the opportunity scanner to analyze a set of tickers.")
        return

    frame = pd.DataFrame(results)
    matched_frame = frame.loc[frame["Rule Matched"] == True].copy()

    top_col, add_col = create_columns([1.5, 1])
    with top_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Rule Matched Companies", tone="positive" if not matched_frame.empty else "neutral")
        render_section_header("New Opportunities", "Companies with stronger rule-fit and higher current company scores.")
        if matched_frame.empty:
            st.info("No scanned companies met the current rule-match threshold.")
        else:
            st.dataframe(
                matched_frame[["Ticker", "Company", "Category", "Score", "Score %", "Suggestion", "Risk"]],
                use_container_width=True,
                hide_index=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    with add_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Watchlist Action", tone="info")
        render_section_header("Add To Watchlist", "Select one discovered company and move it into the research queue.")
        selectable = matched_frame if not matched_frame.empty else frame
        selected_ticker = st.selectbox(
            "Select company",
            options=selectable["Ticker"].tolist(),
            key="market_discovery_watchlist_pick",
        )
        selected_company = selectable.loc[selectable["Ticker"] == selected_ticker, "Company"].iloc[0]
        if st.button("Add Selected Company To Watchlist", use_container_width=True):
            try:
                add_watchlist_item(WatchlistInput(ticker=selected_ticker, company_name=str(selected_company)))
                st.success("Company added to the watchlist.")
            except ValueError as exc:
                st.error(str(exc))
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
    render_status_badge("All Scanned Companies", tone="neutral")
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
