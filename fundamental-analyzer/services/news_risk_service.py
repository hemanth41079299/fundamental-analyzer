"""Negative news risk scanner using RSS feeds and keyword detection."""

from __future__ import annotations

from html import unescape
import re
from typing import Any
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

import pandas as pd

NEWS_SIGNAL_RULES: dict[str, dict[str, object]] = {
    "fraud": {
        "severity": "high",
        "terms": ["fraud", "forgery", "accounting irregularity", "misstatement"],
        "message": "fraud mentioned in news",
    },
    "regulatory action": {
        "severity": "high",
        "terms": ["regulatory action", "regulator action", "sebi action", "sec action", "compliance action"],
        "message": "regulatory action mentioned in news",
    },
    "debt default": {
        "severity": "high",
        "terms": ["debt default", "defaulted", "payment default", "missed debt payment", "credit event"],
        "message": "debt default mentioned in news",
    },
    "pledge increase": {
        "severity": "moderate",
        "terms": ["pledge increase", "pledge rises", "pledge increased", "shares pledged", "promoter pledge"],
        "message": "pledge increase mentioned in news",
    },
    "governance issue": {
        "severity": "moderate",
        "terms": ["governance issue", "corporate governance", "whistleblower", "related party concern"],
        "message": "governance issue mentioned in news",
    },
    "earnings miss": {
        "severity": "moderate",
        "terms": ["earnings miss", "missed estimates", "below estimates", "profit warning", "weak earnings"],
        "message": "earnings miss mentioned in news",
    },
    "investigation": {
        "severity": "high",
        "terms": ["investigation", "probe", "investigated", "under scanner", "under scrutiny"],
        "message": "regulatory investigation mentioned in news",
    },
    "penalty": {
        "severity": "high",
        "terms": ["penalty", "fine", "fined", "penalised", "penalized"],
        "message": "penalty mentioned in news",
    },
}

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _safe_string(value: object) -> str:
    """Convert a raw value to a stripped string."""
    if value is None:
        return ""
    return str(value).strip()


def _strip_html(value: object) -> str:
    """Convert HTML content to plain text."""
    cleaned = _HTML_TAG_RE.sub(" ", _safe_string(value))
    return re.sub(r"\s+", " ", unescape(cleaned)).strip()


def _build_queries(ticker: str | None, company_name: str | None) -> list[str]:
    """Build RSS search queries for a company."""
    parts = [_safe_string(ticker).upper(), _safe_string(company_name)]
    parts = [part for part in parts if part]
    if not parts:
        return []

    base_query = " ".join(parts[:2])
    return [
        f'"{base_query}" stock',
        f'"{base_query}" fraud OR investigation OR penalty OR debt OR pledge OR earnings',
    ]


