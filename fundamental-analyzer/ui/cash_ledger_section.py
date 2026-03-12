"""Cash ledger UI."""

from __future__ import annotations

import streamlit as st

from services.cash_service import CashEntryInput, add_cash_entry, get_cash_balance, get_cash_entries


def render_cash_ledger_section() -> None:
    """Render cash ledger entry form and table."""
    st.subheader("Cash Ledger")
    st.metric("Cash Balance", f"{get_cash_balance():.2f}")

    with st.form("cash_form", clear_on_submit=True):
        entry_date = st.date_input("Date")
        entry_type = st.selectbox("Entry Type", options=["DEPOSIT", "WITHDRAWAL"])
        amount = st.number_input("Amount", min_value=0.0, value=0.0, step=0.01)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Cash Entry")

    if submitted:
        try:
            add_cash_entry(
                CashEntryInput(
                    date=entry_date.isoformat(),
                    entry_type=entry_type,
                    amount=amount,
                    notes=notes,
                )
            )
            st.success("Cash entry saved.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    entries = get_cash_entries()
    if entries.empty:
        st.info("No cash ledger entries recorded yet.")
    else:
        st.dataframe(entries, use_container_width=True, hide_index=True)
