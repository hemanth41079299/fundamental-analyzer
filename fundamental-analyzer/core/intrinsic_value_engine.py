"""Deterministic intrinsic value estimation engine."""

from __future__ import annotations

from models.company_data import CompanyData
from models.result_model import IntrinsicValueSummary, ValuationModelResult


def _safe_round(value: float | None, digits: int = 2) -> float | None:
    """Round a float when available."""
    if value is None:
        return None
    return round(value, digits)


def _estimate_eps(company_data: CompanyData) -> tuple[float | None, str | None]:
    """Return EPS directly or approximate from price and PE."""
    if company_data.eps is not None:
        return company_data.eps, None
    if company_data.current_price is not None and company_data.stock_pe not in {None, 0}:
        return company_data.current_price / company_data.stock_pe, "EPS approximated using price / PE."
    return None, "EPS is unavailable, so fair value methods using earnings are limited."


def _valuation_label(fair_value: float | None, current_price: float | None) -> tuple[str | None, float | None]:
    """Classify valuation relative to current price."""
    if fair_value in {None, 0} or current_price is None:
        return None, None

    difference_percent = ((fair_value - current_price) / current_price) * 100
    if difference_percent > 10:
        label = "Undervalued"
    elif difference_percent < -10:
        label = "Overvalued"
    else:
        label = "Fair"
    return label, round(difference_percent, 2)


def _growth_rate(company_data: CompanyData) -> float | None:
    """Select a growth rate for PEG-style valuation."""
    if company_data.profit_growth_5y is not None:
        return company_data.profit_growth_5y
    return company_data.sales_growth_5y


def build_peg_fair_value(company_data: CompanyData) -> ValuationModelResult:
    """Calculate PEG-style fair value."""
    current_price = company_data.current_price
    eps, eps_note = _estimate_eps(company_data)
    growth_rate = _growth_rate(company_data)

    if eps is None or growth_rate is None or growth_rate <= 0:
        return ValuationModelResult(
            method="PEG",
            current_price=current_price,
            notes="PEG fair value could not be calculated because growth rate or EPS is unavailable.",
        )

    fair_pe = growth_rate
    fair_value = fair_pe * eps
    valuation, difference_percent = _valuation_label(fair_value, current_price)

    note = f"Fair PE set equal to growth rate ({growth_rate:.2f})."
    if eps_note:
        note = f"{note} {eps_note}"

    return ValuationModelResult(
        method="PEG",
        fair_value=_safe_round(fair_value),
        current_price=current_price,
        valuation=valuation,
        difference_percent=difference_percent,
        notes=note,
    )


def build_reverse_dcf(
    company_data: CompanyData,
    discount_rate: float = 0.12,
    terminal_growth: float = 0.04,
) -> ValuationModelResult:
    """Estimate the growth rate implied by the current price using a simplified reverse DCF."""
    current_price = company_data.current_price
    eps, eps_note = _estimate_eps(company_data)

    if current_price is None or eps is None or eps <= 0 or discount_rate <= terminal_growth:
        return ValuationModelResult(
            method="Reverse DCF",
            current_price=current_price,
            notes="Reverse DCF could not be calculated because price, earnings, or discount assumptions are invalid.",
        )

    implied_growth = ((current_price * (discount_rate - terminal_growth)) / eps) - 1
    note = f"Uses discount rate {discount_rate:.0%} and terminal growth {terminal_growth:.0%}."
    if eps_note:
        note = f"{note} {eps_note}"

    return ValuationModelResult(
        method="Reverse DCF",
        current_price=current_price,
        implied_growth=_safe_round(implied_growth * 100),
        notes=note,
    )


def _owner_earnings(company_data: CompanyData) -> tuple[float | None, str | None]:
    """Calculate owner earnings, with CFO fallback when detailed inputs are unavailable."""
    if company_data.net_profit is not None and company_data.depreciation is not None and company_data.capex is not None:
        owner_earnings = company_data.net_profit + company_data.depreciation - company_data.capex
        return owner_earnings, None

    if company_data.cfo_last_year is not None:
        return company_data.cfo_last_year, "Owner earnings approximated using CFO because net profit, depreciation, and capex are unavailable."
    if company_data.cfo_5y is not None:
        return company_data.cfo_5y, "Owner earnings approximated using CFO because net profit, depreciation, and capex are unavailable."
    return None, "Owner earnings inputs are unavailable."


def build_owner_earnings_value(
    company_data: CompanyData,
    discount_rate: float = 0.12,
) -> ValuationModelResult:
    """Estimate intrinsic value using owner earnings."""
    current_price = company_data.current_price
    owner_earnings, note = _owner_earnings(company_data)

    if owner_earnings is None or discount_rate <= 0:
        return ValuationModelResult(
            method="Owner Earnings",
            current_price=current_price,
            notes="Owner earnings value could not be calculated because required inputs are unavailable.",
        )

    fair_value = owner_earnings / discount_rate
    valuation, difference_percent = _valuation_label(fair_value, current_price)
    return ValuationModelResult(
        method="Owner Earnings",
        fair_value=_safe_round(fair_value),
        current_price=current_price,
        valuation=valuation,
        difference_percent=difference_percent,
        owner_earnings=_safe_round(owner_earnings),
        notes=note or f"Intrinsic value estimated using discount rate {discount_rate:.0%}.",
    )


def _consensus_fair_value(models: list[ValuationModelResult]) -> float | None:
    """Calculate a consensus fair value from available model outputs."""
    values = [model.fair_value for model in models if model.fair_value is not None]
    if not values:
        return None
    return _safe_round(sum(values) / len(values))


def _build_summary(consensus_fair_value: float | None, current_price: float | None) -> str:
    """Build a plain-English valuation summary."""
    if consensus_fair_value is None or current_price is None:
        return "Intrinsic value could not be estimated reliably from the currently available metrics."

    difference_percent = ((consensus_fair_value - current_price) / current_price) * 100
    if difference_percent > 15:
        return "The company appears moderately undervalued relative to the available growth and earnings inputs."
    if difference_percent < -15:
        return "The company appears moderately overvalued relative to growth expectations."
    return "The company appears broadly fairly valued under the simplified intrinsic value framework."


def build_intrinsic_value_analysis(company_data: CompanyData) -> IntrinsicValueSummary:
    """Run all intrinsic value methods and return a combined summary."""
    models = [
        build_peg_fair_value(company_data),
        build_reverse_dcf(company_data),
        build_owner_earnings_value(company_data),
    ]
    consensus = _consensus_fair_value(models)
    summary = _build_summary(consensus, company_data.current_price)

    return IntrinsicValueSummary(
        valuation_models=models,
        consensus_fair_value=consensus,
        valuation_summary=summary,
    )
