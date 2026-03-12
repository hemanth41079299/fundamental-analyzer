"""Normalized news fetching helpers for company, sector, and macro coverage."""

from __future__ import annotations

from html import unescape
import re
from typing import Iterable
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

_HTML_TAG_RE = re.compile(r"<[^>]+>")

MACRO_NEWS_QUERIES = [
    "India interest rates inflation stock market",
    "India oil price spike economy",
    "India budget policy tax change stocks",
    "India trade restrictions sanctions exports",
    "India defense budget stocks",
    "India rupee weakness imports exports",
]


def _safe_text(value: object) -> str:
    """Return a stripped string."""
    if value is None:
        return ""
    return str(value).strip()


def _strip_html(value: object) -> str:
    """Convert HTML text into plain text."""
    cleaned = _HTML_TAG_RE.sub(" ", _safe_text(value))
    return re.sub(r"\s+", " ", unescape(cleaned)).strip()


def _google_news_rss_url(query: str) -> str:
    """Build a Google News RSS URL for one search query."""
    encoded = quote_plus(query)
    return f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"


def _fetch_rss_items(url: str, limit: int = 8) -> tuple[list[dict[str, str]], str | None]:
    """Fetch normalized items from one RSS feed."""
    request = Request(url, headers={"User-Agent": "FundamentalAnalyzer/1.0"})
    try:
        with urlopen(request, timeout=8) as response:
            payload = response.read()
    except Exception as exc:  # pragma: no cover - network dependent
        return [], str(exc)

    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        return [], str(exc)

    items: list[dict[str, str]] = []
    for item in root.findall(".//item")[:limit]:
        title = _strip_html(item.findtext("title"))
        if not title:
            continue
        url = _safe_text(item.findtext("link"))
        items.append(
            {
                "title": title,
                "source": urlparse(url).netloc.replace("www.", "") if url else "unknown",
                "published_at": _safe_text(item.findtext("pubDate")),
                "url": url,
                "snippet": _strip_html(item.findtext("description")),
            }
        )
    return items, None


def _deduplicate_items(items: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """Deduplicate news items by title and URL."""
    deduplicated: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (_safe_text(item.get("title")).lower(), _safe_text(item.get("url")))
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(item)
    return deduplicated


def _fetch_queries(queries: list[str], limit_per_query: int = 6) -> dict[str, object]:
    """Fetch news across multiple queries with normalized output."""
    all_items: list[dict[str, str]] = []
    source_errors: list[str] = []
    for query in queries:
        items, error = _fetch_rss_items(_google_news_rss_url(query), limit=limit_per_query)
        all_items.extend(items)
        if error:
            source_errors.append(error)
    return {
        "items": _deduplicate_items(all_items),
        "errors": source_errors,
    }


def fetch_company_news(ticker: str, company_name: str | None = None, limit: int = 8) -> dict[str, object]:
    """Fetch recent company-specific news."""
    cleaned_ticker = _safe_text(ticker).upper()
    cleaned_name = _safe_text(company_name)
    queries = [part for part in [f'"{cleaned_name}" stock', f'"{cleaned_ticker}" stock'] if part.strip('" stock')]
    if cleaned_name and cleaned_ticker:
        queries.insert(0, f'"{cleaned_name}" "{cleaned_ticker}"')
    result = _fetch_queries(queries or [cleaned_name or cleaned_ticker], limit_per_query=max(3, limit // max(len(queries), 1)))
    return {
        "query_type": "company",
        "ticker": cleaned_ticker,
        "company_name": cleaned_name,
        "items": list(result["items"])[:limit],
        "errors": result["errors"],
    }


def fetch_sector_news(sector_name: str, limit: int = 8) -> dict[str, object]:
    """Fetch recent sector-level news."""
    cleaned_sector = _safe_text(sector_name)
    result = _fetch_queries(
        [
            f'"{cleaned_sector}" sector India stocks',
            f'"{cleaned_sector}" demand regulation India',
        ],
        limit_per_query=max(3, limit // 2),
    )
    return {
        "query_type": "sector",
        "sector_name": cleaned_sector,
        "items": list(result["items"])[:limit],
        "errors": result["errors"],
    }


def fetch_macro_news(limit: int = 12) -> dict[str, object]:
    """Fetch macroeconomic, policy, and geopolitical news."""
    result = _fetch_queries(MACRO_NEWS_QUERIES, limit_per_query=4)
    return {
        "query_type": "macro",
        "items": list(result["items"])[:limit],
        "errors": result["errors"],
    }
