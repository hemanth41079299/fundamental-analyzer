"""Portfolio news monitor that maps news events to holdings and watchlist names."""

from __future__ import annotations

from typing import Any

import pandas as pd

from services.geopolitical_impact_service import build_geopolitical_impact
from services.news_fetch_service import fetch_company_news, fetch_macro_news, fetch_sector_news
from services.news_impact_classifier import classify_news_item

_SEVERITY_RANK = {"Low": 1, "Moderate": 2, "High": 3}


def _sort_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Sort impact rows by severity and recency label."""
    return sorted(
        rows,
        key=lambda row: (
            -_SEVERITY_RANK.get(str(row.get("severity")), 0),
            str(row.get("event_date") or ""),
            str(row.get("ticker") or ""),
        ),
    )


def _deduplicate_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Deduplicate impact rows by ticker and event title."""
    deduplicated: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (
            str(row.get("ticker") or "").upper(),
            str(row.get("event_title") or "").lower(),
            str(row.get("event_type") or "").lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(row)
    return deduplicated


def _build_company_rows(holdings: pd.DataFrame, limit_per_holding: int = 3) -> tuple[list[dict[str, object]], list[str]]:
    """Fetch and classify company-specific news for holdings."""
    rows: list[dict[str, object]] = []
    errors: list[str] = []
    for row in holdings.itertuples(index=False):
        ticker = str(getattr(row, "Ticker", "") or "")
        company_name = str(getattr(row, "Company", "") or ticker)
        result = fetch_company_news(ticker=ticker, company_name=company_name, limit=limit_per_holding)
        errors.extend(list(result.get("errors", [])))
        for item in list(result.get("items", []))[:limit_per_holding]:
            classification = classify_news_item(item)
            rows.append(
                {
                    "ticker": ticker,
                    "company_name": company_name,
                    "event_title": item.get("title"),
                    "event_type": classification["event_type"],
                    "impact_direction": classification["impact_direction"],
                    "severity": classification["severity"],
                    "summary": item.get("snippet") or item.get("title"),
                    "source": item.get("source"),
                    "event_date": item.get("published_at"),
                    "why_it_matters": _build_monitoring_note(classification, company_name),
                }
            )
    return rows, errors


def _build_sector_rows(holdings: pd.DataFrame, limit_per_sector: int = 2) -> tuple[list[dict[str, object]], list[str]]:
    """Fetch and classify sector news and map it to matching holdings."""
    rows: list[dict[str, object]] = []
    errors: list[str] = []
    if "Sector" not in holdings.columns:
        return rows, errors

    sectors = [
        str(sector).strip()
        for sector in holdings["Sector"].dropna().tolist()
        if str(sector).strip() and str(sector).strip().lower() != "unknown"
    ]
    seen_sectors: set[str] = set()
    for sector in sectors:
        sector_key = sector.lower()
        if sector_key in seen_sectors:
            continue
        seen_sectors.add(sector_key)
        result = fetch_sector_news(sector, limit=limit_per_sector)
        errors.extend(list(result.get("errors", [])))
        matched_holdings = holdings[holdings["Sector"].astype(str).str.lower() == sector_key]
        for item in list(result.get("items", []))[:limit_per_sector]:
            classification = classify_news_item(item)
            for holding in matched_holdings.itertuples(index=False):
                company_name = str(getattr(holding, "Company", "") or getattr(holding, "Ticker", ""))
                rows.append(
                    {
                        "ticker": str(getattr(holding, "Ticker", "") or ""),
                        "company_name": company_name,
                        "event_title": item.get("title"),
                        "event_type": classification["event_type"],
                        "impact_direction": classification["impact_direction"],
                        "severity": classification["severity"],
                        "summary": item.get("snippet") or item.get("title"),
                        "source": item.get("source"),
                        "event_date": item.get("published_at"),
                        "why_it_matters": f"{sector} sector coverage may influence demand, regulation, or sentiment for {company_name}.",
                    }
                )
    return rows, errors


def _build_monitoring_note(classification: dict[str, str], company_name: str) -> str:
    """Convert one classification into a monitoring note."""
    theme = classification["theme"].replace("_", " ")
    direction = classification["impact_direction"]
    if direction == "Positive Tailwind":
        return f"Monitor whether {company_name} converts the {theme} signal into earnings or order-flow improvement."
    if direction == "Negative Headwind":
        return f"Monitor whether the {theme} signal changes earnings quality, sentiment, or execution for {company_name}."
    return f"Monitor the {theme} development for second-order effects on {company_name}."


def _flatten_macro_events(macro_events: list[dict[str, object]]) -> list[dict[str, object]]:
    """Flatten macro-event mappings into holding-level rows."""
    rows: list[dict[str, object]] = []
    for event in macro_events:
        for holding in list(event.get("affected_holdings", [])):
            rows.append(
                {
                    "ticker": holding.get("ticker"),
                    "company_name": holding.get("company_name"),
                    "event_title": event.get("event_title"),
                    "event_type": event.get("event_type"),
                    "impact_direction": holding.get("impact_direction"),
                    "severity": holding.get("severity"),
                    "summary": holding.get("reason"),
                    "source": event.get("source"),
                    "event_date": event.get("event_date"),
                    "why_it_matters": holding.get("reason"),
                }
            )
    return rows


def _build_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    """Build a simple portfolio-level summary from mapped rows."""
    positive_rows = [row for row in rows if row.get("impact_direction") == "Positive Tailwind"]
    negative_rows = [row for row in rows if row.get("impact_direction") == "Negative Headwind"]
    neutral_rows = [row for row in rows if row.get("impact_direction") == "Neutral / Monitor"]
    return {
        "impacted_holdings": len({str(row.get("ticker")) for row in rows if row.get("ticker")}),
        "positive_events": len(positive_rows),
        "negative_events": len(negative_rows),
        "monitor_events": len(neutral_rows),
    }


def build_portfolio_news_monitor(
    user_id: int,
    holdings: pd.DataFrame,
    watchlist: pd.DataFrame | None = None,
    recent_news_items: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Build holding-level and portfolio-level news impact output."""
    del user_id
    del watchlist

    if holdings.empty:
        return {
            "impact_rows": [],
            "portfolio_summary": {"impacted_holdings": 0, "positive_events": 0, "negative_events": 0, "monitor_events": 0},
            "top_positive_tailwinds": [],
            "top_negative_headwinds": [],
            "macro_events": [],
            "exposure_map": {},
            "source_errors": [],
        }

    company_rows, company_errors = _build_company_rows(holdings)
    sector_rows, sector_errors = _build_sector_rows(holdings)
    macro_fetch = {"items": recent_news_items or [], "errors": []}
    if recent_news_items is None:
        macro_fetch = fetch_macro_news(limit=10)
    geo_output = build_geopolitical_impact(holdings, list(macro_fetch.get("items", [])))
    macro_rows = _flatten_macro_events(list(geo_output.get("macro_events", [])))

    impact_rows = _deduplicate_rows(_sort_rows(company_rows + sector_rows + macro_rows))
    top_positive = [row for row in impact_rows if row.get("impact_direction") == "Positive Tailwind"][:6]
    top_negative = [row for row in impact_rows if row.get("impact_direction") == "Negative Headwind"][:6]

    return {
        "impact_rows": impact_rows,
        "portfolio_summary": _build_summary(impact_rows),
        "top_positive_tailwinds": top_positive,
        "top_negative_headwinds": top_negative,
        "macro_events": geo_output.get("macro_events", []),
        "exposure_map": geo_output.get("exposure_map", {}),
        "source_errors": company_errors + sector_errors + list(macro_fetch.get("errors", [])),
    }
