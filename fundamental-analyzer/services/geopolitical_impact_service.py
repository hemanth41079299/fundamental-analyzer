"""Map macro and geopolitical themes to portfolio holdings using sensitivity tags."""

from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

from config.settings import CONFIG_DIR
from services.news_impact_classifier import classify_news_item

_TICKER_NORMALIZE_RE = re.compile(r"[^A-Z0-9]")

_SECTOR_TAG_FALLBACKS: dict[str, list[str]] = {
    "information technology": ["export_sensitive", "it_spending_sensitive"],
    "it services": ["export_sensitive", "it_spending_sensitive"],
    "financial services": ["rate_sensitive", "policy_sensitive"],
    "banking": ["rate_sensitive", "policy_sensitive"],
    "defence": ["defense_sensitive", "policy_sensitive"],
    "capital goods": ["policy_sensitive", "commodity_sensitive"],
    "power": ["commodity_sensitive", "policy_sensitive"],
    "energy": ["commodity_sensitive", "policy_sensitive", "import_sensitive"],
    "oil & gas": ["commodity_sensitive", "import_sensitive"],
    "pharmaceuticals": ["export_sensitive", "policy_sensitive"],
    "consumer staples": ["consumer_defensive"],
    "tobacco": ["tobacco_tax_sensitive", "consumer_defensive", "policy_sensitive"],
}

_THEME_IMPACT_MAP: dict[str, dict[str, tuple[str, str, str]]] = {
    "defense_budget_increase": {
        "defense_sensitive": (
            "Positive Tailwind",
            "Moderate",
            "Higher defense spending may support order inflow and visibility.",
        ),
        "policy_sensitive": (
            "Positive Tailwind",
            "Low",
            "Policy support may improve execution visibility.",
        ),
    },
    "rate_hike": {
        "rate_sensitive": (
            "Negative Headwind",
            "Moderate",
            "Higher rates can pressure funding conditions and valuation multiples.",
        ),
    },
    "rate_cut": {
        "rate_sensitive": (
            "Positive Tailwind",
            "Moderate",
            "Lower rates can support credit growth and valuation support.",
        ),
    },
    "inflation_spike": {
        "commodity_sensitive": (
            "Negative Headwind",
            "Moderate",
            "Input-cost inflation can pressure margins.",
        ),
        "consumer_defensive": (
            "Neutral / Monitor",
            "Low",
            "Demand may be more resilient than cyclical sectors.",
        ),
    },
    "oil_price_spike": {
        "import_sensitive": (
            "Negative Headwind",
            "High",
            "Higher energy and import costs can pressure profitability.",
        ),
        "commodity_sensitive": (
            "Neutral / Monitor",
            "Moderate",
            "Commodity exposure increases earnings sensitivity to input prices.",
        ),
    },
    "trade_restriction": {
        "export_sensitive": (
            "Negative Headwind",
            "High",
            "Trade restrictions can weaken export-linked demand and execution.",
        ),
        "import_sensitive": (
            "Negative Headwind",
            "Moderate",
            "Supply chains and landed costs can become less predictable.",
        ),
    },
    "war_escalation": {
        "export_sensitive": (
            "Negative Headwind",
            "High",
            "Escalation can disrupt demand, currency, and global risk appetite.",
        ),
        "geopolitical_sensitive": (
            "Negative Headwind",
            "High",
            "Operations and sentiment become more exposed to external shocks.",
        ),
        "defense_sensitive": (
            "Positive Tailwind",
            "Moderate",
            "Defense procurement attention may strengthen.",
        ),
    },
    "currency_weakness": {
        "export_sensitive": (
            "Positive Tailwind",
            "Moderate",
            "A weaker domestic currency can support export realizations.",
        ),
        "import_sensitive": (
            "Negative Headwind",
            "Moderate",
            "Imported inputs become more expensive in local currency terms.",
        ),
    },
    "tax_increase": {
        "tobacco_tax_sensitive": (
            "Negative Headwind",
            "High",
            "Higher taxation can pressure volumes and profitability.",
        ),
        "policy_sensitive": (
            "Negative Headwind",
            "Moderate",
            "Policy tightening can reduce earnings visibility.",
        ),
    },
    "tax_relief": {
        "policy_sensitive": (
            "Positive Tailwind",
            "Moderate",
            "Tax relief can support profitability or demand.",
        ),
    },
    "regulatory_action": {
        "policy_sensitive": (
            "Negative Headwind",
            "High",
            "Regulatory pressure can affect sentiment and execution.",
        ),
    },
}


