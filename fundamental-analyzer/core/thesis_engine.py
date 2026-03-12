"""Template-based investment thesis generation."""

from __future__ import annotations

from models.result_model import RuleEvaluationResult, ThesisSummary


def _has_failed_result(results: list[RuleEvaluationResult], parameters: set[str]) -> bool:
    """Check whether any given parameters failed their rules."""
    return any(result.parameter in parameters and result.status == "Fail" for result in results)


def _has_passed_result(results: list[RuleEvaluationResult], parameters: set[str]) -> bool:
    """Check whether any given parameters passed their rules."""
    return any(result.parameter in parameters and result.status == "Pass" for result in results)


def build_thesis(results: list[RuleEvaluationResult], final_verdict: str) -> ThesisSummary:
    """Generate a structured investment thesis from rule results."""
    bull_case: list[str] = []
    bear_case: list[str] = []
    key_risks: list[str] = []
    key_triggers: list[str] = []

    if _has_passed_result(results, {"roe", "roce"}):
        bull_case.append("Strong profitability and high ROCE indicate solid capital efficiency.")
        key_triggers.append("Sustained return ratios can support premium valuation and market confidence.")

    if _has_passed_result(results, {"sales_growth_5y", "profit_growth_5y"}):
        bull_case.append("Healthy growth metrics indicate the business has been compounding with momentum.")
        key_triggers.append("Revenue acceleration and earnings compounding can improve upside potential.")

    if _has_passed_result(results, {"opm"}):
        bull_case.append("Healthy operating margins suggest durable business quality and pricing power.")

    if _has_passed_result(results, {"debt_to_equity", "cfo"}):
        bull_case.append("Cash generation and debt control improve financial resilience.")
        key_triggers.append("Improved cash conversion or lower leverage can strengthen the balance-sheet narrative.")

    if _has_passed_result(results, {"promoter_holding", "pledge"}):
        bull_case.append("Governance indicators are supportive, with promoter alignment and low pledge risk.")

    if _has_failed_result(results, {"pe", "pb", "peg"}):
        bear_case.append("Valuation multiples already reflect optimistic expectations.")
        key_risks.append("Multiple de-rating risk remains if growth moderates or execution weakens.")

    if _has_failed_result(results, {"sales_growth_5y", "profit_growth_5y"}):
        bear_case.append("Growth metrics are below the preferred threshold and can cap upside.")
        key_risks.append("Demand slowdown or weak execution can pressure sales and profit growth.")

    if _has_failed_result(results, {"opm"}):
        bear_case.append("Margin quality is weaker than preferred under the selected framework.")
        key_risks.append("Margin compression can reduce earnings quality and valuation support.")

    if _has_failed_result(results, {"debt_to_equity", "cfo"}):
        bear_case.append("Cash-flow quality or leverage is weaker than preferred.")
        key_risks.append("Poor cash conversion or higher leverage can reduce financial flexibility.")

    if _has_failed_result(results, {"promoter_holding", "pledge"}):
        bear_case.append("Governance metrics are not fully aligned with the preferred framework.")
        key_risks.append("Governance slippage or promoter-related stress can hurt market confidence.")

    if _has_passed_result(results, {"pe", "pb", "peg"}):
        key_triggers.append("Reasonable valuation can allow re-rating if business execution remains strong.")

    if not bull_case:
        bull_case.append("The business shows some supportive fundamentals, but the bull case is not dominant under the current rule set.")
    if not bear_case:
        bear_case.append("Current rule evaluation does not point to a major structural bear case.")
    if not key_risks:
        key_risks.append("No major risk stands out from the current rule framework, though execution risk remains.")
    if not key_triggers:
        key_triggers.append("Improvement in growth, profitability, or valuation comfort can strengthen the investment case.")

    return ThesisSummary(
        bull_case=bull_case[:3],
        bear_case=bear_case[:3],
        key_risks=key_risks[:3],
        key_triggers=key_triggers[:3],
        final_verdict=final_verdict,
    )
