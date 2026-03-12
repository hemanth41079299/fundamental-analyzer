"""Premium research workspace for single-company analysis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from core.analysis_engine import build_analysis
from core.classifier import classify_market_cap
from core.narration_engine import build_narration
from models.company_data import CompanyData
from models.result_model import AnalysisResult, IntrinsicValueSummary, RedFlagSummary
from services.history_service import load_company_history, save_company_history
from services.report_service import save_analysis_output
from services.rule_service import RuleService
from ui.charts_section import render_charts_section
from ui.design_system import (
    format_currency,
    format_percentage,
    render_empty_state,
    render_kpi_row,
    render_section_header,
    render_status_badge,
)
from ui.rules_editor import render_rules_editor
from ui.suggestion_section import render_suggestion_section
from ui.ui_theme import apply_finance_theme


def _format_metric(value: object, suffix: str | None = None) -> str:
    """Format numeric metrics for KPI cards."""
    if value is None:
        return "NA"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if suffix == "%":
        return f"{numeric:.2f}%"
    return f"{numeric:.2f}"


def _render_company_header(
    company_data: CompanyData,
    market_cap_category: str,
    source_label: str,
    rule_source: str,
) -> None:
    """Render the company analysis header."""
    apply_finance_theme()
    company_name = company_data.company_name or "Unknown Company"
    st.markdown('<div class="finance-page-header">', unsafe_allow_html=True)
    st.markdown(f"<h2>{company_name}</h2>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="finance-page-subtitle">Source: {source_label} | Category: {market_cap_category.replace("_", " ").title()}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    badge_columns = st.columns(3)
    with badge_columns[0]:
        render_status_badge(market_cap_category.replace("_", " ").title(), tone="info")
    with badge_columns[1]:
        render_status_badge("Custom Rules" if rule_source == "custom" else "Default Rules", tone="neutral")
    with badge_columns[2]:
        render_status_badge("Research Workspace", tone="positive")


def _render_company_snapshot(company_data: CompanyData, analysis_result: AnalysisResult) -> None:
    """Render company snapshot KPI cards."""
    render_section_header("Company Snapshot", "Core business, valuation, and profitability metrics at a glance.")
    render_kpi_row(
        [
            {
                "title": "Market Cap (Cr)",
                "value": _format_metric(company_data.market_cap_cr),
                "delta": analysis_result.score.interpretation,
            },
            {
                "title": "Current Price",
                "value": format_currency(company_data.current_price),
                "delta": None,
            },
            {
                "title": "ROE",
                "value": _format_metric(company_data.roe, "%"),
                "delta": None,
            },
            {
                "title": "ROCE",
                "value": _format_metric(company_data.roce, "%"),
                "delta": None,
            },
            {
                "title": "Sales Growth 5Y",
                "value": _format_metric(company_data.sales_growth_5y, "%"),
                "delta": None,
            },
            {
                "title": "Profit Growth 5Y",
                "value": _format_metric(company_data.profit_growth_5y, "%"),
                "delta": None,
            },
        ]
    )


def _render_metrics_card(company_data: CompanyData) -> None:
    """Render extracted metrics inside a premium card."""
    render_section_header("Extracted Metrics", "Normalized company metrics used by the rule engine.")
    rows: list[dict[str, object]] = []
    for field_name, value in company_data.to_dict().items():
        if field_name in {"source_file", "financial_trends"}:
            continue
        rows.append({"Metric": field_name.replace("_", " ").title(), "Value": "NA" if value is None else value})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_scorecard_card(analysis_result: AnalysisResult) -> None:
    """Render score, scorecard, and rule evaluation tables."""
    render_section_header("Scorecard", "Rule performance by category plus the supporting evaluation grid.")
    render_kpi_row(
        [
            {"title": "Passed Rules", "value": str(analysis_result.score.total_passed), "delta": None},
            {"title": "Applicable Rules", "value": str(analysis_result.score.total_applicable), "delta": None},
            {"title": "Score", "value": format_percentage(analysis_result.score.percentage), "delta": analysis_result.score.interpretation},
            {
                "title": "Total Score",
                "value": f"{analysis_result.scorecard.total_score} / {analysis_result.scorecard.max_score}",
                "delta": "Category weighted view",
            },
        ]
    )

    scorecard_frame = pd.DataFrame([detail.to_dict() for detail in analysis_result.scorecard.details])
    if not scorecard_frame.empty:
        scorecard_frame["Summary"] = scorecard_frame["passed"].astype(str) + "/" + scorecard_frame["applicable"].astype(str)
        st.dataframe(
            scorecard_frame[["category", "Summary", "score", "percentage"]].rename(
                columns={
                    "category": "Category",
                    "score": "Score (0-10)",
                    "percentage": "Percentage",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(scorecard_frame.set_index("category")[["score"]], use_container_width=True)

    results_frame = pd.DataFrame([result.to_dict() for result in analysis_result.rule_results])
    st.dataframe(results_frame, use_container_width=True, hide_index=True)


def _render_strengths_and_observations(analysis_result: AnalysisResult) -> None:
    """Render strengths, weaknesses, and observations."""
    render_section_header("Business Quality", "Summarized positives, negatives, and category-level observations.")
    strengths_col, weaknesses_col = st.columns(2)
    with strengths_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Strengths", tone="positive")
        if analysis_result.strengths:
            for item in analysis_result.strengths:
                st.write(f"- {item}")
        else:
            st.write("No clear strengths identified.")
        st.markdown("</div>", unsafe_allow_html=True)
    with weaknesses_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Weaknesses", tone="warning")
        if analysis_result.weaknesses:
            for item in analysis_result.weaknesses:
                st.write(f"- {item}")
        else:
            st.write("No clear weaknesses identified.")
        st.markdown("</div>", unsafe_allow_html=True)

    observations_frame = pd.DataFrame(
        [{"Category": key.title(), "Observation": value} for key, value in analysis_result.observations.items()]
    )
    st.dataframe(observations_frame, use_container_width=True, hide_index=True)


def _render_valuation_card(intrinsic_value: IntrinsicValueSummary) -> None:
    """Render valuation analysis."""
    render_section_header("Valuation", "Fair-value lenses built from PEG, reverse DCF, and owner-earnings methods.")
    rows = [model.to_dict() for model in intrinsic_value.valuation_models]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    render_kpi_row(
        [
            {
                "title": "Consensus Fair Value",
                "value": format_currency(intrinsic_value.consensus_fair_value),
                "delta": None,
            },
            {
                "title": "Valuation Summary",
                "value": intrinsic_value.valuation_summary,
                "delta": None,
            },
        ]
    )


def _render_thesis_card(analysis_result: AnalysisResult) -> None:
    """Render thesis and final verdict."""
    render_section_header("Investment Thesis", "Template-based bull case, bear case, risks, triggers, and verdict.")
    left_col, right_col = st.columns(2)
    with left_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Bull Case", tone="positive")
        for item in analysis_result.thesis.bull_case:
            st.write(f"- {item}")
        render_status_badge("Key Risks", tone="warning")
        for item in analysis_result.thesis.key_risks:
            st.write(f"- {item}")
        st.markdown("</div>", unsafe_allow_html=True)
    with right_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Bear Case", tone="negative")
        for item in analysis_result.thesis.bear_case:
            st.write(f"- {item}")
        render_status_badge("Key Triggers", tone="info")
        for item in analysis_result.thesis.key_triggers:
            st.write(f"- {item}")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
    render_status_badge("Final Verdict", tone="neutral")
    st.write(analysis_result.final_verdict)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_red_flags_card(red_flags: RedFlagSummary) -> None:
    """Render red flag section."""
    render_section_header("Red Flags", "Suspicious financial patterns detected from deterministic checks.")
    st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
    render_status_badge(f"{red_flags.red_flag_count} flags", tone="warning" if red_flags.red_flag_count else "positive")
    if red_flags.red_flags:
        st.dataframe(pd.DataFrame([flag.to_dict() for flag in red_flags.red_flags]), use_container_width=True, hide_index=True)
    else:
        render_empty_state("No major financial red flags", "The current rule-based scan did not find major warning patterns.")
    st.caption(red_flags.summary)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_narration_card(narration: str) -> None:
    """Render narration output."""
    render_section_header("Narration", "Readable summary of the research outcome in the selected tone.")
    st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
    st.write(narration)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_history_card(history_rows: list[dict[str, object]]) -> None:
    """Render company research history."""
    render_section_header("Research History", "Previous saved analyses for this company under the current user.")
    if not history_rows:
        render_empty_state("No previous analysis history", "Run and save more analyses to build a history for this company.")
        return
    display_rows = [
        {
            "Timestamp": item.get("timestamp"),
            "Score": item.get("score"),
            "Total Score": item.get("total_score"),
            "Verdict": item.get("verdict"),
            "Source": item.get("source_file"),
        }
        for item in reversed(history_rows)
    ]
    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)


def render_company_analysis_view(
    company_data: CompanyData,
    narration_style: str,
    source_label: str,
    output_dir: Path,
) -> None:
    """Render the full premium company analysis workspace."""
    rule_service = RuleService()
    market_cap_category = classify_market_cap(company_data.market_cap_cr)
    _, rule_source = rule_service.get_rules_with_source(market_cap_category)

    _render_company_header(company_data, market_cap_category, source_label, rule_source)

    top_left, top_right = st.columns([2, 1.2])
    with top_left:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_section_header("Analysis Controls", "Selected market-cap rules drive the scorecard and verdict.")
        active_rules = render_rules_editor(rule_service, market_cap_category, rule_source=rule_source)
        st.markdown("</div>", unsafe_allow_html=True)
    with top_right:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_section_header("Source Context", "Extraction source and classification used for this research run.")
        st.metric("Source", source_label)
        st.metric("Category", market_cap_category.replace("_", " ").title())
        st.metric("Rule Set", "Custom Rules" if rule_source == "custom" else "Default Rules")
        st.metric("Narration Tone", narration_style.title())
        st.markdown("</div>", unsafe_allow_html=True)

    analysis_result = build_analysis(company_data, market_cap_category, active_rules)
    narration = build_narration(company_data, analysis_result, tone=narration_style)
    history_path = save_company_history(company_data, analysis_result, narration)
    history_rows = load_company_history(company_data.company_name or "Unknown Company")
    output_path = save_analysis_output(
        output_dir=output_dir,
        company_data=company_data,
        analysis_result=analysis_result,
        narration=narration,
    )

    render_section_header("Research Dashboard", "Premium card-based view of the company fundamentals and rule-based research output.")
    _render_company_snapshot(company_data, analysis_result)

    overview_left, overview_right = st.columns([1.4, 1])
    with overview_left:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        _render_scorecard_card(analysis_result)
        st.markdown("</div>", unsafe_allow_html=True)
    with overview_right:
        render_suggestion_section(analysis_result)

    value_left, value_right = st.columns(2)
    with value_left:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        _render_valuation_card(analysis_result.intrinsic_value)
        st.markdown("</div>", unsafe_allow_html=True)
    with value_right:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        _render_red_flags_card(analysis_result.red_flags)
        st.markdown("</div>", unsafe_allow_html=True)

    thesis_left, thesis_right = st.columns([1.3, 1])
    with thesis_left:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        _render_thesis_card(analysis_result)
        st.markdown("</div>", unsafe_allow_html=True)
    with thesis_right:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        _render_narration_card(narration)
        st.markdown("</div>", unsafe_allow_html=True)

    info_left, info_right = st.columns([1.2, 1])
    with info_left:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        _render_metrics_card(company_data)
        st.markdown("</div>", unsafe_allow_html=True)
    with info_right:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        _render_history_card(history_rows)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
    render_section_header("Financial Trends", "Historical visuals based on available annual statement data.")
    render_charts_section(company_data)
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption(f"Analysis output saved to: {output_path}")
    st.caption(f"Company history stored at: {history_path}")
