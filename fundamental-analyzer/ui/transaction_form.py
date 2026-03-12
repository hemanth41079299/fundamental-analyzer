"""Transaction entry UI."""

from __future__ import annotations

import streamlit as st

from services.transaction_service import TransactionInput, add_transaction, transaction_form_defaults
from ui.design_system import render_empty_state, render_insight_card, render_section_header, render_status_badge
from ui.layout_helpers import create_columns
from ui.ui_theme import apply_finance_theme


def render_transaction_form() -> None:
    """Render the add-transaction form."""
    apply_finance_theme()
    render_section_header(
        "Transactions",
        "Record buys and sells with charges included in the cost basis for average-cost tracking.",
    )
    defaults = transaction_form_defaults()

    form_column, info_column = create_columns([1.6, 1])
    with form_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Ledger Entry", tone="info")
        render_section_header("Add Transaction", "Capture trade details exactly as executed.")
        with st.form("transaction_form", clear_on_submit=True):
            row_1_col_1, row_1_col_2 = st.columns(2)
            with row_1_col_1:
                transaction_date = st.date_input("Date", value=defaults["date"])
            with row_1_col_2:
                transaction_type = st.selectbox("Transaction Type", options=["BUY", "SELL"], index=0)

            row_2_col_1, row_2_col_2 = st.columns(2)
            with row_2_col_1:
                ticker = st.text_input("Ticker", value=str(defaults["ticker"]), placeholder="INFY.NS")
            with row_2_col_2:
                company_name = st.text_input("Company Name", value=str(defaults["company_name"]), placeholder="Infosys")

            row_3_col_1, row_3_col_2, row_3_col_3 = st.columns(3)
            with row_3_col_1:
                quantity = st.number_input("Quantity", min_value=0.0, value=0.0, step=1.0)
            with row_3_col_2:
                price = st.number_input("Price", min_value=0.0, value=0.0, step=0.01)
            with row_3_col_3:
                charges = st.number_input("Charges", min_value=0.0, value=0.0, step=0.01)

            notes = st.text_area("Notes", value=str(defaults["notes"]), placeholder="Broker, thesis, or execution notes")
            submitted = st.form_submit_button("Save Transaction", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with info_column:
        render_insight_card("Validation", "SELL quantities are checked", "A sell cannot exceed available holdings.", "warning")
        render_insight_card("Cost Basis", "Average-cost method", "Charges are included in invested cost for P&L tracking.", "neutral")
        render_insight_card("Best Practice", "Use exact trade data", "Include charges and notes to keep the ledger audit-ready.", "positive")

    if submitted:
        try:
            add_transaction(
                TransactionInput(
                    date=transaction_date.isoformat(),
                    ticker=ticker,
                    company_name=company_name,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    price=price,
                    charges=charges,
                    notes=notes,
                )
            )
            st.success("Transaction saved.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
