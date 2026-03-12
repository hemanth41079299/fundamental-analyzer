"""Intrinsic value analysis UI section."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from models.result_model import IntrinsicValueSummary


def render_valuation_section(intrinsic_value: IntrinsicValueSummary) -> None:
    """Render valuation model outputs and consensus fair value."""
    st.subheader("Valuation Analysis")

    valuation_rows = []
    for model in intrinsic_value.valuation_models:
        valuation_rows.append(
            {
                "Method": model.method,
                "Fair Value": model.fair_value if model.fair_value is not None else "NA",
                "Current Price": model.current_price if model.current_price is not None else "NA",
                "Valuation": model.valuation if model.valuation is not None else "NA",
                "Difference %": model.difference_percent if model.difference_percent is not None else "NA",
                "Implied Growth %": model.implied_growth if model.implied_growth is not None else "NA",
                "Owner Earnings": model.owner_earnings if model.owner_earnings is not None else "NA",
                "Notes": model.notes if model.notes is not None else "",
            }
        )

    st.dataframe(pd.DataFrame(valuation_rows), use_container_width=True, hide_index=True)

    col_1, col_2 = st.columns(2)
    col_1.metric(
        "Consensus Fair Value",
        "NA" if intrinsic_value.consensus_fair_value is None else f"{intrinsic_value.consensus_fair_value:.2f}",
    )
    col_2.markdown("**Valuation Summary**")
    col_2.write(intrinsic_value.valuation_summary)
