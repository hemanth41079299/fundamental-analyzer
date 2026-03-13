"""Google News RSS fetching helpers for the Monitor page."""

from __future__ import annotations

from collections.abc import Iterable
from html import unescape
import re
import ssl
from typing import Any
from urllib.request import Request, urlopen
from urllib.parse import quote_plus

import certifi
import feedparser
import streamlit as st

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
_GOOGLE_NEWS_HOME_RSS_URL = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
_GOOGLE_NEWS_WORLD_RSS_URL = "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-IN&gl=IN&ceid=IN:en"
_GOOGLE_NEWS_BUSINESS_RSS_URL = "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-IN&gl=IN&ceid=IN:en"
_GOOGLE_NEWS_NATION_RSS_URL = "https://news.google.com/rss/headlines/section/topic/NATION?hl=en-IN&gl=IN&ceid=IN:en"
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}

_GEOPOLITICAL_QUERIES = [
    "geopolitics",
    "war OR sanctions OR trade restriction OR border tension",
    "oil prices OR crude shock",
    "global conflict markets",
]

_GEOPOLITICAL_FALLBACK_QUERIES = [
    "world news markets",
    "global markets conflict",
    "war markets",
    "sanctions markets",
]

_INDIA_POLICY_QUERIES = [
    "India policy",
    "India budget",
    "RBI policy",
    "Indian economy",
    "tax policy India",
    "election policy India",
    "ministry regulation India",
]

_INDIA_POLICY_FALLBACK_QUERIES = [
    "India economy news",
    "India government policy",
    "RBI India news",
    "India regulation markets",
]

_BUSINESS_QUERIES = [
    "Indian stock market",
    "earnings India",
    "sector news India",
    "business India",
    "market outlook India",
]

_BUSINESS_FALLBACK_QUERIES = [
    "India markets news",
    "India stocks",
    "NSE BSE market news",
    "India business headlines",
]

_GEOPOLITICAL_FILTER_KEYWORDS = [
    "war",
    "conflict",
    "missile",
    "attack",
    "border",
    "sanction",
    "tariff",
    "trade",
    "oil",
    "crude",
    "iran",
    "china",
    "russia",
    "ukraine",
]

_INDIA_POLICY_FILTER_KEYWORDS = [
    "rbi",
    "budget",
    "policy",
    "tax",
    "ministry",
    "government",
    "parliament",
    "regulation",
    "economy",
    "india",
]

_BUSINESS_FILTER_KEYWORDS = [
    "market",
    "business",
    "earnings",
    "stocks",
    "sector",
    "company",
    "nifty",
    "sensex",
    "demand",
    "outlook",
]


def _clean_text(value: object) -> str:
    """Normalize text from RSS payloads."""
    if value is None:
        return ""
    text = unescape(str(value))
    text = _TAG_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def _format_published(entry: Any) -> str:
    """Return one normalized published timestamp string."""
    published_struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if published_struct:
        try:
            return f"{published_struct.tm_year:04d}-{published_struct.tm_mon:02d}-{published_struct.tm_mday:02d} {published_struct.tm_hour:02d}:{published_struct.tm_min:02d}"
        except (AttributeError, TypeError, ValueError):
            pass
    return _clean_text(getattr(entry, "published", None) or getattr(entry, "updated", None))


def _extract_source(entry: Any, cleaned_title: str) -> tuple[str, str]:
    """Extract source and refined title from one feed item."""
    source_title = _clean_text(getattr(getattr(entry, "source", None), "title", None))
    if source_title:
        return source_title, cleaned_title

    if " - " in cleaned_title:
        possible_title, possible_source = cleaned_title.rsplit(" - ", 1)
        if 1 < len(possible_source) <= 60:
            return possible_source.strip(), possible_title.strip()
    return "Google News", cleaned_title


