"""Layout helpers for clean Streamlit finance pages."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import streamlit as st

from ui.design_system import render_empty_state, render_section_header
from ui.ui_theme import apply_finance_theme


def setup_page_shell(page_title: str, caption: str | None = None) -> None:
    """Apply the shared theme and render a page header."""
    apply_finance_theme()
    render_section_header(page_title, caption)


def render_spacer(lines: int = 1) -> None:
    """Render vertical spacing."""
    for _ in range(max(lines, 0)):
        st.write("")


def create_columns(spec: Sequence[float] | int) -> list[Any]:
    """Create Streamlit columns from a ratio spec or a column count."""
    apply_finance_theme()
    return list(st.columns(spec))


def render_empty_page(title: str, message: str) -> None:
    """Render a page-level empty state."""
    apply_finance_theme()
    render_empty_state(title, message)
