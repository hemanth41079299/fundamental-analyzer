"""Result models for the starter scaffold."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class RuleEvaluationResult:
    """Outcome for a single rule evaluation."""

    parameter: str
    category: str
    actual_value: float | None
    rule_display: str
    status: str
    rationale: str

    def to_dict(self) -> dict[str, object]:
        """Convert result to a dictionary."""
        return asdict(self)


@dataclass
class ScoreSummary:
    """Score summary for a ruleset."""

    total_passed: int
    total_applicable: int
    percentage: float
    interpretation: str

    def to_dict(self) -> dict[str, object]:
        """Convert score to a dictionary."""
        return asdict(self)


@dataclass
class CategoryScore:
    """Score summary for one scorecard category."""

    category: str
    passed: int
    applicable: int
    score: int
    percentage: float

    def to_dict(self) -> dict[str, object]:
        """Convert category score to a dictionary."""
        return asdict(self)


@dataclass
class ScorecardSummary:
    """Scorecard output grouped by rule category."""

    category_scores: dict[str, int]
    total_score: int
    max_score: int
    details: list[CategoryScore]

    def to_dict(self) -> dict[str, object]:
        """Convert scorecard to a dictionary."""
        return {
            "category_scores": self.category_scores,
            "total_score": self.total_score,
            "max_score": self.max_score,
            "details": [item.to_dict() for item in self.details],
        }


@dataclass
class ThesisSummary:
    """Structured investment thesis output."""

    bull_case: list[str]
    bear_case: list[str]
    key_risks: list[str]
    key_triggers: list[str]
    final_verdict: str

    def to_dict(self) -> dict[str, object]:
        """Convert thesis summary to a dictionary."""
        return asdict(self)


@dataclass
class RiskFlagResult:
    """Serializable risk flag model."""

    category: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, object]:
        """Convert risk flag to a dictionary."""
        return asdict(self)


@dataclass
class RiskScanSummary:
    """Structured risk scan summary."""

    risk_flags: list[RiskFlagResult]
    overall_risk_level: str

    def to_dict(self) -> dict[str, object]:
        """Convert risk scan summary to a dictionary."""
        return {
            "risk_flags": [flag.to_dict() for flag in self.risk_flags],
            "overall_risk_level": self.overall_risk_level,
        }


@dataclass
class ResearchSuggestionSummary:
    """Deterministic research suggestion output."""

    label: str
    summary: str
    confidence: str
    action_points: list[str]
    why_this_label: str

    def to_dict(self) -> dict[str, object]:
        """Convert research suggestion to a dictionary."""
        return asdict(self)


@dataclass
class ValuationModelResult:
    """Result for one intrinsic value method."""

    method: str
    fair_value: float | None = None
    current_price: float | None = None
    valuation: str | None = None
    difference_percent: float | None = None
    implied_growth: float | None = None
    owner_earnings: float | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Convert valuation model result to a dictionary."""
        return asdict(self)


@dataclass
class IntrinsicValueSummary:
    """Combined intrinsic value analysis output."""

    valuation_models: list[ValuationModelResult]
    consensus_fair_value: float | None
    valuation_summary: str

    def to_dict(self) -> dict[str, object]:
        """Convert intrinsic value summary to a dictionary."""
        return {
            "valuation_models": [model.to_dict() for model in self.valuation_models],
            "consensus_fair_value": self.consensus_fair_value,
            "valuation_summary": self.valuation_summary,
        }


@dataclass
class EarningsQualitySummary:
    """Structured earnings quality output."""

    cash_conversion_ratio: float | None
    earnings_quality: str
    flags: list[str]
    summary: str

    def to_dict(self) -> dict[str, object]:
        """Convert earnings quality summary to a dictionary."""
        return asdict(self)


@dataclass
class RedFlagResult:
    """Serializable red flag model."""

    type: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, object]:
        """Convert red flag to a dictionary."""
        return asdict(self)


@dataclass
class RedFlagSummary:
    """Structured red flag output."""

    red_flags: list[RedFlagResult]
    red_flag_count: int
    summary: str

    def to_dict(self) -> dict[str, object]:
        """Convert red flag summary to a dictionary."""
        return {
            "red_flags": [flag.to_dict() for flag in self.red_flags],
            "red_flag_count": self.red_flag_count,
            "summary": self.summary,
        }


@dataclass
class AnalysisResult:
    """Full analysis output for the application."""

    company_name: str
    market_cap_category: str
    rule_results: list[RuleEvaluationResult]
    score: ScoreSummary
    scorecard: ScorecardSummary
    thesis: ThesisSummary
    risk_scan: RiskScanSummary
    suggestion: ResearchSuggestionSummary
    intrinsic_value: IntrinsicValueSummary
    earnings_quality: EarningsQualitySummary
    red_flags: RedFlagSummary
    strengths: list[str]
    weaknesses: list[str]
    observations: dict[str, str]
    final_verdict: str

    def to_dict(self) -> dict[str, object]:
        """Convert the analysis to a dictionary."""
        return {
            "company_name": self.company_name,
            "market_cap_category": self.market_cap_category,
            "rule_results": [item.to_dict() for item in self.rule_results],
            "score": self.score.to_dict(),
            "scorecard": self.scorecard.to_dict(),
            "thesis": self.thesis.to_dict(),
            "risk_scan": self.risk_scan.to_dict(),
            "suggestion": self.suggestion.to_dict(),
            "intrinsic_value": self.intrinsic_value.to_dict(),
            "earnings_quality": self.earnings_quality.to_dict(),
            "red_flags": self.red_flags.to_dict(),
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "observations": self.observations,
            "final_verdict": self.final_verdict,
        }
