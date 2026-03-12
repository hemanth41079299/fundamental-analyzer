"""Holdings calculation services using average-cost accounting."""

from __future__ import annotations

from io import StringIO
import json
import re
from typing import Any

import pandas as pd

from services.auth_service import require_current_user_id
from core.analysis_engine import build_analysis
from core.classifier import classify_market_cap
from models.company_data import CompanyData
from services.db import get_connection
from services.portfolio_service import web_payload_to_company_data
from services.rule_service import RuleService
from services.web_data_service import fetch_company_data

_IMPORT_META_PATTERN = re.compile(r"\[import_meta\](\{.*\})")


def get_transactions_frame() -> pd.DataFrame:
    """Return transactions ordered for holdings calculations."""
    user_id = require_current_user_id()
    with get_connection() as connection:
        frame = pd.read_sql_query(
            "SELECT * FROM transactions WHERE user_id = %s ORDER BY date ASC, id ASC",
            connection,
            params=(user_id,),
        )
    return frame


def _compute_position_rows(transactions: pd.DataFrame) -> list[dict[str, object]]:
    """Compute average-cost holdings from transactions."""
    positions: dict[str, dict[str, float | str]] = {}

    for _, row in transactions.iterrows():
        ticker = str(row["ticker"]).strip().upper()
        company_name = str(row["company_name"]).strip()
        transaction_type = str(row["transaction_type"]).strip().upper()
        quantity = float(row["quantity"])
        price = float(row["price"])
        charges = float(row["charges"])

        state = positions.setdefault(
            ticker,
            {
                "ticker": ticker,
                "company_name": company_name,
                "net_quantity": 0.0,
                "cost_basis": 0.0,
                "realized_pnl": 0.0,
                "total_bought_quantity": 0.0,
                "total_sold_quantity": 0.0,
                "imported_ltp": None,
                "imported_present_value": None,
            },
        )
        state["company_name"] = company_name or state["company_name"]

        if transaction_type == "BUY":
            total_cost = (quantity * price) + charges
            state["net_quantity"] += quantity
            state["cost_basis"] += total_cost
            state["total_bought_quantity"] += quantity
            metadata = _extract_import_metadata(row.get("notes"))
            if metadata.get("imported_ltp") is not None:
                state["imported_ltp"] = metadata["imported_ltp"]
            if metadata.get("imported_present_value") is not None:
                state["imported_present_value"] = metadata["imported_present_value"]
        elif transaction_type == "SELL":
            net_quantity = float(state["net_quantity"])
            average_cost = (float(state["cost_basis"]) / net_quantity) if net_quantity > 0 else 0.0
            sell_proceeds = (quantity * price) - charges
            realized_pnl = sell_proceeds - (average_cost * quantity)
            state["realized_pnl"] += realized_pnl
            state["net_quantity"] -= quantity
            state["cost_basis"] -= average_cost * quantity
            state["total_sold_quantity"] += quantity

            if float(state["net_quantity"]) <= 0:
                state["net_quantity"] = 0.0
                state["cost_basis"] = 0.0

    rows: list[dict[str, object]] = []
    for state in positions.values():
        if float(state["net_quantity"]) <= 0:
            continue
        average_buy_price = float(state["cost_basis"]) / float(state["net_quantity"])
        rows.append(
            {
                "Ticker": state["ticker"],
                "Company": state["company_name"],
                "Qty": round(float(state["net_quantity"]), 4),
                "Avg Buy": round(average_buy_price, 2),
                "Invested": round(float(state["cost_basis"]), 2),
                "Realized P&L": round(float(state["realized_pnl"]), 2),
                "Total Bought Qty": round(float(state["total_bought_quantity"]), 4),
                "Total Sold Qty": round(float(state["total_sold_quantity"]), 4),
                "Imported LTP": _safe_float(state.get("imported_ltp")),
                "Imported Present Value": _safe_float(state.get("imported_present_value")),
            }
        )
    return rows


def _extract_import_metadata(notes: object) -> dict[str, float | None]:
    """Extract structured import metadata from transaction notes."""
    if notes is None:
        return {}
    match = _IMPORT_META_PATTERN.search(str(notes))
    if match is None:
        return {}
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    return {
        "imported_ltp": _safe_float(payload.get("imported_ltp")),
        "imported_present_value": _safe_float(payload.get("imported_present_value")),
    }


