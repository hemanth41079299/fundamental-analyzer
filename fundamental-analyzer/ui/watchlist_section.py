"""Watchlist management UI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from services.watchlist_service import WatchlistInput, add_watchlist_item, get_watchlist, remove_watchlist_item
from ui.design_system import render_empty_state, render_section_header, render_status_badge
from ui.layout_helpers import create_columns
from ui.ui_theme import apply_finance_theme


def render_watchlist_section() -> None:
    """Render watchlist add/remove interface."""
    apply_finance_theme()
    render_section_header(
        "Watchlist",
        "Track companies separately from active positions and keep quick notes for follow-up research.",
    )

    form_column, table_column = create_columns([1, 1.4])
    with form_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Research Queue", tone="info")
        render_section_header("Add Watchlist Item", "Save a ticker for later review.")
        with st.form("watchlist_form", clear_on_submit=True):
            ticker = st.text_input("Ticker", placeholder="INFY.NS")
            company_name = st.text_input("Company Name", placeholder="Infosys")
            notes = st.text_area("Notes", placeholder="Thesis, trigger, or valuation note")
            submitted = st.form_submit_button("Add to Watchlist", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        try:
            add_watchlist_item(WatchlistInput(ticker=ticker, company_name=company_name, notes=notes))
            st.success("Watchlist item added.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    watchlist = get_watchlist()
    with table_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge(f"{len(watchlist)} items", tone="neutral")
        render_section_header("Current Watchlist", "Monitor candidates, themes, and future opportunities.")
        if watchlist.empty:
            render_empty_state("Watchlist is empty", "Add a ticker to build your research pipeline.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        display_frame = watchlist.rename(
            columns={
                "ticker": "Ticker",
                "company_name": "Company",
                "added_on": "Added On",
                "notes": "Notes",
            }
        )
        st.dataframe(display_frame[["Ticker", "Company", "Added On", "Notes"]], use_container_width=True, hide_index=True)

        selected_row = st.selectbox(
            "Remove watchlist item",
            options=watchlist["id"].tolist(),
            format_func=lambda item_id: f"{watchlist.loc[watchlist['id'] == item_id, 'ticker'].iloc[0]} - {watchlist.loc[watchlist['id'] == item_id, 'company_name'].iloc[0]}",
        )
        if st.button("Remove Selected Watchlist Item", use_container_width=True):
            remove_watchlist_item(int(selected_row))
            st.success("Watchlist item removed.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
