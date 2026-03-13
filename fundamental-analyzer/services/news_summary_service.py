"""Template-based news summaries for the Monitor page."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable


def _pretty_theme(theme: str) -> str:
    """Convert one theme key into display text."""
    return str(theme or "").replace("_", " ").strip().capitalize()


def _tone_label(items: list[dict[str, object]]) -> str:
    """Estimate the dominant tone for one bucket."""
    positive = sum(1 for item in items if item.get("impact_direction") == "Positive Tailwind")
    negative = sum(1 for item in items if item.get("impact_direction") == "Negative Headwind")
    if positive > negative:
        return "constructive"
    if negative > positive:
        return "cautious"
    return "mixed"


def summarize_news_bucket(news_items: Iterable[dict[str, object]], bucket_name: str) -> dict[str, object]:
    """Summarize one bucket of classified news items."""
    items = list(news_items)
    if not items:
        return {
            "bucket": bucket_name,
            "top_themes": [],
            "summary_text": f"No recent {bucket_name.lower()} headlines were available.",
            "tone": "neutral",
        }

    theme_counts = Counter(str(item.get("theme") or "general") for item in items)
    top_themes = [_pretty_theme(theme) for theme, _ in theme_counts.most_common(3)]
    tone = _tone_label(items)
    headline_count = len(items)
    focus = ", ".join(top_themes[:2]) if top_themes else "general developments"
    summary_text = f"{bucket_name} headlines are {tone}, with {headline_count} tracked items focused on {focus}."
    return {
        "bucket": bucket_name,
        "top_themes": top_themes,
        "summary_text": summary_text,
        "tone": tone,
    }


def summarize_monitor_page(
    geo_news: Iterable[dict[str, object]],
    india_news: Iterable[dict[str, object]],
    business_news: Iterable[dict[str, object]],
) -> dict[str, object]:
    """Build one top-level monitor summary from the three core buckets."""
    geo_summary = summarize_news_bucket(geo_news, "Geopolitical")
    india_summary = summarize_news_bucket(india_news, "India policy")
    business_summary = summarize_news_bucket(business_news, "Business")

    combined_themes: list[str] = []
    for theme in list(geo_summary["top_themes"]) + list(india_summary["top_themes"]) + list(business_summary["top_themes"]):
        if theme not in combined_themes:
            combined_themes.append(theme)

    top_themes = combined_themes[:5]
    summary_parts = [
        str(geo_summary["summary_text"]),
        str(india_summary["summary_text"]),
        str(business_summary["summary_text"]),
    ]
    return {
        "top_themes": top_themes,
        "summary_text": " ".join(part for part in summary_parts if part),
        "bucket_summaries": {
            "geopolitical": geo_summary,
            "india_policy": india_summary,
            "business": business_summary,
        },
    }
