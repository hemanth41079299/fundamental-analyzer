"""Web data fetch service for company fundamentals using yfinance."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

import pandas as pd

TICKER_SANITIZE_PATTERN = re.compile(r"[\s\u00A0\u200B-\u200D\uFEFF]+")


def _normalize_symbol(symbol: str) -> str:
    """Normalize ticker input, including mobile-copy whitespace artifacts."""
    cleaned = TICKER_SANITIZE_PATTERN.sub("", symbol or "")
    return cleaned.strip().upper()


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


def _to_crore(value: float | None) -> float | None:
    """Convert a rupee market cap value to crore."""
    if value is None:
        return None
    return value / 10_000_000


def _extract_series_value(frame: pd.DataFrame | None, candidates: list[str]) -> float | None:
    """Extract the latest non-null row value from a financial statement frame."""
    if frame is None or frame.empty:
        return None

    for label in candidates:
        if label not in frame.index:
            continue
        series = frame.loc[label]
        if isinstance(series, pd.Series):
            for value in series.tolist():
                parsed = _safe_float(value)
                if parsed is not None:
                    return parsed
        else:
            parsed = _safe_float(series)
            if parsed is not None:
                return parsed
    return None


def _calculate_cagr(values: list[float]) -> float | None:
    """Calculate CAGR percentage from oldest to newest positive values."""
    cleaned = [value for value in values if value is not None and value > 0]
    if len(cleaned) < 2:
        return None

    start_value = cleaned[-1]
    end_value = cleaned[0]
    periods = len(cleaned) - 1
    if start_value <= 0 or periods <= 0:
        return None

    growth = ((end_value / start_value) ** (1 / periods) - 1) * 100
    return round(growth, 2)


def _extract_growth_metric(frame: pd.DataFrame | None, candidates: list[str]) -> float | None:
    """Extract a CAGR-like growth metric from annual statements."""
    if frame is None or frame.empty:
        return None

    for label in candidates:
        if label not in frame.index:
            continue
        series = frame.loc[label]
        if not isinstance(series, pd.Series):
            continue
        numeric_values = [_safe_float(value) for value in series.tolist()]
        growth = _calculate_cagr(numeric_values)
        if growth is not None:
            return growth
    return None


def _extract_roce(info: Mapping[str, Any], balance_sheet: pd.DataFrame | None, income_stmt: pd.DataFrame | None) -> float | None:
    """Approximate ROCE from available statement data."""
    ebit = _extract_series_value(income_stmt, ["EBIT", "Operating Income", "Pretax Income"])
    total_assets = _extract_series_value(balance_sheet, ["Total Assets"])
    current_liabilities = _extract_series_value(
        balance_sheet,
        ["Current Liabilities", "Total Current Liabilities"],
    )
    if ebit is None or total_assets is None or current_liabilities is None:
        return None

    capital_employed = total_assets - current_liabilities
    if capital_employed <= 0:
        return None
    return round((ebit / capital_employed) * 100, 2)


def _extract_promoter_holding(info: Mapping[str, Any]) -> float | None:
    """Map available insider holding data to promoter holding percentage."""
    for key in ["heldPercentInsiders", "insiderPercentHeld", "sharesPercentSharesOut"]:
        value = _safe_float(info.get(key))
        if value is not None:
            if value <= 1:
                return round(value * 100, 2)
            return round(value, 2)
    return None


def _extract_company_name(info: Mapping[str, Any], symbol: str) -> str:
    """Resolve a company name with fallback to the input symbol."""
    for key in ["longName", "shortName", "displayName"]:
        value = info.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return symbol.upper().strip()


def _year_labels(frame: pd.DataFrame | None) -> list[str]:
    """Return ordered year labels from a statement frame, oldest to newest."""
    if frame is None or frame.empty:
        return []

    labels: list[str] = []
    for column in reversed(list(frame.columns)):
        if hasattr(column, "year"):
            labels.append(str(column.year))
        else:
            labels.append(str(column))
    return labels


def _series_for_candidates(frame: pd.DataFrame | None, candidates: list[str]) -> list[float | None]:
    """Return a numeric series for the first matching statement row."""
    if frame is None or frame.empty:
        return []

    for label in candidates:
        if label not in frame.index:
            continue
        series = frame.loc[label]
        if isinstance(series, pd.Series):
            return [_safe_float(value) for value in reversed(series.tolist())]
    return []


def _pair_years_and_values(years: list[str], values: list[float | None]) -> list[dict[str, float | str]]:
    """Pair year labels and values, skipping null values."""
    return [
        {"year": year, "value": float(value)}
        for year, value in zip(years, values)
        if value is not None
    ]


def _build_ratio_trend(
    years: list[str],
    numerator_values: list[float | None],
    denominator_values: list[float | None],
    multiplier: float = 100.0,
) -> list[dict[str, float | str]]:
    """Build a ratio trend from aligned numerator and denominator series."""
    records: list[dict[str, float | str]] = []
    for year, numerator, denominator in zip(years, numerator_values, denominator_values):
        if numerator is None or denominator in {None, 0}:
            continue
        records.append({"year": year, "value": round((numerator / denominator) * multiplier, 2)})
    return records


def _build_financial_trends(income_stmt: pd.DataFrame | None, balance_sheet: pd.DataFrame | None) -> dict[str, list[dict[str, float | str]]]:
    """Build chart-ready annual trend data from available statement history."""
    years = _year_labels(income_stmt if income_stmt is not None and not income_stmt.empty else balance_sheet)

    revenue_values = _series_for_candidates(income_stmt, ["Total Revenue", "Revenue", "Operating Revenue"])
    profit_values = _series_for_candidates(
        income_stmt,
        ["Net Income", "Net Income Common Stockholders", "Normalized Income"],
    )
    operating_income_values = _series_for_candidates(income_stmt, ["Operating Income", "EBIT"])
    equity_values = _series_for_candidates(
        balance_sheet,
        ["Stockholders Equity", "Total Equity Gross Minority Interest", "Common Stock Equity"],
    )
    total_debt_values = _series_for_candidates(
        balance_sheet,
        ["Total Debt", "Long Term Debt And Capital Lease Obligation", "Long Term Debt"],
    )

    trends = {
        "revenue": _pair_years_and_values(years, revenue_values),
        "profit": _pair_years_and_values(years, profit_values),
        "roe": _build_ratio_trend(years, profit_values, equity_values),
        "margin": _build_ratio_trend(years, operating_income_values, revenue_values),
        "debt": _build_ratio_trend(years, total_debt_values, equity_values, multiplier=1.0),
    }
    return trends


def _extract_latest_cashflow_value(cashflow: pd.DataFrame | None, candidates: list[str]) -> float | None:
    """Extract the latest non-null value from the cashflow statement."""
    return _extract_series_value(cashflow, candidates)


def fetch_company_data(symbol: str) -> dict[str, float | str | None]:
    """Fetch company fundamentals from yfinance.

    The function returns a normalized dictionary that can be mapped into the
    existing ``CompanyData`` model. Missing metrics are returned as ``None``.
    """
    cleaned_symbol = _normalize_symbol(symbol)
    if not cleaned_symbol:
        raise ValueError("Ticker is required.")

    try:
        import yfinance as yf
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on local env
        raise ValueError("yfinance is not installed. Run: pip install yfinance") from exc

    ticker = yf.Ticker(cleaned_symbol)
    network_errors: list[str] = []

    info: Mapping[str, Any] = {}
    fast_info: Mapping[str, Any] = {}
    income_stmt: pd.DataFrame | None = None
    balance_sheet: pd.DataFrame | None = None
    cashflow: pd.DataFrame | None = None
    history: pd.DataFrame | None = None

    try:
        info = ticker.get_info() or {}
    except Exception as exc:
        network_errors.append(str(exc))
        try:
            info = ticker.info or {}
        except Exception as inner_exc:
            network_errors.append(str(inner_exc))
            info = {}

    try:
        fast_info = dict(ticker.fast_info) if ticker.fast_info else {}
    except Exception as exc:
        network_errors.append(str(exc))
        fast_info = {}

    try:
        income_stmt = ticker.income_stmt
    except Exception as exc:
        network_errors.append(str(exc))
        income_stmt = None

    try:
        balance_sheet = ticker.balance_sheet
    except Exception as exc:
        network_errors.append(str(exc))
        balance_sheet = None

    try:
        cashflow = ticker.cashflow
    except Exception as exc:
        network_errors.append(str(exc))
        cashflow = None

    try:
        history = ticker.history(period="5d", auto_adjust=False)
    except Exception as exc:
        network_errors.append(str(exc))
        history = None

    if not info and not fast_info and (history is None or history.empty):
        combined_errors = " | ".join(network_errors).lower()
        if "could not resolve host" in combined_errors or "curl: (6)" in combined_errors:
            raise ValueError(
                "Yahoo Finance is not reachable from the app environment right now. "
                "This is a network/DNS issue, not an invalid ticker."
            )
        raise ValueError(f"Unable to fetch web data for ticker: {cleaned_symbol}")

    current_price = (
        _safe_float(info.get("currentPrice"))
        or _safe_float(info.get("regularMarketPrice"))
        or _safe_float(fast_info.get("lastPrice"))
        or _safe_float(fast_info.get("regularMarketPrice"))
    )
    if current_price is None and history is not None and not history.empty and "Close" in history.columns:
        current_price = _safe_float(history["Close"].dropna().iloc[-1]) if not history["Close"].dropna().empty else None

    market_cap = _safe_float(info.get("marketCap")) or _safe_float(fast_info.get("marketCap"))
    pe = _safe_float(info.get("trailingPE")) or _safe_float(info.get("forwardPE"))
    pb = _safe_float(info.get("priceToBook"))
    roe = _safe_float(info.get("returnOnEquity"))
    if roe is not None and roe <= 1:
        roe = round(roe * 100, 2)
    elif roe is not None:
        roe = round(roe, 2)

    opm = _safe_float(info.get("operatingMargins"))
    if opm is not None and opm <= 1:
        opm = round(opm * 100, 2)
    elif opm is not None:
        opm = round(opm, 2)

    debt_to_equity = _safe_float(info.get("debtToEquity"))
    if debt_to_equity is not None and debt_to_equity > 10:
        debt_to_equity = round(debt_to_equity / 100, 2)

    net_profit = _extract_series_value(
        income_stmt,
        ["Net Income", "Net Income Common Stockholders", "Normalized Income"],
    )
    depreciation = _extract_latest_cashflow_value(
        cashflow,
        ["Depreciation And Amortization", "Depreciation", "Depreciation Amortization Depletion"],
    )
    capex_raw = _extract_latest_cashflow_value(
        cashflow,
        ["Capital Expenditure", "Capital Expenditures"],
    )
    capex = abs(capex_raw) if capex_raw is not None else None
    cfo_growth_5y = _extract_growth_metric(
        cashflow,
        ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities", "Cash From Operations"],
    )
    receivables_growth_5y = _extract_growth_metric(
        balance_sheet,
        ["Accounts Receivable", "Receivables", "Net Receivables"],
    )

    result: dict[str, float | str | None] = {
        "company_name": _extract_company_name(info, cleaned_symbol),
        "sector": info.get("sector") if isinstance(info.get("sector"), str) else None,
        "market_cap_cr": round(_to_crore(market_cap), 2) if _to_crore(market_cap) is not None else None,
        "current_price": current_price,
        "pe": pe,
        "pb": pb,
        "roe": roe,
        "roce": _extract_roce(info, balance_sheet, income_stmt),
        "sales_growth_5y": _extract_growth_metric(
            income_stmt,
            ["Total Revenue", "Revenue", "Operating Revenue"],
        ),
        "profit_growth_5y": _extract_growth_metric(
            income_stmt,
            ["Net Income", "Net Income Common Stockholders", "Normalized Income"],
        ),
        "opm": opm,
        "debt_to_equity": debt_to_equity,
        "promoter_holding": _extract_promoter_holding(info),
        "net_profit": net_profit,
        "depreciation": depreciation,
        "capex": capex,
        "cfo_growth_5y": cfo_growth_5y,
        "receivables_growth_5y": receivables_growth_5y,
        "financial_trends": _build_financial_trends(income_stmt, balance_sheet),
    }
    return result
