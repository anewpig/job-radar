from __future__ import annotations

import streamlit as st

from .base_theme_styles import BASE_THEME_STYLES
from .dev_annotation_styles import DEV_ANNOTATION_STYLES
from .navigation_styles import NAVIGATION_STYLES


def inject_global_styles() -> None:
    st.markdown(
        "<style>\n"
        + BASE_THEME_STYLES
        + "\n"
        + DEV_ANNOTATION_STYLES
        + "\n"
        + NAVIGATION_STYLES
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
    padding-bottom: 3rem;
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

.st-key-search-setup-shell,
[data-testid="stAppViewContainer"] > .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"]:first-of-type {
    position: relative;
    overflow: hidden;
    width: 100%;
    border-radius: 30px !important;
    border: 1px solid rgba(123, 97, 255, 0.12) !important;
    background:
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.18), transparent 22%),
        linear-gradient(135deg, #ffffff 0%, #f8f4ff 68%, #f3edff 100%) !important;
    box-shadow: var(--shadow-soft);
}

.st-key-search-setup-shell::before,
[data-testid="stAppViewContainer"] > .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"]:first-of-type::before {
    content: "";
    position: absolute;
    right: -36px;
    top: -36px;
    width: 180px;
    height: 180px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123, 97, 255, 0.16) 0%, rgba(123, 97, 255, 0.03) 68%, transparent 100%);
    pointer-events: none;
}

.st-key-search-setup-shell::after,
[data-testid="stAppViewContainer"] > .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"]:first-of-type::after {
    content: "";
    position: absolute;
    left: -48px;
    bottom: -52px;
    width: 170px;
    height: 170px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(255, 215, 126, 0.20) 0%, rgba(255, 215, 126, 0.03) 68%, transparent 100%);
    pointer-events: none;
}

details {
    border-radius: 20px;
    border: 1px solid var(--border) !important;
    background: var(--panel);
    box-shadow: var(--shadow-soft);
    padding: 0.28rem 0.42rem;
}

.top-header-fixed {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 1000;
    pointer-events: none;
}

.top-header-host {
    height: 0;
    line-height: 0;
    overflow: visible;
}

.top-header-shell {
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin: 0;
    width: 100%;
    min-height: 3.5rem;
    padding: 0.55rem 0.8rem;
    box-sizing: border-box;
    border-radius: 0;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: rgba(255,255,255,0.92);
    box-shadow: 0 14px 30px rgba(116, 86, 204, 0.10);
    backdrop-filter: blur(16px);
    pointer-events: auto;
}

.top-header-shell::after {
    content: "";
    position: absolute;
    top: -28px;
    right: -28px;
    width: 120px;
    height: 120px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123, 97, 255, 0.14) 0%, rgba(123, 97, 255, 0.02) 70%, transparent 100%);
    pointer-events: none;
}

.top-header-brand {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    min-width: 0;
}

.top-header-logo {
    width: 2.7rem;
    height: 2.7rem;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6f56f6 0%, #7b61ff 55%, #9672ff 100%);
    color: #ffffff;
    font-size: 0.95rem;
    font-weight: 900;
    box-shadow: 0 14px 24px rgba(123, 97, 255, 0.20);
    flex-shrink: 0;
}

.top-header-title {
    font-size: 1rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1.1;
}

.top-header-subtitle {
    margin-top: 0.12rem;
    color: #756f97;
    font-size: 0.8rem;
    line-height: 1.35;
}

.st-key-header-auth-trigger-button {
    position: fixed;
    top: 0;
    right: 1rem;
    left: auto;
    transform: none;
    width: auto;
    height: 0;
    margin: 0 !important;
    padding: 0 !important;
    z-index: 1001;
    pointer-events: none;
    overflow: visible;
}

.st-key-header-auth-trigger-button .stButton {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    min-height: 3.5rem;
    padding: 0 0.18rem 0 0;
}

.st-key-header-auth-trigger-button .stButton > button {
    min-height: auto;
    padding: 0.2rem 0.1rem;
    border: none;
    background: transparent;
    box-shadow: none;
    color: #756f97;
    border-radius: 0;
    font-size: 1rem;
    font-weight: 700;
    pointer-events: auto;
}

.st-key-header-auth-trigger-button .stButton > button:hover {
    color: #756f97;
    border: none;
    background: transparent;
    box-shadow: none;
}

[data-testid="stDialog"] [role="dialog"] {
    border-radius: 28px !important;
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    box-shadow: 0 24px 60px rgba(31, 27, 77, 0.18) !important;
}

.auth-dialog-shell {
    padding: 0.35rem 0 0.15rem;
    text-align: center;
}

.auth-dialog-brand {
    display: inline-flex;
    align-items: center;
    gap: 0.85rem;
    justify-content: center;
}

.auth-dialog-logo {
    width: 3rem;
    height: 3rem;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #44b36b 0%, #67c98a 100%);
    color: #ffffff;
    font-size: 1rem;
    font-weight: 900;
    box-shadow: 0 14px 24px rgba(71, 168, 110, 0.22);
}

.auth-dialog-title {
    font-size: 1.7rem;
    line-height: 1.1;
    font-weight: 800;
    color: var(--text);
}

.auth-dialog-subtitle {
    margin-top: 0.18rem;
    color: #6f6990;
    font-size: 0.92rem;
    line-height: 1.45;
}

[data-testid="stDialog"] [data-testid="stTabs"] {
    margin-top: 0.5rem;
}

[data-testid="stDialog"] .stTabs [role="tablist"] {
    gap: 0.35rem;
}

