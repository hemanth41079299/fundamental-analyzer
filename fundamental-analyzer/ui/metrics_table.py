"""Render extracted company metrics in a table."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from models.company_data import CompanyData

DISPLAY_LABELS: dict[str, str] = {
    "company_name": "Company Name",
    "market_cap_cr": "Market Cap (Cr)",
    "current_price": "Current Price",
    "stock_pe": "Stock P/E",
    "book_value": "Book Value",
    "dividend_yield": "Dividend Yield (%)",
    "roce": "ROCE (%)",
    "roe": "ROE (%)",
    "sales_growth_5y": "Sales Growth 5Y (%)",
    "profit_growth_5y": "Profit Growth 5Y (%)",
    "opm": "OPM (%)",
    "debt_to_equity": "Debt to Equity",
    "peg_ratio": "PEG Ratio",
    "cfo_5y": "CFO 5Y",
    "cfo_last_year": "CFO Last Year",
    "promoter_holding": "Promoter Holding (%)",
    "pledge": "Pledge (%)",
    "industry_pe": "Industry P/E",
}


def render_metrics_table(company_data: CompanyData) -> None:
    """Render extracted metrics as a dataframe."""
    st.subheader("Extracted Metrics")
    rows: list[dict[str, object]] = []
    for field_name, value in company_data.to_dict().items():
        if field_name in {"source_file", "financial_trends"}:
            continue
        rows.append(
            {
                "Metric": DISPLAY_LABELS.get(field_name, field_name),
                "Value": "NA" if value is None else value,
            }
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
