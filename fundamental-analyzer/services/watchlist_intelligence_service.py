"""Watchlist intelligence and alerting service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import DEFAULT_RULES_PATH
from core.analysis_engine import build_analysis
from core.classifier import classify_market_cap
from models.rule_model import Rule
from services.db import get_connection
from services.geopolitical_impact_service import build_geopolitical_impact
from services.news_fetch_service import fetch_company_news, fetch_macro_news
from services.news_impact_classifier import classify_news_item
from services.portfolio_service import web_payload_to_company_data
from services.web_data_service import fetch_company_data


def _safe_float(value: Any) -> float | None:
    """Convert a raw value to ``float`` when possible."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_rules(raw_rules: list[dict[str, object]]) -> list[Rule]:
    """Convert rule dictionaries into rule models."""
    rules: list[Rule] = []
    for raw_rule in raw_rules:
        rules.append(
            Rule(
                parameter=str(raw_rule.get("parameter", "")).strip(),
                operator=str(raw_rule.get("operator", "")).strip(),
                value=float(raw_rule.get("value", 0)),
                rationale=str(raw_rule.get("rationale", "")).strip(),
                category=str(raw_rule.get("category")).strip() if raw_rule.get("category") else None,
                label=str(raw_rule.get("label")).strip() if raw_rule.get("label") else None,
            )
        )
    return rules


def _load_default_rules() -> dict[str, list[dict[str, object]]]:
    """Load the default market-cap rule sets."""
    path = Path(DEFAULT_RULES_PATH)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_rules_for_user(user_id: int, category: str) -> list[Rule]:
    """Load user custom rules for a category or fall back to defaults."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT rules_json FROM custom_rules WHERE user_id = %s AND category = %s",
            (int(user_id), category),
        ).fetchone()

    if row is not None:
        try:
            return _coerce_rules(json.loads(str(row["rules_json"])))
        except json.JSONDecodeError:
            return []

    default_rules = _load_default_rules()
    return _coerce_rules(default_rules.get(category, []))


def _load_watchlist_items(user_id: int) -> pd.DataFrame:
    """Return watchlist items for a user."""
    with get_connection() as connection:
        frame = pd.read_sql_query(
            "SELECT id, ticker, company_name, added_on, notes FROM watchlist WHERE user_id = %s ORDER BY added_on DESC, id DESC",
            connection,
            params=(int(user_id),),
        )
    return frame


def _load_company_history_entries(user_id: int, ticker: str, company_name: str) -> list[dict[str, Any]]:
    """Load historical research entries for a watchlist company."""
    source_candidates = [f"web:{ticker.upper().strip()}", f"portfolio:{ticker.upper().strip()}"]
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT timestamp, company_name, source_file, metrics_json, score, total_score, verdict, narration
            FROM company_history
            WHERE user_id = %s
              AND (
                    company_name = %s
                    OR source_file = %s
                    OR source_file = %s
              )
            ORDER BY timestamp ASC, id ASC
            """,
            (int(user_id), company_name.strip(), source_candidates[0], source_candidates[1]),
        ).fetchall()

    history: list[dict[str, Any]] = []
    for row in rows:
        try:
            metrics = json.loads(str(row["metrics_json"]))
        except json.JSONDecodeError:
            metrics = {}
        history.append(
            {
                "timestamp": row["timestamp"],
                "company_name": row["company_name"],
                "source_file": row["source_file"],
                "metrics": metrics,
                "score": _safe_float(row["score"]),
                "total_score": _safe_float(row["total_score"]),
                "verdict": row["verdict"],
                "narration": row["narration"],
            }
        )
    return history


def _score_on_ten(total_score: float | None) -> float | None:
    """Convert a 0-100 total score into a 0-10 score."""
    if total_score is None:
        return None
    return round(float(total_score) / 10.0, 1)


def _format_score(value: float | None) -> str:
    """Format a 0-10 score for alerts."""
    if value is None:
        return "NA"
    if value.is_integer():
        return str(int(value))
    return f"{value:.1f}"


