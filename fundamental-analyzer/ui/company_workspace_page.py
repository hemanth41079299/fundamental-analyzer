"""Investment dossier UI for company-level research workspaces."""

from __future__ import annotations

import html
import pandas as pd
import streamlit as st

from services.company_research_workspace import (
    CompanyWorkspaceRecord,
    build_company_workspace,
    save_company_workspace_record,
)
from ui.design_system import render_empty_state, render_kpi_row, render_page_header, render_section_header, render_status_badge


def _workspace_key() -> str:
    """Return the session-state key for the current company workspace."""
    return "company_workspace_target"


def _escape_text(value: object) -> str:
    """Escape and normalize free-form text before rendering into HTML blocks."""
    cleaned = str(value or "").strip()
    if not cleaned:
        return ""
    return html.escape(cleaned).replace("\n", "<br>")


def _render_workspace_editor(record: CompanyWorkspaceRecord) -> None:
    """Render editable thesis and notes fields."""
    render_section_header("Research Notes", "Edit and persist dossier fields for this company.")
    with st.form("company_workspace_editor_form", clear_on_submit=False):
        ai_summary = st.text_area("AI Company Summary", value=record.ai_summary, height=120)
        investment_thesis = st.text_area("Investment Thesis", value=record.investment_thesis, height=120)
        bear_case = st.text_area("Bear Case", value=record.bear_case, height=120)
        watch_triggers = st.text_area("Watch Triggers", value=record.watch_triggers, height=100)
        research_notes = st.text_area("Research Notes", value=record.research_notes, height=160)
        submitted = st.form_submit_button("Save Dossier Notes", use_container_width=True)

    if submitted:
        save_company_workspace_record(
            CompanyWorkspaceRecord(
                company_key=record.company_key,
                ticker=record.ticker,
                company_name=record.company_name,
                ai_summary=ai_summary.strip(),
                investment_thesis=investment_thesis.strip(),
                bear_case=bear_case.strip(),
                watch_triggers=watch_triggers.strip(),
                research_notes=research_notes.strip(),
                updated_at=record.updated_at,
            )
        )
        st.success("Investment dossier updated.")
        st.session_state[f"{record.company_key}_workspace_saved"] = True