def _safe_float(value: Any) -> float | None:
    """Convert a value to float when possible."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _enrich_holding_row(base_row: dict[str, object], rule_service: RuleService) -> dict[str, object]:
    """Add market price, valuation, and analysis metadata to one holding row."""
    ticker = str(base_row["Ticker"])
    try:
        payload = fetch_company_data(ticker)
    except Exception:
        payload = {}

    imported_ltp = _safe_float(base_row.get("Imported LTP"))
    imported_present_value = _safe_float(base_row.get("Imported Present Value"))
    current_price = _safe_float(payload.get("current_price"))
    if current_price is None:
        current_price = imported_ltp
    current_value = round(float(base_row["Qty"]) * current_price, 2) if current_price is not None else None
    if current_value is None:
        current_value = imported_present_value
    unrealized_pnl = round(current_value - float(base_row["Invested"]), 2) if current_value is not None else None
    return_pct = round((unrealized_pnl / float(base_row["Invested"])) * 100, 2) if unrealized_pnl is not None and float(base_row["Invested"]) != 0 else None

    category = "Unknown"
    score = None
    suggestion = None
    risk_level = None
    red_flag_count = None
    valuation_summary = None
    earnings_quality_summary = None
    thesis_summary = None
    sector = payload.get("sector") if isinstance(payload.get("sector"), str) else "Unknown"

    if payload:
        company_data = web_payload_to_company_data(payload, source_file=f"portfolio:{ticker}")
        category_key = classify_market_cap(company_data.market_cap_cr)
        category = category_key.replace("_", " ").title()
        rules = rule_service.get_rules(category_key)
        analysis = build_analysis(company_data, category_key, rules)
        score = analysis.scorecard.total_score
        suggestion = analysis.suggestion.label
        risk_level = analysis.risk_scan.overall_risk_level
        red_flag_count = analysis.red_flags.red_flag_count
        valuation_summary = analysis.intrinsic_value.valuation_summary
        earnings_quality_summary = analysis.earnings_quality.summary
        thesis_summary = analysis.thesis.final_verdict
        if not base_row["Company"]:
            base_row["Company"] = company_data.company_name

    return {
        **base_row,
        "LTP": current_price,
        "Current Value": current_value,
        "Unrealized P&L": unrealized_pnl,
        "Return %": return_pct,
        "Imported LTP": imported_ltp,
        "Score": score,
        "Suggestion": suggestion,
        "Risk": risk_level,
        "Red Flags": red_flag_count,
        "Valuation Summary": valuation_summary,
        "Earnings Quality Summary": earnings_quality_summary,
        "Thesis Summary": thesis_summary,
        "Category": category,
        "Sector": sector or "Unknown",
    }


def calculate_holdings() -> pd.DataFrame:
    """Calculate current holdings using average-cost method."""
    transactions = get_transactions_frame()
    if transactions.empty:
        return pd.DataFrame(
            columns=[
                "Ticker",
                "Company",
                "Qty",
                "Avg Buy",
                "LTP",
                "Invested",
                "Current Value",
                "Unrealized P&L",
                "Realized P&L",
                "Return %",
                "Imported LTP",
                "Score",
                "Suggestion",
                "Risk",
                "Red Flags",
                "Valuation Summary",
                "Earnings Quality Summary",
                "Thesis Summary",
                "Category",
                "Sector",
            ]
        )

    rows = _compute_position_rows(transactions)
    rule_service = RuleService()
    enriched_rows = [_enrich_holding_row(row, rule_service) for row in rows]
    return pd.DataFrame(enriched_rows)


def get_total_realized_pnl() -> float:
    """Calculate total realized P&L from all transactions."""
    transactions = get_transactions_frame()
    position_state: dict[str, dict[str, float]] = {}
    realized = 0.0
    for _, row in transactions.iterrows():
        ticker = str(row["ticker"]).strip().upper()
        quantity = float(row["quantity"])
        price = float(row["price"])
        charges = float(row["charges"])
        state = position_state.setdefault(ticker, {"qty": 0.0, "cost_basis": 0.0})
        if row["transaction_type"] == "BUY":
            state["qty"] += quantity
            state["cost_basis"] += (quantity * price) + charges
        else:
            avg_cost = (state["cost_basis"] / state["qty"]) if state["qty"] > 0 else 0.0
            realized += ((quantity * price) - charges) - (avg_cost * quantity)
            state["qty"] -= quantity
            state["cost_basis"] -= avg_cost * quantity
            if state["qty"] <= 0:
                state["qty"] = 0.0
                state["cost_basis"] = 0.0
    return round(realized, 2)


def build_portfolio_summary(holdings: pd.DataFrame, cash_balance: float) -> dict[str, float]:
    """Build top-level portfolio metrics."""
    realized_pnl = get_total_realized_pnl()
    if holdings.empty:
        return {
            "invested_amount": 0.0,
            "portfolio_value": 0.0,
            "unrealized_pnl": 0.0,
            "realized_pnl": round(realized_pnl, 2),
            "total_return_pct": 0.0,
            "cash_balance": round(cash_balance, 2),
            "total_net_worth": round(cash_balance, 2),
        }

    invested_amount = float(holdings["Invested"].fillna(0).sum())
    portfolio_value = float(holdings["Current Value"].fillna(0).sum())
    unrealized_pnl = float(holdings["Unrealized P&L"].fillna(0).sum())
    total_return_pct = ((portfolio_value - invested_amount) / invested_amount * 100) if invested_amount else 0.0
    total_net_worth = portfolio_value + cash_balance

    return {
        "invested_amount": round(invested_amount, 2),
        "portfolio_value": round(portfolio_value, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "realized_pnl": round(realized_pnl, 2),
        "total_return_pct": round(total_return_pct, 2),
        "cash_balance": round(cash_balance, 2),
        "total_net_worth": round(total_net_worth, 2),
    }


def export_holdings_csv(holdings: pd.DataFrame) -> str:
    """Export holdings as CSV text."""
    buffer = StringIO()
    holdings.to_csv(buffer, index=False)
    return buffer.getvalue()
