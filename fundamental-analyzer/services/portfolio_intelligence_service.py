"""Portfolio intelligence summary service."""

from __future__ import annotations

from typing import Any

import pandas as pd

from services.portfolio_health_service import (
    calculate_position_weights as _calculate_position_weights,
    calculate_sector_allocation as _calculate_sector_allocation,
    detect_concentration_risk as _detect_concentration_risk,
)


def _safe_float(value: Any) -> float | None:
    """Convert a value to ``float`` when possible."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_position_weights(holdings: pd.DataFrame) -> pd.DataFrame:
    """Return position weights for the current holdings."""
    return _calculate_position_weights(holdings)


def calculate_sector_allocation(
    holdings: pd.DataFrame,
    sector_mapping: dict[str, str] | None = None,
) -> dict[str, float]:
    """Return sector allocation percentages."""
    return _calculate_sector_allocation(holdings, sector_mapping=sector_mapping)


def detect_concentration_risk(holdings: pd.DataFrame) -> list[str]:
    """Return position and sector concentration warnings."""
    return _detect_concentration_risk(holdings)


def _calculate_asset_allocation(holdings: pd.DataFrame, cash_balance: float = 0.0) -> dict[str, float]:
    """Calculate basic asset allocation across equity and cash."""
    equity_value = float(pd.to_numeric(holdings.get("Current Value"), errors="coerce").fillna(0.0).sum()) if not holdings.empty and "Current Value" in holdings.columns else 0.0
    total_value = equity_value + float(cash_balance)
    if total_value <= 0:
        return {"Equity": 0.0, "Cash": 0.0}
    return {
        "Equity": round((equity_value / total_value) * 100, 2),
        "Cash": round((float(cash_balance) / total_value) * 100, 2),
    }


def _summarize_top_holdings(holdings: pd.DataFrame) -> list[dict[str, object]]:
    """Return the top holdings by weight."""
    weights = calculate_position_weights(holdings)
    if weights.empty:
        return []
    return [
        {
            "ticker": str(row.ticker),
            "company_name": str(row.company_name),
            "weight": round(float(row.weight), 4),
            "weight_pct": round(float(row.weight) * 100, 2),
            "position_value": round(float(row.position_value), 2),
        }
        for row in weights.head(5).itertuples(index=False)
    ]


def _position_size_warnings(holdings: pd.DataFrame) -> list[str]:
    """Return warnings for large single-stock weights."""
    warnings: list[str] = []
    weights = calculate_position_weights(holdings)
    for row in weights.itertuples(index=False):
        weight_pct = float(row.weight) * 100
        if weight_pct >= 15:
            warnings.append(f"{row.ticker} is a large position at {weight_pct:.1f}% of the portfolio.")
    return warnings


def _risk_warnings(holdings: pd.DataFrame) -> list[str]:
    """Build deterministic portfolio risk warnings."""
    warnings = detect_concentration_risk(holdings)
    warnings.extend(_position_size_warnings(holdings))

    if not holdings.empty and "Risk" in holdings.columns and "Ticker" in holdings.columns:
        frame = holdings.copy()
        for row in frame.itertuples(index=False):
            risk_level = str(getattr(row, "Risk", "") or "")
            ticker = str(getattr(row, "Ticker", "") or "")
            if risk_level == "High":
                warnings.append(f"{ticker} is marked as high risk by the company analysis engine.")
        red_flag_frame = frame.copy()
        if "Red Flags" in red_flag_frame.columns:
            red_flags = pd.to_numeric(red_flag_frame["Red Flags"], errors="coerce").fillna(0.0)
            for ticker, red_flag_count in zip(red_flag_frame["Ticker"], red_flags):
                if red_flag_count >= 2:
                    warnings.append(f"{ticker} has {int(red_flag_count)} red flags and needs closer review.")

    seen: set[str] = set()
    deduplicated: list[str] = []
    for warning in warnings:
        if warning not in seen:
            seen.add(warning)
            deduplicated.append(warning)
    return deduplicated


def _portfolio_summary(holdings: pd.DataFrame) -> dict[str, float]:
    """Build core portfolio summary numbers from holdings."""
    invested = float(pd.to_numeric(holdings.get("Invested"), errors="coerce").fillna(0.0).sum()) if not holdings.empty and "Invested" in holdings.columns else 0.0
    current_value = float(pd.to_numeric(holdings.get("Current Value"), errors="coerce").fillna(0.0).sum()) if not holdings.empty and "Current Value" in holdings.columns else 0.0
    unrealized_pnl = float(pd.to_numeric(holdings.get("Unrealized P&L"), errors="coerce").fillna(0.0).sum()) if not holdings.empty and "Unrealized P&L" in holdings.columns else current_value - invested
    return_pct = (unrealized_pnl / invested * 100) if invested else 0.0
    return {
        "total_invested": round(invested, 2),
        "current_value": round(current_value, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "return_pct": round(return_pct, 2),
    }


def build_portfolio_intelligence(
    user_id: int,
    holdings: pd.DataFrame,
    transaction_history: pd.DataFrame,
    sector_mapping: dict[str, str] | None = None,
    cash_balance: float = 0.0,
) -> dict[str, object]:
    """Build a portfolio intelligence payload from holdings and transactions."""
    del user_id
    del transaction_history

    summary = _portfolio_summary(holdings)
    top_holdings = _summarize_top_holdings(holdings)
    sector_allocation = calculate_sector_allocation(holdings, sector_mapping=sector_mapping)
    asset_allocation = _calculate_asset_allocation(holdings, cash_balance=cash_balance)
    risk_warnings = _risk_warnings(holdings)

    return {
        "portfolio_summary": summary,
        "top_holdings": top_holdings,
        "sector_allocation": sector_allocation,
        "asset_allocation": asset_allocation,
        "risk_warnings": risk_warnings,
        "position_weights": calculate_position_weights(holdings).to_dict(orient="records"),
        "portfolio_beta": None,
        "portfolio_volatility": None,
    }