def _build_feed_urls(ticker: str | None, company_name: str | None) -> list[str]:
    """Return RSS feed URLs to scan for company-specific news."""
    urls: list[str] = []
    for query in _build_queries(ticker, company_name):
        encoded = quote_plus(query)
        urls.append(f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en")
    return urls


def _fetch_rss_items(url: str, max_items: int = 10) -> tuple[list[dict[str, str]], str | None]:
    """Fetch RSS items from one feed URL."""
    request = Request(url, headers={"User-Agent": "FundamentalAnalyzer/1.0"})
    try:
        with urlopen(request, timeout=8) as response:
            payload = response.read()
    except Exception as exc:
        return [], str(exc)

    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        return [], str(exc)

    items: list[dict[str, str]] = []
    for item in root.findall(".//item")[:max_items]:
        title = _strip_html(item.findtext("title"))
        description = _strip_html(item.findtext("description"))
        link = _safe_string(item.findtext("link"))
        published = _safe_string(item.findtext("pubDate"))
        source = urlparse(link).netloc.replace("www.", "") if link else "unknown"
        if not title:
            continue
        items.append(
            {
                "title": title,
                "description": description,
                "link": link,
                "published": published,
                "source": source,
            }
        )
    return items, None


def _deduplicate_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    """Deduplicate articles by title and link."""
    seen: set[tuple[str, str]] = set()
    unique_items: list[dict[str, str]] = []
    for item in items:
        key = (item.get("title", "").lower(), item.get("link", ""))
        if key in seen:
            continue
        seen.add(key)
        unique_items.append(item)
    return unique_items


def _detect_signals(items: list[dict[str, str]]) -> tuple[list[str], list[dict[str, object]]]:
    """Detect negative-news signals in article titles and descriptions."""
    signals: list[str] = []
    matched_articles: list[dict[str, object]] = []

    for item in items:
        text = f"{item.get('title', '')} {item.get('description', '')}".lower()
        matched_signal_names: list[str] = []
        matched_messages: list[str] = []
        matched_severities: list[str] = []

        for signal_name, rule in NEWS_SIGNAL_RULES.items():
            for term in rule["terms"]:
                if str(term).lower() in text:
                    matched_signal_names.append(signal_name)
                    matched_messages.append(str(rule["message"]))
                    matched_severities.append(str(rule["severity"]))
                    break

        if not matched_signal_names:
            continue

        for message in matched_messages:
            if message not in signals:
                signals.append(message)

        matched_articles.append(
            {
                **item,
                "matched_signals": matched_signal_names,
                "matched_messages": matched_messages,
                "matched_severities": matched_severities,
            }
        )

    return signals, matched_articles


def _resolve_risk_level(matched_articles: list[dict[str, object]]) -> str:
    """Map matched article severities to a final risk level."""
    if not matched_articles:
        return "low"

    severities = [severity for item in matched_articles for severity in item.get("matched_severities", [])]
    high_count = severities.count("high")
    moderate_count = severities.count("moderate")

    if high_count >= 2 or (high_count >= 1 and moderate_count >= 1) or len(matched_articles) >= 3:
        return "high"
    if high_count >= 1 or moderate_count >= 1:
        return "moderate"
    return "low"


def scan_company_news_risk(
    ticker: str | None = None,
    company_name: str | None = None,
    max_items_per_feed: int = 8,
) -> dict[str, object]:
    """Scan RSS-based news coverage for negative signals about a company."""
    feed_urls = _build_feed_urls(ticker, company_name)
    identifier = _safe_string(ticker).upper() or _safe_string(company_name) or "UNKNOWN"
    if not feed_urls:
        return {
            "ticker": identifier,
            "risk_level": "low",
            "signals": [],
            "matched_articles": [],
            "article_count": 0,
            "source_errors": ["No ticker or company name was available for news scanning."],
        }

    all_items: list[dict[str, str]] = []
    source_errors: list[str] = []
    for url in feed_urls:
        items, error = _fetch_rss_items(url, max_items=max_items_per_feed)
        all_items.extend(items)
        if error:
            source_errors.append(error)

    deduplicated_items = _deduplicate_items(all_items)
    signals, matched_articles = _detect_signals(deduplicated_items)

    return {
        "ticker": identifier,
        "risk_level": _resolve_risk_level(matched_articles),
        "signals": signals,
        "matched_articles": matched_articles,
        "article_count": len(matched_articles),
        "source_errors": source_errors,
    }


def scan_portfolio_news_risk(holdings: pd.DataFrame, top_n: int = 5) -> dict[str, object]:
    """Scan negative news risk for the largest holdings in a portfolio."""
    if holdings.empty:
        return {"overall_risk_level": "low", "company_results": [], "alerts": []}

    value_column = "Current Value" if "Current Value" in holdings.columns else None
    scan_frame = holdings.copy()
    if value_column is not None:
        scan_frame[value_column] = pd.to_numeric(scan_frame[value_column], errors="coerce").fillna(0.0)
        scan_frame = scan_frame.sort_values(by=value_column, ascending=False)

    scan_frame = scan_frame.head(top_n)
    company_results: list[dict[str, object]] = []
    alerts: list[dict[str, str]] = []

    for row in scan_frame.itertuples(index=False):
        ticker = _safe_string(getattr(row, "Ticker", None) or getattr(row, "ticker", None)).upper()
        company_name = _safe_string(getattr(row, "Company", None) or getattr(row, "company_name", None))
        result = scan_company_news_risk(ticker=ticker or None, company_name=company_name or None)
        company_results.append(result)
        for signal in result["signals"]:
            alerts.append({"ticker": str(result["ticker"]), "message": signal})

    risk_levels = [str(item["risk_level"]) for item in company_results]
    overall_risk = "low"
    if "high" in risk_levels:
        overall_risk = "high"
    elif "moderate" in risk_levels:
        overall_risk = "moderate"

    return {
        "overall_risk_level": overall_risk,
        "company_results": company_results,
        "alerts": alerts,
    }