def _safe_float(value: Any) -> float:
    """Convert a value to float when possible."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def normalize_ticker(ticker: str) -> str:
    """Normalize a ticker for config lookups."""
    cleaned = str(ticker or "").strip().upper()
    cleaned = cleaned.split(".", 1)[0]
    return _TICKER_NORMALIZE_RE.sub("", cleaned)


def load_holding_sensitivity_map() -> dict[str, list[str]]:
    """Load the configurable sensitivity map."""
    path = CONFIG_DIR / "holding_sensitivity_map.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def infer_sensitivity_tags(ticker: str, sector: str | None = None) -> list[str]:
    """Resolve sensitivity tags from config and sector fallbacks."""
    sensitivity_map = load_holding_sensitivity_map()
    normalized_ticker = normalize_ticker(ticker)
    tags = list(sensitivity_map.get(normalized_ticker, []))

    cleaned_sector = str(sector or "").strip().lower()
    for sector_key, sector_tags in _SECTOR_TAG_FALLBACKS.items():
        if sector_key in cleaned_sector:
            tags.extend(sector_tags)

    deduplicated: list[str] = []
    for tag in tags:
        if tag not in deduplicated:
            deduplicated.append(tag)
    return deduplicated


def calculate_exposure_map(holdings: pd.DataFrame) -> dict[str, float]:
    """Calculate portfolio exposure percentages by sensitivity theme."""
    if holdings.empty or "Current Value" not in holdings.columns:
        return {}

    frame = holdings.copy()
    frame["Current Value"] = pd.to_numeric(frame["Current Value"], errors="coerce").fillna(0.0)
    total_value = float(frame["Current Value"].sum())
    if total_value <= 0:
        return {}

    exposure_totals = {
        "rate_sensitive": 0.0,
        "export_sensitive": 0.0,
        "policy_sensitive": 0.0,
        "commodity_sensitive": 0.0,
        "geopolitical_sensitive": 0.0,
    }

    for _, row in frame.iterrows():
        tags = infer_sensitivity_tags(str(row.get("Ticker", "")), str(row.get("Sector", "") or ""))
        current_value = _safe_float(row.get("Current Value"))
        if "rate_sensitive" in tags:
            exposure_totals["rate_sensitive"] += current_value
        if "export_sensitive" in tags:
            exposure_totals["export_sensitive"] += current_value
            exposure_totals["geopolitical_sensitive"] += current_value
        if "policy_sensitive" in tags or "tobacco_tax_sensitive" in tags or "defense_sensitive" in tags:
            exposure_totals["policy_sensitive"] += current_value
        if "commodity_sensitive" in tags or "import_sensitive" in tags:
            exposure_totals["commodity_sensitive"] += current_value
        if "defense_sensitive" in tags or "import_sensitive" in tags:
            exposure_totals["geopolitical_sensitive"] += current_value

    return {key: round((value / total_value) * 100, 2) for key, value in exposure_totals.items() if value > 0}


def map_macro_events_to_holdings(
    holdings: pd.DataFrame,
    macro_items: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Map classified macro or geopolitical events to affected holdings."""
    if holdings.empty:
        return []

    events: list[dict[str, object]] = []
    for item in macro_items:
        classification = classify_news_item(item)
        theme = classification["theme"]
        if theme not in _THEME_IMPACT_MAP:
            continue

        affected_holdings: list[dict[str, object]] = []
        for row in holdings.itertuples(index=False):
            ticker = str(getattr(row, "Ticker", "") or "")
            company_name = str(getattr(row, "Company", "") or ticker)
            sector = str(getattr(row, "Sector", "") or "")
            tags = infer_sensitivity_tags(ticker, sector)
            for tag, impact in _THEME_IMPACT_MAP[theme].items():
                if tag not in tags:
                    continue
                affected_holdings.append(
                    {
                        "ticker": ticker,
                        "company_name": company_name,
                        "impact_direction": impact[0],
                        "severity": impact[1],
                        "reason": impact[2],
                        "tags": tags,
                    }
                )
                break

        if affected_holdings:
            events.append(
                {
                    "theme": theme.replace("_", " ").title(),
                    "event_title": item.get("title"),
                    "event_type": classification["event_type"],
                    "event_date": item.get("published_at"),
                    "source": item.get("source"),
                    "affected_holdings": affected_holdings,
                }
            )
    return events


def build_geopolitical_impact(
    holdings: pd.DataFrame,
    macro_items: list[dict[str, object]],
) -> dict[str, object]:
    """Build macro and geopolitical impact output for holdings."""
    return {
        "macro_events": map_macro_events_to_holdings(holdings, macro_items),
        "exposure_map": calculate_exposure_map(holdings),
    }
