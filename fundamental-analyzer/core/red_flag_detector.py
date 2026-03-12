"""Deterministic financial red flag detection."""

from __future__ import annotations

from models.company_data import CompanyData
from models.result_model import RedFlagResult, RedFlagSummary


def _latest_trend_change(trend_points: list[dict[str, object]]) -> float | None:
    """Return the change between the last two trend values."""
    if len(trend_points) < 2:
        return None
    previous = trend_points[-2].get("value")
    current = trend_points[-1].get("value")
    if not isinstance(previous, (int, float)) or not isinstance(current, (int, float)):
        return None
    return float(current) - float(previous)


def _add_flag(red_flags: list[RedFlagResult], flag_type: str, severity: str, message: str) -> None:
    """Append a new red flag."""
    red_flags.append(RedFlagResult(type=flag_type, severity=severity, message=message))


def detect_red_flags(company_data: CompanyData) -> RedFlagSummary:
    """Detect suspicious financial patterns from available company metrics."""
    red_flags: list[RedFlagResult] = []

    receivables_growth = company_data.receivables_growth_5y
    revenue_growth = company_data.sales_growth_5y
    if receivables_growth is not None and revenue_growth is not None and receivables_growth > revenue_growth:
        _add_flag(
            red_flags,
            "Receivable Risk",
            "Medium",
            "Receivables growing faster than revenue.",
        )

    margin_trend = (company_data.financial_trends or {}).get("margin", [])
    margin_change = _latest_trend_change(margin_trend)
    if margin_change is not None and margin_change > 5:
        _add_flag(
            red_flags,
            "Margin Spike Risk",
            "Medium",
            "Operating margin has risen sharply in the latest period and may not be sustainable.",
        )

    debt_trend = (company_data.financial_trends or {}).get("debt", [])
    debt_change = _latest_trend_change(debt_trend)
    if debt_change is not None and debt_change > 0.3:
        _add_flag(
            red_flags,
            "Debt Increase Risk",
            "High",
            "Debt to equity appears to be rising sharply.",
        )

    profit_growth = company_data.profit_growth_5y
    cfo_growth = company_data.cfo_growth_5y
    if profit_growth is not None and cfo_growth is not None and profit_growth > 0 and cfo_growth < 0:
        _add_flag(
            red_flags,
            "Cash Flow Divergence",
            "High",
            "Profit is rising while cash flow is falling.",
        )

    pledge = company_data.pledge
    if pledge is not None and pledge > 5:
        _add_flag(
            red_flags,
            "Promoter Pledge Risk",
            "High",
            "Promoter pledge is elevated and should be monitored closely.",
        )
    elif pledge is not None and pledge > 0:
        _add_flag(
            red_flags,
            "Promoter Pledge Risk",
            "Medium",
            "Promoter pledge is present and may indicate financing stress.",
        )

    if not red_flags:
        summary = "No major financial red flags detected."
    elif any(flag.severity == "High" for flag in red_flags):
        summary = "Several material financial red flags require closer review."
    else:
        summary = "Some financial red flags are present and should be monitored."

    return RedFlagSummary(
        red_flags=red_flags,
        red_flag_count=len(red_flags),
        summary=summary,
    )
