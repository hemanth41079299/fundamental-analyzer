"""Company research history UI section."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_history_section(history_rows: list[dict[str, object]]) -> None:
    """Render prior company analysis history."""
    st.subheader("Company Research History")
    if not history_rows:
        st.info("No previous analysis history available for this company.")
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
