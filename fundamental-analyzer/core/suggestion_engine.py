"""Deterministic research suggestion engine."""

from __future__ import annotations

from models.result_model import (
    EarningsQualitySummary,
    IntrinsicValueSummary,
    RedFlagSummary,
    ResearchSuggestionSummary,
    RiskScanSummary,
    RuleEvaluationResult,
    ScoreSummary,
    ScorecardSummary,
)


def _has_risk(risk_scan: RiskScanSummary, category: str, severity: str | None = None) -> bool:
    """Check whether a given risk category exists in the risk scan."""
    for risk_flag in risk_scan.risk_flags:
        if risk_flag.category != category:
            continue
        if severity is None or risk_flag.severity == severity:
            return True
    return False


def _na_ratio(rule_results: list[RuleEvaluationResult]) -> float:
    """Calculate the ratio of NA rule outcomes."""
    if not rule_results:
        return 1.0
    na_count = sum(1 for result in rule_results if result.status == "NA")
    return na_count / len(rule_results)


def build_research_suggestion(
    score: ScoreSummary,
    scorecard: ScorecardSummary,
    risk_scan: RiskScanSummary,
    red_flags: RedFlagSummary,
    intrinsic_value: IntrinsicValueSummary,
    earnings_quality: EarningsQualitySummary,
    rule_results: list[RuleEvaluationResult],
    final_verdict: str,
) -> ResearchSuggestionSummary:
    """Generate a deterministic research suggestion label and explanation."""
    total_score = scorecard.total_score
    na_ratio = _na_ratio(rule_results)
    governance_high = _has_risk(risk_scan, "Governance Risk", "High")
    valuation_risk = _has_risk(risk_scan, "Valuation Risk")
    overall_risk = risk_scan.overall_risk_level
    red_flag_count = red_flags.red_flag_count
    earnings_quality_label = earnings_quality.earnings_quality.lower()
    valuation_summary = intrinsic_value.valuation_summary.lower()
    valuation_expensive = "overvalued" in valuation_summary or valuation_risk
    valuation_fair = "fairly valued" in valuation_summary or (
        intrinsic_value.consensus_fair_value is not None
        and any(model.valuation == "Fair" for model in intrinsic_value.valuation_models)
    )
    low_risk = overall_risk == "Low" and red_flag_count == 0

    if governance_high:
        label = "Governance Concern"
        confidence = "High"
        summary = "Governance-related risk flags dominate the current research view."
        why_this_label = "High-severity governance issues tend to override otherwise positive operational metrics."
        action_points = [
            "Review promoter pledge trends and ownership changes.",
            "Check recent disclosures, related-party items, and governance commentary.",
        ]
    elif red_flag_count > 2:
        label = "Caution Required"
        confidence = "High"
        summary = "Multiple financial red flags reduce confidence in the current research view."
        why_this_label = "More than two red flags indicate recurring accounting, balance-sheet, or cash-flow concerns."
        action_points = [
            "Review the most severe red flags in detail before prioritizing the company.",
            "Check whether the flagged patterns are temporary or recurring across periods.",
        ]
    elif earnings_quality_label == "weak":
        label = "Further Research Needed"
        confidence = "Medium"
        summary = "Reported profit quality is not yet fully supported by cash flow."
        why_this_label = "Weak earnings quality reduces confidence in headline profitability and valuation comfort."
        action_points = [
            "Review cash-flow statements, receivables, and working-capital movements.",
            "Check whether weak cash conversion is structural or cyclical.",
        ]
    elif na_ratio >= 0.4:
        label = "Further Research Needed"
        confidence = "Low"
        summary = "The current dataset is incomplete for a high-confidence research conclusion."
        why_this_label = "A large share of rules could not be evaluated, which reduces confidence in the framework output."
        action_points = [
            "Collect missing financial metrics before prioritizing the company.",
            "Re-run the analysis with richer source data or more complete statements.",
        ]
    elif total_score >= 85 and valuation_expensive:
        label = "High Quality, Expensive"
        confidence = "High"
        summary = "Business quality looks strong, but valuation risk is already visible in the framework."
        why_this_label = "The score is strong, yet valuation-related rules or risk flags indicate limited margin of safety."
        action_points = [
            "Track valuation normalization or better entry levels.",
            "Monitor whether growth continues to justify current multiples.",
        ]
    elif total_score >= 85 and low_risk and valuation_fair:
        label = "Strong Candidate"
        confidence = "High"
        summary = "The company scores well across the framework with limited flagged risks."
        why_this_label = "High category scores and low overall risk suggest a strong research candidate."
        action_points = [
            "Validate the thesis against management commentary and industry context.",
            "Track whether recent performance remains consistent with the framework score.",
        ]
    elif total_score >= 70 and overall_risk in {"Low", "Medium"}:
        label = "Watchlist Candidate"
        confidence = "Medium"
        summary = "The company has enough quality signals to stay on the active research list."
        why_this_label = "The score is constructive, but some gaps or risks still need confirmation."
        action_points = [
            "Watch the weakest scorecard categories over the next few quarters.",
            "Compare the company with direct peers on growth and valuation.",
        ]
    elif valuation_expensive and total_score >= 60:
        label = "Await Better Price"
        confidence = "Medium"
        summary = "The business may be interesting, but valuation comfort is not yet sufficient."
        why_this_label = "Research quality is acceptable, but valuation risk reduces attractiveness under the framework."
        action_points = [
            "Set valuation checkpoints before elevating the company in research priority.",
            "Watch for earnings upgrades or price corrections.",
        ]
    elif overall_risk == "High":
        label = "Caution Required"
        confidence = "High"
        summary = "High-severity risk flags make the company a cautious research case."
        why_this_label = "The risk scanner shows several material concerns across the current framework."
        action_points = [
            "Investigate the highest-severity risk flags before proceeding further.",
            "Look for evidence that balance-sheet, governance, or cash-flow issues are improving.",
        ]
    elif total_score >= 55:
        label = "Monitor Closely"
        confidence = "Medium"
        summary = "The company shows mixed signals and needs closer monitoring before stronger conviction."
        why_this_label = "The framework output is neither weak enough to reject nor strong enough to prioritize immediately."
        action_points = [
            "Monitor trend changes in the weakest categories.",
            "Reassess after the next result cycle or major business update.",
        ]
    else:
        label = "Weak Fundamentals"
        confidence = "High"
        summary = "The company does not currently meet the preferred framework standards."
        why_this_label = "Low scorecard output and/or elevated risks weaken the research case."
        action_points = [
            "Focus on the failed rule clusters before revisiting the company.",
            "Look for evidence of turnaround in growth, profitability, or governance.",
        ]

    return ResearchSuggestionSummary(
        label=label,
        summary=summary,
        confidence=confidence,
        action_points=action_points,
        why_this_label=why_this_label,
    )
