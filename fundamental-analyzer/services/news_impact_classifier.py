"""Rule-based news impact classifier for finance research workflows."""

from __future__ import annotations

from typing import Any

_CLASSIFICATION_RULES = [
    {
        "terms": ["fraud", "forgery", "misstatement", "accounting irregularity"],
        "event_type": "governance",
        "impact_direction": "Negative Headwind",
        "severity": "High",
        "theme": "governance_issue",
    },
    {
        "terms": ["investigation", "probe", "under scrutiny", "penalty", "fined", "sebi", "regulatory action"],
        "event_type": "regulation",
        "impact_direction": "Negative Headwind",
        "severity": "High",
        "theme": "regulatory_action",
    },
    {
        "terms": ["debt default", "defaulted", "payment default"],
        "event_type": "macro",
        "impact_direction": "Negative Headwind",
        "severity": "High",
        "theme": "debt_default",
    },
    {
        "terms": ["earnings miss", "below estimates", "profit warning", "weak earnings"],
        "event_type": "earnings",
        "impact_direction": "Negative Headwind",
        "severity": "Moderate",
        "theme": "earnings_miss",
    },
    {
        "terms": ["order win", "large order", "contract win", "record order book"],
        "event_type": "sector demand",
        "impact_direction": "Positive Tailwind",
        "severity": "Moderate",
        "theme": "order_win",
    },
    {
        "terms": ["budget increase", "defense budget", "capex push", "policy support", "incentive"],
        "event_type": "policy",
        "impact_direction": "Positive Tailwind",
        "severity": "Moderate",
        "theme": "defense_budget_increase",
    },
    {
        "terms": ["rate hike", "interest rate rise", "hawkish", "higher rates"],
        "event_type": "macro",
        "impact_direction": "Negative Headwind",
        "severity": "Moderate",
        "theme": "rate_hike",
    },
    {
        "terms": ["rate cut", "lower rates", "easing cycle"],
        "event_type": "macro",
        "impact_direction": "Positive Tailwind",
        "severity": "Moderate",
        "theme": "rate_cut",
    },
    {
        "terms": ["inflation", "input cost surge", "cost pressure"],
        "event_type": "macro",
        "impact_direction": "Negative Headwind",
        "severity": "Moderate",
        "theme": "inflation_spike",
    },
    {
        "terms": ["oil price spike", "higher crude", "crude jumps", "brent rises"],
        "event_type": "commodity",
        "impact_direction": "Negative Headwind",
        "severity": "Moderate",
        "theme": "oil_price_spike",
    },
    {
        "terms": ["trade restriction", "tariff", "export curb", "export slowdown", "weak global demand"],
        "event_type": "geopolitical",
        "impact_direction": "Negative Headwind",
        "severity": "High",
        "theme": "trade_restriction",
    },
    {
        "terms": ["sanction", "war", "border tension", "geopolitical", "conflict escalation"],
        "event_type": "geopolitical",
        "impact_direction": "Negative Headwind",
        "severity": "High",
        "theme": "war_escalation",
    },
    {
        "terms": ["rupee weakens", "currency weakness", "forex pressure"],
        "event_type": "macro",
        "impact_direction": "Neutral / Monitor",
        "severity": "Moderate",
        "theme": "currency_weakness",
    },
    {
        "terms": ["tax increase", "sin tax", "tobacco tax", "duty hike"],
        "event_type": "taxation",
        "impact_direction": "Negative Headwind",
        "severity": "High",
        "theme": "tax_increase",
    },
    {
        "terms": ["tax cut", "duty cut", "gst relief"],
        "event_type": "taxation",
        "impact_direction": "Positive Tailwind",
        "severity": "Moderate",
        "theme": "tax_relief",
    },
]


def classify_news_item(item: dict[str, Any]) -> dict[str, str]:
    """Classify one normalized news item."""
    title = str(item.get("title") or "")
    snippet = str(item.get("snippet") or "")
    text = f"{title} {snippet}".lower()

    for rule in _CLASSIFICATION_RULES:
        if any(term in text for term in rule["terms"]):
            return {
                "event_type": str(rule["event_type"]),
                "impact_direction": str(rule["impact_direction"]),
                "severity": str(rule["severity"]),
                "theme": str(rule["theme"]),
            }

    return {
        "event_type": "general",
        "impact_direction": "Neutral / Monitor",
        "severity": "Low",
        "theme": "general_monitoring",
    }
