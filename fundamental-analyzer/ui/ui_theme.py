"""Centralized theme system for the finance UI."""

from __future__ import annotations

from typing import Any

import streamlit as st

THEME_LIGHT: dict[str, str] = {
    "mode": "light",
    "bg": "#f5f7fb",
    "bg_alt": "#edf2ff",
    "surface": "#fbfdff",
    "surface_alt": "#f3f7ff",
    "card": "rgba(255,255,255,0.86)",
    "border": "rgba(15, 23, 42, 0.08)",
    "border_strong": "rgba(15, 23, 42, 0.14)",
    "text": "#0f172a",
    "text_secondary": "#334155",
    "text_muted": "#64748b",
    "accent": "#4f46e5",
    "accent_soft": "rgba(79, 70, 229, 0.10)",
    "accent_alt": "#0ea5a4",
    "positive": "#15803d",
    "positive_soft": "rgba(34, 197, 94, 0.14)",
    "negative": "#dc2626",
    "negative_soft": "rgba(239, 68, 68, 0.14)",
    "warning": "#d97706",
    "warning_soft": "rgba(245, 158, 11, 0.16)",
    "info": "#2563eb",
    "info_soft": "rgba(37, 99, 235, 0.14)",
    "chip": "#e2e8f0",
    "hover": "rgba(79, 70, 229, 0.06)",
    "shadow": "0 18px 50px rgba(15, 23, 42, 0.08)",
    "shadow_soft": "0 8px 24px rgba(15, 23, 42, 0.06)",
    "gradient": "linear-gradient(135deg, rgba(79,70,229,0.12), rgba(14,165,164,0.10), rgba(255,255,255,0.78))",
}

THEME_DARK: dict[str, str] = {
    "mode": "dark",
    "bg": "#0b1220",
    "bg_alt": "#11192b",
    "surface": "#131d31",
    "surface_alt": "#182338",
    "card": "rgba(19,29,49,0.86)",
    "border": "rgba(148, 163, 184, 0.14)",
    "border_strong": "rgba(148, 163, 184, 0.22)",
    "text": "#f8fafc",
    "text_secondary": "#dbe4f0",
    "text_muted": "#94a3b8",
    "accent": "#7c83ff",
    "accent_soft": "rgba(124, 131, 255, 0.18)",
    "accent_alt": "#2dd4bf",
    "positive": "#4ade80",
    "positive_soft": "rgba(74, 222, 128, 0.18)",
    "negative": "#fb7185",
    "negative_soft": "rgba(251, 113, 133, 0.18)",
    "warning": "#fbbf24",
    "warning_soft": "rgba(251, 191, 36, 0.18)",
    "info": "#60a5fa",
    "info_soft": "rgba(96, 165, 250, 0.18)",
    "chip": "#24324a",
    "hover": "rgba(124, 131, 255, 0.12)",
    "shadow": "0 22px 60px rgba(2, 6, 23, 0.48)",
    "shadow_soft": "0 10px 28px rgba(2, 6, 23, 0.34)",
    "gradient": "linear-gradient(135deg, rgba(124,131,255,0.18), rgba(45,212,191,0.12), rgba(19,29,49,0.92))",
}

THEME_OPTIONS = {"Light": THEME_LIGHT, "Dark": THEME_DARK}


def initialize_theme_state() -> None:
    """Initialize theme session state."""
    st.session_state.setdefault("finance_theme_mode", "Light")


def get_theme_mode() -> str:
    """Return the active theme mode."""
    initialize_theme_state()
    mode = str(st.session_state.get("finance_theme_mode", "Light"))
    return mode if mode in THEME_OPTIONS else "Light"


def set_theme_mode(mode: str) -> None:
    """Persist a theme mode in session state."""
    cleaned = str(mode).title()
    if cleaned not in THEME_OPTIONS:
        cleaned = "Light"
    st.session_state["finance_theme_mode"] = cleaned


def get_theme() -> dict[str, str]:
    """Return the current theme tokens."""
    return THEME_OPTIONS[get_theme_mode()]


