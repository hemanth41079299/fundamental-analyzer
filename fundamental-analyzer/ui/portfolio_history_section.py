"""Portfolio history and snapshot UI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from services.portfolio_snapshot_service import get_snapshots, save_snapshot
from ui.design_system import render_chart_card, render_empty_state, render_kpi_row, render_section_header
from ui.ui_theme import apply_finance_theme


def render_portfolio_history_section() -> None:
    """Render portfolio snapshot history and value trends."""
    apply_finance_theme()
    render_section_header(
        "Portfolio History",
        "Review saved snapshots and track how portfolio value and net worth evolved over time.",
    )
    toolbar_col_1, toolbar_col_2 = st.columns([0.2, 0.8])
    with toolbar_col_1:
        save_clicked = st.button("Save Snapshot", use_container_width=True)
    if save_clicked:
        save_snapshot()
        st.success("Portfolio snapshot saved.")
        st.rerun()

    snapshots = get_snapshots()
    if snapshots.empty:
        render_empty_state("No snapshots yet", "Save a portfolio snapshot to start building historical performance.")
        return

    latest_row = snapshots.iloc[-1]
    earliest_row = snapshots.iloc[0]
    net_worth_change = float(latest_row["total_net_worth"]) - float(earliest_row["total_net_worth"])
    render_kpi_row(
        [
            {"title": "Snapshots", "value": str(len(snapshots)), "delta": "Saved checkpoints"},
            {"title": "Latest Net Worth", "value": f"Rs {float(latest_row['total_net_worth']):,.2f}", "delta": None},
            {"title": "Latest Portfolio Value", "value": f"Rs {float(latest_row['portfolio_value']):,.2f}", "delta": None},
            {"title": "Net Worth Change", "value": f"Rs {net_worth_change:,.2f}", "delta": "Since first snapshot"},
        ]
    )

    trend_frame = snapshots.copy()
    trend_frame["snapshot_date"] = pd.to_datetime(trend_frame["snapshot_date"], errors="coerce")
    trend_frame = trend_frame.dropna(subset=["snapshot_date"])
    chart_frame = trend_frame.set_index("snapshot_date")[["portfolio_value", "total_net_worth"]]
    render_chart_card(
        "Historical Performance",
        lambda: st.line_chart(chart_frame),
        "Portfolio value and total net worth across saved snapshots.",
    )
    render_section_header("Snapshot Log", "Stored snapshot values used for history and dashboard charts.")
    st.dataframe(snapshots, use_container_width=True, hide_index=True)
