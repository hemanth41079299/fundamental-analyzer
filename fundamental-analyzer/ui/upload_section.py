"""Sidebar input components."""

from __future__ import annotations

import streamlit as st


def render_upload_section():
    """Render the upload widget in the sidebar."""
    st.markdown("### Upload PDF")
    return st.file_uploader("Upload company report", type=["pdf"])


def render_company_search_section() -> tuple[str, bool]:
    """Render the web company search input and action button."""
    st.markdown("### Company Search")
    ticker = st.text_input("Enter company ticker", placeholder="INFY.NS")
    fetch_clicked = st.button("Fetch Company Data")
    return ticker, fetch_clicked


def render_portfolio_upload_section():
    """Render the portfolio CSV upload widget."""
    st.markdown("### Portfolio Analyzer")
    return st.file_uploader("Upload Portfolio CSV", type=["csv"])


def render_bulk_analysis_upload_section():
    """Render the Screener CSV upload widget."""
    st.markdown("### Bulk Company Analysis")
    return st.file_uploader("Upload Screener CSV", type=["csv"])
