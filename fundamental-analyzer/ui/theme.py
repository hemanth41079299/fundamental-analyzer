"""Centralized light and dark theme system for the Streamlit UI."""

from __future__ import annotations

import streamlit as st

LIGHT_THEME: dict[str, str] = {
    "background": "#F6F8FB",
    "card_background": "#FFFFFF",
    "border": "#E5E7EB",
    "text_primary": "#111827",
    "text_secondary": "#4B5563",
    "text_muted": "#6B7280",
    "sidebar_text": "#374151",
    "sidebar_text_active": "#111827",
    "sidebar_text_inactive": "#374151",
    "heading_text": "#111827",
    "caption_text": "#4B5563",
    "card_text": "#111827",
    "info_text": "#1E40AF",
    "warning_text": "#92400E",
    "positive_text": "#166534",
    "negative_text": "#B91C1C",
    "accent": "#2563EB",
    "positive": "#15803D",
    "risk": "#DC2626",
    "watch": "#D97706",
    "info": "#2563EB",
    "shadow": "0 1px 2px rgba(15,23,42,0.05), 0 8px 18px rgba(15,23,42,0.03)",
    "hover": "rgba(15,23,42,0.03)",
    "table_header": "#F8FAFC",
    "sidebar_active_background": "rgba(37, 99, 235, 0.06)",
    "sidebar_hover_background": "rgba(15, 23, 42, 0.03)",
    "info_background": "#F4F8FF",
    "warning_background": "#FFFBEB",
    "positive_background": "#F4FBF6",
    "negative_background": "#FEF6F5",
}

DARK_THEME: dict[str, str] = {
    "background": "#111827",
    "card_background": "#1F2937",
    "border": "#374151",
    "text_primary": "#F9FAFB",
    "text_secondary": "#D1D5DB",
    "text_muted": "#9CA3AF",
    "sidebar_text": "#CBD5E1",
    "sidebar_text_active": "#FFFFFF",
    "sidebar_text_inactive": "#CBD5E1",
    "heading_text": "#F9FAFB",
    "caption_text": "#D1D5DB",
    "card_text": "#F9FAFB",
    "info_text": "#BFDBFE",
    "warning_text": "#FDE68A",
    "positive_text": "#BBF7D0",
    "negative_text": "#FECACA",
    "accent": "#3B82F6",
    "positive": "#22C55E",
    "risk": "#F87171",
    "watch": "#F59E0B",
    "info": "#60A5FA",
    "shadow": "0 1px 2px rgba(0,0,0,0.28), 0 10px 24px rgba(0,0,0,0.18)",
    "hover": "rgba(255,255,255,0.04)",
    "table_header": "#18212F",
    "sidebar_active_background": "rgba(59, 130, 246, 0.14)",
    "sidebar_hover_background": "rgba(255, 255, 255, 0.04)",
    "info_background": "rgba(59, 130, 246, 0.12)",
    "warning_background": "rgba(217, 119, 6, 0.12)",
    "positive_background": "rgba(34, 197, 94, 0.1)",
    "negative_background": "rgba(239, 68, 68, 0.1)",
}


def get_theme_name() -> str:
    """Return the active theme name."""
    current = str(st.session_state.get("theme", "Dark")).title()
    if current not in {"Light", "Dark"}:
        current = "Dark"
    st.session_state["theme"] = current
    return current


def get_theme() -> dict[str, str]:
    """Return the active theme tokens."""
    return LIGHT_THEME if get_theme_name() == "Light" else DARK_THEME


def toggle_theme() -> None:
    """Toggle the active theme in session state."""
    st.session_state["theme"] = "Light" if get_theme_name() == "Dark" else "Dark"


def render_theme_toggle(location: str = "sidebar", key: str = "theme_toggle") -> str:
    """Render a visible theme toggle and persist the selection."""
    container = st.sidebar if location == "sidebar" else st
    selected = container.radio(
        "Theme",
        options=["Light", "Dark"],
        horizontal=True,
        index=0 if get_theme_name() == "Light" else 1,
        key=key,
    )
    st.session_state["theme"] = selected
    return selected


