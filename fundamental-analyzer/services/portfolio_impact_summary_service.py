"""Summarize portfolio-impacting events into concise research outputs."""

from __future__ import annotations

from collections import Counter
from typing import Any


_SEVERITY_RANK = {"Low": 1, "Moderate": 2, "High": 3}


def _top_row(rows: list[dict[str, object]], direction: str) -> dict[str, object] | None:
    """Return the highest-priority row for one direction."""
    candidates = [row for row in rows if row.get("impact_direction") == direction]
    if not candidates:
        return None
    return sorted(candidates, key=lambda row: -_SEVERITY_RANK.get(str(row.get("severity")), 0))[0]


def build_portfolio_impact_summary(
    impact_rows: list[dict[str, object]],
    macro_events: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Build a concise portfolio impact summary from holding-level rows."""
    macro_events = macro_events or []
    if not impact_rows:
        return {
            "top_portfolio_risk_today": None,
            "top_portfolio_tailwind_today": None,
            "most_affected_stock": None,
            "most_vulnerable_sector": None,
            "macro_themes_affecting_portfolio": [],
            "geopolitical_themes_affecting_portfolio": [],
            "summary_text": "No major portfolio-impacting news items were mapped in the current scan.",
        }

    negative_top = _top_row(impact_rows, "Negative Headwind")
    positive_top = _top_row(impact_rows, "Positive Tailwind")
    ticker_counts = Counter(str(row.get("ticker")) for row in impact_rows if row.get("ticker"))
    sector_counts = Counter(
        str(row.get("event_type")) for row in impact_rows if str(row.get("event_type")) in {"macro", "geopolitical", "policy", "commodity", "sector demand"}
    )

    macro_themes = [str(event.get("theme")) for event in macro_events if str(event.get("event_type")) == "macro"]
    geopolitical_themes = [str(event.get("theme")) for event in macro_events if str(event.get("event_type")) == "geopolitical"]
    most_affected_stock = ticker_counts.most_common(1)[0][0] if ticker_counts else None
    most_vulnerable_sector = sector_counts.most_common(1)[0][0] if sector_counts else None

    summary_parts: list[str] = []
    if negative_top is not None:
        summary_parts.append(
            f"Top risk today is {negative_top.get('ticker')} from {str(negative_top.get('event_type')).replace('_', ' ')} pressure."
        )
    if positive_top is not None:
        summary_parts.append(
            f"Top tailwind today is {positive_top.get('ticker')} from {str(positive_top.get('event_type')).replace('_', ' ')} support."
        )
    if macro_themes:
        summary_parts.append(f"Macro themes in focus: {', '.join(macro_themes[:3])}.")
    if geopolitical_themes:
        summary_parts.append(f"Geopolitical themes in focus: {', '.join(geopolitical_themes[:3])}.")

    return {
        "top_portfolio_risk_today": negative_top,
        "top_portfolio_tailwind_today": positive_top,
        "most_affected_stock": most_affected_stock,
        "most_vulnerable_sector": most_vulnerable_sector,
        "macro_themes_affecting_portfolio": macro_themes,
        "geopolitical_themes_affecting_portfolio": geopolitical_themes,
        "summary_text": " ".join(summary_parts) or "Portfolio-impacting events were detected but did not resolve into a dominant headline risk or tailwind.",
    }