[data-testid="stDialog"] .stTabs [role="tab"] {
    border-radius: 999px;
    padding-inline: 1rem;
}

[data-testid="stDialog"] .stTabs [aria-selected="true"] {
    background: rgba(71, 168, 110, 0.10);
    color: #2f8d54;
}

.hero-shell {
    position: relative;
    overflow: hidden;
    width: 100%;
    box-sizing: border-box;
    margin-left: auto;
    margin-right: auto;
    margin-top: -3.4rem;
    margin-bottom: 1.5rem;
    padding: 1.6rem 1.5rem;
    border-radius: 30px;
    border: 1px solid rgba(123, 97, 255, 0.12);
    background:
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.18), transparent 22%),
        linear-gradient(135deg, #ffffff 0%, #f8f4ff 68%, #f3edff 100%);
    box-shadow: var(--shadow-soft);
}

.hero-shell::before {
    content: "";
    position: absolute;
    right: -36px;
    top: -36px;
    width: 180px;
    height: 180px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123, 97, 255, 0.16) 0%, rgba(123, 97, 255, 0.03) 68%, transparent 100%);
    pointer-events: none;
}

.hero-shell::after {
    content: "";
    position: absolute;
    left: -48px;
    bottom: -52px;
    width: 170px;
    height: 170px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(255, 215, 126, 0.20) 0%, rgba(255, 215, 126, 0.03) 68%, transparent 100%);
    pointer-events: none;
}

.hero-grid {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: minmax(0, 0.98fr) minmax(390px, 1.02fr);
    gap: 2.4rem;
    align-items: stretch;
}

.hero-copy {
    align-self: stretch;
    display: flex;
    flex-direction: column;
    margin-top: 0.1rem;
    max-width: 32rem;
    min-height: 100%;
    padding-left: 1.1rem;
}

.hero-kicker {
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-weight: 800;
    color: var(--accent);
}

.hero-title {
    margin: 0.3rem 0 0;
    font-size: 2.8rem;
    line-height: 1.08;
    font-weight: 800;
    color: #27234e;
}

.hero-subtitle {
    margin: 1.75rem 0 0;
    max-width: 30rem;
    font-size: 1.02rem;
    line-height: 1.65;
    color: #5f587e;
    font-weight: 700;
}

.hero-description {
    margin: 2.0rem 0 0;
    max-width: 31rem;
    font-size: 0.96rem;
    line-height: 1.82;
    color: #6f6990;
}

.hero-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-top: 1.1rem;
}

.hero-actions {
    display: flex;
    flex-direction: row;
    align-items: flex-end;
    gap: 1rem;
    margin-top: auto;
    margin-bottom: 0.85rem;
    padding-top: 1.75rem;
    flex-wrap: wrap;
}

.hero-action-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 9.6rem;
    min-height: 3.2rem;
    padding: 0 1.35rem;
    border-radius: 18px;
    background: linear-gradient(135deg, #6f56f6 0%, #7b61ff 55%, #9672ff 100%);
    box-shadow: 0 16px 28px rgba(123, 97, 255, 0.18);
    color: #ffffff !important;
    font-size: 1rem;
    font-weight: 800;
    text-decoration: none;
    transform: translateY(0.125rem);
}

.hero-shell a.hero-action-button,
.hero-shell a.hero-action-button:link,
.hero-shell a.hero-action-button:visited,
.hero-shell a.hero-action-button:hover,
.hero-shell a.hero-action-button:focus,
.hero-action-button--link,
.hero-action-button--link:link,
.hero-action-button--link:visited,
.hero-action-button--link:hover,
.hero-action-button--link:focus {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff;
    text-decoration: none;
}

.hero-action-note {
    color: #756f97;
    font-size: 0.92rem;
    line-height: 1.45;
    font-weight: 700;
    padding-bottom: 0.22rem;
}

.hero-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.42rem 0.76rem;
    border-radius: 999px;
    background: rgba(123, 97, 255, 0.08);
    border: 1px solid rgba(123, 97, 255, 0.10);
    color: #5d4cc4;
    font-size: 0.86rem;
    font-weight: 700;
}

.hero-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.85rem;
    margin-top: 1.25rem;
}

.hero-meta-card,
.hero-note-card,
.hero-stat-card {
    border-radius: 22px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: rgba(255, 255, 255, 0.92);
    box-shadow: var(--shadow-soft);
}

.hero-meta-card,
.hero-note-card {
    padding: 0.95rem 1rem;
    min-width: 13rem;
}

.hero-meta-label,
.hero-stat-label {
    font-size: 0.74rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 800;
    color: #8a84ab;
}

.hero-meta-value {
    margin-top: 0.34rem;
    font-size: 0.98rem;
    font-weight: 700;
    color: var(--text);
}

.hero-visual {
    position: relative;
    align-self: start;
}

.hero-mockup {
    position: relative;
    min-height: 21.8rem;
    border-radius: 30px;
    overflow: hidden;
    background:
        radial-gradient(circle at 18% 20%, rgba(255, 255, 255, 0.34), transparent 18%),
        radial-gradient(circle at 88% 12%, rgba(255, 255, 255, 0.24), transparent 18%),
        linear-gradient(135deg, #a987ff 0%, #8b6cff 40%, #7759ec 70%, #6949d8 100%);
    box-shadow: 0 24px 46px rgba(108, 79, 210, 0.22);
}

.hero-mockup::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 0% 68%, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0.08) 20%, transparent 22%),
        radial-gradient(circle at 18% 78%, rgba(255, 255, 255, 0.16) 0%, rgba(255, 255, 255, 0.04) 28%, transparent 30%),
        radial-gradient(circle at 82% 94%, rgba(255, 255, 255, 0.10) 0%, transparent 18%);
    pointer-events: none;
}

