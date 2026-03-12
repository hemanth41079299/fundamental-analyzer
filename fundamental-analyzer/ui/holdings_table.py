"""Holdings table UI."""

from __future__ import annotations

import pandas as pd

from ui.design_system import render_section_header
from ui.portfolio_holdings_table import render_portfolio_holdings_table
from ui.ui_theme import apply_finance_theme


def render_holdings_table(holdings: pd.DataFrame) -> None:
    """Render the current holdings table."""
    apply_finance_theme()
    render_section_header("Holdings", "Live positions with P&L, research score, suggestion, and risk context.")
    render_portfolio_holdings_table(holdings)
