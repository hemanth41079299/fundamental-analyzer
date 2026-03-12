"""Suggestion and risk display section."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from models.result_model import AnalysisResult
from ui.design_system import render_insight_card, render_section_header, render_status_badge
from ui.ui_theme import apply_finance_theme


def _valuation_status(analysis_result: AnalysisResult) -> str:
    """Return a compact valuation status for display."""
    labels = [model.valuation for model in analysis_result.intrinsic_value.valuation_models if model.valuation]
    if not labels:
        return "Unavailable"
    if "Overvalued" in labels:
        return "Expensive"
    if "Undervalued" in labels:
        return "Attractive"
    return "Fair"


def render_suggestion_section(analysis_result: AnalysisResult) -> None:
    """Render research suggestion and deterministic risk output."""
    apply_finance_theme()
    st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
    render_status_badge(analysis_result.suggestion.label, tone="info")
    render_section_header(
        "Research Suggestion",
        "Recommendation label, confidence, risk context, and required follow-up actions.",
    )

    top_cols = st.columns(2)
    with top_cols[0]:
        render_insight_card("Suggestion Label", analysis_result.suggestion.label, analysis_result.suggestion.summary, "info")
    with top_cols[1]:
        render_insight_card("Confidence", analysis_result.suggestion.confidence, analysis_result.suggestion.why_this_label, "neutral")

    context_cols = st.columns(3)
    with context_cols[0]:
        render_insight_card("Valuation", _valuation_status(analysis_result), "Cross-method valuation lens", "warning")
    with context_cols[1]:
        render_insight_card("Earnings Quality", analysis_result.earnings_quality.earnings_quality, analysis_result.earnings_quality.summary, "neutral")
    with context_cols[2]:
        render_insight_card("Overall Risk", analysis_result.risk_scan.overall_risk_level, f"{analysis_result.red_flags.red_flag_count} red flags", "warning" if analysis_result.risk_scan.overall_risk_level != "Low" else "positive")

    render_section_header("Action Points", "Deterministic next checks generated from the research engine.")
    for action_point in analysis_result.suggestion.action_points:
        st.write(f"- {action_point}")

    render_section_header("Risk Flags", "Specific issues surfaced by the risk scanner.")
    if analysis_result.risk_scan.risk_flags:
        risk_frame = pd.DataFrame([flag.to_dict() for flag in analysis_result.risk_scan.risk_flags])
        st.dataframe(risk_frame, use_container_width=True, hide_index=True)
    else:
        st.info("No major deterministic risk flags were triggered under the current framework.")
    st.markdown("</div>", unsafe_allow_html=True)
