"""Portfolio dashboard page."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from services.news_risk_service import scan_portfolio_news_risk
from services.portfolio_health_service import calculate_portfolio_health_score
from services.portfolio_impact_summary_service import build_portfolio_impact_summary
from services.portfolio_intelligence_service import build_portfolio_intelligence
from services.portfolio_news_service import build_portfolio_news_monitor
from ui.design_system import (
    render_action_bar,
    format_currency,
    format_percentage,
    render_chart_card,
    render_empty_state,
    render_insight_card,
    render_kpi_row,
    render_page_header,
    render_section_header,
    render_status_badge,
)
from ui.geopolitical_risk_section import render_geopolitical_risk_section
from ui.layout_helpers import create_columns, render_spacer
from ui.news_alerts_dashboard import render_news_alerts_dashboard
from ui.portfolio_charts import render_portfolio_performance_chart, render_top_holdings_bar_chart
from ui.portfolio_holdings_table import render_portfolio_holdings_table
from ui.portfolio_news_section import render_portfolio_news_section
from ui.ui_theme import apply_finance_theme


def _render_portfolio_score_gauge(score: float) -> None:
    """Render a portfolio health gauge."""
    try:
        import plotly.graph_objects as go
    except ModuleNotFoundError:
        st.info("Install plotly to view the portfolio score gauge: pip install plotly")
        return

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(score),
            number={"suffix": "/10"},
            gauge={
                "axis": {"range": [0, 10]},
                "bar": {"color": "#155eef"},
                "steps": [
                    {"range": [0, 4], "color": "#fee4e2"},
                    {"range": [4, 7], "color": "#fef0c7"},
                    {"range": [7, 10], "color": "#dcfae6"},
                ],
            },
        )
    )
    fig.update_layout(height=280, margin={"l": 10, "r": 10, "t": 10, "b": 10}, paper_bgcolor="#ffffff")
    st.plotly_chart(fig, use_container_width=True)


def _render_sector_chart(intelligence: dict[str, object]) -> None:
    """Render sector allocation chart."""
    sector_allocation = intelligence.get("sector_allocation", {})
    if not sector_allocation:
        st.info("Sector allocation will appear after holdings are available.")
        return

    try:
        import plotly.express as px
    except ModuleNotFoundError:
        st.info("Install plotly to view sector allocation charts: pip install plotly")
        return

    frame = pd.DataFrame(
        [{"Sector": sector, "Weight": weight} for sector, weight in dict(sector_allocation).items()]
    )
    fig = px.pie(frame, names="Sector", values="Weight", hole=0.62)
    fig.update_traces(textposition="inside", textinfo="percent")
    fig.update_layout(height=340, margin={"l": 10, "r": 10, "t": 20, "b": 10}, paper_bgcolor="#ffffff")
    st.plotly_chart(fig, use_container_width=True)


def _render_top_holdings(intelligence: dict[str, object]) -> None:
    """Render top holdings summary table."""
    top_holdings = intelligence.get("top_holdings", [])
    if not top_holdings:
        st.info("Top holdings will appear after positions are added.")
        return

    frame = pd.DataFrame(top_holdings).rename(
        columns={
            "ticker": "Ticker",
            "company_name": "Company",
            "weight_pct": "Weight %",
            "position_value": "Current Value",
        }
    )
    if "Weight %" in frame.columns:
        frame["Weight %"] = frame["Weight %"].map(lambda value: f"{float(value):.2f}%")
    if "Current Value" in frame.columns:
        frame["Current Value"] = frame["Current Value"].map(format_currency)
    st.dataframe(frame[["Ticker", "Company", "Weight %", "Current Value"]], use_container_width=True, hide_index=True)


def _render_alerts(title: str, alerts: list[str] | list[dict[str, object]], empty_message: str) -> None:
    """Render generic alert blocks."""
    render_section_header(title, None)
    if not alerts:
        st.info(empty_message)
        return

    if alerts and isinstance(alerts[0], dict):
        frame = pd.DataFrame(alerts)
        st.dataframe(frame, use_container_width=True, hide_index=True)
        return

    for alert in alerts:
        st.write(f"- {alert}")


def render_portfolio_dashboard(
    user_id: int,
    summary: dict[str, float],
    holdings: pd.DataFrame,
    snapshot_df: pd.DataFrame,
    transaction_history: pd.DataFrame,
    watchlist: pd.DataFrame | None = None,
) -> None:
    """Render the main portfolio dashboard page."""
    apply_finance_theme()
    render_page_header(
        "Portfolio Dashboard",
        f"Updated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Premium broker-style analytics workspace for holdings, performance, risk, and news flow.",
        badges=[("Live Portfolio", "positive"), ("Impact Layer", "info")],
    )
    render_action_bar(
        "Dashboard flow",
        "Performance, allocation, holdings intelligence, risk alerts, and macro/news mapping are grouped into premium cards.",
        badges=[("Hero Chart", "neutral"), ("Health Score", "warning"), ("News-Aware", "info")],
    )

    if holdings.empty:
        render_empty_state("No holdings yet", "Add transactions or import holdings to activate portfolio intelligence.")
        render_chart_card(
            "Portfolio Performance",
            lambda: render_portfolio_performance_chart(snapshot_df),
            "Historical value and net-worth trend.",
        )
        return

    try:
        portfolio_health = calculate_portfolio_health_score(holdings)
        intelligence = build_portfolio_intelligence(
            user_id=user_id,
            holdings=holdings,
            transaction_history=transaction_history,
            cash_balance=summary.get("cash_balance", 0.0),
        )
    except Exception as exc:
        st.error(f"Unable to build portfolio intelligence: {exc}")
        return

    try:
        portfolio_news = build_portfolio_news_monitor(
            user_id=user_id,
            holdings=holdings,
            watchlist=watchlist,
        )
        impact_summary = build_portfolio_impact_summary(
            impact_rows=list(portfolio_news.get("impact_rows", [])),
            macro_events=list(portfolio_news.get("macro_events", [])),
        )
    except Exception as exc:
        portfolio_news = {
            "impact_rows": [],
            "portfolio_summary": {},
            "top_positive_tailwinds": [],
            "top_negative_headwinds": [],
            "macro_events": [],
            "exposure_map": {},
            "source_errors": [str(exc)],
        }
        impact_summary = {"summary_text": "Portfolio news impact summary is unavailable right now."}

    try:
        news_risk = scan_portfolio_news_risk(holdings, top_n=5)
    except Exception:
        news_risk = {"overall_risk_level": "low", "alerts": [], "company_results": []}

    render_kpi_row(
        [
            {
                "title": "Portfolio Health Score",
                "value": f"{float(portfolio_health['portfolio_score']):.1f}/10",
                "delta": "Weighted portfolio quality lens",
            },
            {
                "title": "Total Invested",
                "value": format_currency(summary.get("invested_amount")),
                "delta": None,
            },
            {
                "title": "Current Value",
                "value": format_currency(summary.get("portfolio_value")),
                "delta": format_percentage(summary.get("total_return_pct")),
            },
            {
                "title": "Unrealized P&L",
                "value": format_currency(summary.get("unrealized_pnl")),
                "delta": None,
            },
        ]
    )

    render_spacer()
    render_chart_card(
        "Portfolio Performance",
        lambda: render_portfolio_performance_chart(snapshot_df),
        "Portfolio value, invested value, and net worth over time.",
    )

    render_spacer()
    left_column, right_column = create_columns([1.1, 1])
    with left_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Portfolio Intelligence", tone="info")
        render_section_header("Portfolio Intelligence Summary", "Current allocation, position size, and risk context.")
        intelligence_summary = intelligence.get("portfolio_summary", {})
        render_kpi_row(
            [
                {"title": "Return %", "value": format_percentage(intelligence_summary.get("return_pct")), "delta": None},
                {"title": "Top Holdings", "value": str(len(intelligence.get("top_holdings", []))), "delta": "Largest live positions"},
                {"title": "Risk Alerts", "value": str(len(intelligence.get("risk_warnings", []))), "delta": "Deterministic warnings"},
            ]
        )
        components = portfolio_health.get("components", {})
        component_frame = pd.DataFrame(
            [{"Component": key.replace("_", " ").title(), "Score": value} for key, value in components.items()]
        )
        st.dataframe(component_frame, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with right_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Portfolio Score Gauge", tone="neutral")
        render_section_header("Portfolio Score Gauge", "Weighted 0-10 portfolio health indicator.")
        _render_portfolio_score_gauge(float(portfolio_health["portfolio_score"]))
        st.markdown("</div>", unsafe_allow_html=True)

    render_spacer()
    alloc_col, top_holdings_col = create_columns([1, 1.2])
    with alloc_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Sector Allocation", tone="neutral")
        render_section_header("Sector Allocation Chart", "Current portfolio concentration by sector.")
        _render_sector_chart(intelligence)
        st.markdown("</div>", unsafe_allow_html=True)
    with top_holdings_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Top Holdings", tone="info")
        render_section_header("Top Holdings", "Largest holdings ranked by current portfolio weight.")
        _render_top_holdings(intelligence)
        render_top_holdings_bar_chart(holdings)
        st.markdown("</div>", unsafe_allow_html=True)

    render_spacer()
    risk_alerts_col, news_col = create_columns([1, 1])
    with top_holdings_col:
        pass
    with risk_alerts_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Risk Alerts", tone="warning")
        _render_alerts(
            "Risk Alerts",
            list(intelligence.get("risk_warnings", [])),
            "No concentration or position-size alerts were triggered.",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with news_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge(f"News Risk: {str(news_risk['overall_risk_level']).title()}", tone="warning" if news_risk["overall_risk_level"] != "low" else "positive")
        _render_alerts(
            "News Alerts",
            list(news_risk.get("alerts", [])),
            "No negative news signals were detected for the largest holdings.",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    render_spacer()
    holdings_col = create_columns([1])[0]
    with holdings_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Holdings Analytics", tone="neutral")
        render_section_header("Holdings Analytics", "Per-holding score, suggestion, and risk from the research engine.")
        render_portfolio_holdings_table(holdings)
        st.markdown("</div>", unsafe_allow_html=True)

    render_spacer()
    st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
    render_portfolio_news_section(portfolio_news, impact_summary)
    st.markdown("</div>", unsafe_allow_html=True)

    render_spacer()
    geo_col, alerts_col = create_columns([1.15, 0.95])
    with geo_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_geopolitical_risk_section(portfolio_news, impact_summary)
        st.markdown("</div>", unsafe_allow_html=True)
    with alerts_col:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        news_alert_rows = [
            {
                "Ticker": row.get("ticker"),
                "Event": row.get("event_title"),
                "Direction": row.get("impact_direction"),
                "Severity": row.get("severity"),
            }
            for row in list(portfolio_news.get("impact_rows", []))[:8]
        ]
        render_news_alerts_dashboard(
            title="News Alerts",
            alerts=news_alert_rows,
            caption="Current portfolio-impacting alerts across company, sector, and macro coverage.",
            empty_message="No portfolio news alerts were generated in the latest scan.",
        )
        st.markdown("</div>", unsafe_allow_html=True)
