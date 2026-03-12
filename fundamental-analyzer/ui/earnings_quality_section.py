"""Earnings quality analysis UI section."""

from __future__ import annotations

import streamlit as st

from models.result_model import EarningsQualitySummary


def render_earnings_quality_section(earnings_quality: EarningsQualitySummary) -> None:
    """Render earnings quality analysis."""
    st.subheader("Earnings Quality Analysis")

    col_1, col_2 = st.columns(2)
    col_1.metric(
        "Cash Conversion Ratio",
        "NA" if earnings_quality.cash_conversion_ratio is None else f"{earnings_quality.cash_conversion_ratio:.2f}",
    )
    col_2.metric("Earnings Quality Rating", earnings_quality.earnings_quality)

    st.markdown("**Flags**")
    if earnings_quality.flags:
        for flag in earnings_quality.flags:
            st.write(f"- {flag}")
    else:
        st.write("No major earnings-quality flags were detected.")

    st.markdown("**Summary**")
    st.write(earnings_quality.summary)
