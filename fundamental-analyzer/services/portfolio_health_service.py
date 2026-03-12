"""Portfolio health scoring service."""

from __future__ import annotations

from typing import Any

import pandas as pd

HEALTH_SCORE_WEIGHTS = {
    "diversification": 0.25,
    "growth": 0.20,
    "balance_sheet": 0.20,
    "valuation": 0.20,
    "risk": 0.15,
}


def _safe_float(value: Any) -> float | None:
    """Convert a value to ``float`` when possible."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_value_column(holdings: pd.DataFrame) -> str | None:
    """Pick the best available portfolio value column."""
    for candidate in ("Current Value", "present_value", "Present Value", "Market Value", "Invested", "buy_value"):
        if candidate in holdings.columns:
            return candidate
    return None


def calculate_position_weights(holdings: pd.DataFrame) -> pd.DataFrame:
    """Calculate position weights from the best available value column."""
    if holdings.empty:
        return pd.DataFrame(columns=["ticker", "company_name", "position_value", "weight"])

    value_column = _resolve_value_column(holdings)
    if value_column is None:
        return pd.DataFrame(columns=["ticker", "company_name", "position_value", "weight"])

    frame = holdings.copy()
    frame["position_value"] = pd.to_numeric(frame[value_column], errors="coerce").fillna(0.0)
    total_value = float(frame["position_value"].sum())
    if total_value <= 0:
        frame["weight"] = 0.0
    else:
        frame["weight"] = frame["position_value"] / total_value

    ticker_column = "Ticker" if "Ticker" in frame.columns else "ticker"
    company_column = "Company" if "Company" in frame.columns else "company_name"
    return (
        frame[[ticker_column, company_column, "position_value", "weight"]]
        .rename(columns={ticker_column: "ticker", company_column: "company_name"})
        .sort_values(by="weight", ascending=False)
        .reset_index(drop=True)
    )


def calculate_sector_allocation(
    holdings: pd.DataFrame,
    sector_mapping: dict[str, str] | None = None,
) -> dict[str, float]:
    """Calculate sector allocation percentages."""
    if holdings.empty:
        return {}

    weights = calculate_position_weights(holdings)
    if weights.empty:
        return {}

    frame = holdings.copy()
    ticker_column = "Ticker" if "Ticker" in frame.columns else "ticker"
    sector_column = "Sector" if "Sector" in frame.columns else "sector"
    frame[ticker_column] = frame[ticker_column].astype(str).str.upper().str.strip()

    if sector_column not in frame.columns:
        frame[sector_column] = None

    if sector_mapping:
        mapped_sectors = frame[ticker_column].map({key.upper(): value for key, value in sector_mapping.items()})
        frame[sector_column] = frame[sector_column].fillna(mapped_sectors)

    frame[sector_column] = frame[sector_column].fillna("Unknown").replace("", "Unknown")
    merged = frame.merge(weights[["ticker", "weight"]], left_on=ticker_column, right_on="ticker", how="left")
    allocation = (
        merged.groupby(sector_column, dropna=False)["weight"].sum().sort_values(ascending=False) * 100
    )
    return {str(index): round(float(value), 2) for index, value in allocation.items()}


def detect_concentration_risk(holdings: pd.DataFrame) -> list[str]:
    """Detect concentration risk from position weights and sector concentration."""
    warnings: list[str] = []
    weights = calculate_position_weights(holdings)
    if weights.empty:
        return warnings

    for row in weights.itertuples(index=False):
        ticker = str(row.ticker)
        weight_pct = float(row.weight) * 100
        if weight_pct >= 25:
            warnings.append(f"{ticker} exceeds 25% allocation.")
        elif weight_pct >= 20:
            warnings.append(f"{ticker} exceeds 20% allocation.")

    sector_allocation = calculate_sector_allocation(holdings)
    for sector, weight_pct in sector_allocation.items():
        if weight_pct >= 40:
            warnings.append(f"{sector} exceeds 40% sector allocation.")

    return warnings


def _weighted_average(frame: pd.DataFrame, value_column: str, weight_column: str = "weight") -> float | None:
    """Calculate a weighted average for numeric series."""
    if value_column not in frame.columns or weight_column not in frame.columns:
        return None

    values = pd.to_numeric(frame[value_column], errors="coerce")
    weights = pd.to_numeric(frame[weight_column], errors="coerce").fillna(0.0)
    valid_mask = values.notna() & weights.notna() & (weights > 0)
    if not valid_mask.any():
        return None
    return float((values[valid_mask] * weights[valid_mask]).sum() / weights[valid_mask].sum())


def _component_from_total_score(holdings: pd.DataFrame) -> float:
    """Use weighted total company scores as a fallback component."""
    weights = calculate_position_weights(holdings)
    if weights.empty:
        return 0.0

    frame = holdings.copy()
    ticker_column = "Ticker" if "Ticker" in frame.columns else "ticker"
    frame[ticker_column] = frame[ticker_column].astype(str).str.upper().str.strip()
    merged = frame.merge(weights[["ticker", "weight"]], left_on=ticker_column, right_on="ticker", how="left")
    total_score = _weighted_average(merged, "Score")
    if total_score is None:
        return 5.0
    return max(0.0, min(10.0, total_score / 10.0))


def _score_diversification(holdings: pd.DataFrame) -> float:
    """Score diversification using holdings count and concentration."""
    weights = calculate_position_weights(holdings)
    if weights.empty:
        return 0.0

    holding_count = len(weights)
    max_weight = float(weights["weight"].max()) if not weights.empty else 1.0
    effective_holdings = 1.0 / float((weights["weight"] ** 2).sum()) if float((weights["weight"] ** 2).sum()) > 0 else 0.0

    score = 10.0
    if holding_count < 5:
        score -= 2.5
    elif holding_count < 8:
        score -= 1.0

    if max_weight > 0.35:
        score -= 3.0
    elif max_weight > 0.25:
        score -= 2.0
    elif max_weight > 0.20:
        score -= 1.0

    if effective_holdings < 4:
        score -= 2.0
    elif effective_holdings < 6:
        score -= 1.0

    sector_allocation = calculate_sector_allocation(holdings)
    largest_sector = max(sector_allocation.values(), default=0.0)
    if largest_sector > 45:
        score -= 2.0
    elif largest_sector > 35:
        score -= 1.0

    return round(max(0.0, min(10.0, score)), 1)


def _find_component_column(frame: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first matching score column from a candidate list."""
    normalized_map = {str(column).strip().lower(): str(column) for column in frame.columns}
    for candidate in candidates:
        if candidate.lower() in normalized_map:
            return normalized_map[candidate.lower()]
    return None


