"""CSV holdings parser with normalized output columns."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

NORMALIZED_HOLDINGS_COLUMNS = [
    "ticker",
    "company_name",
    "quantity",
    "avg_buy",
    "buy_value",
    "ltp",
    "present_value",
    "pnl",
    "pnl_pct",
]

_COLUMN_ALIASES: dict[str, str] = {
    "ticker": "ticker",
    "symbol": "ticker",
    "stock": "ticker",
    "security": "ticker",
    "instrument": "ticker",
    "isin": "ticker",
    "company": "company_name",
    "company_name": "company_name",
    "name": "company_name",
    "stock_name": "company_name",
    "security_name": "company_name",
    "qty": "quantity",
    "quantity": "quantity",
    "shares": "quantity",
    "units": "quantity",
    "avg_buy": "avg_buy",
    "avg_cost": "avg_buy",
    "average_buy_price": "avg_buy",
    "average_price": "avg_buy",
    "buy_avg": "avg_buy",
    "cost_price": "avg_buy",
    "buy_price": "avg_buy",
    "buy_value": "buy_value",
    "invested": "buy_value",
    "invested_amount": "buy_value",
    "cost": "buy_value",
    "cost_value": "buy_value",
    "purchase_value": "buy_value",
    "ltp": "ltp",
    "cmp": "ltp",
    "price": "ltp",
    "current_price": "ltp",
    "market_price": "ltp",
    "last_traded_price": "ltp",
    "present_value": "present_value",
    "current_value": "present_value",
    "market_value": "present_value",
    "value": "present_value",
    "net_value": "present_value",
    "pnl": "pnl",
    "p_l": "pnl",
    "gain_loss": "pnl",
    "profit_loss": "pnl",
    "unrealized_pnl": "pnl",
    "pnl_pct": "pnl_pct",
    "return_pct": "pnl_pct",
    "gain_pct": "pnl_pct",
    "profit_pct": "pnl_pct",
    "return_percent": "pnl_pct",
    "pnl_percent": "pnl_pct",
}


def _canonicalize_column_name(column_name: object) -> str:
    """Convert a raw column name to a comparable key."""
    cleaned = re.sub(r"[^a-z0-9]+", "_", str(column_name).strip().lower())
    return cleaned.strip("_")


def _safe_string(value: Any) -> str | None:
    """Convert a value to a stripped string or ``None``."""
    if value is None or pd.isna(value):
        return None
    cleaned = str(value).strip()
    return cleaned or None


def safe_parse_number(value: Any) -> float | None:
    """Safely parse a numeric value from common finance-style strings."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    raw = str(value).strip()
    if not raw or raw.lower() in {"na", "n/a", "none", "-", "--"}:
        return None

    negative = False
    if raw.startswith("(") and raw.endswith(")"):
        negative = True
        raw = raw[1:-1].strip()

    raw = raw.replace(",", "").replace("%", "").replace("Rs.", "").replace("Rs", "").replace("INR", "").strip()
    raw = raw.replace("\u20b9", "").replace("+", "")

    match = re.search(r"-?\d+(?:\.\d+)?", raw)
    if match is None:
        return None

    number = float(match.group(0))
    return -number if negative else number


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Rename recognized columns to the normalized schema."""
    rename_map: dict[str, str] = {}
    for column in frame.columns:
        canonical = _canonicalize_column_name(column)
        if canonical in _COLUMN_ALIASES:
            rename_map[column] = _COLUMN_ALIASES[canonical]
    return frame.rename(columns=rename_map)


def normalize_holdings_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize a holdings dataframe to the standard column contract."""
    if frame.empty:
        return pd.DataFrame(columns=NORMALIZED_HOLDINGS_COLUMNS)

    normalized = _normalize_columns(frame.copy())
    result = pd.DataFrame(index=normalized.index)

    for column in NORMALIZED_HOLDINGS_COLUMNS:
        if column in normalized.columns:
            result[column] = normalized[column]
        else:
            result[column] = None

    if result["ticker"].isna().all() and result["company_name"].isna().all():
        raise ValueError("Unable to identify holdings columns. Include at least a ticker or company name column.")

    for text_column in ("ticker", "company_name"):
        result[text_column] = result[text_column].apply(_safe_string)

    result["ticker"] = result["ticker"].apply(lambda value: value.upper() if value else None)

    numeric_columns = [
        "quantity",
        "avg_buy",
        "buy_value",
        "ltp",
        "present_value",
        "pnl",
        "pnl_pct",
    ]
    for column in numeric_columns:
        result[column] = result[column].apply(safe_parse_number)

    missing_buy_value = result["buy_value"].isna() & result["quantity"].notna() & result["avg_buy"].notna()
    result.loc[missing_buy_value, "buy_value"] = result.loc[missing_buy_value, "quantity"] * result.loc[missing_buy_value, "avg_buy"]

    missing_present_value = result["present_value"].isna() & result["quantity"].notna() & result["ltp"].notna()
    result.loc[missing_present_value, "present_value"] = (
        result.loc[missing_present_value, "quantity"] * result.loc[missing_present_value, "ltp"]
    )

    missing_pnl = result["pnl"].isna() & result["present_value"].notna() & result["buy_value"].notna()
    result.loc[missing_pnl, "pnl"] = result.loc[missing_pnl, "present_value"] - result.loc[missing_pnl, "buy_value"]

    missing_pnl_pct = result["pnl_pct"].isna() & result["pnl"].notna() & result["buy_value"].notna() & (result["buy_value"] != 0)
    result.loc[missing_pnl_pct, "pnl_pct"] = (result.loc[missing_pnl_pct, "pnl"] / result.loc[missing_pnl_pct, "buy_value"]) * 100

    result = result.dropna(how="all", subset=["ticker", "company_name", "quantity", "avg_buy", "buy_value", "ltp", "present_value", "pnl", "pnl_pct"])
    return result.reset_index(drop=True)


def parse_holdings_csv(file) -> pd.DataFrame:
    """Read and normalize a CSV holdings file."""
    try:
        frame = pd.read_csv(file)
    except Exception as exc:
        raise ValueError("Unable to read the holdings CSV file.") from exc

    return normalize_holdings_frame(frame)
