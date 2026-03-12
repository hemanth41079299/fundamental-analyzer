"""Metric extraction logic for company fundamental data."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from core.parser_utils import clean_text, extract_company_name, extract_labeled_value, parse_numeric_value
from models.company_data import CompanyData

METRIC_LABELS: dict[str, list[str]] = {
    "company_name": ["company name", "name of company"],
    "market_cap_cr": ["market cap", "market capitalization", "mcap"],
    "current_price": ["current price", "cmp", "price"],
    "stock_pe": ["stock p/e", "stock pe", "p/e", "pe"],
    "book_value": ["book value", "book value/share"],
    "dividend_yield": ["dividend yield", "div yield"],
    "roce": ["roce", "return on capital employed"],
    "roe": ["roe", "return on equity"],
    "sales_growth_5y": ["sales growth 5years", "sales growth 5 years", "sales growth"],
    "profit_growth_5y": ["profit growth 5years", "profit growth 5 years", "profit growth"],
    "opm": ["opm", "operating profit margin"],
    "debt_to_equity": ["debt to equity", "debt equity", "debt/equity"],
    "peg_ratio": ["peg ratio", "peg"],
    "cfo_5y": ["cash from operations 5years", "cfo 5years", "cash flow from operations 5 years"],
    "cfo_last_year": ["cash from operations", "cfo", "operating cash flow"],
    "promoter_holding": ["promoter holding", "promoters holding"],
    "pledge": ["pledge", "promoter pledge"],
    "industry_pe": ["industry p/e", "industry pe"],
}


class FundamentalExtractor:
    """Extract structured company metrics from PDF text."""

    def extract(self, text: str, source_file: str | None = None) -> CompanyData:
        """Extract company metrics from cleaned text.

        Missing values are returned as ``None``.
        """
        cleaned_text = clean_text(text)
        extracted: dict[str, object] = {"source_file": source_file}

        for field in fields(CompanyData):
            if field.name == "source_file":
                continue

            if field.name == "company_name":
                extracted["company_name"] = extract_company_name(cleaned_text)
                continue

            labels = METRIC_LABELS.get(field.name, [])
            raw_value = extract_labeled_value(cleaned_text, labels)
            extracted[field.name] = parse_numeric_value(raw_value)

        if extracted.get("cfo_5y") is None:
            extracted["cfo_5y"] = extracted.get("cfo_last_year")

        if extracted.get("company_name") is None and source_file:
            extracted["company_name"] = Path(source_file).stem.replace("_", " ").strip()

        return CompanyData(**extracted)
