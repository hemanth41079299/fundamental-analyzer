"""Portfolio dashboard chart components."""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st


def _filter_snapshot_range(snapshot_df: pd.DataFrame, range_label: str) -> pd.DataFrame:
    """Filter snapshots to a selected trailing range."""
    if snapshot_df.empty or range_label == "Max":
        return snapshot_df

    frame = snapshot_df.copy()
    frame["snapshot_date"] = pd.to_datetime(frame["snapshot_date"], errors="coerce")
    frame = frame.dropna(subset=["snapshot_date"])
    if frame.empty:
        return frame

    end_date = frame["snapshot_date"].max()
    days_map = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}
    start_date = end_date - timedelta(days=days_map[range_label])
    return frame[frame["snapshot_date"] >= start_date]


def render_portfolio_performance_chart(snapshot_df: pd.DataFrame) -> None:
    """Render the main portfolio performance chart."""
    st.subheader("Portfolio Performance")

    if snapshot_df.empty:
        st.info("Save a portfolio snapshot to start building a performance chart.")
        return

    try:
        import plotly.graph_objects as go
    except ModuleNotFoundError:
        st.info("Install plotly to view portfolio charts: pip install plotly")
        return

    range_label = st.radio(
        "Date range",
        options=["1M", "3M", "6M", "1Y", "Max"],
        horizontal=True,
        index=4,
        key="portfolio_chart_range",
    )

    frame = _filter_snapshot_range(snapshot_df, range_label).copy()
    frame["snapshot_date"] = pd.to_datetime(frame["snapshot_date"], errors="coerce")
    frame = frame.dropna(subset=["snapshot_date"])
    if frame.empty:
        st.info("No snapshots available for the selected range.")
        return

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=frame["snapshot_date"],
            y=frame["portfolio_value"],
            mode="lines",
            name="Portfolio Value",
            line={"color": "#155eef", "width": 3},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=frame["snapshot_date"],
            y=frame["invested_amount"],
            mode="lines",
            name="Invested Value",
            line={"color": "#98a2b3", "width": 2, "dash": "dash"},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=frame["snapshot_date"],
            y=frame["total_net_worth"],
            mode="lines",
            name="Net Worth",
            line={"color": "#12b76a", "width": 2.5},
        )
    )
    fig.update_layout(
        height=420,
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        legend={"orientation": "h", "y": 1.08, "x": 0},
        xaxis={"title": "", "showgrid": False},
        yaxis={"title": "", "gridcolor": "#eaecf0", "zeroline": False},
    )
    st.plotly_chart(fig, use_container_width=True)


def render_top_holdings_bar_chart(holdings: pd.DataFrame) -> None:
    """Render a bar chart for the top holdings by current value."""
    st.subheader("Top Holdings")
    if holdings.empty or "Current Value" not in holdings.columns:
        st.info("No holdings available for the allocation chart.")
        return

    try:
        import plotly.express as px
    except ModuleNotFoundError:
        st.info("Install plotly to view portfolio charts: pip install plotly")
        return

    frame = holdings.copy()
    frame["Current Value"] = pd.to_numeric(frame["Current Value"], errors="coerce").fillna(0.0)
    frame = frame.sort_values("Current Value", ascending=False).head(8)
    if frame.empty:
        st.info("No holdings available for the allocation chart.")
        return

    fig = px.bar(
        frame,
        x="Ticker",
        y="Current Value",
        color="Current Value",
        color_continuous_scale=["#d1e9ff", "#155eef"],
    )
    fig.update_layout(
        height=320,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        coloraxis_showscale=False,
        xaxis_title="",
        yaxis_title="",
    )
    st.plotly_chart(fig, use_container_width=True)
