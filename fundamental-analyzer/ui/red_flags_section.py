"""Financial red flags UI section."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from models.result_model import RedFlagSummary


def render_red_flags_section(red_flags: RedFlagSummary) -> None:
    """Render financial red flags and summary."""
    st.subheader("Financial Red Flags")
    if red_flags.red_flags:
        frame = pd.DataFrame([flag.to_dict() for flag in red_flags.red_flags])
        st.dataframe(frame, use_container_width=True, hide_index=True)
    else:
        st.info("No major financial red flags detected.")

    st.caption(red_flags.summary)
