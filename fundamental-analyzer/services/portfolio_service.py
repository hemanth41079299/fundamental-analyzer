"""Portfolio analysis services for batch company evaluation."""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.analysis_engine import build_analysis
from core.classifier import classify_market_cap
from models.company_data import CompanyData
from services.rule_service import RuleService
from services.web_data_service import fetch_company_data


def _safe_float(value: Any) -> float | None:
    """Convert a raw value to float when possible."""
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


def _safe_str(value: Any) -> str | None:
    """Convert a raw value to a stripped string when possible."""
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None


def web_payload_to_company_data(payload: dict[str, Any], source_file: str | None = None) -> CompanyData:
    """Map a web data payload into the internal ``CompanyData`` model."""
    current_price = _safe_float(payload.get("current_price"))
    pb = _safe_float(payload.get("pb"))
    book_value: float | None = None
    if current_price is not None and pb not in {None, 0}:
        book_value = round(current_price / pb, 2)

    return CompanyData(
        company_name=_safe_str(payload.get("company_name")),
        market_cap_cr=_safe_float(payload.get("market_cap_cr")),
        current_price=current_price,
        stock_pe=_safe_float(payload.get("pe")),
        book_value=book_value,
        roce=_safe_float(payload.get("roce")),
        roe=_safe_float(payload.get("roe")),
        sales_growth_5y=_safe_float(payload.get("sales_growth_5y")),
        profit_growth_5y=_safe_float(payload.get("profit_growth_5y")),
        opm=_safe_float(payload.get("opm")),
        debt_to_equity=_safe_float(payload.get("debt_to_equity")),
        net_profit=_safe_float(payload.get("net_profit")),
        depreciation=_safe_float(payload.get("depreciation")),
        capex=_safe_float(payload.get("capex")),
        cfo_growth_5y=_safe_float(payload.get("cfo_growth_5y")),
        receivables_growth_5y=_safe_float(payload.get("receivables_growth_5y")),
        promoter_holding=_safe_float(payload.get("promoter_holding")),
        financial_trends=payload.get("financial_trends"),
        source_file=source_file or "web_search",
    )


def load_portfolio_csv(file) -> pd.DataFrame:
    """Load and validate a portfolio CSV file.

    Expected columns:
    - ``stock``
    - ``quantity``
    """
    try:
        portfolio_df = pd.read_csv(file)
    except Exception as exc:
        raise ValueError("Unable to read portfolio CSV.") from exc

    normalized_columns = {column: column.strip().lower() for column in portfolio_df.columns}
    portfolio_df = portfolio_df.rename(columns=normalized_columns)

    required_columns = {"stock", "quantity"}
    missing_columns = required_columns - set(portfolio_df.columns)
    if missing_columns:
        missing_text = ", ".join(sorted(missing_columns))
        raise ValueError(f"Portfolio CSV is missing required columns: {missing_text}")

    portfolio_df["stock"] = portfolio_df["stock"].astype(str).str.strip().str.upper()
    portfolio_df["quantity"] = pd.to_numeric(portfolio_df["quantity"], errors="coerce")
    portfolio_df = portfolio_df.dropna(subset=["stock", "quantity"])
    portfolio_df = portfolio_df[portfolio_df["stock"] != ""]
    if portfolio_df.empty:
        raise ValueError("Portfolio CSV does not contain any valid stock rows.")

    return portfolio_df[["stock", "quantity"]].reset_index(drop=True)


def analyze_portfolio(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    """Fetch web data and analyze each stock in the portfolio."""
    rule_service = RuleService()
    records: list[dict[str, object]] = []

    for row in portfolio_df.itertuples(index=False):
        stock = str(row.stock).strip().upper()
        quantity = _safe_float(getattr(row, "quantity", None))

        try:
            payload = fetch_company_data(stock)
            company_data = web_payload_to_company_data(payload, source_file=f"web:{stock}")
            category = classify_market_cap(company_data.market_cap_cr)
            rules = rule_service.get_rules(category)
            analysis = build_analysis(company_data, category, rules)

            records.append(
                {
                    "Stock": stock,
                    "Quantity": quantity,
                    "Company": company_data.company_name,
                    "Score": analysis.scorecard.total_score,
                    "Rating": analysis.score.interpretation,
                    "Suggestion Label": analysis.suggestion.label,
                    "Risk Level": analysis.risk_scan.overall_risk_level,
                    "Red Flags": analysis.red_flags.red_flag_count,
                    "Verdict": analysis.final_verdict,
                    "Category": category.replace("_", " ").title(),
                }
            )
        except Exception as exc:
            records.append(
                {
                    "Stock": stock,
                    "Quantity": quantity,
                    "Company": None,
                    "Score": None,
                    "Rating": "Error",
                    "Suggestion Label": "Unavailable",
                    "Risk Level": "Unknown",
                    "Red Flags": None,
                    "Verdict": str(exc),
                    "Category": "Unknown",
                }
            )

    return pd.DataFrame(records)
