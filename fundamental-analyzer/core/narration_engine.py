"""Template-based narration generation."""

from __future__ import annotations

from models.company_data import CompanyData
from models.result_model import AnalysisResult


def build_narration(
    company_data: CompanyData,
    analysis_result: AnalysisResult,
    tone: str = "simple",
) -> str:
    """Build a plain-English narration summary for the analysis."""
    company_name = company_data.company_name or "This company"
    category = analysis_result.market_cap_category.replace("_", " ")
    score = analysis_result.score

    profitability = analysis_result.observations.get("profitability", "profitability data is limited")
    debt = analysis_result.observations.get("debt", "debt data is limited")
    valuation = analysis_result.observations.get("valuation", "valuation data is limited")

    templates = {
        "simple": (
            f"{company_name} is classified as a {category} company. "
            f"It scores {score.percentage:.0f}% under the current framework, which is rated {score.interpretation.lower()}. "
            f"Profitability review shows that {profitability}. Debt review shows that {debt}. "
            f"Valuation review shows that {valuation}. Final verdict: {analysis_result.final_verdict}."
        ),
        "investor": (
            f"{company_name} falls in the {category} bucket and passes {score.total_passed} out of "
            f"{score.total_applicable} applicable rules, resulting in a {score.percentage:.0f}% score. "
            f"Profitability signals indicate {profitability}, leverage checks indicate {debt}, and "
            f"valuation checks indicate {valuation}. Overall view: {analysis_result.final_verdict}."
        ),
        "professional": (
            f"{company_name} has been assessed as a {category} business and achieved a "
            f"{score.percentage:.2f}% score across applicable rules. Profitability observation: {profitability}. "
            f"Debt observation: {debt}. Valuation observation: {valuation}. "
            f"Conclusion: {analysis_result.final_verdict}."
        ),
    }
    return templates.get(tone, templates["simple"])
