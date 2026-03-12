"""Market-cap classification rules."""

from __future__ import annotations


def classify_market_cap(market_cap_cr: float | None) -> str:
    """Classify a company by market cap in crore."""
    if market_cap_cr is None:
        return "unknown"
    if market_cap_cr > 50000:
        return "large_cap"
    if 5000 <= market_cap_cr <= 50000:
        return "mid_cap"
    if 200 <= market_cap_cr < 5000:
        return "small_cap"
    return "micro_cap"