.hero-mockup::after {
    content: "";
    position: absolute;
    left: 36%;
    top: 10%;
    width: 10rem;
    height: 10rem;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.34) 0%, rgba(255, 255, 255, 0.08) 62%, transparent 66%);
    pointer-events: none;
}

.hero-mockup-orb {
    position: absolute;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.34) 0%, rgba(255, 255, 255, 0.10) 62%, transparent 68%);
    pointer-events: none;
}

.hero-mockup-orb--one {
    left: -2.8rem;
    bottom: 1rem;
    width: 12rem;
    height: 12rem;
}

.hero-mockup-orb--two {
    right: -2rem;
    top: 1.2rem;
    width: 8.5rem;
    height: 8.5rem;
}

.hero-mockup-radar-ring {
    position: absolute;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.16);
    pointer-events: none;
    z-index: 0;
}

.hero-mockup-radar-ring--one {
    right: -3.8rem;
    bottom: -5.4rem;
    width: 17rem;
    height: 17rem;
    opacity: 0.3;
}

.hero-mockup-radar-ring--two {
    right: 0.4rem;
    bottom: -2.2rem;
    width: 11.8rem;
    height: 11.8rem;
    opacity: 0.24;
}

.hero-mockup-badge {
    position: absolute;
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.96);
    box-shadow: 0 12px 26px rgba(65, 44, 153, 0.16);
    color: #352a77;
    font-weight: 700;
    z-index: 2;
}

.hero-mockup-badge--label {
    top: 1.45rem;
    left: 1.3rem;
    padding: 0.7rem 1rem;
    gap: 0.65rem;
    font-size: 0.88rem;
}

.hero-mockup-badge--label::before {
    content: "";
    width: 2.1rem;
    height: 2.1rem;
    border-radius: 999px;
    background: linear-gradient(135deg, #6f56f6 0%, #8d74ff 100%);
    box-shadow: inset 0 0 0 6px rgba(255, 255, 255, 0.18);
}

.hero-mockup-badge--stat {
    top: 1.2rem;
    right: 1.3rem;
    padding: 0.82rem 1rem;
    min-width: 7.8rem;
    justify-content: center;
    font-size: 0.82rem;
    letter-spacing: 0.04em;
}

.hero-mockup-card {
    position: absolute;
    border-radius: 26px;
    background: rgba(255, 255, 255, 0.97);
    border: 1px solid rgba(123, 97, 255, 0.08);
    box-shadow: 0 18px 34px rgba(56, 35, 145, 0.16);
    backdrop-filter: blur(12px);
}

.hero-mockup-card--main {
    top: 4rem;
    left: 4.5rem;
    right: 2rem;
    min-height: 13.4rem;
    padding: 1rem 1rem 0.95rem;
    z-index: 1;
}

.hero-mockup-card-head {
    display: flex;
    align-items: flex-start;
    gap: 0.85rem;
}

.hero-mockup-appmark {
    width: 3.2rem;
    height: 3.2rem;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6f56f6 0%, #8b6cff 100%);
    color: #ffffff;
    font-size: 1.02rem;
    font-weight: 900;
    box-shadow: 0 14px 24px rgba(123, 97, 255, 0.18);
    flex-shrink: 0;
}

.hero-mockup-kicker {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 800;
    color: #9f97c2;
}

.hero-mockup-title {
    margin-top: 0.28rem;
    font-size: 1rem;
    line-height: 1.55;
    font-weight: 800;
    color: #2d275f;
}

.hero-mockup-board-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.75rem;
}

.hero-mockup-board-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 2rem;
    padding: 0 0.72rem;
    border-radius: 999px;
    background: rgba(123, 97, 255, 0.10);
    color: #5e49cf;
    font-size: 0.76rem;
    font-weight: 800;
    white-space: nowrap;
}

.hero-mockup-job-list {
    display: flex;
    flex-direction: column;
    gap: 0.72rem;
    margin-top: 0.85rem;
}

.hero-mockup-job-card {
    border-radius: 22px;
    background: linear-gradient(180deg, rgba(247, 243, 255, 0.96) 0%, rgba(255, 255, 255, 0.96) 100%);
    border: 1px solid rgba(123, 97, 255, 0.08);
    padding: 0.76rem 0.82rem 0.78rem;
}

.hero-mockup-job-card--active {
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.99) 0%, rgba(242, 237, 255, 0.98) 100%);
    border-color: rgba(111, 86, 246, 0.22);
    box-shadow: 0 16px 28px rgba(111, 86, 246, 0.14);
}

.hero-mockup-job-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.7rem;
}

.hero-mockup-job-title {
    font-size: 0.92rem;
    line-height: 1.35;
    font-weight: 800;
    color: #2f285f;
}

.hero-mockup-job-card--active .hero-mockup-job-title {
    font-size: 1rem;
    color: #2a215e;
}

.hero-mockup-job-meta {
    margin-top: 0.2rem;
    font-size: 0.74rem;
    line-height: 1.4;
    color: #8b84af;
    font-weight: 700;
}

.hero-mockup-job-score {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 2rem;
    padding: 0 0.72rem;
    border-radius: 999px;
    background: rgba(123, 97, 255, 0.08);
    color: #5f4cc8;
    font-size: 0.78rem;
    font-weight: 800;
    white-space: nowrap;
}

