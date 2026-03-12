"""Generate structured analysis output from metrics and rules."""

from __future__ import annotations

from collections import defaultdict

from core.earnings_quality_analyzer import analyze_earnings_quality
from core.intrinsic_value_engine import build_intrinsic_value_analysis
from core.red_flag_detector import detect_red_flags
from core.risk_scanner import run_risk_scan
from core.rule_engine import build_score_summary, build_scorecard_summary, evaluate_rules
from core.suggestion_engine import build_research_suggestion
from core.thesis_engine import build_thesis
from models.company_data import CompanyData
from models.result_model import AnalysisResult, RiskFlagResult, RiskScanSummary, RuleEvaluationResult
from models.rule_model import Rule

OBSERVATION_GROUPS: dict[str, set[str]] = {
    "growth": {"sales_growth_5y", "profit_growth_5y"},
    "profitability": {"roe", "roce"},
    "margins": {"opm"},
    "debt": {"debt_to_equity"},
    "valuation": {"stock_pe", "book_value", "peg_ratio", "industry_pe", "pe", "pb", "peg"},
    "cash_flow": {"cfo", "cfo_5y", "cfo_last_year"},
    "governance": {"promoter_holding", "pledge"},
}


def build_strengths_and_weaknesses(
    results: list[RuleEvaluationResult],
) -> tuple[list[str], list[str]]:
    """Build readable strengths and weaknesses lists from rule results."""
    strengths: list[str] = []
    weaknesses: list[str] = []

    for result in results:
        message = f"{result.parameter} against rule `{result.rule_display}`"
        if result.status == "Pass":
            strengths.append(message)
        elif result.status == "Fail":
            weaknesses.append(message)

    return strengths, weaknesses


def build_observations(results: list[RuleEvaluationResult]) -> dict[str, str]:
    """Build category-wise observation strings."""
    grouped: dict[str, list[str]] = defaultdict(list)

    for result in results:
        matching_groups = [
            group_name
            for group_name, parameters in OBSERVATION_GROUPS.items()
            if result.parameter in parameters
        ]
        if not matching_groups:
            continue

        if result.status == "Pass":
            text = f"{result.parameter} is within the preferred range"
        elif result.status == "Fail":
            text = f"{result.parameter} is outside the preferred range"
        else:
            text = f"{result.parameter} could not be evaluated"

        for group_name in matching_groups:
            grouped[group_name].append(text)

    observations: dict[str, str] = {}
    for group_name in OBSERVATION_GROUPS:
        values = grouped.get(group_name, [])
        observations[group_name] = "; ".join(values) if values else "No clear observation"
    return observations


def build_final_verdict(score_label: str, weaknesses: list[str]) -> str:
    """Generate a concise verdict from score and failure patterns."""
    has_valuation_issue = any(
        any(token in item.lower() for token in {"stock_pe", "peg", "pb", "pe against rule"})
        for item in weaknesses
    )
    has_governance_issue = any("pledge" in item.lower() or "promoter_holding" in item.lower() for item in weaknesses)
    has_cash_issue = any("cfo" in item.lower() for item in weaknesses)

    if score_label == "Excellent" and has_valuation_issue:
        return "Fundamentally strong but expensive"
    if has_governance_issue:
        return "Good growth, weak governance"
    if has_cash_issue:
        return "Average business with poor cash quality"

    fallback = {
        "Excellent": "High-quality business under the selected rules",
        "Strong": "Fundamentally solid with a few manageable gaps",
        "Average": "Average business with mixed signals",
        "Weak": "Weak fundamentals under the selected framework",
    }
    return fallback.get(score_label, "Insufficient data for a clear verdict")


def build_analysis(
    company_data: CompanyData,
    market_cap_category: str,
    rules: list[Rule],
) -> AnalysisResult:
    """Build the full analysis result for a company."""
    results = evaluate_rules(company_data, rules)
    score = build_score_summary(results)
    scorecard = build_scorecard_summary(results)
    raw_risk_scan = run_risk_scan(company_data, results, scorecard)
    intrinsic_value = build_intrinsic_value_analysis(company_data)
    earnings_quality = analyze_earnings_quality(company_data)
    red_flags = detect_red_flags(company_data)
    strengths, weaknesses = build_strengths_and_weaknesses(results)
    observations = build_observations(results)
    verdict = build_final_verdict(score.interpretation, weaknesses)
    thesis = build_thesis(results, verdict)
    risk_scan = RiskScanSummary(
        risk_flags=[
            RiskFlagResult(category=flag.category, severity=flag.severity, message=flag.message)
            for flag in raw_risk_scan.risk_flags
        ],
        overall_risk_level=raw_risk_scan.overall_risk_level,
    )
    suggestion = build_research_suggestion(
        score,
        scorecard,
        risk_scan,
        red_flags,
        intrinsic_value,
        earnings_quality,
        results,
        verdict,
    )

    return AnalysisResult(
        company_name=company_data.company_name or "Unknown Company",
        market_cap_category=market_cap_category,
        rule_results=results,
        score=score,
        scorecard=scorecard,
        thesis=thesis,
        risk_scan=risk_scan,
        suggestion=suggestion,
        intrinsic_value=intrinsic_value,
        earnings_quality=earnings_quality,
        red_flags=red_flags,
        strengths=strengths,
        weaknesses=weaknesses,
        observations=observations,
        final_verdict=verdict,
    )
