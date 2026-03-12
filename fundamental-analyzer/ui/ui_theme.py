"""Backward-compatible theme wrapper."""

from __future__ import annotations

from ui.theme import apply_theme_css, get_plotly_layout, get_theme, get_theme_name, render_theme_toggle, toggle_theme


def apply_finance_theme() -> None:
    """Compatibility wrapper for legacy imports."""
    apply_theme_css()


__all__ = [
    "apply_finance_theme",
    "apply_theme_css",
    "get_plotly_layout",
    "get_theme",
    "get_theme_name",
    "render_theme_toggle",
    "toggle_theme",
]
