"""Centralized theme and CSS for the finance UI."""

from __future__ import annotations

import streamlit as st

FINANCE_THEME_CSS = """
<style>
:root {
    --finance-bg: #f8fafc;
    --finance-surface: #ffffff;
    --finance-border: #eaecf0;
    --finance-border-strong: #d0d5dd;
    --finance-text: #101828;
    --finance-text-muted: #667085;
    --finance-text-soft: #475467;
    --finance-shadow: 0 1px 2px rgba(16, 24, 40, 0.05);
    --finance-radius: 18px;
    --finance-success-bg: #ecfdf3;
    --finance-success-text: #027a48;
    --finance-warning-bg: #fff6ed;
    --finance-warning-text: #b54708;
    --finance-danger-bg: #fef3f2;
    --finance-danger-text: #b42318;
    --finance-neutral-bg: #f2f4f7;
    --finance-neutral-text: #344054;
    --finance-info-bg: #eff8ff;
    --finance-info-text: #175cd3;
}

.finance-page-header {
    padding: 0.2rem 0 1rem 0;
}
.finance-page-header h2 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: var(--finance-text);
}
.finance-page-subtitle {
    color: var(--finance-text-muted);
    font-size: 0.96rem;
    margin-top: 0.25rem;
}
.finance-page-status {
    margin-top: 0.75rem;
    display: inline-block;
    padding: 0.45rem 0.8rem;
    border: 1px solid var(--finance-border);
    border-radius: 999px;
    background: var(--finance-bg);
    color: var(--finance-neutral-text);
    font-size: 0.88rem;
}
.finance-section-header {
    margin: 1.25rem 0 0.85rem 0;
}
.finance-section-header h3 {
    margin: 0;
    color: var(--finance-text);
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}
.finance-section-caption {
    margin-top: 0.18rem;
    color: var(--finance-text-muted);
    font-size: 0.9rem;
}
.finance-card,
.finance-chart-card,
.finance-insight-card,
.finance-side-card {
    background: var(--finance-surface);
    border: 1px solid var(--finance-border);
    border-radius: var(--finance-radius);
    box-shadow: var(--finance-shadow);
}
.finance-card {
    padding: 1rem 1.1rem;
    min-height: 118px;
}
.finance-card-title {
    color: var(--finance-text-muted);
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.5rem;
}
.finance-card-value {
    color: var(--finance-text);
    font-size: 1.45rem;
    font-weight: 700;
    line-height: 1.2;
}
.finance-card-delta {
    margin-top: 0.45rem;
    color: var(--finance-text-soft);
    font-size: 0.9rem;
}
.finance-card-help {
    margin-top: 0.5rem;
    color: var(--finance-text-muted);
    font-size: 0.8rem;
}
.finance-chart-card,
.finance-side-card {
    padding: 1rem;
}
.finance-insight-card {
    padding: 0.95rem 1rem;
    min-height: 110px;
}
.finance-insight-label {
    color: var(--finance-text-muted);
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.4rem;
}
.finance-insight-value {
    color: var(--finance-text);
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 0.35rem;
}
.finance-insight-meta {
    color: var(--finance-text-soft);
    font-size: 0.88rem;
    line-height: 1.4;
}
.finance-badge {
    display: inline-block;
    border-radius: 999px;
    padding: 0.2rem 0.6rem;
    font-size: 0.78rem;
    font-weight: 600;
}
.finance-badge-positive { background: var(--finance-success-bg); color: var(--finance-success-text); }
.finance-badge-warning { background: var(--finance-warning-bg); color: var(--finance-warning-text); }
.finance-badge-negative { background: var(--finance-danger-bg); color: var(--finance-danger-text); }
.finance-badge-neutral { background: var(--finance-neutral-bg); color: var(--finance-neutral-text); }
.finance-badge-info { background: var(--finance-info-bg); color: var(--finance-info-text); }
.finance-empty-state {
    padding: 2rem 1rem;
    border: 1px dashed var(--finance-border-strong);
    border-radius: var(--finance-radius);
    text-align: center;
    background: #fcfcfd;
}
.finance-empty-state h3 {
    margin: 0 0 0.5rem 0;
    color: var(--finance-text);
}
.finance-empty-state p {
    margin: 0;
    color: var(--finance-text-muted);
}

/* Backward-compatible portfolio classes */
.portfolio-header { padding: 0.2rem 0 1rem 0; }
.portfolio-header h2 { margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: -0.03em; color: var(--finance-text); }
.portfolio-subtitle { color: var(--finance-text-muted); font-size: 0.96rem; margin-top: 0.25rem; }
.portfolio-status { margin-top: 0.75rem; display: inline-block; padding: 0.45rem 0.8rem; border: 1px solid var(--finance-border); border-radius: 999px; background: var(--finance-bg); color: var(--finance-neutral-text); font-size: 0.88rem; }
.portfolio-card { background: var(--finance-surface); border: 1px solid var(--finance-border); border-radius: var(--finance-radius); padding: 1rem 1.1rem; min-height: 118px; box-shadow: var(--finance-shadow); }
.portfolio-card-title { color: var(--finance-text-muted); font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.5rem; }
.portfolio-card-value { color: var(--finance-text); font-size: 1.45rem; font-weight: 700; line-height: 1.2; }
.portfolio-card-delta { margin-top: 0.45rem; color: var(--finance-text-soft); font-size: 0.9rem; }
.portfolio-card-help { margin-top: 0.5rem; color: var(--finance-text-muted); font-size: 0.8rem; }
.portfolio-insight-card { background: var(--finance-surface); border: 1px solid var(--finance-border); border-radius: var(--finance-radius); padding: 0.95rem 1rem; min-height: 110px; box-shadow: var(--finance-shadow); }
.portfolio-insight-label { color: var(--finance-text-muted); font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.4rem; }
.portfolio-insight-value { color: var(--finance-text); font-size: 1.05rem; font-weight: 700; margin-bottom: 0.35rem; }
.portfolio-insight-meta { color: var(--finance-text-soft); font-size: 0.88rem; line-height: 1.4; }
.portfolio-side-card { background: var(--finance-surface); border: 1px solid var(--finance-border); border-radius: var(--finance-radius); padding: 1rem; box-shadow: var(--finance-shadow); }
.portfolio-badge { display: inline-block; border-radius: 999px; padding: 0.2rem 0.6rem; font-size: 0.78rem; font-weight: 600; }
.badge-positive { background: var(--finance-success-bg); color: var(--finance-success-text); }
.badge-neutral { background: var(--finance-neutral-bg); color: var(--finance-neutral-text); }
.badge-warning { background: var(--finance-warning-bg); color: var(--finance-warning-text); }
.badge-negative { background: var(--finance-danger-bg); color: var(--finance-danger-text); }
.portfolio-empty-state { padding: 2rem 1rem; border: 1px dashed var(--finance-border-strong); border-radius: var(--finance-radius); text-align: center; background: #fcfcfd; }
</style>
"""


def apply_finance_theme() -> None:
    """Inject the shared finance design system CSS."""
    if st.session_state.get("_finance_theme_loaded"):
        return
    st.markdown(FINANCE_THEME_CSS, unsafe_allow_html=True)
    st.session_state["_finance_theme_loaded"] = True