def _normalize_entry(entry: Any, category: str) -> dict[str, str] | None:
    """Normalize one RSS entry into the monitor schema."""
    raw_title = _clean_text(getattr(entry, "title", None))
    raw_summary = _clean_text(getattr(entry, "summary", None) or getattr(entry, "description", None))
    url = _clean_text(getattr(entry, "link", None))
    if not raw_title or not url:
        return None

    source, title = _extract_source(entry, raw_title)
    summary = raw_summary or title
    return {
        "title": title,
        "source": source,
        "published_at": _format_published(entry),
        "url": url,
        "summary": summary,
        "category": category,
    }


@st.cache_data(ttl=900, show_spinner=False)
def _fetch_google_feed_cached(url: str, limit: int, category: str) -> dict[str, object]:
    """Fetch one Google News RSS feed with short-lived caching."""
    items: list[dict[str, str]] = []
    errors: list[str] = []
    try:
        request = Request(url, headers=_BROWSER_HEADERS)
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=15, context=ssl_context) as response:
            payload = response.read()
        feed = feedparser.parse(payload)
    except Exception as exc:  # pragma: no cover - network failures are environment-dependent
        return {"items": [], "errors": [f"{category}: {exc}"]}

    if getattr(feed, "bozo", 0):
        bozo_error = getattr(feed, "bozo_exception", None)
        if bozo_error:
            errors.append(f"{category}: {bozo_error}")

    for entry in list(getattr(feed, "entries", [])):
        normalized = _normalize_entry(entry, category)
        if normalized is None:
            continue
        items.append(normalized)
        if len(items) >= limit:
            break

    return {"items": items, "errors": errors}


def _merge_results(results: Iterable[dict[str, object]], limit: int) -> dict[str, object]:
    """Merge and deduplicate multiple query results."""
    merged_items: list[dict[str, str]] = []
    merged_errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    for result in results:
        for error in list(result.get("errors", [])):
            if error not in merged_errors:
                merged_errors.append(str(error))
        for item in list(result.get("items", [])):
            key = (str(item.get("title", "")).lower(), str(item.get("url", "")).lower())
            if key in seen:
                continue
            seen.add(key)
            merged_items.append(dict(item))
            if len(merged_items) >= limit:
                return {"items": merged_items, "errors": merged_errors}

    return {"items": merged_items[:limit], "errors": merged_errors}


