"""Map monitor news items to user holdings using ticker, sector, and sensitivity logic."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from services.geopolitical_impact_service import infer_sensitivity_tags, normalize_ticker

_SEVERITY_RANK = {"Low": 1, "Moderate": 2, "High": 3}
_TEXT_CLEAN_RE = re.compile(r"[^a-z0-9]+")

_THEME_TAG_RULES: dict[str, dict[str, tuple[str, str, str]]] = {
    "war_escalation": {
        "defense_sensitive": ("Positive Tailwind", "Moderate", "Higher defense preparedness may support order visibility."),
        "export_sensitive": ("Negative Headwind", "High", "Global conflict can pressure demand, sentiment, and execution."),
        "import_sensitive": ("Negative Headwind", "Moderate", "Supply chains and landed costs can become more volatile."),
    },
    "trade_restriction": {
        "export_sensitive": ("Negative Headwind", "High", "Trade restrictions can weaken export-linked demand."),
        "import_sensitive": ("Negative Headwind", "Moderate", "Restricted trade can pressure costs and supply visibility."),
    },
    "oil_price_spike": {
        "commodity_sensitive": ("Negative Headwind", "Moderate", "Input-cost sensitivity rises when crude prices move sharply."),
        "import_sensitive": ("Negative Headwind", "High", "Imported energy or raw materials become more expensive."),
    },
    "inflation_spike": {
        "commodity_sensitive": ("Negative Headwind", "Moderate", "Inflation pressure can compress margins."),
        "consumer_defensive": ("Neutral / Monitor", "Low", "Demand may hold up better than cyclical categories."),
    },
    "rate_hike": {
        "rate_sensitive": ("Negative Headwind", "Moderate", "Higher rates can pressure funding conditions and valuations."),
    },
    "rate_cut": {
        "rate_sensitive": ("Positive Tailwind", "Moderate", "Lower rates can support credit growth and sentiment."),
    },
    "budget_support": {
        "policy_sensitive": ("Positive Tailwind", "Moderate", "Policy support may improve demand or execution visibility."),
        "defense_sensitive": ("Positive Tailwind", "Moderate", "Government support may improve order visibility."),
    },
    "tax_increase": {
        "tobacco_tax_sensitive": ("Negative Headwind", "High", "Higher taxation can pressure volumes and margins."),
        "policy_sensitive": ("Negative Headwind", "Moderate", "Policy tightening can reduce earnings visibility."),
    },
    "regulatory_action": {
        "policy_sensitive": ("Negative Headwind", "High", "Regulatory action can affect sentiment and execution."),
    },
    "earnings_pressure": {
        "it_spending_sensitive": ("Negative Headwind", "Moderate", "Softer client budgets can pressure growth visibility."),
        "export_sensitive": ("Negative Headwind", "Moderate", "Global demand pressure can affect export-linked earnings."),
    },
    "earnings_improvement": {
        "it_spending_sensitive": ("Positive Tailwind", "Moderate", "Improving demand conditions may support growth visibility."),
        "export_sensitive": ("Positive Tailwind", "Moderate", "Stronger global demand can support export-linked execution."),
    },
}


def _clean_text(value: object) -> str:
    """Normalize text for fuzzy matching."""
    return _TEXT_CLEAN_RE.sub(" ", str(value or "").lower()).strip()


def _company_aliases(company_name: str, ticker: str) -> list[str]:
    """Build simple aliases for one holding name."""
    aliases = {_clean_text(company_name), _clean_text(normalize_ticker(ticker))}
    words = [word for word in _clean_text(company_name).split() if len(word) >= 4]
    if words:
        aliases.add(words[0])
        aliases.add(words[-1])
    return [alias for alias in aliases if alias]


def _resolve_tags(ticker: str, sector: str, holding_sensitivity_map: dict[str, list[str]] | None = None) -> list[str]:
    """Resolve tags from explicit mapping first, then sector fallback."""
    if holding_sensitivity_map:
        mapped = list(holding_sensitivity_map.get(normalize_ticker(ticker), []))
        if mapped:
            return mapped
    return infer_sensitivity_tags(ticker, sector)


def _direct_company_match(item_text: str, ticker: str, company_name: str) -> bool:
    """Check whether one news item directly references the holding."""
    for alias in _company_aliases(company_name, ticker):
        if alias and alias in item_text:
            return True
    return False


def _sector_match(item_text: str, sector: str) -> bool:
    """Check whether the news text mentions the holding sector."""
    sector_text = _clean_text(sector)
    return bool(sector_text and sector_text != "unknown" and sector_text in item_text)


def _build_row(
    ticker: str,
    company_name: str,
    item: dict[str, object],
    impact_direction: str,
    severity: str,
    reason: str,
) -> dict[str, object]:
    """Create one normalized portfolio-impact row."""
    return {
        "ticker": ticker,
        "company_name": company_name,
        "news_title": item.get("title"),
        "event_title": item.get("title"),
        "news_category": item.get("category"),
        "category": item.get("category"),
        "event_type": item.get("event_type"),
        "impact_direction": impact_direction,
        "severity": severity,
        "reason": reason,
        "why_it_matters": reason,
        "published_at": item.get("published_at"),
        "event_date": item.get("published_at"),
        "url": item.get("url"),
        "source": item.get("source"),
        "theme": item.get("theme"),
    }


def _sort_and_deduplicate(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Sort and deduplicate mapped impact rows."""
    seen: set[tuple[str, str]] = set()
    deduplicated: list[dict[str, object]] = []
    for row in sorted(
        rows,
        key=lambda item: (
            -_SEVERITY_RANK.get(str(item.get("severity") or "Low"), 0),
            str(item.get("published_at") or ""),
            str(item.get("ticker") or ""),
        ),
    ):
        key = (str(row.get("ticker") or "").upper(), str(row.get("news_title") or "").lower())
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(row)
    return deduplicated