def rank_watchlist_companies(user_id: int) -> list[dict[str, object]]:
    """Rank watchlist companies by current analysis score."""
    watchlist = _load_watchlist_items(user_id)
    ranked: list[dict[str, object]] = []

    for row in watchlist.itertuples(index=False):
        ticker = str(row.ticker).strip().upper()
        company_name = str(row.company_name or "").strip()
        try:
            payload = fetch_company_data(ticker)
            company_data = web_payload_to_company_data(payload, source_file=f"web:{ticker}")
            category = classify_market_cap(company_data.market_cap_cr)
            rules = _load_rules_for_user(user_id, category)
            analysis = build_analysis(company_data, category, rules)
            ranked.append(
                {
                    "ticker": ticker,
                    "company_name": company_data.company_name or company_name or ticker,
                    "score": analysis.scorecard.total_score,
                    "score_on_10": _score_on_ten(analysis.scorecard.total_score),
                    "suggestion": analysis.suggestion.label,
                    "risk": analysis.risk_scan.overall_risk_level,
                    "valuation_summary": analysis.intrinsic_value.valuation_summary,
                    "debt_to_equity": company_data.debt_to_equity,
                    "sales_growth_5y": company_data.sales_growth_5y,
                    "profit_growth_5y": company_data.profit_growth_5y,
                    "pe": company_data.stock_pe,
                    "category": category,
                    "sector": payload.get("sector") or "Unknown",
                }
            )
        except Exception as exc:
            ranked.append(
                {
                    "ticker": ticker,
                    "company_name": company_name or ticker,
                    "score": None,
                    "score_on_10": None,
                    "suggestion": "Unavailable",
                    "risk": "Unknown",
                    "valuation_summary": None,
                    "debt_to_equity": None,
                    "sales_growth_5y": None,
                    "profit_growth_5y": None,
                    "pe": None,
                    "category": "unknown",
                    "sector": "Unknown",
                    "error": str(exc),
                }
            )

    return sorted(ranked, key=lambda item: (item.get("score") is None, -(item.get("score") or 0.0)))


def detect_score_improvements(current_items: list[dict[str, object]], user_id: int) -> list[dict[str, str]]:
    """Detect score improvements versus the latest stored research snapshot."""
    alerts: list[dict[str, str]] = []
    for item in current_items:
        ticker = str(item["ticker"])
        company_name = str(item["company_name"])
        current_score = _safe_float(item.get("score"))
        if current_score is None:
            continue

        history = _load_company_history_entries(user_id, ticker, company_name)
        if not history:
            continue

        previous_score = _safe_float(history[-1].get("total_score"))
        if previous_score is None:
            continue

        current_score_10 = _score_on_ten(current_score)
        previous_score_10 = _score_on_ten(previous_score)
        if current_score_10 is not None and previous_score_10 is not None and current_score_10 >= previous_score_10 + 0.5:
            alerts.append(
                {
                    "ticker": ticker,
                    "message": f"Score improved from {_format_score(previous_score_10)} -> {_format_score(current_score_10)}",
                }
            )
    return alerts


def detect_valuation_improvements(current_items: list[dict[str, object]], user_id: int) -> list[dict[str, str]]:
    """Detect valuation improvements based on current PE versus historical PE levels."""
    alerts: list[dict[str, str]] = []
    for item in current_items:
        ticker = str(item["ticker"])
        company_name = str(item["company_name"])
        current_pe = _safe_float(item.get("pe"))
        if current_pe is None:
            continue

        history = _load_company_history_entries(user_id, ticker, company_name)
        historical_pes = [
            _safe_float(entry.get("metrics", {}).get("stock_pe"))
            for entry in history
        ]
        historical_pes = [value for value in historical_pes if value is not None]
        if not historical_pes:
            continue

        historical_average = sum(historical_pes) / len(historical_pes)
        latest_historical_pe = historical_pes[-1]
        if current_pe <= historical_average * 0.9:
            alerts.append({"ticker": ticker, "message": "PE dropped below historical average"})
        elif current_pe <= latest_historical_pe * 0.9:
            alerts.append({"ticker": ticker, "message": "Valuation improved versus the previous review"})
    return alerts


def detect_debt_reduction(current_items: list[dict[str, object]], user_id: int) -> list[dict[str, str]]:
    """Detect improving balance-sheet leverage."""
    alerts: list[dict[str, str]] = []
    for item in current_items:
        ticker = str(item["ticker"])
        company_name = str(item["company_name"])
        current_debt = _safe_float(item.get("debt_to_equity"))
        if current_debt is None:
            continue

        history = _load_company_history_entries(user_id, ticker, company_name)
        if not history:
            continue
        previous_debt = _safe_float(history[-1].get("metrics", {}).get("debt_to_equity"))
        if previous_debt is not None and current_debt <= previous_debt - 0.1:
            alerts.append({"ticker": ticker, "message": "Debt to equity has improved meaningfully since the last review"})
    return alerts