def render_theme_toggle(location: str = "sidebar", key: str = "finance_theme_selector") -> str:
    """Render a visible light/dark toggle and persist the selection."""
    initialize_theme_state()
    current_mode = get_theme_mode()
    container = st.sidebar if location == "sidebar" else st
    with container:
        selection = st.radio(
            "Theme",
            options=["Light", "Dark"],
            index=0 if current_mode == "Light" else 1,
            horizontal=True,
            key=key,
        )
    if selection != current_mode:
        set_theme_mode(selection)
    return get_theme_mode()


def get_plotly_theme() -> dict[str, Any]:
    """Return theme-aware Plotly styling tokens."""
    theme = get_theme()
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font_color": theme["text_secondary"],
        "grid_color": theme["border"],
        "accent": theme["accent"],
        "accent_alt": theme["accent_alt"],
    }


def _css_variables(theme: dict[str, str]) -> str:
    """Convert theme tokens into CSS variables."""
    return "\n".join(f"    --finance-{key.replace('_', '-')}: {value};" for key, value in theme.items())


def _build_theme_css(theme: dict[str, str]) -> str:
    """Generate centralized CSS for the active theme."""
    return f"""
    <style>
    :root {{
{_css_variables(theme)}
        --finance-radius-xl: 28px;
        --finance-radius-lg: 22px;
        --finance-radius-md: 16px;
        --finance-radius-sm: 12px;
        --finance-space-1: 0.4rem;
        --finance-space-2: 0.7rem;
        --finance-space-3: 1rem;
        --finance-space-4: 1.35rem;
        --finance-space-5: 1.75rem;
    }}

    html, body, [class*="css"], .stApp {{
        color: var(--finance-text);
        font-feature-settings: "ss01" on, "cv01" on;
    }}

    .stApp {{
        background:
            radial-gradient(circle at top left, var(--finance-accent-soft), transparent 26%),
            radial-gradient(circle at top right, rgba(14,165,164,0.10), transparent 24%),
            linear-gradient(180deg, var(--finance-bg-alt) 0%, var(--finance-bg) 26%, var(--finance-bg) 100%);
    }}

    [data-testid="stAppViewContainer"] > .main {{
        background: transparent;
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.0)), var(--finance-surface);
        border-right: 1px solid var(--finance-border);
    }}

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label {{
        color: var(--finance-text) !important;
    }}

    [data-testid="stSidebarUserContent"] {{
        padding-top: 1rem;
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1440px;
    }}

    .finance-page-shell {{
        display: flex;
        flex-direction: column;
        gap: 1.15rem;
    }}

    .finance-page-header {{
        position: relative;
        padding: 1.25rem 1.35rem 1.35rem 1.35rem;
        border-radius: var(--finance-radius-xl);
        background: var(--finance-gradient);
        border: 1px solid var(--finance-border);
        box-shadow: var(--finance-shadow);
        overflow: hidden;
        margin-bottom: 0.5rem;
    }}

    .finance-page-header::after {{
        content: "";
        position: absolute;
        inset: auto -12% -45% auto;
        width: 280px;
        height: 280px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(255,255,255,0.14), transparent 64%);
        pointer-events: none;
    }}

    .finance-page-header h1,
    .finance-page-header h2 {{
        margin: 0;
        font-size: clamp(1.9rem, 2.8vw, 2.8rem);
        line-height: 1.06;
        letter-spacing: -0.045em;
        color: var(--finance-text);
        font-weight: 760;
    }}

    .finance-page-subtitle {{
        color: var(--finance-text-muted);
        font-size: 0.98rem;
        margin-top: 0.55rem;
        max-width: 72ch;
        line-height: 1.55;
    }}

    .finance-page-status-row {{
        display: flex;
        gap: 0.55rem;
        flex-wrap: wrap;
        margin-top: 0.95rem;
    }}

    .finance-section-header {{
        margin: 0 0 0.85rem 0;
    }}

    .finance-section-header h3 {{
        margin: 0;
        color: var(--finance-text);
        font-size: 1.08rem;
        font-weight: 720;
        letter-spacing: -0.03em;
    }}

    .finance-section-caption {{
        margin-top: 0.3rem;
        color: var(--finance-text-muted);
        font-size: 0.92rem;
        line-height: 1.5;
    }}

    .finance-card,
    .finance-chart-card,
    .finance-insight-card,
    .finance-side-card,
    .finance-glass-panel,
    .finance-form-card,
    .finance-table-card,
    .finance-auth-card,
    .finance-hero-panel,
    .portfolio-side-card,
    .portfolio-card,
    .portfolio-insight-card {{
        position: relative;
        background: var(--finance-card);
        border: 1px solid var(--finance-border);
        border-radius: var(--finance-radius-lg);
        box-shadow: var(--finance-shadow-soft);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
    }}

    .finance-card:hover,
    .finance-chart-card:hover,
    .finance-insight-card:hover,
    .finance-side-card:hover,
    .finance-table-card:hover {{
        transform: translateY(-1px);
        box-shadow: var(--finance-shadow);
        border-color: var(--finance-border-strong);
    }}

    .finance-card {{
        padding: 1.15rem;
        min-height: 132px;
    }}

    .finance-side-card,
    .finance-chart-card,
    .finance-form-card,
    .finance-table-card,
    .finance-glass-panel,
    .portfolio-side-card {{
        padding: 1.2rem;
    }}

    .finance-card-title,
    .finance-insight-label {{
        color: var(--finance-text-muted);
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.10em;
        margin-bottom: 0.55rem;
    }}

    .finance-card-value {{
        color: var(--finance-text);
        font-size: clamp(1.32rem, 2vw, 1.9rem);
        font-weight: 760;
        letter-spacing: -0.04em;
        line-height: 1.08;
    }}

    .finance-card-delta,
    .finance-insight-meta,
    .finance-card-help {{
        color: var(--finance-text-muted);
        font-size: 0.9rem;
        line-height: 1.5;
        margin-top: 0.45rem;
    }}

    .finance-insight-card {{
        padding: 1rem 1.05rem;
        min-height: 122px;
    }}

    .finance-insight-value {{
        color: var(--finance-text);
        font-size: 1.08rem;
        font-weight: 720;
        line-height: 1.28;
        margin-bottom: 0.4rem;
    }}

    .finance-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        border-radius: 999px;
        padding: 0.34rem 0.72rem;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.01em;
        border: 1px solid transparent;
    }}

    .finance-badge-positive {{ background: var(--finance-positive-soft); color: var(--finance-positive); border-color: rgba(34,197,94,0.16); }}
    .finance-badge-warning {{ background: var(--finance-warning-soft); color: var(--finance-warning); border-color: rgba(245,158,11,0.16); }}
    .finance-badge-negative {{ background: var(--finance-negative-soft); color: var(--finance-negative); border-color: rgba(239,68,68,0.16); }}
    .finance-badge-neutral {{ background: color-mix(in srgb, var(--finance-chip) 88%, transparent); color: var(--finance-text-secondary); border-color: var(--finance-border); }}
    .finance-badge-info {{ background: var(--finance-info-soft); color: var(--finance-info); border-color: rgba(37,99,235,0.16); }}

    .finance-empty-state {{
        padding: 2.4rem 1.35rem;
        border: 1px dashed var(--finance-border-strong);
        border-radius: var(--finance-radius-lg);
        text-align: center;
        background: linear-gradient(180deg, color-mix(in srgb, var(--finance-card) 92%, transparent), color-mix(in srgb, var(--finance-surface-alt) 80%, transparent));
    }}

    .finance-empty-state h3 {{
        margin: 0 0 0.55rem 0;
        color: var(--finance-text);
        font-size: 1.15rem;
        letter-spacing: -0.03em;
    }}

    .finance-empty-state p {{
        margin: 0;
        color: var(--finance-text-muted);
        max-width: 42rem;
        margin-inline: auto;
        line-height: 1.6;
    }}

    .finance-auth-layout {{
        display: grid;
        grid-template-columns: 1.05fr 1fr;
        gap: 1.25rem;
        align-items: stretch;
    }}

    .finance-hero-panel {{
        padding: 1.6rem;
        min-height: 100%;
        background: linear-gradient(155deg, color-mix(in srgb, var(--finance-accent-soft) 76%, transparent), color-mix(in srgb, var(--finance-card) 84%, transparent));
    }}

    .finance-hero-panel h2 {{
        margin: 0;
        font-size: 2.15rem;
        letter-spacing: -0.05em;
        color: var(--finance-text);
    }}

    .finance-hero-panel p {{
        color: var(--finance-text-muted);
        line-height: 1.7;
        font-size: 0.98rem;
    }}

    .finance-auth-card {{
        padding: 1.5rem;
    }}

    .finance-auth-kicker {{
        color: var(--finance-accent);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.74rem;
        margin-bottom: 0.75rem;
    }}

    .finance-stat-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
    }}

    .finance-action-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.9rem;
        flex-wrap: wrap;
        padding: 0.9rem 1rem;
        border: 1px solid var(--finance-border);
        border-radius: var(--finance-radius-md);
        background: color-mix(in srgb, var(--finance-surface-alt) 82%, transparent);
        margin-bottom: 1rem;
    }}

    div[data-testid="stForm"] {{
        border: none;
        background: transparent;
        padding: 0;
    }}

    label, .stMarkdown p, .stCaption {{
        color: var(--finance-text-secondary);
    }}

    .stTextInput > div > div,
    .stNumberInput > div > div,
    .stSelectbox > div > div,
    .stTextArea textarea,
    .stDateInput > div > div,
    .stMultiSelect > div > div {{
        background: color-mix(in srgb, var(--finance-surface) 92%, transparent) !important;
        border: 1px solid var(--finance-border) !important;
        border-radius: 14px !important;
        color: var(--finance-text) !important;
        box-shadow: none !important;
    }}

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] input {{
        color: var(--finance-text) !important;
    }}

    .stTextInput > div > div:focus-within,
    .stNumberInput > div > div:focus-within,
    .stSelectbox > div > div:focus-within,
    .stDateInput > div > div:focus-within,
    .stTextArea textarea:focus {{
        border-color: var(--finance-accent) !important;
        box-shadow: 0 0 0 4px var(--finance-accent-soft) !important;
    }}

    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {{
        border-radius: 14px !important;
        border: 1px solid transparent !important;
        background: linear-gradient(135deg, var(--finance-accent), var(--finance-accent-alt)) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: 0.01em !important;
        padding: 0.68rem 1rem !important;
        box-shadow: 0 12px 28px rgba(79, 70, 229, 0.22) !important;
    }}

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {{
        filter: brightness(1.03);
        transform: translateY(-1px);
    }}

    .stDataFrame, [data-testid="stDataFrame"] {{
        border-radius: 18px !important;
        overflow: hidden !important;
        border: 1px solid var(--finance-border) !important;
        box-shadow: var(--finance-shadow-soft) !important;
        background: color-mix(in srgb, var(--finance-card) 95%, transparent) !important;
    }}

    [data-testid="stDataFrame"] [role="grid"] {{
        background: transparent !important;
    }}

    [data-testid="stMetric"] {{
        background: color-mix(in srgb, var(--finance-card) 92%, transparent);
        border: 1px solid var(--finance-border);
        border-radius: var(--finance-radius-md);
        padding: 0.9rem 1rem;
    }}

    [data-testid="stMetricLabel"] {{
        color: var(--finance-text-muted) !important;
    }}

    [data-testid="stMetricValue"] {{
        color: var(--finance-text) !important;
        letter-spacing: -0.03em;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background: transparent;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 2.55rem;
        border-radius: 999px;
        padding-inline: 1rem;
        background: color-mix(in srgb, var(--finance-surface) 94%, transparent);
        border: 1px solid var(--finance-border);
        color: var(--finance-text-secondary);
    }}

    .stTabs [aria-selected="true"] {{
        background: var(--finance-accent-soft) !important;
        color: var(--finance-accent) !important;
        border-color: color-mix(in srgb, var(--finance-accent) 28%, transparent) !important;
    }}

    .stAlert {{
        border-radius: 16px !important;
        border: 1px solid var(--finance-border) !important;
    }}

    @media (max-width: 980px) {{
        .finance-auth-layout {{
            grid-template-columns: 1fr;
        }}
        .block-container {{
            padding-top: 1.25rem;
        }}
    }}
    </style>
    """


def apply_finance_theme() -> None:
    """Inject the current theme CSS."""
    initialize_theme_state()
    st.markdown(_build_theme_css(get_theme()), unsafe_allow_html=True)