.hero-mockup-job-score--active {
    background: linear-gradient(135deg, #6f56f6 0%, #8a6dff 100%);
    color: #ffffff;
    box-shadow: 0 10px 18px rgba(111, 86, 246, 0.18);
}

.hero-mockup-job-card .hero-mini-tags {
    margin-top: 0.5rem;
}

.hero-mockup-job-card .hero-mini-tag {
    background: rgba(123, 97, 255, 0.07);
    border: 1px solid rgba(123, 97, 255, 0.08);
    color: #6653d3;
}

.hero-mockup-job-card--active .hero-mini-tag {
    background: rgba(111, 86, 246, 0.10);
    border-color: rgba(111, 86, 246, 0.14);
    color: #5a45cc;
}

.hero-mockup-job-footer {
    margin-top: 0.52rem;
    color: #766f98;
    font-size: 0.78rem;
    line-height: 1.4;
    font-weight: 700;
}

.hero-mockup-card--overlay {
    left: 1.15rem;
    top: 8rem;
    width: 11.9rem;
    padding: 0.9rem 0.9rem;
    background: linear-gradient(180deg, rgba(255, 248, 235, 0.96) 0%, rgba(255, 255, 255, 0.98) 100%);
    z-index: 3;
}

.hero-mockup-card--assistant {
    right: 1.15rem;
    bottom: 1rem;
    width: 13.2rem;
    padding: 0.9rem 0.92rem;
    background: linear-gradient(180deg, rgba(246, 242, 255, 0.98) 0%, rgba(255, 255, 255, 0.98) 100%);
    z-index: 3;
}

.hero-mockup-copy {
    margin-top: 0.28rem;
    color: #676083;
    font-size: 0.84rem;
    line-height: 1.6;
    font-weight: 700;
}

.hero-mockup-progress-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.48rem;
    margin-top: 0.58rem;
}

.hero-mockup-progress-item {
    border-radius: 18px;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 240, 255, 0.98) 100%);
    border: 1px solid rgba(123, 97, 255, 0.08);
    padding: 0.58rem 0.42rem 0.56rem;
    text-align: center;
}

.hero-mockup-progress-item span {
    display: block;
    font-size: 0.66rem;
    line-height: 1.3;
    color: #938bb7;
    font-weight: 800;
}

.hero-mockup-progress-item strong {
    display: block;
    margin-top: 0.24rem;
    font-size: 1rem;
    line-height: 1;
    color: #32296f;
    font-weight: 900;
}

.hero-mini-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 0.42rem;
}

.hero-mini-tag {
    display: inline-flex;
    align-items: center;
    padding: 0.3rem 0.58rem;
    border-radius: 999px;
    background: rgba(123, 97, 255, 0.08);
    color: #6653d3;
    font-size: 0.79rem;
    font-weight: 700;
}

.hero-stat-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.7rem;
}

.hero-stat-card {
    padding: 0.78rem 0.8rem;
}

.hero-stat-value {
    margin-top: 0.34rem;
    font-size: 1.26rem;
    font-weight: 800;
    color: #3a2f7a;
}

.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
}

.ui-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.42rem 0.76rem;
    border-radius: 999px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: rgba(255, 255, 255, 0.95);
    font-size: 0.86rem;
    color: #534d73;
}

.ui-chip--accent {
    background: var(--accent-soft);
    color: #5947be;
}

.ui-chip--soft {
    background: #f7f3ff;
    color: #6a6197;
}

.ui-chip--warm {
    background: var(--warm-soft);
    color: #8a5e00;
}

.section-shell {
    margin: 0.15rem 0 1rem;
    text-align: center;
}

.section-kicker {
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    color: var(--accent);
}

.section-title {
    margin: 0.22rem 0 0;
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--text);
}

.section-desc {
    max-width: 46rem;
    margin: 0.42rem auto 0;
    color: var(--muted);
    line-height: 1.75;
}

.search-setup-intro {
    text-align: left;
    margin-top: 0 !important;
    margin-bottom: var(--space-3) !important;
    padding-left: var(--space-4);
    padding-right: var(--space-4);
}

.search-setup-intro-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
}

.search-setup-intro-copy {
    min-width: 0;
}

.search-setup-intro-badge {
    display: inline-flex;
    align-items: center;
    min-height: 2rem;
    padding: 0 0.82rem;
    border-radius: 999px;
    border: 1px solid rgba(123, 97, 255, 0.12);
    background: rgba(123, 97, 255, 0.06);
    color: #5748bb;
    font-size: 0.76rem;
    font-weight: 800;
    white-space: nowrap;
}

.search-setup-intro .section-kicker {
    text-align: left;
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    opacity: 0.72;
}

.search-setup-intro .section-title {
    text-align: left;
    margin-top: 0;
    font-size: 1.44rem;
    line-height: 1.14;
}

.search-setup-intro .section-desc {
    max-width: 30rem;
    margin: 0.42rem 0 0;
    font-size: 0.94rem;
    line-height: 1.58;
    color: rgba(86, 81, 124, 0.9);
    text-align: left;
}

.st-key-search-setup-shell [data-testid="stHorizontalBlock"] {
    align-items: stretch;
}

.st-key-search-setup-shell [data-testid="column"] {
    display: flex;
}

.st-key-search-setup-shell [data-testid="column"] > div {
    width: 100%;
}

.st-key-search-setup-main {
    height: 100%;
    display: flex;
    flex-direction: column;
}

