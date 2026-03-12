"""Layout helpers for the professional fintech interface."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import streamlit as st

from ui.components.section_header import render_page_header
from ui.theme import apply_theme_css


def setup_page_shell(page_title: str, caption: str | None = None) -> None:
    """Apply theme CSS and render a standard page header."""
    apply_theme_css()
    render_page_header(page_title, caption or "")


def render_spacer(lines: int = 1) -> None:
    """Render vertical spacing."""
    for _ in range(max(lines, 0)):
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


def create_columns(spec: Sequence[float] | int, gap: str = "medium") -> list[Any]:
    """Create columns with theme applied."""
    apply_theme_css()
    return list(st.columns(spec, gap=gap))


def centered_auth_columns() -> list[Any]:
    """Return a two-column auth layout."""
    apply_theme_css()
    return list(st.columns([1.1, 0.9], gap="large"))
