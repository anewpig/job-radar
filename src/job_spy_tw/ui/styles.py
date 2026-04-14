from __future__ import annotations

import streamlit as st

from .base_theme_styles import BASE_THEME_STYLES
from .dev_annotation_styles import DEV_ANNOTATION_STYLES
from .header_auth_styles import HEADER_AUTH_STYLES
from .hero_styles import HERO_STYLES
from .navigation_styles import NAVIGATION_STYLES
from .overview_styles import OVERVIEW_STYLES
from .search_setup_styles import SEARCH_SETUP_STYLES
from .surface_styles import SURFACE_STYLES

try:
    from .assistant_launcher_styles import ASSISTANT_LAUNCHER_STYLES
except ModuleNotFoundError:
    ASSISTANT_LAUNCHER_STYLES = """
.st-key-assistant-launcher-trigger-shell {
    position: fixed !important;
    right: var(--floating-fab-right) !important;
    bottom: var(--floating-fab-bottom) !important;
    z-index: 1002;
    width: var(--floating-fab-size) !important;
    min-width: var(--floating-fab-size) !important;
    max-width: var(--floating-fab-size) !important;
    margin: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}

.st-key-assistant-launcher-trigger-button-shell,
.st-key-assistant-launcher-trigger-button-shell [data-testid="stElementContainer"],
.st-key-assistant-launcher-trigger-button-shell [data-testid="stVerticalBlock"],
.st-key-assistant-launcher-trigger-button-shell .stButton {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.st-key-assistant-launcher-trigger-button-shell .stButton > button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: var(--floating-fab-size) !important;
    min-width: var(--floating-fab-size) !important;
    max-width: var(--floating-fab-size) !important;
    height: var(--floating-fab-size) !important;
    min-height: var(--floating-fab-size) !important;
    padding: 0 !important;
    border-radius: var(--floating-fab-radius) !important;
    border: var(--floating-fab-border) !important;
    background: var(--floating-fab-bg) !important;
    color: var(--floating-fab-text) !important;
    box-shadow: var(--floating-fab-shadow) !important;
    backdrop-filter: blur(18px) !important;
    aspect-ratio: 1 / 1;
    font-size: 1rem !important;
    font-weight: 800 !important;
    letter-spacing: 0 !important;
    line-height: 1;
    text-align: center;
    position: relative;
    z-index: 1;
    transition:
        background 160ms ease,
        color 160ms ease,
        box-shadow 160ms ease,
        transform 160ms ease;
}

.st-key-assistant-launcher-trigger-button-shell .stButton > button:hover,
.st-key-assistant-launcher-trigger-button-shell .stButton > button:focus {
    border: var(--floating-fab-border) !important;
    background: var(--floating-fab-hover-bg) !important;
    color: var(--floating-fab-text-hover) !important;
    box-shadow: var(--floating-fab-shadow) !important;
}

.st-key-assistant-launcher-card-shell {
    position: fixed !important;
    right: var(--floating-fab-right) !important;
    bottom: calc(var(--floating-fab-bottom) + var(--floating-fab-size) + var(--launcher-shell-gap)) !important;
    z-index: 1001;
    width: var(--launcher-shell-width) !important;
    max-width: var(--launcher-shell-width) !important;
    margin: 0 !important;
    padding: 0 !important;
    background: #ffffff !important;
    border-radius: 2rem !important;
}

.st-key-assistant-launcher-mobile-shell [data-testid="stVerticalBlockBorderWrapper"] {
    height: var(--launcher-shell-height) !important;
    border-radius: 2rem !important;
    border: 1px solid rgba(123, 97, 255, 0.12) !important;
    background: #ffffff !important;
    box-shadow: 0 26px 52px rgba(31, 27, 77, 0.18) !important;
    overflow: hidden !important;
}

.st-key-assistant-launcher-mobile-shell [data-testid="stVerticalBlockBorderWrapper"] > div {
    height: 100% !important;
    padding: 0 !important;
}

.st-key-assistant-launcher-mobile-shell [data-testid="stVerticalBlock"] {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 0 !important;
}

.st-key-assistant-launcher-mobile-body {
    flex: 1 1 auto;
    min-height: 0 !important;
}

.st-key-assistant-launcher-mobile-body [data-testid="stVerticalBlock"] {
    height: 100% !important;
    min-height: 0 !important;
    overflow-y: auto !important;
}

.st-key-assistant-launcher-mobile-tabbar {
    flex: 0 0 auto;
}

[class*="st-key-assistant-launcher-tab-"] .stButton > button {
    min-height: 3.25rem !important;
    height: 3.25rem !important;
    border-radius: 1rem !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    gap: 0.18rem !important;
}
    """


