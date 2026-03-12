"""Deterministic earnings quality analysis."""

from __future__ import annotations

from models.company_data import CompanyData
from models.result_model import EarningsQualitySummary


def _cash_conversion_ratio(company_data: CompanyData) -> float | None:
    """Calculate CFO divided by net profit when both are available."""
    cfo = company_data.cfo_last_year if company_data.cfo_last_year is not None else company_data.cfo_5y
    net_profit = company_data.net_profit
    if cfo is None or net_profit in {None, 0}:
        return None
    return round(cfo / net_profit, 2)


def _earnings_quality_label(cash_conversion_ratio: float | None) -> str:
    """Classify earnings quality from cash conversion."""
    if cash_conversion_ratio is None:
        return "Moderate"
    if cash_conversion_ratio > 1.0:
        return "Strong"
    if cash_conversion_ratio >= 0.8:
        return "Moderate"
    return "Weak"


def analyze_earnings_quality(company_data: CompanyData) -> EarningsQualitySummary:
    """Analyze whether reported profits are supported by cash generation."""
    flags: list[str] = []
    cash_conversion_ratio = _cash_conversion_ratio(company_data)
    earnings_quality = _earnings_quality_label(cash_conversion_ratio)

    profit_growth = company_data.profit_growth_5y
    cfo_growth = company_data.cfo_growth_5y
    if profit_growth is not None and cfo_growth is not None:
        if profit_growth > 0 and cfo_growth < 0:
            flags.append("Profit growth is not supported by cash flow growth.")

    receivables_growth = company_data.receivables_growth_5y
    revenue_growth = company_data.sales_growth_5y
    if receivables_growth is not None and revenue_growth is not None:
        if receivables_growth > revenue_growth:
            flags.append("Receivables are growing faster than revenue, indicating working-capital stress.")

    cfo = company_data.cfo_last_year if company_data.cfo_last_year is not None else company_data.cfo_5y
    if company_data.capex is not None and cfo is not None:
        if company_data.capex > cfo:
            flags.append("Capex is higher than operating cash flow, which may create cash pressure.")

    if cash_conversion_ratio is not None and cash_conversion_ratio < 0.8:
        flags.append("Cash conversion ratio is weak relative to reported profit.")

    if cash_conversion_ratio is None and not flags:
        summary = "Earnings quality could not be evaluated fully because cash flow or profit data is missing."
    elif earnings_quality == "Strong" and not flags:
        summary = "Earnings quality appears strong with consistent cash conversion."
    elif earnings_quality == "Weak" or len(flags) >= 2:
        summary = "Earnings quality appears weak because profit is not fully backed by cash flow."
    else:
        summary = "Earnings quality appears moderate, with some items requiring closer monitoring."

    return EarningsQualitySummary(
        cash_conversion_ratio=cash_conversion_ratio,
        earnings_quality=earnings_quality,
        flags=flags,
        summary=summary,
    )
