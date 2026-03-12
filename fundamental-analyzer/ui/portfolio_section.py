"""Portfolio analysis UI section."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_portfolio_section(portfolio_results: pd.DataFrame) -> None:
    """Render portfolio results and high-level portfolio insights."""
    st.subheader("Portfolio Results")
    ordered_results = portfolio_results.sort_values(by="Score", ascending=False, na_position="last")
    st.dataframe(ordered_results, use_container_width=True, hide_index=True)

    st.subheader("Portfolio Insights")
    scored_results = ordered_results.dropna(subset=["Score"]).copy()
    if scored_results.empty:
        st.warning("No portfolio scores are available. Check ticker symbols and dependencies.")
        return

    strongest_row = scored_results.loc[scored_results["Score"].idxmax()]
    weakest_row = scored_results.loc[scored_results["Score"].idxmin()]
    average_score = scored_results["Score"].mean()

    col_1, col_2, col_3 = st.columns(3)
    col_1.metric("Strongest Company", str(strongest_row["Stock"]))
    col_2.metric("Weakest Company", str(weakest_row["Stock"]))
    col_3.metric("Average Portfolio Score", f"{average_score:.2f}")