.st-key-search-setup-main [data-testid="stVerticalBlock"] {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.st-key-search-setup-cta {
    padding-top: 4.95rem;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.st-key-search-setup-cta [data-testid="stVerticalBlock"] {
    height: 100%;
}

.st-key-search-setup-body {
    padding-left: var(--space-4);
    padding-right: var(--space-4);
}

.st-key-search-setup-body [data-testid="stCaptionContainer"] {
    text-align: left;
}

[class*="st-key-search-fields-group-shell"],
[class*="st-key-search-controls-group-shell"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.995) 0%, rgba(248,245,255,0.97) 100%);
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    border-radius: 26px !important;
    box-shadow: 0 14px 30px rgba(116, 86, 204, 0.07);
}

[class*="st-key-search-fields-group-shell"] [data-testid="stVerticalBlock"],
[class*="st-key-search-controls-group-shell"] [data-testid="stVerticalBlock"] {
    gap: var(--space-4);
}

.search-card-head {
    display: block;
    padding: 0.08rem 0.12rem 0.12rem;
}

.search-card-head-copy {
    min-width: 0;
}

.search-card-title {
    margin-top: 0;
    font-size: 1.04rem;
    line-height: 1.28;
    font-weight: 800;
    color: #26214f;
}

.search-card-copy {
    margin-top: 0.28rem;
    max-width: 34rem;
    color: #6f688f;
    font-size: 0.88rem;
    line-height: 1.52;
}

.search-controls-group-offset {
    height: var(--space-4);
}

.search-row-header-label {
    padding: 0 0 0.15rem 0.18rem;
    font-size: 0.78rem;
    letter-spacing: 0.02em;
    font-weight: 800;
    color: #857ea9;
}

.search-row-header-label--action {
    text-align: center;
}

.st-key-search-role-rows-shell [data-testid="stVerticalBlock"] {
    gap: var(--space-2);
}

[class*="st-key-search-row-shell-"] {
    padding: 1rem 1rem 0.98rem;
    border-radius: 24px;
    border: 1px solid rgba(123, 97, 255, 0.14);
    background: linear-gradient(180deg, rgba(255,255,255,0.998) 0%, rgba(249,247,255,0.98) 100%);
    box-shadow: 0 14px 28px rgba(111, 86, 201, 0.08);
}

[class*="st-key-search-row-shell-"] [data-testid="stHorizontalBlock"] {
    align-items: flex-end;
}

.search-row-inline-label {
    display: none;
    margin: 0 0 0.34rem;
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    color: #857faf;
}

[class*="st-key-search-row-role-shell-"] [data-baseweb="base-input"],
[class*="st-key-search-row-keywords-shell-"] [data-baseweb="base-input"] {
    border-radius: 18px !important;
    border: 1px solid rgba(123, 97, 255, 0.14) !important;
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(251,249,255,0.97) 100%) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.82) !important;
}

[class*="st-key-search-row-role-shell-"] [data-baseweb="base-input"]:focus-within,
[class*="st-key-search-row-keywords-shell-"] [data-baseweb="base-input"]:focus-within {
    border-color: rgba(123, 97, 255, 0.24) !important;
    box-shadow: 0 0 0 4px rgba(123, 97, 255, 0.08), inset 0 1px 0 rgba(255,255,255,0.84) !important;
}

[class*="st-key-search-row-add-action-shell-"] {
    display: flex;
    align-items: flex-end;
}

[class*="st-key-search-row-add-action-shell-"] .stButton > button {
    min-height: 2.56rem;
    height: 2.56rem;
    padding-top: 0;
    padding-bottom: 0;
    border-radius: 16px !important;
    line-height: 1;
    border: 1px solid rgba(123, 97, 255, 0.16) !important;
    background: linear-gradient(180deg, rgba(123, 97, 255, 0.12) 0%, rgba(123, 97, 255, 0.07) 100%) !important;
    color: #3f338b !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.72), 0 8px 16px rgba(123, 97, 255, 0.08) !important;
    font-weight: 800 !important;
}

[class*="st-key-search-row-add-action-shell-"] .stButton > button:hover {
    border-color: rgba(123, 97, 255, 0.22) !important;
    background: linear-gradient(180deg, rgba(123, 97, 255, 0.14) 0%, rgba(123, 97, 255, 0.08) 100%) !important;
    color: #34297d !important;
}

[class*="st-key-search-row-add-action-shell-"] [data-testid="stVerticalBlock"] {
    row-gap: 0 !important;
    gap: 0 !important;
}

[class*="st-key-search-row-add-action-shell-"] [data-testid="stElementContainer"] {
    margin: 0 !important;
}

[class*="st-key-search-row-add-action-shell-"] .stButton {
    margin: 0 !important;
}

.search-row-action-spacer {
    height: var(--search-row-action-offset);
}

.st-key-search-role-tags-shell {
    margin-top: var(--space-4) !important;
}

.st-key-search-role-tags-shell [data-testid="stVerticalBlock"] {
    gap: var(--space-2);
}

[class*="st-key-search-role-tag-shell-"] {
    padding: 0;
}

[class*="st-key-search-role-tag-shell-"] [data-testid="stHorizontalBlock"] {
    align-items: flex-start;
}

.search-role-badge-cluster {
    display: flex;
    flex-wrap: wrap;
    gap: 0.46rem;
    padding: 0.14rem 0.08rem 0.14rem 0;
}

.search-role-badge-cluster .ui-chip {
    padding: 0.32rem 0.62rem;
    font-size: 0.78rem;
    border-color: rgba(123, 97, 255, 0.08);
    background: rgba(255,255,255,0.92);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.72);
}

.search-role-badge-cluster .ui-chip--accent {
    background: rgba(123, 97, 255, 0.12);
    color: #4f40b3;
}

