"""Professional portfolio dashboard page."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from services.news_risk_service import scan_portfolio_news_risk
from services.portfolio_health_service import calculate_portfolio_health_score
from services.portfolio_impact_summary_service import build_portfolio_impact_summary
from services.portfolio_intelligence_service import build_portfolio_intelligence
from services.portfolio_news_service import build_portfolio_news_monitor
from ui.components.chart_card import close_chart_card, render_chart_card
from ui.components.kpi_card import render_kpi_card
from ui.components.section_header import render_page_header, render_section_header
from ui.components.status_badge import render_status_badge
from ui.geopolitical_risk_section import render_geopolitical_risk_section
from ui.layout_helpers import create_columns, render_spacer
from ui.news_alerts_dashboard import render_news_alerts_dashboard
from ui.portfolio_charts import render_portfolio_performance_chart, render_top_holdings_bar_chart
from ui.portfolio_holdings_table import render_portfolio_holdings_table
from ui.portfolio_news_section import render_portfolio_news_section
from ui.theme import apply_theme_css, get_plotly_layout


def _render_portfolio_score_gauge(score: float) -> None:
    """Render a theme-aware portfolio health gauge."""
    try:
        import plotly.graph_objects as go
    except ModuleNotFoundError:
        st.info("Install plotly to view the portfolio score gauge: pip install plotly")
        return

    theme = get_plotly_layout()
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(score),
            number={"suffix": "/10"},
            gauge={
                "axis": {"range": [0, 10], "tickcolor": theme["font_color"]},
                "bar": {"color": theme["accent"]},
                "steps": [
                    {"range": [0, 4], "color": "rgba(239,68,68,0.12)"},
                    {"range": [4, 7], "color": "rgba(148,163,184,0.18)"},
                    {"range": [7, 10], "color": "rgba(37,99,235,0.12)"},
                ],
            },
        )
    )
    fig.update_layout(
        height=260,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        paper_bgcolor=theme["paper_bgcolor"],
        font={"color": theme["font_color"]},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_sector_chart(intelligence: dict[str, object]) -> None:
    """Render sector allocation donut."""
    sector_allocation = intelligence.get("sector_allocation", {})
    if not sector_allocation:
        st.info("Sector allocation will appear after holdings are available.")
        return
    try:
        import plotly.express as px
    except ModuleNotFoundError:
        st.info("Install plotly to view sector allocation charts: pip install plotly")
        return

    theme = get_plotly_layout()
    frame = pd.DataFrame([{"Sector": sector, "Weight": weight} for sector, weight in dict(sector_allocation).items()])
    fig = px.pie(frame, names="Sector", values="Weight", hole=0.64)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        height=360,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        paper_bgcolor=theme["paper_bgcolor"],
        font={"color": theme["font_color"]},
        legend={"orientation": "h"},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_top_holdings_table(intelligence: dict[str, object]) -> None:
    """Render top holdings summary."""
    top_holdings = intelligence.get("top_holdings", [])
    if not top_holdings:
        st.info("Top holdings will appear after positions are added.")
        return
    frame = pd.DataFrame(top_holdings).rename(
        columns={"ticker": "Ticker", "company_name": "Company", "weight_pct": "Weight %", "position_value": "Current Value"}
    )
    if "Weight %" in frame.columns:
        frame["Weight %"] = frame["Weight %"].map(lambda value: f"{float(value):.2f}%")
    if "Current Value" in frame.columns:
        frame["Current Value"] = frame["Current Value"].map(lambda value: f"Rs {float(value):,.2f}")
    st.dataframe(frame[["Ticker", "Company", "Weight %", "Current Value"]], use_container_width=True, hide_index=True)


def render_portfolio_dashboard(
    user_id: int,
    summary: dict[str, float],
    holdings: pd.DataFrame,
    snapshot_df: pd.DataFrame,
    transaction_history: pd.DataFrame,
    watchlist: pd.DataFrame | None = None,
) -> None:
    """Render the portfolio dashboard."""
    apply_theme_css()
    render_page_header(
        "Portfolio Dashboard",
        f"Updated {datetime.now().strftime('%Y-%m-%d %H:%M')} • Professional analytics workspace for portfolio value, risk monitoring, sector concentration, and current news impact.",
    )

    if holdings.empty:
        st.info("No holdings yet. Add transactions or import positions to activate the portfolio dashboard.")
        render_chart_card("Portfolio Performance", "Performance chart appears after snapshots are saved.")
        render_portfolio_performance_chart(snapshot_df)
        close_chart_card()
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
        portfolio_news = build_portfolio_news_monitor(user_id=user_id, holdings=holdings, watchlist=watchlist)
        impact_summary = build_portfolio_impact_summary(
            impact_rows=list(portfolio_news.get("impact_rows", [])),
            macro_events=list(portfolio_news.get("macro_events", [])),
        )
    except Exception as exc:
        portfolio_news = {"impact_rows": [], "macro_events": [], "exposure_map": {}, "top_positive_tailwinds": [], "top_negative_headwinds": [], "portfolio_summary": {}, "source_errors": [str(exc)]}
        impact_summary = {"summary_text": "Portfolio impact summary is unavailable right now."}

    try:
        news_risk = scan_portfolio_news_risk(holdings, top_n=5)
    except Exception:
        news_risk = {"overall_risk_level": "low", "alerts": []}

    kpi_columns = create_columns(4)
    kpi_data = [
        ("Portfolio Value", f"Rs {float(summary.get('portfolio_value', 0.0)):,.2f}", None),
        ("Total P&L", f"Rs {float(summary.get('unrealized_pnl', 0.0)):,.2f}", f"{float(summary.get('total_return_pct', 0.0)):.2f}%"),
        ("Cash Balance", f"Rs {float(summary.get('cash_balance', 0.0)):,.2f}", None),
        ("Health Score", f"{float(portfolio_health['portfolio_score']):.1f}/10", "Diversification, quality, valuation, and risk"),
    ]
    for column, (title, value, change) in zip(kpi_columns, kpi_data):
        with column:
            render_kpi_card(title, value, change)

    render_spacer(2)
    render_chart_card("Portfolio Performance", "Portfolio value, invested amount, and net worth over time.")
    render_portfolio_performance_chart(snapshot_df)
    close_chart_card()

    render_spacer(2)
    left_column, right_column = create_columns([1.05, 0.95])
    with left_column:
        render_chart_card("Sector Allocation", "Current sector concentration across active holdings.")
        _render_sector_chart(intelligence)
        close_chart_card()
    with right_column:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        render_section_header("Risk Alerts", "Concentration, position-size, and news-risk indicators.")
        render_status_badge(f"News Risk: {str(news_risk.get('overall_risk_level', 'low')).title()}", "watch" if str(news_risk.get("overall_risk_level", "low")).lower() != "low" else "positive")
        for alert in list(intelligence.get("risk_warnings", []))[:5]:
            st.write(f"- {alert}")
        for alert in list(news_risk.get("alerts", []))[:5]:
            message = alert.get("message") if isinstance(alert, dict) else str(alert)
            st.write(f"- {message}")
        st.markdown("</div>", unsafe_allow_html=True)

    render_spacer(2)
    overview_left, overview_right = create_columns([1.15, 0.85])
    with overview_left:
        st.markdown('<div class="ui-table-card">', unsafe_allow_html=True)
        render_section_header("Holdings", "Active positions with portfolio analytics, suggestion labels, and risk states.")
        render_portfolio_holdings_table(holdings)
        st.markdown("</div>", unsafe_allow_html=True)
    with overview_right:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        render_section_header("Top Holdings", "Largest positions by current portfolio weight.")
        _render_top_holdings_table(intelligence)
        render_top_holdings_bar_chart(holdings)
        st.markdown("</div>", unsafe_allow_html=True)

    render_spacer(2)
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    render_portfolio_news_section(portfolio_news, impact_summary)
    st.markdown("</div>", unsafe_allow_html=True)

    render_spacer(2)
    geo_col, summary_col = create_columns([1.1, 0.9])
    with geo_col:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        render_geopolitical_risk_section(portfolio_news, impact_summary)
        st.markdown("</div>", unsafe_allow_html=True)
    with summary_col:
        alerts_rows = [
            {"Ticker": row.get("ticker"), "Event": row.get("event_title"), "Severity": row.get("severity"), "Direction": row.get("impact_direction")}
            for row in list(portfolio_news.get("impact_rows", []))[:8]
        ]
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        render_news_alerts_dashboard(
            title="Current Alerts",
            alerts=alerts_rows,
            caption="Portfolio-impacting company, sector, and macro events from the latest scan.",
            empty_message="No active alerts were generated for the latest portfolio scan.",
        )
        st.markdown("</div>", unsafe_allow_html=True)