def inject_global_styles() -> None:
    st.markdown(
        "<style>\n"
        + BASE_THEME_STYLES
        + "\n"
        + DEV_ANNOTATION_STYLES
        + "\n"
        + HEADER_AUTH_STYLES
        + "\n"
        + NAVIGATION_STYLES
        + "\n"
        + ASSISTANT_LAUNCHER_STYLES
        + "\n"
        + OVERVIEW_STYLES
        + "\n"
        + SURFACE_STYLES
        + "\n"
        + HERO_STYLES
        + "\n"
        + SEARCH_SETUP_STYLES
        + "\n"
        + """
:root {
    --bg-start: #faf7ff;
    --bg-end: #f3efff;
    --page-shell-max: 1240px;
    --page-shell-gutter: 1rem;
    --shared-surface-width: min(1240px, calc(100vw - 2rem));
    --header-shell-max: calc(var(--page-shell-max) + (var(--page-shell-gutter) * 2));
    --panel: rgba(255, 255, 255, 0.96);
    --panel-soft: rgba(248, 245, 255, 0.96);
    --border: rgba(104, 80, 188, 0.12);
    --text: #1f1b4d;
    --muted: #726c96;
    --accent: #7b61ff;
    --accent-soft: #f0ebff;
    --warm-soft: #fff6db;
    --shadow-soft: 0 10px 28px rgba(116, 86, 204, 0.08);
    --search-row-action-offset: 0.0rem;
    --search-row-action-height: 2.25rem;
    --search-row-action-radius: 16px;
    --search-row-action-gap: 0.00rem;
    --floating-fab-size: 2.9rem;
    --floating-fab-radius: 0.9rem;
    --floating-fab-right: calc(env(safe-area-inset-right, 0px) + 1.15rem);
    --floating-fab-bottom: calc(env(safe-area-inset-bottom, 0px) + 1.15rem);
    --floating-fab-gap: 1rem;
    --floating-fab-border: 1px solid rgba(123, 97, 255, 0.10);
    --launcher-shell-width: min(25.75rem, calc(100vw - 1rem));
    --launcher-shell-height: min(21.5rem, calc(100vh - 7.5rem));
    --launcher-shell-gap: 1rem;
    --launcher-shell-stack-height: calc(var(--launcher-shell-height) + var(--launcher-shell-gap));
    --floating-fab-stack-base-bottom: var(--floating-fab-bottom);
    --assistant-launcher-active-offset: 0px;
    --floating-fab-bg:
        linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,245,255,0.94) 100%),
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.10), transparent 28%);
    --floating-fab-hover-bg:
        linear-gradient(180deg, rgba(250,248,255,0.98) 0%, rgba(243,238,255,0.95) 100%),
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.12), transparent 28%);
    --floating-fab-active-bg: linear-gradient(180deg, rgba(123, 97, 255, 0.16) 0%, rgba(123, 97, 255, 0.09) 100%);
    --floating-fab-shadow: 0 10px 20px rgba(96, 74, 180, 0.06);
    --floating-fab-active-shadow:
        inset 0 0 0 1px rgba(123, 97, 255, 0.14),
        0 8px 16px rgba(123, 97, 255, 0.10);
    --floating-fab-text: #59538a;
    --floating-fab-text-hover: #40367d;
    --floating-fab-text-active: #2f285f;
}

.stApp {
    background:
        radial-gradient(circle at 8% 6%, rgba(255, 215, 126, 0.20), transparent 18%),
        radial-gradient(circle at 92% 18%, rgba(123, 97, 255, 0.10), transparent 22%),
        linear-gradient(180deg, var(--bg-start) 0%, var(--bg-end) 100%);
    color: var(--text);
}

[data-testid="stAppViewContainer"] > .main .block-container {
    max-width: var(--page-shell-max);
    padding-top: 0.0rem;
    padding-bottom: calc(3rem + var(--floating-fab-size) + env(safe-area-inset-bottom, 0px) + 1rem);
}

[data-testid="stToolbar"],
[data-testid="stHeader"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"] {
    display: none !important;
}

h1, h2, h3, h4, h5, h6,
p, li, label, span, div {
    color: inherit;
}

[data-testid="metric-container"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(249,246,255,0.98) 100%);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 0.9rem 1rem;
    box-shadow: var(--shadow-soft);
}

[data-testid="metric-container"] label,
[data-testid="stMetricValue"] {
    color: var(--text) !important;
}

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    border-radius: 18px;
    border: 1px solid rgba(123, 97, 255, 0.16);
    min-height: 3rem;
    padding: 0.1rem 1rem;
    font-weight: 700;
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(247,242,255,0.96) 100%);
    color: #463a86;
    box-shadow: 0 10px 22px rgba(116, 86, 204, 0.08);
}

.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    border-color: rgba(123, 97, 255, 0.26);
}

[data-testid="stPopover"] > button {
    width: auto;
    min-width: fit-content;
    min-height: 3.15rem;
    padding: 0.08rem 0.82rem;
    border-radius: 14px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(180deg, rgba(244, 246, 243, 0.96) 0%, rgba(237, 241, 236, 0.96) 100%);
    color: #3f3968;
    box-shadow: none;
    font-weight: 700;
    justify-content: center;
}

[data-testid="stPopover"] > button:hover {
    border-color: rgba(123, 97, 255, 0.16);
    background: linear-gradient(180deg, rgba(240, 243, 240, 0.98) 0%, rgba(233, 238, 233, 0.98) 100%);
    color: #312a5f;
    box-shadow: none;
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    color: #ffffff;
    border: none;
    background: linear-gradient(135deg, #6f56f6 0%, #7b61ff 55%, #9672ff 100%);
    box-shadow: 0 16px 28px rgba(123, 97, 255, 0.20);
}

.stTextInput input,
.stTextArea textarea,
[data-baseweb="base-input"] input,
[data-baseweb="select"] > div,
[data-testid="stNumberInput"] input {
    border-radius: 16px !important;
    border: 1px solid rgba(123, 97, 255, 0.12) !important;
    background: rgba(255, 255, 255, 0.96) !important;
    color: var(--text) !important;
}

[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.25rem;
    box-shadow: var(--shadow-soft);
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,245,255,0.96) 100%);
    border: 1px solid var(--border) !important;
    border-radius: 26px !important;
    box-shadow: var(--shadow-soft);
}

details {
    border-radius: 20px;
    border: 1px solid var(--border) !important;
    background: var(--panel);
    box-shadow: var(--shadow-soft);
    padding: 0.28rem 0.42rem;
}

</style>
        """,
        unsafe_allow_html=True,
    )