.search-role-badge-cluster .ui-chip--soft {
    background: rgba(247, 243, 255, 0.96);
    color: #655d91;
}

[class*="st-key-search-role-tag-edit-shell-"] .stButton > button,
[class*="st-key-search-role-tag-remove-shell-"] .stButton > button {
    min-height: 2.26rem;
    border-radius: 14px !important;
    box-shadow: none !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
}

[class*="st-key-search-role-tag-edit-shell-"] .stButton > button {
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    background: rgba(123, 97, 255, 0.04) !important;
    color: #5547b8 !important;
}

[class*="st-key-search-role-tag-remove-shell-"] .stButton > button {
    border: 1px solid rgba(123, 97, 255, 0.08) !important;
    background: rgba(123, 97, 255, 0.02) !important;
    color: #757091 !important;
}

.search-role-autofill-note {
    margin-top: var(--space-2);
    padding: 0.68rem 0.82rem;
    border-radius: 16px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: rgba(248, 245, 255, 0.84);
    color: #6b648d;
    font-size: 0.82rem;
    line-height: 1.55;
    font-weight: 700;
}

.st-key-search-controls-options-shell [data-testid="stHorizontalBlock"] {
    align-items: flex-start;
}

.st-key-crawl-preset-control-shell,
.st-key-crawl-refresh-control-shell {
    position: relative;
}

.st-key-crawl-preset-control-shell [data-testid="stWidgetLabel"],
.st-key-crawl-refresh-control-shell [data-testid="stWidgetLabel"] {
    margin-bottom: 0.36rem;
}

.st-key-crawl-preset-control-shell [data-testid="stWidgetLabel"] p,
.st-key-crawl-refresh-control-shell [data-testid="stWidgetLabel"] p {
    font-size: 0.8rem;
    font-weight: 800;
    color: #7e78a4;
    letter-spacing: 0.02em;
}

.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"] [role="radiogroup"],
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"] [role="radiogroup"] {
    min-height: var(--control-height) !important;
    width: 100%;
    display: grid !important;
    align-items: stretch !important;
    gap: 0.24rem !important;
    padding: 0.2rem !important;
    border-radius: 20px !important;
    border: 1px solid rgba(123, 97, 255, 0.14) !important;
    background: linear-gradient(180deg, rgba(255,255,255,0.985) 0%, rgba(252,250,255,0.96) 100%) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.82), 0 10px 22px rgba(123, 97, 255, 0.05) !important;
}

.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"] button,
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"] button {
    min-height: calc(var(--control-height) - 0.36rem) !important;
    height: calc(var(--control-height) - 0.36rem) !important;
    padding: 0 0.88rem !important;
    border-radius: 16px !important;
    border: none !important;
    background: transparent !important;
    color: var(--control-text) !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    letter-spacing: 0.01em;
    white-space: nowrap !important;
    box-shadow: none !important;
}

.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"] button:hover,
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"] button:hover {
    background: rgba(123, 97, 255, 0.06) !important;
}

.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"] [aria-checked="true"],
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"] [aria-checked="true"],
.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"] button[kind="primary"],
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"] button[kind="primary"] {
    background: linear-gradient(180deg, rgba(123, 97, 255, 0.17) 0%, rgba(123, 97, 255, 0.09) 100%) !important;
    color: #312c63 !important;
    box-shadow: inset 0 0 0 1px rgba(123, 97, 255, 0.14) !important;
}

.search-controls-helper-note {
    margin-top: var(--space-3);
    color: #746d97;
    font-size: 0.84rem;
    line-height: 1.55;
    font-weight: 700;
}

.st-key-search-setup-run-shell {
    margin-top: var(--space-3);
}

.st-key-search-setup-run-shell .stButton > button {
    min-height: 3.12rem;
    border-radius: 20px !important;
    font-size: 0.96rem;
    font-weight: 800;
    box-shadow: 0 14px 24px rgba(123, 97, 255, 0.16) !important;
    width: 100%;
}

[class*="st-key-search-row-role-shell-"] input::placeholder,
[class*="st-key-search-row-role-shell-"] textarea::placeholder,
[class*="st-key-search-row-keywords-shell-"] input::placeholder,
[class*="st-key-search-row-keywords-shell-"] textarea::placeholder {
    color: rgba(114, 108, 150, 0.52) !important;
    opacity: 1 !important;
}

[class*="st-key-search-row-role-shell-"] input::-webkit-input-placeholder,
[class*="st-key-search-row-role-shell-"] textarea::-webkit-input-placeholder,
[class*="st-key-search-row-keywords-shell-"] input::-webkit-input-placeholder,
[class*="st-key-search-row-keywords-shell-"] textarea::-webkit-input-placeholder {
    color: rgba(114, 108, 150, 0.52) !important;
    opacity: 1 !important;
}

.surface-card,
.info-card,
.summary-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(248,245,255,0.96) 100%);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 1rem 1.05rem;
    box-shadow: var(--shadow-soft);
}

.surface-card {
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.surface-card:hover {
    transform: translateY(-2px);
    border-color: rgba(123, 97, 255, 0.20);
    box-shadow: 0 14px 30px rgba(116, 86, 204, 0.12);
}

.summary-card {
    margin-bottom: 1rem;
}

.cta-shell {
    position: relative;
    overflow: hidden;
    margin: 0;
    padding: 1.16rem 1.08rem 1.06rem;
    width: 100%;
    max-width: none;
    border-radius: 26px;
    border: 1px solid rgba(123, 97, 255, 0.08);
    background: linear-gradient(180deg, rgba(255,255,255,0.995) 0%, rgba(246,244,252,0.97) 100%);
    box-shadow: 0 12px 22px rgba(116, 86, 204, 0.06);
}

.cta-shell--search-summary {
    min-height: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}

.cta-shell::after {
    content: "";
    position: absolute;
    right: -66px;
    bottom: -60px;
    width: 156px;
    height: 156px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123,97,255,0.06) 0%, rgba(123,97,255,0.018) 72%, transparent 100%);
    pointer-events: none;
}