def render_company_workspace_page() -> None:
    """Render the Company Workspace investment dossier page."""
    render_page_header(
        "Company Workspace",
        "Structured investment dossier for one company with editable thesis, notes, rule output, news intelligence, and portfolio exposure context.",
    )

    control_left, control_right = st.columns([1.3, 0.35], gap="large")
    with control_left:
        default_value = str(st.session_state.get(_workspace_key(), ""))
        company_input = st.text_input(
            "Company name or ticker",
            value=default_value,
            placeholder="TATAMOTORS.NS or Tata Motors",
            key="company_workspace_input",
        )
    with control_right:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        load_clicked = st.button("Open Dossier", use_container_width=True, key="company_workspace_open")

    if load_clicked:
        st.session_state[_workspace_key()] = company_input

    current_target = str(st.session_state.get(_workspace_key(), "")).strip()
    if not current_target:
        render_empty_state("No company selected", "Enter a company name or ticker to open its investment dossier.")
        return

    try:
        workspace = build_company_workspace(current_target)
    except ValueError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"Unable to load the company workspace: {exc}")
        return

    analysis_result = workspace["analysis_result"]
    company_data = workspace["company_data"]
    record = workspace["workspace_record"]
    news_intelligence = workspace["news_intelligence"]
    portfolio_exposure = workspace["portfolio_exposure"]

    render_page_header(
        f"Investment Dossier: {workspace['company_name']}",
        f"Ticker: {workspace['ticker']} | Category: {workspace['market_cap_category'].replace('_', ' ').title()}",
    )

    render_kpi_row(
        [
            {"title": "Rule Engine Score", "value": f"{analysis_result.scorecard.total_score}/{analysis_result.scorecard.max_score}"},
            {"title": "Suggestion", "value": analysis_result.suggestion.label},
            {"title": "Risk Level", "value": analysis_result.risk_scan.overall_risk_level},
            {"title": "Red Flags", "value": str(analysis_result.red_flags.red_flag_count)},
        ]
    )

    top_left, top_right = st.columns([1.15, 0.85], gap="large")
    with top_left:
        st.markdown(
            f"""
            <div class="ui-card">
                <div class="ui-card-title">AI Company Summary</div>
                <div class="ui-section-caption">{_escape_text(record.ai_summary)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="ui-card" style="margin-top: 16px;">
                <div class="ui-card-title">Investment Thesis</div>
                <div class="ui-section-caption">{_escape_text(record.investment_thesis)}</div>
                <div class="ui-card-title" style="margin-top: 16px;">Bear Case</div>
                <div class="ui-section-caption">{_escape_text(record.bear_case)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_right:
        exposure_lines = []
        if portfolio_exposure["in_portfolio"]:
            exposure_lines.append(
                f"Held in portfolio: Qty {portfolio_exposure['quantity']} | Weight {portfolio_exposure['portfolio_weight']}%"
            )
        else:
            exposure_lines.append("Not currently held in portfolio.")
        if portfolio_exposure["on_watchlist"]:
            exposure_lines.append("Present in watchlist.")
        if portfolio_exposure.get("suggestion"):
            exposure_lines.append(f"Portfolio suggestion label: {portfolio_exposure['suggestion']}")
        if portfolio_exposure.get("risk"):
            exposure_lines.append(f"Portfolio risk label: {portfolio_exposure['risk']}")
        exposure_markup = "<br>".join(html.escape(line) for line in exposure_lines)
        watch_triggers = _escape_text(record.watch_triggers) or "No watch triggers recorded yet."
        st.markdown(
            f"""
            <div class="ui-card">
                <div class="ui-card-title">Portfolio Exposure</div>
                <div class="ui-section-caption">{exposure_markup}</div>
                <div class="ui-card-title" style="margin-top: 16px;">Watch Triggers</div>
                <div class="ui-section-caption">{watch_triggers}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    mid_left, mid_right = st.columns([1.1, 0.9], gap="large")
    with mid_left:
        render_section_header("Key Financial Metrics", "Core metrics currently available for the dossier.")
        st.dataframe(workspace["key_metrics"], use_container_width=True, hide_index=True)
    with mid_right:
        render_section_header("Risk Alerts", "Risk scan, earnings quality, and red flag summary.")
        risk_rows = pd.DataFrame([flag.to_dict() for flag in analysis_result.risk_scan.risk_flags])
        if not risk_rows.empty:
            st.dataframe(risk_rows, use_container_width=True, hide_index=True)
        st.markdown(
            f"""
            <div class="ui-card" style="margin-top: 16px;">
                <div class="ui-card-title">Earnings Quality</div>
                <div class="ui-section-caption">{_escape_text(analysis_result.earnings_quality.summary)}</div>
                <div class="ui-card-title" style="margin-top: 16px;">Red Flag Summary</div>
                <div class="ui-section-caption">{_escape_text(analysis_result.red_flags.summary)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    rules_left, rules_right = st.columns([1.15, 0.85], gap="large")
    with rules_left:
        render_section_header("Rule Engine Output", "Current rule evaluation results used by the scorecard.")
        st.dataframe(workspace["rule_output"], use_container_width=True, hide_index=True)
    with rules_right:
        st.markdown(
            f"""
            <div class="ui-card">
                <div class="ui-card-title">Scorecard Interpretation</div>
                <div class="ui-section-caption">Final verdict: {_escape_text(analysis_result.final_verdict)}</div>
                <div class="ui-section-caption" style="margin-top: 10px;">Valuation summary: {_escape_text(analysis_result.intrinsic_value.valuation_summary)}</div>
                <div class="ui-section-caption" style="margin-top: 10px;">Suggestion rationale: {_escape_text(analysis_result.suggestion.why_this_label)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_section_header("News Intelligence", "Recent company headlines, news risk, and macro relevance.")
    news_left, news_right = st.columns([1.1, 0.9], gap="large")
    with news_left:
        if not news_intelligence["recent_news"].empty:
            st.dataframe(news_intelligence["recent_news"], use_container_width=True, hide_index=True)
        else:
            render_empty_state("No recent company news", "No recent company headlines were available for this dossier.")
    with news_right:
        news_risk = news_intelligence["news_risk"]
        render_status_badge(f"News Risk: {str(news_risk.get('risk_level', 'low')).title()}", tone="warning")
        signals = list(news_risk.get("signals", []))
        if signals:
            for signal in signals:
                st.write(f"- {signal}")
        else:
            st.write("No major negative news signals detected.")

    _render_workspace_editor(record)
