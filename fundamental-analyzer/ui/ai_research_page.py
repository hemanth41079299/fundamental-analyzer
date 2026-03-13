"""AI Research assistant page for deterministic natural-language research queries."""

from __future__ import annotations

import streamlit as st

from services.ai_research_service import answer_research_query
from ui.design_system import render_empty_state, render_section_header

_EXAMPLE_QUERIES = [
    "Analyze Tata Motors",
    "Compare HDFC Bank vs ICICI Bank",
    "What risks exist in my portfolio?",
    "Explain recent news impact",
]


def render_ai_research_page(user_id: int) -> None:
    """Render the AI Research assistant tab."""
    render_section_header(
        "AI Research",
        "Ask natural-language questions about companies, portfolio risks, news impact, scorecards, and comparative research.",
    )

    st.markdown(
        """
        <div class="ui-card" style="margin-bottom: 16px;">
            <div class="ui-card-title">Example queries</div>
            <div class="ui-section-caption">Analyze Tata Motors | Compare HDFC Bank vs ICICI Bank | What risks exist in my portfolio? | Explain recent news impact</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    example_columns = st.columns(len(_EXAMPLE_QUERIES), gap="small")
    for column, query in zip(example_columns, _EXAMPLE_QUERIES):
        with column:
            if st.button(query, use_container_width=True, key=f"ai_research_example_{query}"):
                st.session_state["ai_research_query"] = query

    with st.form("ai_research_form", clear_on_submit=False):
        query = st.text_area(
            "Ask the research assistant",
            value=str(st.session_state.get("ai_research_query", "")),
            placeholder="Analyze Tata Motors",
            height=120,
        )
        submitted = st.form_submit_button("Run Research", use_container_width=True)

    if submitted:
        st.session_state["ai_research_query"] = query
        try:
            response = answer_research_query(query, user_id=user_id)
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Unable to complete the research request: {exc}")
        else:
            st.markdown(
                """
                <div class="ui-card" style="margin-top: 12px;">
                    <div class="ui-card-title">Research Response</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(response)
    elif not st.session_state.get("ai_research_query"):
        render_empty_state("No research question yet", "Enter a question above or use one of the example prompts.")