def _score_growth(holdings: pd.DataFrame) -> float:
    """Score portfolio growth quality."""
    weights = calculate_position_weights(holdings)
    if weights.empty:
        return 0.0

    frame = holdings.copy()
    ticker_column = "Ticker" if "Ticker" in frame.columns else "ticker"
    frame[ticker_column] = frame[ticker_column].astype(str).str.upper().str.strip()
    merged = frame.merge(weights[["ticker", "weight"]], left_on=ticker_column, right_on="ticker", how="left")

    growth_column = _find_component_column(merged, ["Growth Score", "growth_score", "Growth"])
    if growth_column:
        score = _weighted_average(merged, growth_column)
        if score is not None:
            return round(max(0.0, min(10.0, score / 10.0 if score > 10 else score)), 1)

    base_score = _component_from_total_score(holdings)
    suggestion_column = "Suggestion" if "Suggestion" in merged.columns else None
    boost = 0.0
    if suggestion_column:
        strong_weight = merged.loc[merged[suggestion_column] == "Strong Candidate", "weight"].sum()
        watch_weight = merged.loc[merged[suggestion_column] == "Watchlist Candidate", "weight"].sum()
        boost += float(strong_weight) * 1.0
        boost += float(watch_weight) * 0.5
    return round(max(0.0, min(10.0, base_score + boost)), 1)


def _score_balance_sheet(holdings: pd.DataFrame) -> float:
    """Score balance-sheet quality using available company analysis output."""
    weights = calculate_position_weights(holdings)
    if weights.empty:
        return 0.0

    frame = holdings.copy()
    ticker_column = "Ticker" if "Ticker" in frame.columns else "ticker"
    frame[ticker_column] = frame[ticker_column].astype(str).str.upper().str.strip()
    merged = frame.merge(weights[["ticker", "weight"]], left_on=ticker_column, right_on="ticker", how="left")

    balance_column = _find_component_column(merged, ["Balance Sheet Score", "balance_sheet_score", "Debt Score"])
    if balance_column:
        score = _weighted_average(merged, balance_column)
        if score is not None:
            return round(max(0.0, min(10.0, score / 10.0 if score > 10 else score)), 1)

    base_score = _component_from_total_score(holdings)
    risk_penalty = 0.0
    if "Risk" in merged.columns:
        risk_penalty += float(merged.loc[merged["Risk"].isin(["High"]), "weight"].sum()) * 3.0
        risk_penalty += float(merged.loc[merged["Risk"].isin(["Moderate", "Medium"]), "weight"].sum()) * 1.5
    return round(max(0.0, min(10.0, base_score - risk_penalty)), 1)


