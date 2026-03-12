"""Bulk company analysis UI section."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_bulk_analysis_section(bulk_results: pd.DataFrame) -> None:
    """Render Screener CSV bulk analysis results."""
    st.subheader("Bulk Company Analysis Results")
    ordered = bulk_results.sort_values(by="Score", ascending=False, na_position="last")
    st.dataframe(ordered, use_container_width=True, hide_index=True)
