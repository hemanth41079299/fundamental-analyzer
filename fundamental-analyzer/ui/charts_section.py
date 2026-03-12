"""Plotly chart section for financial trend visualizations."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from models.company_data import CompanyData


def _build_trend_frame(data: list[dict[str, object]]) -> pd.DataFrame:
    """Convert trend records into a dataframe."""
    return pd.DataFrame(data)


def _plot_line(data: list[dict[str, object]], title: str, y_label: str):
    """Build a Plotly line chart from normalized trend records."""
    frame = _build_trend_frame(data)
    if frame.empty:
        return None
    try:
        import plotly.express as px
    except ModuleNotFoundError:
        return None
    return px.line(frame, x="year", y="value", markers=True, title=title, labels={"year": "Year", "value": y_label})


def plot_revenue_trend(data: list[dict[str, object]]):
    """Plot revenue trend."""
    return _plot_line(data, "Revenue Trend", "Revenue")


def plot_profit_trend(data: list[dict[str, object]]):
    """Plot profit trend."""
    return _plot_line(data, "Profit Trend", "Profit")


def plot_roe_trend(data: list[dict[str, object]]):
    """Plot ROE trend."""
    return _plot_line(data, "ROE Trend", "ROE (%)")


def plot_margin_trend(data: list[dict[str, object]]):
    """Plot margin trend."""
    return _plot_line(data, "Margin Trend", "Margin (%)")


def plot_debt_trend(data: list[dict[str, object]]):
    """Plot debt trend."""
    return _plot_line(data, "Debt Trend", "Debt to Equity")


def render_charts_section(company_data: CompanyData) -> None:
    """Render all available financial trend charts."""
    st.subheader("Financial Trends")
    trends = company_data.financial_trends or {}

    if not trends:
        st.info("Financial trend charts are available when web data includes annual statement history.")
        return

    try:
        import plotly.express  # noqa: F401
    except ModuleNotFoundError:
        st.info("Install plotly to view financial trend charts: pip install plotly")
        return

    chart_builders = [
        ("revenue", plot_revenue_trend),
        ("profit", plot_profit_trend),
        ("roe", plot_roe_trend),
        ("margin", plot_margin_trend),
        ("debt", plot_debt_trend),
    ]

    rendered_any = False
    for left, right in zip(chart_builders[::2], chart_builders[1::2]):
        col_1, col_2 = st.columns(2)
        for column, (trend_key, builder) in zip((col_1, col_2), (left, right)):
            figure = builder(trends.get(trend_key, []))
            if figure is not None:
                column.plotly_chart(figure, use_container_width=True)
                rendered_any = True
            else:
                column.info(f"No {trend_key} trend data available.")

    if len(chart_builders) % 2 == 1:
        last_key, last_builder = chart_builders[-1]
        figure = last_builder(trends.get(last_key, []))
        if figure is not None:
            st.plotly_chart(figure, use_container_width=True)
            rendered_any = True
        else:
            st.info(f"No {last_key} trend data available.")

    if not rendered_any:
        st.info("No financial trend data is available for charting.")