def _score_valuation(holdings: pd.DataFrame) -> float:
    """Score valuation using valuation summaries or company scorecard fallbacks."""
    weights = calculate_position_weights(holdings)
    if weights.empty:
        return 0.0

    frame = holdings.copy()
    ticker_column = "Ticker" if "Ticker" in frame.columns else "ticker"
    frame[ticker_column] = frame[ticker_column].astype(str).str.upper().str.strip()
    merged = frame.merge(weights[["ticker", "weight"]], left_on=ticker_column, right_on="ticker", how="left")

    valuation_column = _find_component_column(merged, ["Valuation Score", "valuation_score", "Valuation"])
    if valuation_column:
        score = _weighted_average(merged, valuation_column)
        if score is not None:
            return round(max(0.0, min(10.0, score / 10.0 if score > 10 else score)), 1)

    if "Valuation Summary" not in merged.columns:
        return round(_component_from_total_score(holdings), 1)

    score = 0.0
    total_weight = 0.0
    for row in merged.itertuples(index=False):
        summary = str(getattr(row, "Valuation Summary", "") or "").lower()
        weight = float(getattr(row, "weight", 0.0) or 0.0)
        if weight <= 0:
            continue
        if "undervalued" in summary or "fair" in summary:
            bucket_score = 8.5
        elif "overvalued" in summary or "expensive" in summary or "rich" in summary:
            bucket_score = 4.5
        else:
            bucket_score = 6.0
        score += bucket_score * weight
        total_weight += weight

    if total_weight == 0:
        return 6.0
    return round(max(0.0, min(10.0, score / total_weight)), 1)


def _score_risk(holdings: pd.DataFrame) -> float:
    """Score portfolio risk exposure using risk labels, red flags, and concentration."""
    weights = calculate_position_weights(holdings)
    if weights.empty:
        return 0.0

    frame = holdings.copy()
    ticker_column = "Ticker" if "Ticker" in frame.columns else "ticker"
    frame[ticker_column] = frame[ticker_column].astype(str).str.upper().str.strip()
    merged = frame.merge(weights[["ticker", "weight"]], left_on=ticker_column, right_on="ticker", how="left")

    score = 10.0
    if "Risk" in merged.columns:
        score -= float(merged.loc[merged["Risk"].isin(["High"]), "weight"].sum()) * 4.0
        score -= float(merged.loc[merged["Risk"].isin(["Moderate", "Medium"]), "weight"].sum()) * 2.0

    if "Red Flags" in merged.columns:
        red_flags = pd.to_numeric(merged["Red Flags"], errors="coerce").fillna(0.0)
        weighted_red_flags = float((red_flags * merged["weight"].fillna(0.0)).sum())
        score -= min(3.0, weighted_red_flags * 0.8)

    concentration_warnings = detect_concentration_risk(holdings)
    if concentration_warnings:
        score -= min(2.5, len(concentration_warnings) * 0.75)

    return round(max(0.0, min(10.0, score)), 1)


def calculate_portfolio_health_score(
    holdings: pd.DataFrame,
    weights: dict[str, float] | None = None,
) -> dict[str, object]:
    """Calculate a weighted 0-10 health score for a portfolio."""
    resolved_weights = {**HEALTH_SCORE_WEIGHTS, **(weights or {})}
    if holdings.empty:
        components = {key: 0.0 for key in HEALTH_SCORE_WEIGHTS}
        return {"portfolio_score": 0.0, "components": components}

    components = {
        "diversification": _score_diversification(holdings),
        "growth": _score_growth(holdings),
        "balance_sheet": _score_balance_sheet(holdings),
        "valuation": _score_valuation(holdings),
        "risk": _score_risk(holdings),
    }
    portfolio_score = sum(components[key] * resolved_weights[key] for key in components)

    return {
        "portfolio_score": round(portfolio_score, 1),
        "components": {key: round(value, 1) for key, value in components.items()},
    }
