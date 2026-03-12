"""Backward-compatible KPI and insight components for the portfolio dashboard."""

from __future__ import annotations

from ui.design_system import render_insight_card as _render_insight_card
from ui.design_system import render_kpi_row as _render_kpi_row
from ui.ui_theme import apply_finance_theme


def inject_portfolio_dashboard_css() -> None:
    """Apply the shared finance theme."""
    apply_finance_theme()


def render_kpi_row(cards: list[dict[str, str | None]]) -> None:
    """Render a row of KPI cards."""
    _render_kpi_row(cards)


def render_insight_card(label: str, value: str, meta: str | None = None, tone: str = "neutral") -> None:
    """Render one compact insight card."""
    _render_insight_card(label=label, value=value, meta=meta, tone=tone)
