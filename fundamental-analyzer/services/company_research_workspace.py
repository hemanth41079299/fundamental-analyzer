"""Investment dossier workspace service for company-level research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any

import pandas as pd

from core.analysis_engine import build_analysis
from core.classifier import classify_market_cap
from models.company_data import CompanyData
from models.result_model import AnalysisResult
from services.auth_service import require_current_user_id
from services.db import get_connection
from services.geopolitical_impact_service import build_geopolitical_impact
from services.holdings_service import calculate_holdings
from services.news_fetch_service import fetch_company_news, fetch_macro_news
from services.news_impact_classifier import classify_news_item
from services.news_risk_service import scan_company_news_risk
from services.portfolio_service import web_payload_to_company_data
from services.rule_service import RuleService
from services.watchlist_service import get_watchlist
from services.web_data_service import fetch_company_data

_COMPANY_NAME_MAP: dict[str, str] = {
    "tata motors": "TATAMOTORS.NS",
    "hdfc bank": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "infosys": "INFY.NS",
    "itc": "ITC.NS",
    "tata power": "TATAPOWER.NS",
    "bharat electronics": "BEL.NS",
    "bel": "BEL.NS",
}
_NORMALIZE_RE = re.compile(r"[^A-Z0-9]")


@dataclass
class CompanyWorkspaceRecord:
    """Editable user-authored fields for one company dossier."""

    company_key: str
    ticker: str | None
    company_name: str
    ai_summary: str
    investment_thesis: str
    bear_case: str
    watch_triggers: str
    research_notes: str
    updated_at: str | None = None


def _normalize_company_key(value: str) -> str:
    """Normalize one company key for storage and lookup."""
    cleaned = str(value or "").strip().upper()
    cleaned = cleaned.split(".", 1)[0]
    return _NORMALIZE_RE.sub("", cleaned)


def _coerce_symbol(company_input: str) -> str:
    """Resolve one company input into a likely ticker."""
    cleaned = str(company_input or "").strip()
    if not cleaned:
        raise ValueError("Enter a company name or ticker.")
    lowered = cleaned.lower()
    if lowered in _COMPANY_NAME_MAP:
        return _COMPANY_NAME_MAP[lowered]
    if "." in cleaned:
        return cleaned.upper()
    if " " not in cleaned and cleaned.isalpha():
        return f"{cleaned.upper()}.NS"
    return cleaned.upper()


def _build_analysis_context(company_input: str) -> tuple[str, CompanyData, AnalysisResult, str]:
    """Fetch company fundamentals and build the standard analysis result."""
    symbol = _coerce_symbol(company_input)
    payload = fetch_company_data(symbol)
    company_data = web_payload_to_company_data(payload, source_file=f"web:{symbol}")
    market_cap_category = classify_market_cap(company_data.market_cap_cr)
    rule_service = RuleService()
    rules = rule_service.get_rules(market_cap_category)
    analysis_result = build_analysis(company_data, market_cap_category, rules)
    return symbol, company_data, analysis_result, market_cap_category


def _key_metrics(company_data: CompanyData) -> pd.DataFrame:
    """Build the dossier key-metrics table."""
    metrics = [
        ("Market Cap (Cr)", company_data.market_cap_cr),
        ("Current Price", company_data.current_price),
        ("PE", company_data.stock_pe),
        ("ROE", company_data.roe),
        ("ROCE", company_data.roce),
        ("Sales Growth 5Y", company_data.sales_growth_5y),
        ("Profit Growth 5Y", company_data.profit_growth_5y),
        ("OPM", company_data.opm),
        ("Debt To Equity", company_data.debt_to_equity),
        ("Promoter Holding", company_data.promoter_holding),
    ]
    return pd.DataFrame(
        [{"Metric": label, "Value": "NA" if value is None else value} for label, value in metrics]
    )


def _rule_output_frame(analysis_result: AnalysisResult) -> pd.DataFrame:
    """Build the rule-output table for the dossier."""
    return pd.DataFrame([result.to_dict() for result in analysis_result.rule_results])


def _build_news_intelligence(ticker: str, company_name: str) -> dict[str, object]:
    """Build news intelligence and macro relevance for one company."""
    company_news = fetch_company_news(ticker=ticker, company_name=company_name, limit=6)
    recent_news = []
    for item in list(company_news.get("items", []))[:6]:
        classification = classify_news_item(item)
        recent_news.append(
            {
                "Title": item.get("title"),
                "Type": classification["event_type"],
                "Direction": classification["impact_direction"],
                "Severity": classification["severity"],
                "Source": item.get("source"),
                "Date": item.get("published_at"),
            }
        )

    macro_fetch = fetch_macro_news(limit=8)
    holding_frame = pd.DataFrame(
        [
            {
                "Ticker": ticker,
                "Company": company_name,
                "Sector": "Unknown",
                "Current Value": 100.0,
            }
        ]
    )
    macro_mapping = build_geopolitical_impact(holding_frame, list(macro_fetch.get("items", [])))
    news_risk = scan_company_news_risk(ticker=ticker, company_name=company_name)
    return {
        "recent_news": pd.DataFrame(recent_news),
        "macro_events": list(macro_mapping.get("macro_events", [])),
        "exposure_map": dict(macro_mapping.get("exposure_map", {})),
        "source_errors": list(company_news.get("errors", [])) + list(macro_fetch.get("errors", [])),
        "news_risk": news_risk,
    }


def _build_portfolio_exposure(ticker: str) -> dict[str, object]:
    """Build portfolio and watchlist exposure context for one company."""
    holdings = calculate_holdings()
    watchlist = get_watchlist()

    normalized_ticker = str(ticker).strip().upper()
    exposure = {
        "in_portfolio": False,
        "portfolio_weight": 0.0,
        "quantity": 0.0,
        "current_value": 0.0,
        "suggestion": None,
        "risk": None,
        "on_watchlist": False,
    }

    if not holdings.empty and "Ticker" in holdings.columns:
        matched = holdings[holdings["Ticker"].astype(str).str.upper() == normalized_ticker]
        if not matched.empty:
            total_value = float(holdings["Current Value"].fillna(0).sum()) if "Current Value" in holdings.columns else 0.0
            row = matched.iloc[0]
            current_value = float(row.get("Current Value") or 0.0)
            exposure.update(
                {
                    "in_portfolio": True,
                    "portfolio_weight": round((current_value / total_value) * 100, 2) if total_value > 0 else 0.0,
                    "quantity": float(row.get("Qty") or 0.0),
                    "current_value": current_value,
                    "suggestion": row.get("Suggestion"),
                    "risk": row.get("Risk"),
                }
            )

    if not watchlist.empty and "ticker" in watchlist.columns:
        exposure["on_watchlist"] = bool(
            (watchlist["ticker"].astype(str).str.upper() == normalized_ticker).any()
        )
    return exposure


def _default_ai_summary(company_name: str, analysis_result: AnalysisResult, exposure: dict[str, object]) -> str:
    """Build the default AI company summary text."""
    exposure_text = (
        f"The company is currently held in the portfolio at {exposure['portfolio_weight']}% weight."
        if exposure["in_portfolio"]
        else "The company is not currently held in the live portfolio."
    )
    return (
        f"{company_name} is classified as a {analysis_result.market_cap_category.replace('_', ' ')} company. "
        f"The current rule-based verdict is '{analysis_result.final_verdict}', with suggestion label "
        f"'{analysis_result.suggestion.label}' and overall risk level '{analysis_result.risk_scan.overall_risk_level}'. "
        f"{exposure_text}"
    )


def _default_investment_thesis(analysis_result: AnalysisResult) -> str:
    """Build the default investment thesis text."""
    if analysis_result.thesis.bull_case:
        return " ".join(analysis_result.thesis.bull_case[:3])
    return analysis_result.final_verdict


def _default_bear_case(analysis_result: AnalysisResult) -> str:
    """Build the default bear-case text."""
    if analysis_result.thesis.bear_case:
        return " ".join(analysis_result.thesis.bear_case[:3])
    if analysis_result.weaknesses:
        return " ".join(analysis_result.weaknesses[:2])
    return "No major bear case has been documented yet."


def _default_watch_triggers(analysis_result: AnalysisResult) -> str:
    """Build the default watch-trigger text."""
    if analysis_result.thesis.key_triggers:
        return "; ".join(analysis_result.thesis.key_triggers[:4])
    return "Monitor quarterly score changes, valuation range, and external news impact."


def load_company_workspace_record(company_key: str) -> CompanyWorkspaceRecord | None:
    """Load one saved company workspace record for the authenticated user."""
    user_id = require_current_user_id()
    normalized_key = _normalize_company_key(company_key)
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT company_key, ticker, company_name, ai_summary, investment_thesis,
                   bear_case, watch_triggers, research_notes, updated_at
            FROM company_workspaces
            WHERE user_id = %s AND company_key = %s
            """,
            (user_id, normalized_key),
        ).fetchone()
    if row is None:
        return None
    return CompanyWorkspaceRecord(
        company_key=str(row["company_key"]),
        ticker=row["ticker"],
        company_name=str(row["company_name"]),
        ai_summary=str(row["ai_summary"] or ""),
        investment_thesis=str(row["investment_thesis"] or ""),
        bear_case=str(row["bear_case"] or ""),
        watch_triggers=str(row["watch_triggers"] or ""),
        research_notes=str(row["research_notes"] or ""),
        updated_at=row["updated_at"],
    )


