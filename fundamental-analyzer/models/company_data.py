"""Company data model for the starter scaffold."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class CompanyData:
    """Extracted company metrics from a PDF report."""

    company_name: str | None = None
    market_cap_cr: float | None = None
    current_price: float | None = None
    stock_pe: float | None = None
    book_value: float | None = None
    dividend_yield: float | None = None
    roce: float | None = None
    roe: float | None = None
    sales_growth_5y: float | None = None
    profit_growth_5y: float | None = None
    opm: float | None = None
    debt_to_equity: float | None = None
    peg_ratio: float | None = None
    eps: float | None = None
    net_profit: float | None = None
    depreciation: float | None = None
    capex: float | None = None
    cfo_growth_5y: float | None = None
    receivables_growth_5y: float | None = None
    cfo_5y: float | None = None
    cfo_last_year: float | None = None
    promoter_holding: float | None = None
    pledge: float | None = None
    industry_pe: float | None = None
    financial_trends: dict[str, list[dict[str, Any]]] | None = None
    source_file: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Convert the dataclass to a dictionary."""
        return asdict(self)