def map_monitor_news_to_portfolio(
    user_id: int,
    holdings: pd.DataFrame,
    news_items: list[dict[str, object]],
    holding_sensitivity_map: dict[str, list[str]] | None = None,
) -> list[dict[str, object]]:
    """Map classified monitor news items to portfolio holdings."""
    del user_id
    if holdings.empty or not news_items:
        return []

    rows: list[dict[str, object]] = []
    for holding in holdings.itertuples(index=False):
        ticker = str(getattr(holding, "Ticker", "") or "")
        company_name = str(getattr(holding, "Company", "") or ticker)
        sector = str(getattr(holding, "Sector", "") or "Unknown")
        tags = _resolve_tags(ticker, sector, holding_sensitivity_map)

        for item in news_items:
            item_text = _clean_text(" ".join([str(item.get("title", "")), str(item.get("summary", ""))]))
            if _direct_company_match(item_text, ticker, company_name):
                rows.append(
                    _build_row(
                        ticker=ticker,
                        company_name=company_name,
                        item=item,
                        impact_direction=str(item.get("impact_direction") or "Neutral / Monitor"),
                        severity=str(item.get("severity") or "Moderate"),
                        reason=f"Headline directly references {company_name}.",
                    )
                )
                continue

            theme = str(item.get("theme") or "")
            theme_impacts = _THEME_TAG_RULES.get(theme, {})
            matched_theme = False
            for tag, impact in theme_impacts.items():
                if tag in tags:
                    rows.append(_build_row(ticker, company_name, item, impact[0], impact[1], impact[2]))
                    matched_theme = True
                    break
            if matched_theme:
                continue

            if _sector_match(item_text, sector):
                rows.append(
                    _build_row(
                        ticker=ticker,
                        company_name=company_name,
                        item=item,
                        impact_direction=str(item.get("impact_direction") or "Neutral / Monitor"),
                        severity="Moderate" if str(item.get("severity") or "Low") == "Low" else str(item.get("severity")),
                        reason=f"{sector} sector coverage may affect demand, policy, or sentiment for {company_name}.",
                    )
                )

    return _sort_and_deduplicate(rows)