.cta-summary-head {
    display: flex;
    flex-direction: column;
}

.cta-summary-meta-wrap {
    margin-top: 0.88rem;
}

.cta-title {
    margin-top: 0;
    font-size: 1.14rem;
    line-height: 1.2;
    font-weight: 800;
    color: #1f1b4d;
    max-width: none;
}

.cta-copy {
    max-width: none;
    margin-top: 0.36rem;
    color: #6f698e;
    line-height: 1.56;
    font-size: 0.86rem;
}

.cta-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0;
}

.cta-meta-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    min-height: 1.96rem;
    padding: 0 0.7rem;
    border-radius: 999px;
    background: rgba(123, 97, 255, 0.038);
    border: 1px solid rgba(123, 97, 255, 0.07);
    color: #594dbf;
    font-size: 0.76rem;
    font-weight: 800;
}

.cta-meta-label {
    color: #857ea8;
    font-weight: 700;
}

.cta-meta-pill strong {
    color: #3a2f7a;
    font-weight: 800;
}

.cta-stat-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.72rem;
    margin-top: auto;
    padding-top: 0.96rem;
}

.cta-stat-card {
    padding: 0.84rem 0.88rem;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(123, 97, 255, 0.07);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.74);
}

.cta-stat-card--wide {
    grid-column: 1 / -1;
}

.cta-stat-label {
    font-size: 0.76rem;
    letter-spacing: 0.01em;
    font-weight: 800;
    color: #8a84ab;
}

.cta-stat-value {
    margin-top: 0.32rem;
    font-size: 1.18rem;
    font-weight: 800;
    color: #2a235d;
}

.info-card-title,
.job-card-block-title,
.board-card-section-title {
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #8a84ab;
}

.summary-card-text {
    margin-top: 0.55rem;
    color: #5c567e;
    line-height: 1.8;
}

.job-card-title {
    margin: 0;
    font-size: 1.12rem;
    font-weight: 800;
    color: var(--text);
}

.job-card-company {
    margin-top: 0.24rem;
    color: #6f6990;
    font-weight: 600;
}

.job-card-block {
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(244,240,255,0.92) 100%);
    border: 1px solid rgba(123, 97, 255, 0.09);
    border-radius: 18px;
    padding: 0.85rem 0.9rem;
}

.job-card-list {
    margin: 0.55rem 0 0;
    padding-left: 1rem;
    color: #334155;
}

.job-card-list li {
    margin: 0.3rem 0;
    line-height: 1.55;
}

.board-card-shell {
    position: relative;
    overflow: hidden;
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(247,242,255,0.96) 100%);
    border: 1px solid rgba(123, 97, 255, 0.10);
    border-radius: 24px;
    padding: 1rem 1rem;
    min-height: 22rem;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
    box-shadow: var(--shadow-soft);
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.board-card-shell::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, #ffbe3d 0%, #7b61ff 55%, #9672ff 100%);
}

.board-card-shell:hover {
    transform: translateY(-2px);
    border-color: rgba(123, 97, 255, 0.18);
    box-shadow: 0 16px 30px rgba(116, 86, 204, 0.12);
}

.board-card-icon {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(255, 190, 61, 0.24) 0%, rgba(123, 97, 255, 0.16) 100%);
    color: #6e55e2;
    font-size: 1rem;
    font-weight: 900;
}

.board-card-title {
    margin: 0;
    font-size: 1.02rem;
    font-weight: 800;
    color: var(--text);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.board-card-company {
    color: #6f6990;
    font-weight: 600;
    margin-top: 0.15rem;
}

.board-card-meta,
.board-card-timeline {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
}

.board-card-section {
    background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(244,240,255,0.90) 100%);
    border: 1px solid rgba(123, 97, 255, 0.08);
    border-radius: 18px;
    padding: 0.75rem 0.82rem;
}

.board-card-copy {
    color: #5d587f;
    line-height: 1.6;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 4.8rem;
}

.board-card-footer {
    margin-top: auto;
}

.board-card-footer a,
.job-link a {
    color: #6850dc;
    font-weight: 700;
    text-decoration: none;
}

.newsletter-shell {
    position: relative;
    overflow: hidden;
    margin-top: 0.0rem;
    padding: 1.55rem 1.4rem 1.2rem;
    border-radius: 30px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(180deg, rgba(252,250,255,0.98) 0%, rgba(245,241,255,0.98) 100%);
    box-shadow: var(--shadow-soft);
    text-align: center;
}

.newsletter-shell::before {
    content: "";
    position: absolute;
    left: -42px;
    top: -32px;
    width: 160px;
    height: 160px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123, 97, 255, 0.10) 0%, rgba(123, 97, 255, 0.02) 72%, transparent 100%);
    pointer-events: none;
}

.newsletter-kicker {
    font-size: 0.76rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 800;
    color: #7b61ff;
}

.newsletter-title {
    margin-top: 0.35rem;
    font-size: 1.7rem;
    line-height: 1.2;
    font-weight: 800;
    color: var(--text);
}

.newsletter-copy {
    max-width: 46rem;
    margin: 0.6rem auto 0;
    color: #6f6990;
    line-height: 1.8;
}

