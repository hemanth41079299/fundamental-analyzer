"""Rule evaluation and scoring logic."""

from __future__ import annotations

from models.company_data import CompanyData
from models.result_model import CategoryScore, RuleEvaluationResult, ScoreSummary, ScorecardSummary
from models.rule_model import Rule

RULE_PARAMETER_TO_METRIC = {
    "pe": "stock_pe",
    "peg": "peg_ratio",
}

RULE_CATEGORY_MAP = {
    "sales_growth_5y": "Growth",
    "profit_growth_5y": "Growth",
    "roe": "Profitability",
    "roce": "Profitability",
    "opm": "Margins",
    "debt_to_equity": "Debt",
    "pe": "Valuation",
    "pb": "Valuation",
    "peg": "Valuation",
    "stock_pe": "Valuation",
    "book_value": "Valuation",
    "peg_ratio": "Valuation",
    "cfo": "Cash Flow",
    "cfo_5y": "Cash Flow",
    "cfo_last_year": "Cash Flow",
    "promoter_holding": "Governance",
    "pledge": "Governance",
}

SCORECARD_CATEGORIES = [
    "Growth",
    "Profitability",
    "Margins",
    "Debt",
    "Valuation",
    "Cash Flow",
    "Governance",
]


def resolve_rule_category(parameter: str, explicit_category: str | None = None) -> str:
    """Map a rule parameter to a scorecard category.

    Rule JSON categories take precedence when provided.
    """
    if explicit_category:
        return explicit_category
    return RULE_CATEGORY_MAP.get(parameter, "Other")


def resolve_metric_value(company_data: CompanyData, parameter: str) -> float | None:
    """Resolve a rule parameter to a concrete metric value."""
    if parameter == "pb":
        if company_data.current_price is None or company_data.book_value in {None, 0}:
            return None
        return company_data.current_price / company_data.book_value

    if parameter == "cfo":
        return company_data.cfo_5y if company_data.cfo_5y is not None else company_data.cfo_last_year

    metric_name = RULE_PARAMETER_TO_METRIC.get(parameter, parameter)
    return getattr(company_data, metric_name, None)


def build_rule_display(rule: Rule) -> str:
    """Build a human-readable rule expression."""
    target_label = rule.label or rule.parameter
    if rule.operator == "industry_compare":
        return f"{target_label} < industry_pe"
    return f"{target_label} {rule.operator} {rule.value}"


def evaluate_single_rule(company_data: CompanyData, rule: Rule) -> RuleEvaluationResult:
    """Evaluate a single rule against extracted company metrics."""
    actual_value = resolve_metric_value(company_data, rule.parameter)
    display = build_rule_display(rule)
    category = resolve_rule_category(rule.parameter, rule.category)

    if actual_value is None:
        return RuleEvaluationResult(
            parameter=rule.parameter,
            category=category,
            actual_value=None,
            rule_display=display,
            status="NA",
            rationale=rule.rationale,
        )

    if rule.operator == "industry_compare":
        benchmark = company_data.industry_pe
        if benchmark is None:
            status = "NA"
        else:
            status = "Pass" if actual_value < benchmark else "Fail"
    elif rule.operator == ">":
        status = "Pass" if actual_value > rule.value else "Fail"
    elif rule.operator == "<":
        status = "Pass" if actual_value < rule.value else "Fail"
    elif rule.operator == ">=":
        status = "Pass" if actual_value >= rule.value else "Fail"
    elif rule.operator == "<=":
        status = "Pass" if actual_value <= rule.value else "Fail"
    elif rule.operator == "==":
        status = "Pass" if actual_value == rule.value else "Fail"
    else:
        raise ValueError(f"Unsupported operator: {rule.operator}")

    return RuleEvaluationResult(
        parameter=rule.parameter,
        category=category,
        actual_value=actual_value,
        rule_display=display,
        status=status,
        rationale=rule.rationale,
    )


def evaluate_rules(company_data: CompanyData, rules: list[Rule]) -> list[RuleEvaluationResult]:
    """Evaluate all rules for a company."""
    return [evaluate_single_rule(company_data, rule) for rule in rules]


def build_score_summary(results: list[RuleEvaluationResult]) -> ScoreSummary:
    """Build a score summary from rule evaluation results."""
    applicable_results = [result for result in results if result.status != "NA"]
    total_applicable = len(applicable_results)
    total_passed = sum(1 for result in applicable_results if result.status == "Pass")
    percentage = round((total_passed / total_applicable) * 100, 2) if total_applicable else 0.0

    if percentage >= 85:
        interpretation = "Excellent"
    elif percentage >= 70:
        interpretation = "Strong"
    elif percentage >= 55:
        interpretation = "Average"
    else:
        interpretation = "Weak"

    return ScoreSummary(
        total_passed=total_passed,
        total_applicable=total_applicable,
        percentage=percentage,
        interpretation=interpretation,
    )


def build_scorecard_summary(results: list[RuleEvaluationResult]) -> ScorecardSummary:
    """Build a category-wise scorecard from rule evaluation results.

    Category scores are scaled to integers on a 0-10 basis:
    - 10 means all applicable rules in the category passed
    - 0 means none of the applicable rules passed
    """
    details: list[CategoryScore] = []
    category_scores: dict[str, int] = {}

    for category in SCORECARD_CATEGORIES:
        category_results = [result for result in results if result.category == category and result.status != "NA"]
        applicable = len(category_results)
        passed = sum(1 for result in category_results if result.status == "Pass")
        percentage = round((passed / applicable) * 100, 2) if applicable else 0.0
        score = round((passed / applicable) * 10) if applicable else 0

        details.append(
            CategoryScore(
                category=category,
                passed=passed,
                applicable=applicable,
                score=score,
                percentage=percentage,
            )
        )
        category_scores[category] = score

    overall = build_score_summary(results)
    return ScorecardSummary(
        category_scores=category_scores,
        total_score=round(overall.percentage),
        max_score=100,
        details=details,
    )


def build_empty_score() -> ScoreSummary:
    """Return a default score object."""
    return ScoreSummary(total_passed=0, total_applicable=0, percentage=0.0, interpretation="Not Scored")