def detect_growth_acceleration(current_items: list[dict[str, object]], user_id: int) -> list[dict[str, str]]:
    """Detect improving long-term growth metrics."""
    alerts: list[dict[str, str]] = []
    for item in current_items:
        ticker = str(item["ticker"])
        company_name = str(item["company_name"])
        current_sales_growth = _safe_float(item.get("sales_growth_5y"))
        current_profit_growth = _safe_float(item.get("profit_growth_5y"))

        history = _load_company_history_entries(user_id, ticker, company_name)
        if not history:
            continue
        previous_metrics = history[-1].get("metrics", {})
        previous_sales_growth = _safe_float(previous_metrics.get("sales_growth_5y"))
        previous_profit_growth = _safe_float(previous_metrics.get("profit_growth_5y"))

        if current_sales_growth is not None and previous_sales_growth is not None and current_sales_growth >= previous_sales_growth + 3:
            alerts.append({"ticker": ticker, "message": "Sales growth is accelerating versus the previous review"})
        elif current_profit_growth is not None and previous_profit_growth is not None and current_profit_growth >= previous_profit_growth + 3:
            alerts.append({"ticker": ticker, "message": "Profit growth is accelerating versus the previous review"})
    return alerts


def generate_watchlist_alerts(current_items: list[dict[str, object]], user_id: int) -> list[dict[str, str]]:
    """Generate consolidated watchlist alerts."""
    alerts: list[dict[str, str]] = []
    alerts.extend(detect_score_improvements(current_items, user_id))
    alerts.extend(detect_valuation_improvements(current_items, user_id))
    alerts.extend(detect_debt_reduction(current_items, user_id))
    alerts.extend(detect_growth_acceleration(current_items, user_id))
    return alerts


def _build_watchlist_news_intelligence(item: dict[str, object], macro_items: list[dict[str, object]]) -> dict[str, object]:
    """Build recent news, catalysts, and risks for one watchlist company."""
    ticker = str(item.get("ticker") or "")
    company_name = str(item.get("company_name") or ticker)
    sector = str(item.get("sector") or "Unknown")
    company_news = fetch_company_news(ticker=ticker, company_name=company_name, limit=4)

    latest_news: list[dict[str, object]] = []
    for news_item in list(company_news.get("items", []))[:4]:
        classification = classify_news_item(news_item)
        latest_news.append(
            {
                "title": news_item.get("title"),
                "source": news_item.get("source"),
                "date": news_item.get("published_at"),
                "event_type": classification["event_type"],
                "direction": classification["impact_direction"],
                "severity": classification["severity"],
            }
        )

    holding_frame = pd.DataFrame(
        [
            {
                "Ticker": ticker,
                "Company": company_name,
                "Sector": sector,
                "Current Value": 100.0,
            }
        ]
    )
    geo_output = build_geopolitical_impact(holding_frame, macro_items)
    policy_macro_triggers = [
        str(event.get("theme"))
        for event in list(geo_output.get("macro_events", []))
        if str(event.get("event_type")) in {"macro", "policy", "geopolitical"}
    ]
    positive_catalysts = [item["title"] for item in latest_news if item["direction"] == "Positive Tailwind"][:3]
    negative_news_alerts = [item["title"] for item in latest_news if item["direction"] == "Negative Headwind"][:3]

    return {
        "latest_news": latest_news[:3],
        "policy_macro_triggers": policy_macro_triggers[:3],
        "positive_catalysts": positive_catalysts,
        "negative_news_alerts": negative_news_alerts,
    }


def build_watchlist_intelligence(user_id: int) -> dict[str, object]:
    """Build ranked watchlist output and derived alerts for a user."""
    ranked_watchlist = rank_watchlist_companies(user_id)
    alerts = generate_watchlist_alerts(ranked_watchlist, user_id)
    macro_news = fetch_macro_news(limit=8)
    enriched_watchlist: list[dict[str, object]] = []
    for item in ranked_watchlist:
        try:
            news_payload = _build_watchlist_news_intelligence(item, list(macro_news.get("items", [])))
        except Exception as exc:
            news_payload = {
                "latest_news": [],
                "policy_macro_triggers": [],
                "positive_catalysts": [],
                "negative_news_alerts": [f"News intelligence unavailable: {exc}"],
            }
        enriched_watchlist.append({**item, **news_payload})
    return {
        "ranked_watchlist": enriched_watchlist,
        "alerts": alerts,
        "source_errors": list(macro_news.get("errors", [])),
    }
