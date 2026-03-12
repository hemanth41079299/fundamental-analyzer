"""Render the analysis output sections."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from models.result_model import AnalysisResult


def render_results_section(analysis_result: AnalysisResult) -> None:
    """Render rule evaluation, score, observations, and verdict."""
    st.subheader("Rule Evaluation")
    results_frame = pd.DataFrame([result.to_dict() for result in analysis_result.rule_results])
    st.dataframe(results_frame, use_container_width=True, hide_index=True)

    st.subheader("Score")
    col_1, col_2, col_3 = st.columns(3)
    col_1.metric("Passed", analysis_result.score.total_passed)
    col_2.metric("Applicable", analysis_result.score.total_applicable)
    col_3.metric(
        "Percentage",
        f"{analysis_result.score.percentage:.2f}% ({analysis_result.score.interpretation})",
    )

    st.subheader("Scorecard")
    scorecard_frame = pd.DataFrame([detail.to_dict() for detail in analysis_result.scorecard.details])
    if not scorecard_frame.empty:
        scorecard_frame["Summary"] = scorecard_frame["passed"].astype(str) + "/" + scorecard_frame["applicable"].astype(str)
        scorecard_display = scorecard_frame[["category", "Summary", "score", "percentage"]].rename(
            columns={
                "category": "Category",
                "score": "Score (0-10)",
                "percentage": "Percentage",
            }
        )
        st.dataframe(scorecard_display, use_container_width=True, hide_index=True)

        chart_frame = scorecard_frame.set_index("category")[["score"]]
        st.bar_chart(chart_frame)

    st.metric("Total Score", f"{analysis_result.scorecard.total_score} / {analysis_result.scorecard.max_score}")

    st.subheader("Strengths and Weaknesses")
    strengths_col, weaknesses_col = st.columns(2)
    strengths_col.markdown("**Strengths**")
    if analysis_result.strengths:
        for item in analysis_result.strengths:
            strengths_col.write(f"- {item}")
    else:
        strengths_col.write("No clear strengths identified.")

    weaknesses_col.markdown("**Weaknesses**")
    if analysis_result.weaknesses:
        for item in analysis_result.weaknesses:
            weaknesses_col.write(f"- {item}")
    else:
        weaknesses_col.write("No clear weaknesses identified.")

    st.subheader("Observations")
    observations_frame = pd.DataFrame(
        [
            {"Category": category.title(), "Observation": observation}
            for category, observation in analysis_result.observations.items()
        ]
    )
    st.dataframe(observations_frame, use_container_width=True, hide_index=True)

    st.subheader("Investment Thesis")
    thesis_col_1, thesis_col_2 = st.columns(2)

    thesis_col_1.markdown("**Bull Case**")
    for item in analysis_result.thesis.bull_case:
        thesis_col_1.write(f"- {item}")

    thesis_col_2.markdown("**Bear Case**")
    for item in analysis_result.thesis.bear_case:
        thesis_col_2.write(f"- {item}")

    thesis_col_1.markdown("**Key Risks**")
    for item in analysis_result.thesis.key_risks:
        thesis_col_1.write(f"- {item}")

    thesis_col_2.markdown("**Key Triggers**")
    for item in analysis_result.thesis.key_triggers:
        thesis_col_2.write(f"- {item}")

    st.subheader("Final Verdict")
    st.info(analysis_result.final_verdict)