.newsletter-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    justify-content: center;
    margin-top: 1rem;
}

.newsletter-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.48rem 0.8rem;
    border-radius: 999px;
    background: rgba(123, 97, 255, 0.08);
    border: 1px solid rgba(123, 97, 255, 0.10);
    color: #614ed0;
    font-size: 0.85rem;
    font-weight: 700;
}

.newsletter-footer-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 0.9rem 1rem;
    margin-top: 1.1rem;
    color: #8f88b0;
    font-size: 0.84rem;
}

.newsletter-footer-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.9rem 1rem;
    align-items: center;
    justify-content: center;
}

.newsletter-footer-visit {
    white-space: nowrap;
    font-weight: 700;
}

@media (max-width: 960px) {
    .hero-grid {
        grid-template-columns: 1fr;
        align-items: start;
    }

    .hero-copy {
        align-self: start;
        display: block;
        min-height: auto;
    }

    .hero-shell {
        margin-top: -2.8rem;
    }

    .hero-mockup {
        min-height: 20.2rem;
    }

    .hero-mockup-card--main {
        left: 4rem;
        right: 1rem;
        top: 3.8rem;
        min-height: 12rem;
        padding: 0.88rem;
    }

    .hero-mockup-card--overlay {
        left: 0.85rem;
        top: 8.6rem;
        width: 10.1rem;
    }

    .hero-mockup-card--assistant {
        right: 0.85rem;
        width: 11.1rem;
        bottom: 0.75rem;
    }

    .hero-mockup-badge--label,
    .hero-mockup-badge--stat {
        transform: scale(0.94);
        transform-origin: top left;
    }

    .hero-mockup-board-pill {
        min-height: 1.8rem;
        padding: 0 0.58rem;
        font-size: 0.7rem;
    }

    .hero-mockup-job-title {
        font-size: 0.82rem;
    }

    .hero-mockup-job-card--active .hero-mockup-job-title {
        font-size: 0.88rem;
    }

    .hero-mockup-job-meta,
    .hero-mockup-job-footer {
        font-size: 0.7rem;
    }

    .hero-mockup-job-score {
        min-height: 1.76rem;
        padding: 0 0.56rem;
        font-size: 0.7rem;
    }

    .hero-mockup-progress-grid {
        gap: 0.34rem;
    }

    .hero-mockup-progress-item {
        padding: 0.5rem 0.3rem;
    }

    .hero-title {
        font-size: 2.2rem;
    }

    .hero-subtitle {
        font-size: 1.02rem;
    }

    .hero-description {
        font-size: 0.94rem;
        line-height: 1.75;
    }

    .hero-actions {
        margin-top: 1.75rem;
        padding-top: 0;
    }

    .search-setup-intro {
        padding-left: 0;
        padding-right: 0;
    }

    .search-setup-intro-row,
    .search-card-head {
        flex-direction: column;
        align-items: flex-start;
    }

    .search-setup-intro-badge,
    .search-card-step {
        min-height: 1.9rem;
    }

    .st-key-search-setup-body {
        padding-left: var(--space-3);
        padding-right: var(--space-3);
    }

    .st-key-search-setup-cta {
        padding-top: var(--space-4);
        height: auto;
    }

    .st-key-search-setup-cta [data-testid="stVerticalBlock"] {
        height: auto;
    }

    .cta-shell--search-summary {
        min-height: 0;
    }

    .st-key-search-row-headers-shell {
        display: none;
    }

    [class*="st-key-search-row-shell-"] {
        padding: 0.82rem 0.84rem;
    }

    [class*="st-key-search-row-shell-"] [data-testid="stHorizontalBlock"] {
        flex-direction: column;
        align-items: stretch;
        gap: var(--space-2) !important;
    }

    [class*="st-key-search-row-shell-"] [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }

    .search-row-inline-label {
        display: block;
    }

    [class*="st-key-search-row-add-action-shell-"] .stButton > button {
        width: 100%;
    }

    [class*="st-key-search-role-tag-shell-"] [data-testid="stHorizontalBlock"] {
        flex-direction: column;
        align-items: stretch;
        gap: var(--space-2) !important;
    }

    [class*="st-key-search-role-tag-shell-"] [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }

    [class*="st-key-search-role-tag-edit-shell-"] .stButton > button,
    [class*="st-key-search-role-tag-remove-shell-"] .stButton > button {
        width: 100%;
        min-height: 2.55rem;
    }

    .st-key-search-setup-run-shell {
        margin-top: var(--space-2);
    }

    .search-role-tags-empty {
        padding: 0.84rem 0.9rem;
    }

    .cta-copy {
        max-width: none;
    }

    .cta-shell {
        width: 100%;
        max-width: none;
    }

    [data-testid="stAppViewContainer"] > .main .block-container {
        padding-top: 0.0rem;
    }

    .section-title {
        font-size: 1.35rem;
    }

    .board-card-shell {
        min-height: auto;
    }

    .newsletter-footer-row {
        justify-content: center;
    }

    .top-header-shell {
        width: 100%;
        min-height: 4.2rem;
        padding-right: 4.8rem;
    }

    .top-header-subtitle {
        font-size: 0.74rem;
        line-height: 1.3;
    }

    .st-key-header-auth-trigger-button {
        right: 0.2rem;
        width: auto;
    }

    .st-key-header-auth-trigger-button .stButton {
        min-height: 4.2rem;
        padding: 0 0.18rem 0 0;
    }

    .st-key-header-auth-trigger-button .stButton > button {
        font-size: 0.94rem;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )
