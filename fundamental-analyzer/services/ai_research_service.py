"""Deterministic AI-style research assistant built on existing app modules."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from core.analysis_engine import build_analysis
from core.classifier import classify_market_cap
from services.auth_service import require_current_user_id
from services.google_news_service import fetch_business_news, fetch_geopolitical_news, fetch_india_policy_news
from services.holdings_service import calculate_holdings
from services.monitor_news_classifier import classify_monitor_news_items
from services.monitor_portfolio_mapping_service import map_monitor_news_to_portfolio
from services.portfolio_impact_summary_service import build_portfolio_impact_summary
from services.portfolio_service import web_payload_to_company_data
from services.rule_service import RuleService
from services.web_data_service import fetch_company_data

_COMPARE_PATTERN = re.compile(r"compare\s+(.+?)\s+(?:vs|versus)\s+(.+)", re.IGNORECASE)
_ANALYZE_PATTERN = re.compile(r"(?:analyze|analyse|review|explain)\s+(.+)", re.IGNORECASE)

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


def _normalize_query(question: str) -> str:
    """Normalize one user query for routing."""
    return " ".join(str(question or "").strip().split())


def _is_portfolio_query(question: str) -> bool:
    """Return whether a question is portfolio-oriented."""
    text = question.lower()
    return any(token in text for token in {"my portfolio", "portfolio", "holdings", "allocation", "portfolio risk"})


def _is_news_query(question: str) -> bool:
    """Return whether a question is asking about news or news impact."""
    text = question.lower()
    return any(token in text for token in {"news", "headline", "impact", "macro", "geopolitical"})


def _coerce_symbol(candidate: str) -> str:
    """Resolve a company or ticker input into an NSE-style symbol when possible."""
    cleaned = str(candidate or "").strip()
    lowered = cleaned.lower()
    if lowered in _COMPANY_NAME_MAP:
        return _COMPANY_NAME_MAP[lowered]
    if "." in cleaned:
        return cleaned.upper()
    if " " not in cleaned and cleaned.isalpha():
        return f"{cleaned.upper()}.NS"
    return cleaned.upper()


def _extract_company_target(question: str) -> str | None:
    """Extract one target company string from a natural-language question."""
    match = _ANALYZE_PATTERN.search(question)
    if match:
        return match.group(1).strip()
    stripped = question.strip()
    if stripped:
        return stripped
    return None


def _build_company_analysis(target: str) -> tuple[str, Any, Any]:
    """Fetch company data and build the existing analysis result."""
    symbol = _coerce_symbol(target)
    payload = fetch_company_data(symbol)
    company_data = web_payload_to_company_data(payload, source_file=f"web:{symbol}")
    market_cap_category = classify_market_cap(company_data.market_cap_cr)
    rule_service = RuleService()
    rules = rule_service.get_rules(market_cap_category)
    analysis = build_analysis(company_data, market_cap_category, rules)
    return symbol, company_data, analysis


def _scorecard_lines(analysis: Any) -> list[str]:
    """Format category scorecard lines."""
    lines: list[str] = []
    for detail in analysis.scorecard.details:
        lines.append(f"- {detail.category}: {detail.passed}/{detail.applicable} ({detail.score}/10)")
    return lines


def answer_company_query(question: str) -> str:
    """Answer one company-focused research query."""
    target = _extract_company_target(question)
    if not target:
        raise ValueError("A company name or ticker is required.")

    symbol, company_data, analysis = _build_company_analysis(target)
    strengths = analysis.strengths[:3] or ["No clear strengths were identified."]
    weaknesses = analysis.weaknesses[:3] or ["No major weaknesses were identified."]
    return "\n".join(
        [
            f"### {analysis.company_name} ({symbol})",
            f"- Market-cap bucket: {analysis.market_cap_category.replace('_', ' ').title()}",
            f"- Final verdict: {analysis.final_verdict}",
            f"- Suggestion: {analysis.suggestion.label} ({analysis.suggestion.confidence} confidence)",
            f"- Risk level: {analysis.risk_scan.overall_risk_level}",
            f"- Scorecard: {analysis.scorecard.total_score}/{analysis.scorecard.max_score}",
            f"- Valuation: {analysis.intrinsic_value.valuation_summary}",
            f"- Earnings quality: {analysis.earnings_quality.summary}",
            "",
            "#### Strongest signals",
            *strengths,
            "",
            "#### Weakest signals",
            *weaknesses,
            "",
            "#### Category scorecard",
            *_scorecard_lines(analysis),
        ]
    )


def compare_companies(question: str) -> str:
    """Compare two companies using the existing analysis engine."""
    match = _COMPARE_PATTERN.search(question)
    if not match:
        raise ValueError("Use a comparison query like: Compare HDFC Bank vs ICICI Bank")

    left_target, right_target = match.group(1).strip(), match.group(2).strip()
    left_symbol, left_company, left_analysis = _build_company_analysis(left_target)
    right_symbol, right_company, right_analysis = _build_company_analysis(right_target)

    def _winner(left: float | None, right: float | None, higher_is_better: bool = True) -> str:
        if left is None or right is None:
            return "Insufficient data"
        if left == right:
            return "Even"
        if higher_is_better:
            return left_analysis.company_name if left > right else right_analysis.company_name
        return left_analysis.company_name if left < right else right_analysis.company_name

    return "\n".join(
        [
            f"### Comparison: {left_analysis.company_name} vs {right_analysis.company_name}",
            "",
            "| Metric | " + left_symbol + " | " + right_symbol + " | Better positioned |",
            "|---|---:|---:|---|",
            f"| Scorecard | {left_analysis.scorecard.total_score}/{left_analysis.scorecard.max_score} | {right_analysis.scorecard.total_score}/{right_analysis.scorecard.max_score} | {_winner(left_analysis.scorecard.total_score, right_analysis.scorecard.total_score)} |",
            f"| ROE | {left_company.roe if left_company.roe is not None else 'NA'} | {right_company.roe if right_company.roe is not None else 'NA'} | {_winner(left_company.roe, right_company.roe)} |",
            f"| ROCE | {left_company.roce if left_company.roce is not None else 'NA'} | {right_company.roce if right_company.roce is not None else 'NA'} | {_winner(left_company.roce, right_company.roce)} |",
            f"| Sales Growth 5Y | {left_company.sales_growth_5y if left_company.sales_growth_5y is not None else 'NA'} | {right_company.sales_growth_5y if right_company.sales_growth_5y is not None else 'NA'} | {_winner(left_company.sales_growth_5y, right_company.sales_growth_5y)} |",
            f"| Debt/Equity | {left_company.debt_to_equity if left_company.debt_to_equity is not None else 'NA'} | {right_company.debt_to_equity if right_company.debt_to_equity is not None else 'NA'} | {_winner(left_company.debt_to_equity, right_company.debt_to_equity, higher_is_better=False)} |",
            "",
            f"- {left_analysis.company_name}: {left_analysis.final_verdict}; suggestion = {left_analysis.suggestion.label}; risk = {left_analysis.risk_scan.overall_risk_level}.",
            f"- {right_analysis.company_name}: {right_analysis.final_verdict}; suggestion = {right_analysis.suggestion.label}; risk = {right_analysis.risk_scan.overall_risk_level}.",
        ]
    )


def answer_portfolio_query(question: str, user_id: int | None = None) -> str:
    """Answer one portfolio-focused query from current holdings and research overlays."""
    del question
    resolved_user_id = user_id if user_id is not None else require_current_user_id()
    del resolved_user_id
    holdings = calculate_holdings()
    if holdings.empty:
        return "### Portfolio\nNo holdings are available yet. Add transactions or import a portfolio first."

    total_value = float(holdings["Current Value"].fillna(0).sum())
    risk_counts = holdings["Risk"].fillna("Unknown").astype(str).value_counts().to_dict() if "Risk" in holdings.columns else {}
    highest_risk = holdings.sort_values(by=["Red Flags", "Unrealized P&L"], ascending=[False, True]).head(3)
    strongest = holdings.sort_values(by="Score", ascending=False).head(3)

    lines = [
        "### Portfolio Risk Review",
        f"- Holdings tracked: {len(holdings)}",
        f"- Current portfolio value: Rs {total_value:,.2f}",
        f"- Risk mix: {', '.join(f'{key}={value}' for key, value in risk_counts.items()) if risk_counts else 'No risk labels available'}",
        "",
        "#### Highest-risk holdings",
    ]
    for row in highest_risk.itertuples(index=False):
        lines.append(
            f"- {getattr(row, 'Ticker', 'Unknown')}: risk = {getattr(row, 'Risk', 'Unknown')}, red flags = {getattr(row, 'Red Flags', 0)}, suggestion = {getattr(row, 'Suggestion', 'NA')}."
        )
    lines.append("")
    lines.append("#### Strongest holdings by score")
    for row in strongest.itertuples(index=False):
        lines.append(
            f"- {getattr(row, 'Ticker', 'Unknown')}: score = {getattr(row, 'Score', 'NA')}, suggestion = {getattr(row, 'Suggestion', 'NA')}, thesis = {getattr(row, 'Thesis Summary', 'NA')}."
        )
    return "\n".join(lines)


def explain_news_impact(question: str, user_id: int | None = None) -> str:
    """Explain current news impact for the portfolio or a named company."""
    resolved_user_id = user_id if user_id is not None else require_current_user_id()
    del resolved_user_id

    holdings = calculate_holdings()
    if holdings.empty:
        return "### News Impact\nNo holdings are available yet, so there is no portfolio news impact to explain."

    geopolitical_news = classify_monitor_news_items(list(fetch_geopolitical_news(limit=8).get("items", [])))
    india_policy_news = classify_monitor_news_items(list(fetch_india_policy_news(limit=8).get("items", [])))
    business_news = classify_monitor_news_items(list(fetch_business_news(limit=8).get("items", [])))
    all_news = geopolitical_news + india_policy_news + business_news

    impact_rows = map_monitor_news_to_portfolio(user_id=0, holdings=holdings, news_items=all_news)
    if not impact_rows:
        return "### News Impact\nNo current headlines were mapped to the portfolio holdings."

    summary = build_portfolio_impact_summary(impact_rows)
    query_text = question.lower()
    filtered_rows = impact_rows
    if not _is_portfolio_query(question):
        target = _extract_company_target(question)
        if target:
            target_key = target.lower()
            filtered_rows = [
                row for row in impact_rows if target_key in str(row.get("ticker", "")).lower() or target_key in str(row.get("company_name", "")).lower()
            ]
            if not filtered_rows:
                filtered_rows = impact_rows[:5]

    lines = [
        "### News Impact Explanation",
        f"- Portfolio summary: {summary.get('summary_text')}",
        "",
        "#### Most relevant current items",
    ]
    for row in filtered_rows[:5]:
        lines.append(
            f"- {row.get('ticker')}: {row.get('event_title')} | {row.get('impact_direction')} | {row.get('severity')} | {row.get('why_it_matters')}"
        )
    return "\n".join(lines)


def _portfolio_scanner_snapshot() -> str:
    """Return a concise portfolio scanner snapshot for tool-style questions."""
    holdings = calculate_holdings()
    if holdings.empty:
        return "No holdings are available for a portfolio scan."
    weak = holdings[holdings["Risk"].astype(str).str.lower().isin({"high", "moderate"})] if "Risk" in holdings.columns else pd.DataFrame()
    return (
        f"{len(holdings)} holdings scanned. "
        f"{len(weak)} holdings currently carry Moderate/High risk labels."
    )


def answer_research_query(question: str, user_id: int | None = None) -> str:
    """Route one natural-language query to the correct deterministic helper."""
    normalized = _normalize_query(question)
    if not normalized:
        raise ValueError("Enter a question to start the research assistant.")

    lowered = normalized.lower()
    if _COMPARE_PATTERN.search(normalized):
        return compare_companies(normalized)
    if "portfolio scanner" in lowered:
        return f"### Portfolio Scanner\n{_portfolio_scanner_snapshot()}"
    if _is_news_query(lowered):
        return explain_news_impact(normalized, user_id=user_id)
    if _is_portfolio_query(lowered) or "what risks exist" in lowered:
        return answer_portfolio_query(normalized, user_id=user_id)
    return answer_company_query(normalized)
