"""Theme styling engine and CSS design tokens for Syntecxhub Sales Analysis Dashboard.
Implements dual-theming (Dark/Light mode) with exact hex palettes and Electric Blue accents.
"""
from __future__ import annotations

DARK_MODE = {
    "bg": "#0F172A",
    "card_bg": "#1E293B",
    "card_border": "#334155",
    "card_border_active": "#3B82F6",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "accent": "#3B82F6",
    "accent_hover": "#60A5FA",
    "accent_subtle": "rgba(59, 130, 246, 0.12)",
    "positive_trend": "#10B981",
    "negative_trend": "#EF4444",
    "chart_bg": "rgba(30, 41, 59, 0.7)",
    "chart_paper": "#1E293B",
    "grid_color": "#334155",
}

LIGHT_MODE = {
    "bg": "#F8FAFC",
    "card_bg": "#FFFFFF",
    "card_border": "#E2E8F0",
    "card_border_active": "#0052FF",
    "text_primary": "#0F172A",
    "text_secondary": "#64748B",
    "accent": "#0052FF",
    "accent_hover": "#2563EB",
    "accent_subtle": "rgba(0, 82, 255, 0.08)",
    "positive_trend": "#059669",
    "negative_trend": "#DC2626",
    "chart_bg": "#FFFFFF",
    "chart_paper": "#FFFFFF",
    "grid_color": "#F1F5F9",
}


def get_theme_colors(is_dark: bool) -> dict[str, str]:
    """Retrieve theme tokens based on theme state."""
    return DARK_MODE if is_dark else LIGHT_MODE


def get_custom_css(is_dark: bool) -> str:
    """Generate high-fidelity CSS matching exact theme specifications and corporate card grid layout."""
    t = get_theme_colors(is_dark)

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {t['bg']} !important;
        color: {t['text_primary']} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    header, [data-testid="stHeader"] {{
        background-color: {t['bg']} !important;
    }}

    /* Global Typography */
    h1, h2, h3, h4, p, span, div {{
        color: {t['text_primary']};
    }}

    /* Header Brand Bar */
    .brand-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.2rem 1.5rem;
        background-color: {t['card_bg']};
        border-radius: 12px;
        border: 1px solid {t['card_border']};
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    }}

    .brand-title {{
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: {t['text_primary']};
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }}

    .brand-badge {{
        background-color: {t['accent']};
        color: #FFFFFF;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }}

    /* Top Row KPI Cards */
    .kpi-card {{
        background-color: {t['card_bg']};
        border: 1px solid {t['card_border']};
        border-radius: 12px;
        padding: 1.35rem 1.25rem;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        position: relative;
        overflow: hidden;
    }}

    .kpi-card:hover {{
        border-color: {t['accent']};
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 82, 255, 0.12);
    }}

    .kpi-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, {t['accent']}, transparent);
        opacity: 0.85;
    }}

    .kpi-label {{
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: {t['text_secondary']};
        margin-bottom: 0.5rem;
    }}

    .kpi-value {{
        font-size: 1.85rem;
        font-weight: 800;
        color: {t['text_primary']};
        letter-spacing: -0.03em;
        line-height: 1.1;
        margin-bottom: 0.4rem;
        font-family: 'Inter', sans-serif;
    }}

    .kpi-trend {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.5rem;
        border-radius: 6px;
    }}

    .trend-up {{
        color: {t['positive_trend']};
        background-color: rgba(16, 185, 129, 0.12);
    }}

    .trend-neutral {{
        color: {t['accent']};
        background-color: {t['accent_subtle']};
    }}

    /* Card Containers for Charts & AI */
    .dashboard-panel {{
        background-color: {t['card_bg']};
        border: 1px solid {t['card_border']};
        border-radius: 12px;
        padding: 1.25rem 1.4rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        margin-bottom: 1.25rem;
    }}

    .dashboard-panel:hover {{
        border-color: {t['card_border_active']};
    }}

    .panel-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.65rem;
        border-bottom: 1px solid {t['card_border']};
    }}

    .panel-title {{
        font-size: 0.95rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        color: {t['text_primary']};
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    /* AI Summary Text Container */
    .ai-summary-box {{
        background-color: {t['accent_subtle']};
        border-left: 4px solid {t['accent']};
        border-radius: 0 10px 10px 0;
        padding: 1.15rem 1.35rem;
        margin: 0.75rem 0;
    }}

    .ai-bullet {{
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        margin-bottom: 0.55rem;
        font-size: 0.88rem;
        line-height: 1.5;
        color: {t['text_primary']};
    }}

    .ai-bullet-icon {{
        color: {t['accent']};
        font-weight: 800;
        line-height: 1.2;
    }}

    /* Primary CTA Button Overrides */
    div.stButton > button:first-child {{
        background-color: {t['accent']} !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.3rem !important;
        font-size: 0.88rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(0, 82, 255, 0.25) !important;
    }}

    div.stButton > button:first-child:hover {{
        background-color: {t['accent_hover']} !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 18px rgba(0, 82, 255, 0.35) !important;
    }}

    div.stDownloadButton > button:first-child {{
        background-color: {t['accent']} !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.3rem !important;
        font-size: 0.88rem !important;
        box-shadow: 0 4px 12px rgba(0, 82, 255, 0.25) !important;
    }}

    div.stDownloadButton > button:first-child:hover {{
        background-color: {t['accent_hover']} !important;
        transform: translateY(-1px) !important;
    }}

    /* Streamlit widgets adjustment */
    [data-testid="stSidebar"] {{
        background-color: {t['card_bg']} !important;
        border-right: 1px solid {t['card_border']} !important;
    }}

    .stSelectbox, .stTextInput, .stFileUploader {{
        color: {t['text_primary']} !important;
    }}
    </style>
    """
    return css