def save_company_workspace_record(record: CompanyWorkspaceRecord) -> None:
    """Upsert one company workspace record for the authenticated user."""
    user_id = require_current_user_id()
    updated_at = datetime.utcnow().isoformat(timespec="seconds")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO company_workspaces (
                user_id, company_key, ticker, company_name, ai_summary, investment_thesis,
                bear_case, watch_triggers, research_notes, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, company_key)
            DO UPDATE SET
                ticker = excluded.ticker,
                company_name = excluded.company_name,
                ai_summary = excluded.ai_summary,
                investment_thesis = excluded.investment_thesis,
                bear_case = excluded.bear_case,
                watch_triggers = excluded.watch_triggers,
                research_notes = excluded.research_notes,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                record.company_key,
                record.ticker,
                record.company_name,
                record.ai_summary,
                record.investment_thesis,
                record.bear_case,
                record.watch_triggers,
                record.research_notes,
                updated_at,
            ),
        )
        connection.commit()


def build_company_workspace(company_input: str) -> dict[str, object]:
    """Build one complete investment dossier from stored and live research data."""
    ticker, company_data, analysis_result, market_cap_category = _build_analysis_context(company_input)
    company_key = _normalize_company_key(ticker or company_data.company_name or company_input)
    saved_record = load_company_workspace_record(company_key)
    portfolio_exposure = _build_portfolio_exposure(ticker)
    news_intelligence = _build_news_intelligence(ticker, analysis_result.company_name)

    workspace_record = CompanyWorkspaceRecord(
        company_key=company_key,
        ticker=ticker,
        company_name=analysis_result.company_name,
        ai_summary=(saved_record.ai_summary if saved_record and saved_record.ai_summary else _default_ai_summary(analysis_result.company_name, analysis_result, portfolio_exposure)),
        investment_thesis=(saved_record.investment_thesis if saved_record and saved_record.investment_thesis else _default_investment_thesis(analysis_result)),
        bear_case=(saved_record.bear_case if saved_record and saved_record.bear_case else _default_bear_case(analysis_result)),
        watch_triggers=(saved_record.watch_triggers if saved_record and saved_record.watch_triggers else _default_watch_triggers(analysis_result)),
        research_notes=(saved_record.research_notes if saved_record else ""),
        updated_at=saved_record.updated_at if saved_record else None,
    )

    return {
        "ticker": ticker,
        "company_name": analysis_result.company_name,
        "market_cap_category": market_cap_category,
        "company_data": company_data,
        "analysis_result": analysis_result,
        "workspace_record": workspace_record,
        "key_metrics": _key_metrics(company_data),
        "rule_output": _rule_output_frame(analysis_result),
        "news_intelligence": news_intelligence,
        "portfolio_exposure": portfolio_exposure,
    }
