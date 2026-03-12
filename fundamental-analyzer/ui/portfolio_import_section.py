"""Portfolio holdings import UI."""

from __future__ import annotations

from datetime import date

import streamlit as st

from services.portfolio_import_service import IMPORT_MODE_LABELS, build_portfolio_import_preview, import_portfolio_holdings
from ui.design_system import render_insight_card, render_section_header, render_status_badge
from ui.layout_helpers import create_columns
from ui.ui_theme import apply_finance_theme


def render_portfolio_import_section() -> None:
    """Render the holdings import workflow."""
    apply_finance_theme()
    render_section_header(
        "Portfolio Holdings Import",
        "Upload CSV, Excel, or holdings-style PDF files and convert them into BUY transactions after preview.",
    )

    left_column, right_column = create_columns([1.6, 1])
    with left_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_status_badge("Holdings Import", tone="info")
        upload = st.file_uploader(
            "Upload Holdings File",
            type=["csv", "xlsx", "xls", "pdf"],
            key="portfolio_holdings_import_file",
            help="Supported formats: CSV, Excel, and text-based holdings PDFs.",
        )
        import_mode = st.selectbox(
            "Import Mode",
            options=list(IMPORT_MODE_LABELS.keys()),
            format_func=lambda key: IMPORT_MODE_LABELS[key],
            index=0,
            key="portfolio_holdings_import_mode",
        )
        import_date = st.date_input(
            "Transaction Date",
            value=date.today(),
            key="portfolio_holdings_import_date",
        )
        import_note = st.text_area(
            "Import Note",
            placeholder="Optional note to add to imported BUY transactions",
            key="portfolio_holdings_import_note",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right_column:
        render_insight_card("Default Mode", "BUY transactions", "Parsed holdings are converted into BUY ledger entries using quantity and avg buy.", "neutral")
        render_insight_card("Required Fields", "Ticker, quantity, avg buy", "Avg buy can be derived from buy value divided by quantity when available.", "positive")
        render_insight_card("Import Safety", "Preview before save", "Rows are validated first. The import stops if any row is incomplete.", "warning")

    if upload is None:
        return

    try:
        preview = build_portfolio_import_preview(upload)
    except ValueError as exc:
        st.error(str(exc))
        return

    stats_left, stats_right, stats_third = st.columns(3)
    with stats_left:
        st.metric("File", preview.file_name)
    with stats_right:
        st.metric("Parsed Rows", len(preview.holdings))
    with stats_third:
        ready_count = int((preview.import_ready["validation_status"] == "Ready").sum()) if not preview.import_ready.empty else 0
        st.metric("Import Ready", ready_count)

    preview_column, validation_column = create_columns([1.5, 1])
    with preview_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_section_header("Parsed Holdings Preview", "Normalized holdings data before conversion into portfolio transactions.")
        st.dataframe(preview.holdings, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with validation_column:
        st.markdown('<div class="finance-side-card">', unsafe_allow_html=True)
        render_section_header("Import Preview", "Rows marked Ready will be converted into BUY transactions.")
        st.dataframe(preview.import_ready, use_container_width=True, hide_index=True)
        confirm_disabled = preview.import_ready.empty or bool((preview.import_ready["validation_status"] != "Ready").any())
        if st.button("Confirm Holdings Import", use_container_width=True, disabled=confirm_disabled):
            try:
                imported_count = import_portfolio_holdings(
                    holdings=preview.holdings,
                    import_mode=import_mode,
                    import_date=import_date.isoformat(),
                    import_note=import_note,
                )
                st.session_state["portfolio_import_completed"] = {
                    "rows_imported": imported_count,
                    "file_name": preview.file_name,
                }
                st.success(f"Imported {imported_count} BUY transactions into the portfolio ledger.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if confirm_disabled:
            st.caption("Resolve all invalid rows before confirming the import.")
        st.markdown("</div>", unsafe_allow_html=True)
