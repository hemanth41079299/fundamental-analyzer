"""Narration display section."""

from __future__ import annotations

import streamlit as st


def render_narration(narration: str) -> None:
    """Render narration output."""
    st.subheader("Narration")
    st.write(narration)
