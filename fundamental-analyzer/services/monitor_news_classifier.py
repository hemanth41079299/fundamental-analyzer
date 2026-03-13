"""Deterministic Google News classification for the Monitor page."""

from __future__ import annotations

from collections.abc import Iterable

_THEME_RULES: list[dict[str, object]] = [
    {
        "theme": "war_escalation",
        "keywords": ["war", "missile", "attack", "military", "border tension", "conflict", "airstrike"],
        "category": "Geopolitics",
        "event_type": "geopolitical",
        "impact_direction": "Negative Headwind",
        "severity": "High",
    },
    {
        "theme": "trade_restriction",
        "keywords": ["sanction", "tariff", "trade restriction", "export curb", "import ban", "trade war"],
        "category": "Geopolitics",
        "event_type": "geopolitical",
        "impact_direction": "Negative Headwind",
        "severity": "High",
    },
    {
        "theme": "oil_price_spike",
        "keywords": ["oil price", "crude", "brent", "fuel shock"],
        "category": "Macro",
        "event_type": "macro",
        "impact_direction": "Negative Headwind",
        "severity": "High",
    },
    {
        "theme": "inflation_spike",
        "keywords": ["inflation", "cpi", "wpi", "price pressure"],
        "category": "Macro",
        "event_type": "macro",
        "impact_direction": "Negative Headwind",
        "severity": "Moderate",
    },
    {
        "theme": "rate_hike",
        "keywords": ["rate hike", "repo hike", "tightening", "hawkish"],
        "category": "India Policy",
        "event_type": "policy",
        "impact_direction": "Negative Headwind",
        "severity": "Moderate",
    },
    {
        "theme": "rate_cut",
        "keywords": ["rate cut", "repo cut", "easing", "dovish"],
        "category": "India Policy",
        "event_type": "policy",
        "impact_direction": "Positive Tailwind",
        "severity": "Moderate",
    },
    {
        "theme": "budget_support",
        "keywords": ["budget increase", "capex push", "incentive", "policy support", "subsidy", "government push"],
        "category": "India Policy",
        "event_type": "policy",
        "impact_direction": "Positive Tailwind",
        "severity": "Moderate",
    },
    {
        "theme": "tax_increase",
        "keywords": ["tax hike", "cess", "duty increase", "levy", "higher tax"],
        "category": "Regulation",
        "event_type": "policy",
        "impact_direction": "Negative Headwind",
        "severity": "High",
    },
    {
        "theme": "regulatory_action",
        "keywords": ["regulation", "ministry", "regulator", "sebi", "rbi", "penalty", "investigation", "crackdown"],
        "category": "Regulation",
        "event_type": "regulation",
        "impact_direction": "Negative Headwind",
        "severity": "High",
    },
    {
        "theme": "earnings_pressure",
        "keywords": ["earnings miss", "profit miss", "weak demand", "guidance cut", "slowdown", "margin pressure"],
        "category": "Business",
        "event_type": "business",
        "impact_direction": "Negative Headwind",
        "severity": "Moderate",
    },
    {
        "theme": "earnings_improvement",
        "keywords": ["order win", "earnings beat", "margin expansion", "demand recovery", "guidance raise", "approval"],
        "category": "Business",
        "event_type": "business",
        "impact_direction": "Positive Tailwind",
        "severity": "Moderate",
    },
    {
        "theme": "market_volatility",
        "keywords": ["selloff", "volatility", "market outlook", "risk-off", "market pressure"],
        "category": "Markets",
        "event_type": "markets",
        "impact_direction": "Neutral / Monitor",
        "severity": "Moderate",
    },
    {
        "theme": "currency_weakness",
        "keywords": ["rupee", "currency weakness", "dollar strength", "forex pressure"],
        "category": "Macro",
        "event_type": "macro",
        "impact_direction": "Neutral / Monitor",
        "severity": "Moderate",
    },
]

_CATEGORY_DEFAULTS: dict[str, tuple[str, str, str, str]] = {
    "geopolitics": ("Geopolitics", "geopolitical", "Neutral / Monitor", "Moderate"),
    "india policy": ("India Policy", "policy", "Neutral / Monitor", "Moderate"),
    "business": ("Business", "business", "Neutral / Monitor", "Low"),
    "markets": ("Markets", "markets", "Neutral / Monitor", "Low"),
    "regulation": ("Regulation", "regulation", "Negative Headwind", "Moderate"),
    "macro": ("Macro", "macro", "Neutral / Monitor", "Moderate"),
}


def _text_blob(item: dict[str, object]) -> str:
    """Build one lowercase blob for rule matching."""
    return " ".join(
        [
            str(item.get("title", "") or ""),
            str(item.get("summary", "") or ""),
            str(item.get("category", "") or ""),
        ]
    ).lower()


def _default_classification(item: dict[str, object]) -> dict[str, str]:
    """Return a category-based default classification."""
    key = str(item.get("category", "") or "Business").strip().lower()
    category, event_type, direction, severity = _CATEGORY_DEFAULTS.get(key, ("Business", "business", "Neutral / Monitor", "Low"))
    return {
        "category": category,
        "event_type": event_type,
        "impact_direction": direction,
        "severity": severity,
        "theme": event_type,
    }


def classify_monitor_news_item(item: dict[str, object]) -> dict[str, str]:
    """Classify one news item into category, event type, direction, severity, and theme."""
    text = _text_blob(item)
    for rule in _THEME_RULES:
        if any(keyword in text for keyword in list(rule["keywords"])):
            return {
                "category": str(rule["category"]),
                "event_type": str(rule["event_type"]),
                "impact_direction": str(rule["impact_direction"]),
                "severity": str(rule["severity"]),
                "theme": str(rule["theme"]),
            }
    return _default_classification(item)


def classify_monitor_news_items(news_items: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    """Attach deterministic classifications to a list of normalized items."""
    classified_items: list[dict[str, object]] = []
    for item in news_items:
        classification = classify_monitor_news_item(item)
        classified_items.append({**dict(item), **classification})
    return classified_items
