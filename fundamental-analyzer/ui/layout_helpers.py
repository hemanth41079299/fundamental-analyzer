"""Layout helpers for the premium finance interface."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import streamlit as st

from ui.design_system import render_empty_state, render_page_header
from ui.ui_theme import apply_finance_theme


def setup_page_shell(page_title: str, caption: str | None = None, badges: list[tuple[str, str]] | None = None) -> None:
    """Apply the shared theme and render a page header."""
    apply_finance_theme()
    render_page_header(page_title, caption or "", badges=badges)


def render_spacer(lines: int = 1) -> None:
    """Render vertical spacing."""
    for _ in range(max(lines, 0)):
        st.markdown("<div style='height:0.45rem;'></div>", unsafe_allow_html=True)


def create_columns(spec: Sequence[float] | int, gap: str = "large") -> list[Any]:
    """Create Streamlit columns from a ratio spec or count."""
    apply_finance_theme()
    return list(st.columns(spec, gap=gap))


def render_empty_page(title: str, message: str) -> None:
    """Render a page-level empty state."""
    apply_finance_theme()
    render_empty_state(title, message)


def centered_auth_columns() -> list[Any]:
    """Return a balanced layout for auth pages."""
    apply_finance_theme()
    return list(st.columns([1.15, 1], gap="large"))
