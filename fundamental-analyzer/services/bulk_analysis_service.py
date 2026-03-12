"""Bulk analysis service for Screener-style CSV uploads."""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.analysis_engine import build_analysis
from core.classifier import classify_market_cap
from models.company_data import CompanyData
from services.rule_service import RuleService


def _safe_float(value: Any) -> float | None:
    """Convert CSV cell values to floats when possible."""
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in {"", "na", "n/a", "-", "--"}:
            return None
        cleaned = cleaned.replace(",", "").replace("%", "").replace("x", "")
        value = cleaned
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize CSV column names for flexible mapping."""
    normalized = {
        column: column.strip().lower().replace("%", "").replace("_", " ")
        for column in frame.columns
    }
    return frame.rename(columns=normalized)


def _get_value(row: pd.Series, aliases: list[str]) -> Any:
    """Return the first available value for a set of column aliases."""
    for alias in aliases:
        if alias in row.index:
            return row[alias]
    return None


def _row_to_company_data(row: pd.Series) -> CompanyData:
    """Convert a Screener CSV row into the internal CompanyData model."""
    company_name = _get_value(row, ["name", "company", "company name"])
    market_cap_cr = _safe_float(_get_value(row, ["market cap", "market capitalization", "mcap"]))
    stock_pe = _safe_float(_get_value(row, ["pe", "stock pe", "p/e"]))
    roe = _safe_float(_get_value(row, ["roe", "return on equity"]))
    roce = _safe_float(_get_value(row, ["roce", "return on capital employed"]))
    opm = _safe_float(_get_value(row, ["opm", "operating profit margin"]))
    sales_growth_5y = _safe_float(_get_value(row, ["sales growth", "sales growth 5y", "sales growth 5 years"]))
    profit_growth_5y = _safe_float(_get_value(row, ["profit growth", "profit growth 5y", "profit growth 5 years"]))
    debt_to_equity = _safe_float(_get_value(row, ["debt to equity", "debt/equity", "debt equity", "debt"]))
    book_value = _safe_float(_get_value(row, ["book value", "book value/share"]))
    current_price = _safe_float(_get_value(row, ["current price", "cmp", "price"]))
    promoter_holding = _safe_float(_get_value(row, ["promoter holding", "promoters holding"]))
    pledge = _safe_float(_get_value(row, ["pledge", "promoter pledge"]))
    peg_ratio = _safe_float(_get_value(row, ["peg", "peg ratio"]))

    return CompanyData(
        company_name=str(company_name).strip() if company_name is not None else None,
        market_cap_cr=market_cap_cr,
        current_price=current_price,
        stock_pe=stock_pe,
        book_value=book_value,
        roce=roce,
        roe=roe,
        sales_growth_5y=sales_growth_5y,
        profit_growth_5y=profit_growth_5y,
        opm=opm,
        debt_to_equity=debt_to_equity,
        peg_ratio=peg_ratio,
        promoter_holding=promoter_holding,
        pledge=pledge,
        source_file="bulk_csv",
    )


def analyze_bulk_companies(csv_file) -> pd.DataFrame:
    """Analyze multiple companies from a Screener export CSV."""
    try:
        raw_df = pd.read_csv(csv_file)
    except Exception as exc:
        raise ValueError("Unable to read bulk company CSV.") from exc

    if raw_df.empty:
        raise ValueError("Bulk company CSV is empty.")

    frame = _normalize_columns(raw_df)
    if "name" not in frame.columns and "company" not in frame.columns and "company name" not in frame.columns:
        raise ValueError("Bulk company CSV must include a company name column.")

    rule_service = RuleService()
    records: list[dict[str, object]] = []

    for _, row in frame.iterrows():
        company_data = _row_to_company_data(row)
        if not company_data.company_name:
            continue

        category = classify_market_cap(company_data.market_cap_cr)
        rules = rule_service.get_rules(category)
        analysis = build_analysis(company_data, category, rules)

        records.append(
            {
                "Company": company_data.company_name,
                "Score": analysis.scorecard.total_score,
                "Verdict": analysis.final_verdict,
                "Category": category.replace("_", " ").title(),
            }
        )

    if not records:
        raise ValueError("No valid company rows found in the bulk company CSV.")

    return pd.DataFrame(records).sort_values(by="Score", ascending=False, na_position="last").reset_index(drop=True)