def _fetch_query_group(queries: list[str], limit: int, category: str) -> dict[str, object]:
    """Fetch and merge one group of related Google News queries."""
    per_query_limit = max(3, limit // max(len(queries), 1) + 1)
    return _merge_results(
        [fetch_google_news_by_query(query, limit=per_query_limit, category=category) for query in queries],
        limit=limit,
    )


def _filter_items_by_keywords(items: list[dict[str, str]], keywords: list[str], limit: int, category: str) -> list[dict[str, str]]:
    """Filter generic feed items into one bucket with keyword matching."""
    filtered: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        if not any(keyword in text for keyword in keywords):
            continue
        key = (str(item.get("title", "")).lower(), str(item.get("url", "")).lower())
        if key in seen:
            continue
        seen.add(key)
        filtered.append({**dict(item), "category": category})
        if len(filtered) >= limit:
            break
    return filtered


def _fetch_topic_fallback(feed_urls: list[str], keywords: list[str], limit: int, category: str) -> dict[str, object]:
    """Fetch more stable Google News topic feeds and filter them into one bucket."""
    results = [_fetch_google_feed_cached(url, max(limit * 2, 12), category) for url in feed_urls]
    merged = _merge_results(results, limit=max(limit * 3, 20))
    filtered = _filter_items_by_keywords(list(merged.get("items", [])), keywords=keywords, limit=limit, category=category)

    if filtered:
        return {"items": filtered, "errors": list(merged.get("errors", []))}

    generic_items = list(merged.get("items", []))[:limit]
    return {
        "items": [{**dict(item), "category": category} for item in generic_items],
        "errors": list(merged.get("errors", [])),
    }


def _fetch_with_fallback(primary_queries: list[str], fallback_queries: list[str], limit: int, category: str) -> dict[str, object]:
    """Fetch one bucket and retry broader queries if the primary set is empty."""
    primary = _fetch_query_group(primary_queries, limit=limit, category=category)
    if list(primary.get("items", [])):
        return primary

    fallback = _fetch_query_group(fallback_queries, limit=limit, category=category)
    fallback_errors = list(primary.get("errors", [])) + [error for error in list(fallback.get("errors", [])) if error not in list(primary.get("errors", []))]
    return {
        "items": list(fallback.get("items", [])),
        "errors": fallback_errors,
    }


def fetch_google_news_by_query(query: str, limit: int = 10, category: str = "General") -> dict[str, object]:
    """Fetch normalized Google News results for one search query."""
    cleaned_query = str(query or "").strip()
    if not cleaned_query:
        return {"items": [], "errors": ["Empty Google News query."]}
    url = _GOOGLE_NEWS_RSS_URL.format(query=quote_plus(cleaned_query))
    return _fetch_google_feed_cached(url, max(int(limit), 1), category)


def fetch_geopolitical_news(limit: int = 10) -> dict[str, object]:
    """Fetch recent geopolitical headlines from Google News RSS."""
    result = _fetch_with_fallback(
        primary_queries=_GEOPOLITICAL_QUERIES,
        fallback_queries=_GEOPOLITICAL_FALLBACK_QUERIES,
        limit=limit,
        category="Geopolitics",
    )
    if list(result.get("items", [])):
        return result
    topic_result = _fetch_topic_fallback(
        feed_urls=[_GOOGLE_NEWS_WORLD_RSS_URL, _GOOGLE_NEWS_HOME_RSS_URL],
        keywords=_GEOPOLITICAL_FILTER_KEYWORDS,
        limit=limit,
        category="Geopolitics",
    )
    return {
        "items": list(topic_result.get("items", [])),
        "errors": list(result.get("errors", [])) + [error for error in list(topic_result.get("errors", [])) if error not in list(result.get("errors", []))],
    }


def fetch_india_policy_news(limit: int = 10) -> dict[str, object]:
    """Fetch recent India policy and politics headlines from Google News RSS."""
    result = _fetch_with_fallback(
        primary_queries=_INDIA_POLICY_QUERIES,
        fallback_queries=_INDIA_POLICY_FALLBACK_QUERIES,
        limit=limit,
        category="India Policy",
    )
    if list(result.get("items", [])):
        return result
    topic_result = _fetch_topic_fallback(
        feed_urls=[_GOOGLE_NEWS_NATION_RSS_URL, _GOOGLE_NEWS_HOME_RSS_URL],
        keywords=_INDIA_POLICY_FILTER_KEYWORDS,
        limit=limit,
        category="India Policy",
    )
    return {
        "items": list(topic_result.get("items", [])),
        "errors": list(result.get("errors", [])) + [error for error in list(topic_result.get("errors", [])) if error not in list(result.get("errors", []))],
    }


def fetch_business_news(limit: int = 10) -> dict[str, object]:
    """Fetch recent Indian business and market headlines from Google News RSS."""
    result = _fetch_with_fallback(
        primary_queries=_BUSINESS_QUERIES,
        fallback_queries=_BUSINESS_FALLBACK_QUERIES,
        limit=limit,
        category="Business",
    )
    if list(result.get("items", [])):
        return result
    topic_result = _fetch_topic_fallback(
        feed_urls=[_GOOGLE_NEWS_BUSINESS_RSS_URL, _GOOGLE_NEWS_HOME_RSS_URL],
        keywords=_BUSINESS_FILTER_KEYWORDS,
        limit=limit,
        category="Business",
    )
    return {
        "items": list(topic_result.get("items", [])),
        "errors": list(result.get("errors", [])) + [error for error in list(topic_result.get("errors", [])) if error not in list(result.get("errors", []))],
    }


def clear_google_news_cache() -> None:
    """Clear the cached Google News queries."""
    _fetch_google_feed_cached.clear()
