"""Deterministic risk scanner for equity analysis."""

from __future__ import annotations

from dataclasses import dataclass

from models.company_data import CompanyData
from models.result_model import RuleEvaluationResult, ScorecardSummary


@dataclass
class RiskFlag:
    """A single risk flag detected by the scanner."""

    category: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, object]:
        """Convert the flag to a dictionary."""
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
        }


@dataclass
class RiskScanResult:
    """Structured result from the deterministic risk scanner."""

    risk_flags: list[RiskFlag]
    overall_risk_level: str

    def to_dict(self) -> dict[str, object]:
        """Convert the risk scan result to a dictionary."""
        return {
            "risk_flags": [flag.to_dict() for flag in self.risk_flags],
            "overall_risk_level": self.overall_risk_level,
        }


def _failed_results(results: list[RuleEvaluationResult], parameters: set[str]) -> list[RuleEvaluationResult]:
    """Return failed results for a parameter set."""
    return [result for result in results if result.parameter in parameters and result.status == "Fail"]


def _scorecard_score(scorecard: ScorecardSummary, category: str) -> int:
    """Return the normalized scorecard score for a category."""
    return scorecard.category_scores.get(category, 0)


def _severity_points(severity: str) -> int:
    """Map severity labels to numeric points."""
    return {"Low": 1, "Medium": 2, "High": 3}.get(severity, 0)


def _scan_governance_risk(company_data: CompanyData, results: list[RuleEvaluationResult]) -> RiskFlag | None:
    """Scan governance-related risks."""
    failed = _failed_results(results, {"promoter_holding", "pledge"})
    pledge = company_data.pledge
    promoter_holding = company_data.promoter_holding

    if pledge is not None and pledge > 5:
        return RiskFlag("Governance Risk", "High", "Promoter pledge is elevated and creates governance concern.")
    if promoter_holding is not None and promoter_holding < 35:
        return RiskFlag("Governance Risk", "Medium", "Promoter holding is below the preferred comfort range.")
    if failed:
        return RiskFlag("Governance Risk", "Medium", "One or more governance rules failed under the selected framework.")
    return None


def _scan_valuation_risk(company_data: CompanyData, results: list[RuleEvaluationResult], scorecard: ScorecardSummary) -> RiskFlag | None:
    """Scan valuation-related risks."""
    failed = _failed_results(results, {"pe", "pb", "peg"})
    valuation_score = _scorecard_score(scorecard, "Valuation")

    if len(failed) >= 2 or valuation_score <= 3:
        return RiskFlag("Valuation Risk", "High", "Valuation metrics are stretched versus the preferred framework.")
    if failed or (company_data.peg_ratio is not None and company_data.peg_ratio > 1.8):
        return RiskFlag("Valuation Risk", "Medium", "Valuation appears rich relative to current fundamentals.")
    return None


def _scan_leverage_risk(company_data: CompanyData, results: list[RuleEvaluationResult], scorecard: ScorecardSummary) -> RiskFlag | None:
    """Scan leverage-related risks."""
    failed = _failed_results(results, {"debt_to_equity"})
    debt_value = company_data.debt_to_equity
    debt_score = _scorecard_score(scorecard, "Debt")

    if debt_value is not None and debt_value > 1.5:
        return RiskFlag("Leverage Risk", "High", "Debt to equity is elevated and may pressure financial flexibility.")
    if failed or debt_score <= 4:
        return RiskFlag("Leverage Risk", "Medium", "Leverage is above the preferred range.")
    return None


def _scan_cash_flow_risk(company_data: CompanyData, results: list[RuleEvaluationResult], scorecard: ScorecardSummary) -> RiskFlag | None:
    """Scan cash-flow-related risks."""
    failed = _failed_results(results, {"cfo", "cfo_5y", "cfo_last_year"})
    cfo_value = company_data.cfo_5y if company_data.cfo_5y is not None else company_data.cfo_last_year
    cash_flow_score = _scorecard_score(scorecard, "Cash Flow")

    if cfo_value is not None and cfo_value < 0:
        return RiskFlag("Cash Flow Risk", "High", "Operating cash flow is negative, which weakens earnings quality.")
    if failed or cash_flow_score <= 4:
        return RiskFlag("Cash Flow Risk", "Medium", "Cash-flow conversion is weaker than preferred.")
    return None


def _scan_profitability_risk(results: list[RuleEvaluationResult], scorecard: ScorecardSummary) -> RiskFlag | None:
    """Scan profitability-related risks."""
    failed = _failed_results(results, {"roe", "roce", "opm"})
    profitability_score = _scorecard_score(scorecard, "Profitability")
    margins_score = _scorecard_score(scorecard, "Margins")

    if len(failed) >= 2 or profitability_score <= 3 or margins_score <= 3:
        return RiskFlag("Profitability Risk", "High", "Profitability quality is materially below the preferred threshold.")
    if failed:
        return RiskFlag("Profitability Risk", "Medium", "Some profitability metrics are below the preferred range.")
    return None


def _scan_growth_risk(results: list[RuleEvaluationResult], scorecard: ScorecardSummary) -> RiskFlag | None:
    """Scan growth-related risks."""
    failed = _failed_results(results, {"sales_growth_5y", "profit_growth_5y"})
    growth_score = _scorecard_score(scorecard, "Growth")

    if len(failed) >= 2 or growth_score <= 3:
        return RiskFlag("Growth Risk", "High", "Growth metrics are materially weaker than the selected framework expects.")
    if failed:
        return RiskFlag("Growth Risk", "Medium", "Growth is below the preferred threshold on one or more metrics.")
    return None


def _overall_risk_level(risk_flags: list[RiskFlag]) -> str:
    """Calculate overall risk level from individual flag severities."""
    if not risk_flags:
        return "Low"

    total_points = sum(_severity_points(flag.severity) for flag in risk_flags)
    average_points = total_points / len(risk_flags)

    if average_points >= 2.5:
        return "High"
    if average_points >= 1.5:
        return "Medium"
    return "Low"


def run_risk_scan(
    company_data: CompanyData,
    rule_results: list[RuleEvaluationResult],
    scorecard: ScorecardSummary,
) -> RiskScanResult:
    """Generate deterministic risk flags from metrics, rules, and scorecard data."""
    flags = [
        _scan_governance_risk(company_data, rule_results),
        _scan_valuation_risk(company_data, rule_results, scorecard),
        _scan_leverage_risk(company_data, rule_results, scorecard),
        _scan_cash_flow_risk(company_data, rule_results, scorecard),
        _scan_profitability_risk(rule_results, scorecard),
        _scan_growth_risk(rule_results, scorecard),
    ]

    risk_flags = [flag for flag in flags if flag is not None]
    return RiskScanResult(
        risk_flags=risk_flags,
        overall_risk_level=_overall_risk_level(risk_flags),
    )