def get_plotly_layout() -> dict[str, str]:
    """Return theme-aware colors for Plotly charts."""
    theme = get_theme()
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font_color": theme["text_secondary"],
        "grid_color": theme["border"],
        "accent": theme["accent"],
        "positive": theme["positive"],
        "risk": theme["risk"],
        "watch": theme["watch"],
    }


def apply_theme_css() -> None:
    """Inject theme-aware CSS globally."""
    theme = get_theme()
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {{
            --ui-background: {theme["background"]};
            --ui-card: {theme["card_background"]};
            --ui-border: {theme["border"]};
            --ui-text: {theme["text_primary"]};
            --ui-text-secondary: {theme["text_secondary"]};
            --ui-text-muted: {theme["text_muted"]};
            --ui-sidebar-text: {theme["sidebar_text"]};
            --ui-sidebar-text-active: {theme["sidebar_text_active"]};
            --ui-sidebar-text-inactive: {theme["sidebar_text_inactive"]};
            --ui-heading-text: {theme["heading_text"]};
            --ui-caption-text: {theme["caption_text"]};
            --ui-card-text: {theme["card_text"]};
            --ui-accent: {theme["accent"]};
            --ui-positive: {theme["positive"]};
            --ui-risk: {theme["risk"]};
            --ui-watch: {theme["watch"]};
            --ui-info: {theme["info"]};
            --ui-info-text: {theme["info_text"]};
            --ui-warning-text: {theme["warning_text"]};
            --ui-positive-text: {theme["positive_text"]};
            --ui-negative-text: {theme["negative_text"]};
            --ui-sidebar-active-background: {theme["sidebar_active_background"]};
            --ui-sidebar-hover-background: {theme["sidebar_hover_background"]};
            --ui-info-background: {theme["info_background"]};
            --ui-warning-background: {theme["warning_background"]};
            --ui-positive-background: {theme["positive_background"]};
            --ui-negative-background: {theme["negative_background"]};
            --ui-shadow: {theme["shadow"]};
            --ui-hover: {theme["hover"]};
            --ui-table-header: {theme["table_header"]};
            --ui-radius: 12px;
            --ui-space-section: 24px;
            --ui-space-card: 16px;
        }}

        html {{
            font-size: 16px;
        }}

        html, body, [class*="css"], .stApp {{
            font-family: 'Inter', sans-serif;
            color: var(--ui-text);
            font-size: 15px;
        }}

        body,
        p,
        span,
        label,
        li,
        div {{
            font-size: 14px;
        }}

        .stApp {{
            background: var(--ui-background);
        }}

        [data-testid="stSidebar"] {{
            background: var(--ui-card);
            border-right: 1px solid var(--ui-border);
        }}

        [data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
            padding-top: 0.5rem;
        }}

        [data-testid="stSidebar"] *,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label {{
            color: var(--ui-sidebar-text) !important;
        }}

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {{
            color: var(--ui-sidebar-text) !important;
        }}

        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
            color: var(--ui-sidebar-text-inactive) !important;
            font-weight: 600 !important;
            opacity: 1 !important;
            font-size: 13px !important;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] {{
            gap: 8px;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] > label {{
            border: 1px solid transparent;
            border-radius: 10px;
            padding: 8px 10px;
            transition: background 120ms ease, border-color 120ms ease, color 120ms ease;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
            background: var(--ui-sidebar-hover-background);
            border-color: var(--ui-border);
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] label p {{
            color: var(--ui-sidebar-text-inactive) !important;
            font-weight: 600 !important;
            opacity: 1 !important;
            font-size: 14px !important;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background: var(--ui-sidebar-active-background);
            border-color: var(--ui-border);
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {{
            color: var(--ui-sidebar-text-active) !important;
            font-weight: 700 !important;
        }}

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] strong {{
            color: var(--ui-sidebar-text-active) !important;
        }}

        .ui-sidebar-group-label {{
            margin: 14px 0 8px 0;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--ui-sidebar-text-inactive);
        }}

        .ui-sidebar-profile-name {{
            margin: 8px 0 2px 0;
            font-size: 14px;
            font-weight: 700;
            line-height: 1.4;
            color: var(--ui-sidebar-text-active);
        }}

        .ui-sidebar-profile-email {{
            margin: 0 0 12px 0;
            font-size: 13px;
            font-weight: 500;
            line-height: 1.5;
            color: var(--ui-sidebar-text-inactive);
        }}

        .block-container {{
            max-width: 1440px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }}

        .ui-page-header {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 24px;
        }}

        .ui-page-title {{
            margin: 0;
            font-size: 36px;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: var(--ui-heading-text);
        }}

        .ui-page-subtitle {{
            font-size: 15px;
            line-height: 1.6;
            color: var(--ui-caption-text);
            max-width: 860px;
            font-weight: 500;
        }}

        .ui-card,
        .ui-chart-card,
        .ui-table-card,
        .ui-auth-card,
        .ui-panel,
        .finance-side-card {{
            background: var(--ui-card);
            border: 1px solid var(--ui-border);
            border-radius: var(--ui-radius);
            padding: 20px;
            box-shadow: var(--ui-shadow);
        }}

        .ui-chart-card,
        .ui-table-card {{
            box-shadow: var(--ui-shadow);
        }}

        .finance-side-card {{
            margin-bottom: 16px;
        }}

        .ui-card-title,
        .ui-section-title {{
            margin: 0 0 8px 0;
            font-size: 20px;
            font-weight: 600;
            color: var(--ui-heading-text);
        }}

        .ui-caption,
        .ui-section-caption {{
            font-size: 14px;
            color: var(--ui-caption-text);
            line-height: 1.6;
            font-weight: 500;
        }}

        .ui-card-title {{
            font-size: 16px;
        }}

        .ui-kpi-label {{
            font-size: 14px;
            color: var(--ui-caption-text);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .ui-kpi-value {{
            font-size: 26px;
            font-weight: 700;
            color: var(--ui-card-text);
            letter-spacing: -0.03em;
        }}

        .ui-kpi-change {{
            margin-top: 6px;
            font-size: 14px;
            color: var(--ui-caption-text);
            font-weight: 500;
        }}

        .ui-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 13px;
            font-weight: 600;
            border: 1px solid var(--ui-border);
        }}

        .ui-badge-positive {{ background: var(--ui-positive-background); color: var(--ui-positive); }}
        .ui-badge-risk {{ background: var(--ui-negative-background); color: var(--ui-risk); }}
        .ui-badge-watch {{ background: var(--ui-warning-background); color: var(--ui-watch); }}
        .ui-badge-info {{ background: var(--ui-info-background); color: var(--ui-info-text); }}

        .stMarkdown p,
        .stMarkdown li,
        .stMarkdown span,
        .stText,
        p {{
            color: var(--ui-text-secondary);
            font-size: 14px;
            line-height: 1.65;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: var(--ui-heading-text);
        }}

        small,
        .ui-helper-text {{
            color: var(--ui-caption-text);
            font-size: 13px;
        }}

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] span {{
            font-size: 14px !important;
            line-height: 1.65 !important;
        }}

        .stCaption,
        [data-testid="stCaptionContainer"] p {{
            color: var(--ui-caption-text) !important;
            opacity: 1 !important;
            font-weight: 500 !important;
            font-size: 13px !important;
        }}

        .ui-table-card [data-testid="stDataFrame"],
        .ui-card [data-testid="stDataFrame"],
        [data-testid="stDataFrame"] {{
            border: 1px solid var(--ui-border) !important;
            border-radius: 12px !important;
            overflow: hidden !important;
            background: var(--ui-card) !important;
        }}

        [data-testid="stDataFrame"] [role="grid"] {{
            background: var(--ui-card) !important;
        }}

        [data-testid="stDataFrame"] [role="columnheader"] {{
            background: var(--ui-table-header) !important;
            color: var(--ui-heading-text) !important;
            font-weight: 700 !important;
            font-size: 13px !important;
        }}

        [data-testid="stDataFrame"] [role="gridcell"] {{
            color: var(--ui-card-text) !important;
            font-size: 14px !important;
        }}

        [data-testid="stDataFrame"] [role="row"]:hover {{
            background: var(--ui-hover) !important;
        }}

        .stTextInput > div > div,
        .stTextArea textarea,
        .stSelectbox > div > div,
        .stDateInput > div > div,
        .stNumberInput > div > div {{
            border-radius: 10px !important;
            border: 1px solid var(--ui-border) !important;
            background: var(--ui-card) !important;
            color: var(--ui-text) !important;
            box-shadow: none !important;
        }}

        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox input,
        .stNumberInput input {{
            font-size: 15px !important;
        }}

        .stTextInput label,
        .stTextArea label,
        .stSelectbox label,
        .stDateInput label,
        .stNumberInput label,
        .stRadio label {{
            color: var(--ui-heading-text) !important;
            font-weight: 600 !important;
            font-size: 15px !important;
        }}

        .stTextInput [data-testid="stMarkdownContainer"] p,
        .stTextArea [data-testid="stMarkdownContainer"] p,
        .stSelectbox [data-testid="stMarkdownContainer"] p,
        .stDateInput [data-testid="stMarkdownContainer"] p,
        .stNumberInput [data-testid="stMarkdownContainer"] p,
        .stRadio [data-testid="stMarkdownContainer"] p {{
            color: var(--ui-caption-text) !important;
            font-weight: 500 !important;
            font-size: 13px !important;
        }}

        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] span {{
            font-size: 15px !important;
            font-weight: 600 !important;
        }}

        [data-testid="stForm"] {{
            background: var(--ui-card);
            border: 1px solid var(--ui-border);
            border-radius: 12px;
            padding: 20px;
            box-shadow: var(--ui-shadow);
        }}

        [data-baseweb="tab-list"] button,
        [data-baseweb="tab"] {{
            font-size: 14px !important;
            font-weight: 600 !important;
        }}

        .stButton > button,
        .stFormSubmitButton > button,
        .stDownloadButton > button {{
            border-radius: 10px !important;
            background: var(--ui-accent) !important;
            color: #ffffff !important;
            border: 1px solid var(--ui-accent) !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            padding: 0.65rem 1rem !important;
            box-shadow: none !important;
        }}

        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        .stDownloadButton > button:hover {{
            filter: brightness(0.94);
        }}

        .stButton > button[kind="secondary"],
        .stDownloadButton > button[kind="secondary"] {{
            background: var(--ui-card) !important;
            color: var(--ui-heading-text) !important;
            border: 1px solid var(--ui-border) !important;
        }}

        [data-testid="stMetric"] {{
            background: var(--ui-card);
            border: 1px solid var(--ui-border);
            border-radius: 12px;
            padding: 12px 14px;
            box-shadow: var(--ui-shadow);
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--ui-text-secondary) !important;
            font-weight: 600 !important;
        }}

        [data-testid="stMetricValue"] {{
            color: var(--ui-heading-text) !important;
        }}

        .stAlert {{
            border: 1px solid var(--ui-border) !important;
            border-radius: 12px !important;
        }}

        [data-testid="stAlertContainer"] [data-baseweb="notification"] {{
            background: var(--ui-info-background) !important;
        }}

        [data-testid="stAlertContainer"] [kind="warning"] {{
            background: var(--ui-warning-background) !important;
        }}

        [data-testid="stAlertContainer"] [kind="success"] {{
            background: var(--ui-positive-background) !important;
        }}

        [data-testid="stAlertContainer"] [kind="error"] {{
            background: var(--ui-negative-background) !important;
        }}

        .stAlert [data-testid="stMarkdownContainer"] p,
        .stAlert [data-testid="stMarkdownContainer"] li,
        [data-testid="stAlertContainer"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stAlertContainer"] [data-testid="stMarkdownContainer"] li {{
            color: var(--ui-info-text) !important;
            font-weight: 500 !important;
        }}

        [data-testid="stAlertContainer"] [kind="warning"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stAlertContainer"] [kind="warning"] [data-testid="stMarkdownContainer"] li {{
            color: var(--ui-warning-text) !important;
        }}

        [data-testid="stAlertContainer"] [kind="success"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stAlertContainer"] [kind="success"] [data-testid="stMarkdownContainer"] li {{
            color: var(--ui-positive-text) !important;
        }}

        [data-testid="stAlertContainer"] [kind="error"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stAlertContainer"] [kind="error"] [data-testid="stMarkdownContainer"] li {{
            color: var(--ui-negative-text) !important;
        }}

        .ui-auth-layout {{
            display: grid;
            grid-template-columns: minmax(0, 1.08fr) minmax(360px, 0.92fr);
            gap: 28px;
            align-items: stretch;
        }}

        .ui-auth-hero {{
            display: flex;
            flex-direction: column;
            gap: 18px;
            justify-content: center;
            min-height: 100%;
        }}

        .ui-auth-brand-panel {{
            background: var(--ui-card);
            border: 1px solid var(--ui-border);
            border-radius: 16px;
            padding: 30px;
            box-shadow: var(--ui-shadow);
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .ui-auth-product-title {{
            font-size: 16px;
            font-weight: 700;
            color: var(--ui-heading-text);
            letter-spacing: -0.01em;
        }}

        .ui-auth-product-subtitle {{
            margin-top: -8px;
            font-size: 14px;
            font-weight: 500;
            color: var(--ui-caption-text);
        }}

        .ui-auth-brand-headline {{
            font-size: 32px;
            line-height: 1.2;
            font-weight: 700;
            color: var(--ui-heading-text);
            letter-spacing: -0.03em;
            max-width: 560px;
        }}

        .ui-auth-brand-copy {{
            font-size: 15px;
            line-height: 1.7;
            color: var(--ui-text-secondary);
            max-width: 560px;
        }}

        .ui-auth-card {{
            min-height: 100%;
            padding: 28px;
        }}

        .ui-auth-card .ui-section-title {{
            margin-bottom: 6px;
            font-size: 22px;
            font-weight: 700;
        }}

        .ui-auth-card .ui-section-caption {{
            font-size: 15px;
            line-height: 1.65;
        }}

        .ui-auth-feature-list {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .ui-auth-feature-item {{
            padding: 14px 16px;
            border: 1px solid var(--ui-border);
            border-radius: 12px;
            background: var(--ui-background);
        }}

        .ui-auth-feature-title {{
            margin-bottom: 4px;
            font-size: 15px;
            font-weight: 600;
            color: var(--ui-heading-text);
        }}

        .ui-auth-feature-copy {{
            font-size: 14px;
            line-height: 1.65;
            color: var(--ui-text-secondary);
        }}

        .ui-auth-inline-note {{
            margin: 2px 0 14px 0;
            font-size: 14px;
            line-height: 1.6;
            color: var(--ui-caption-text);
        }}

        .ui-auth-link {{
            color: var(--ui-accent);
            font-weight: 600;
        }}

        .ui-auth-security-note {{
            margin-top: 16px;
            padding: 12px 14px;
            border: 1px solid var(--ui-border);
            border-radius: 12px;
            background: var(--ui-info-background);
            font-size: 14px;
            line-height: 1.65;
            color: var(--ui-info-text);
            font-weight: 500;
        }}

        .ui-panel {{
            background: var(--ui-card);
        }}

        @media (max-width: 980px) {{
            .ui-auth-layout {{
                grid-template-columns: 1fr;
            }}

            .ui-auth-brand-panel {{
                padding: 24px;
            }}

            .ui-auth-brand-headline {{
                font-size: 28px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
