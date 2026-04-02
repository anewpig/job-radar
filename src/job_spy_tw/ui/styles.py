from __future__ import annotations

import streamlit as st


def inject_global_styles() -> None:
    st.markdown(
        """
<style>
:root {
    --bg-start: #eef3fb;
    --bg-end: #f8fafc;
    --panel: rgba(255, 255, 255, 0.96);
    --panel-strong: #ffffff;
    --border: rgba(15, 23, 42, 0.07);
    --border-strong: rgba(37, 99, 235, 0.18);
    --text: #0f172a;
    --muted: #64748b;
    --teal: #2563eb;
    --teal-soft: #e8f0ff;
    --sky-soft: #eef4ff;
    --amber-soft: #fff6e8;
    --shadow: 0 18px 36px rgba(15, 23, 42, 0.06);
    --shadow-soft: 0 8px 20px rgba(15, 23, 42, 0.04);
}

.stApp {
    font-family: "SF Pro Text", "PingFang TC", "Noto Sans TC", "Segoe UI", sans-serif;
    background:
        radial-gradient(circle at top left, rgba(37, 99, 235, 0.08), transparent 24%),
        linear-gradient(180deg, var(--bg-start) 0%, var(--bg-end) 100%);
    color: var(--text);
}

[data-testid="stAppViewContainer"] > .main .block-container {
    max-width: 1360px;
    padding-top: 0.6rem;
    padding-bottom: 3rem;
}

[data-testid="stToolbar"] {
    display: none !important;
}

[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
}

[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.86);
    border-right: 1px solid rgba(15, 23, 42, 0.05);
    backdrop-filter: blur(10px);
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption {
    color: #4b5563;
}

h1, h2, h3, h4 {
    letter-spacing: -0.02em;
}

[data-testid="metric-container"] {
    background: rgba(255,255,255,0.96);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.95rem 1rem;
    box-shadow: var(--shadow-soft);
}

[data-testid="metric-container"] label {
    color: var(--muted);
    font-weight: 700;
}

[data-testid="stMetricValue"] {
    color: var(--text);
}

button[role="tab"] {
    border-radius: 999px !important;
    border: 1px solid rgba(15, 23, 42, 0.09) !important;
    background: rgba(255, 255, 255, 0.88) !important;
    color: #475569 !important;
    padding: 0.55rem 1rem !important;
    font-weight: 700 !important;
}

button[role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
    color: #ffffff !important;
    border-color: transparent !important;
    box-shadow: 0 12px 24px rgba(37, 99, 235, 0.22);
}

.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    border-radius: 14px;
    border: 1px solid rgba(15, 23, 42, 0.09);
    min-height: 2.8rem;
    font-weight: 700;
    box-shadow: 0 6px 14px rgba(15, 23, 42, 0.04);
    background: rgba(255, 255, 255, 0.96);
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    color: #ffffff;
    border: none;
    background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
}

.stTextInput input,
.stTextArea textarea,
[data-baseweb="base-input"] input,
[data-baseweb="select"] > div,
[data-testid="stNumberInput"] input {
    border-radius: 14px !important;
    border: 1px solid rgba(15, 23, 42, 0.09) !important;
    background: rgba(255, 255, 255, 0.96) !important;
}

[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 0.35rem;
    box-shadow: var(--shadow);
}

[data-testid="stAlert"] {
    border-radius: 16px;
    border: 1px solid rgba(15, 23, 42, 0.08);
}

details {
    border-radius: 18px;
    border: 1px solid var(--border) !important;
    background: var(--panel-strong);
    box-shadow: var(--shadow-soft);
    padding: 0.2rem 0.35rem;
}

.hero-shell {
    position: relative;
    overflow: hidden;
    margin-bottom: 1.35rem;
    padding: 1.55rem 1.6rem;
    border-radius: 26px;
    border: 1px solid rgba(255,255,255,0.08);
    background:
        radial-gradient(circle at top right, rgba(96, 165, 250, 0.18), transparent 28%),
        linear-gradient(135deg, #0f172a 0%, #162447 100%);
    box-shadow: var(--shadow);
}

.hero-shell::after {
    content: "";
    position: absolute;
    right: -52px;
    top: -52px;
    width: 180px;
    height: 180px;
    border-radius: 999px;
    background: rgba(96, 165, 250, 0.16);
    filter: blur(8px);
}

.hero-kicker {
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-weight: 800;
    color: rgba(191, 219, 254, 0.95);
}

.hero-title {
    margin: 0.3rem 0 0;
    font-size: 2.25rem;
    line-height: 1.08;
    color: #ffffff !important;
}

.hero-subtitle {
    max-width: 58rem;
    margin: 0.85rem 0 0;
    font-size: 1rem;
    line-height: 1.7;
    color: rgba(226, 232, 240, 0.92);
}

.hero-pill-row,
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
}

.hero-pill-row {
    margin-top: 1rem;
}

.hero-pill,
.ui-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.36rem 0.68rem;
    border-radius: 999px;
    border: 1px solid rgba(15, 23, 42, 0.08);
    background: rgba(255, 255, 255, 0.92);
    font-size: 0.86rem;
    color: #334155;
}

.hero-pill {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.14);
    color: #e2e8f0;
}

.ui-chip--accent {
    background: var(--teal-soft);
    border-color: rgba(15, 118, 110, 0.14);
    color: #115e59;
}

.ui-chip--soft {
    background: var(--sky-soft);
    border-color: rgba(14, 165, 233, 0.12);
    color: #0f4c81;
}

.ui-chip--warm {
    background: var(--amber-soft);
    border-color: rgba(245, 158, 11, 0.14);
    color: #92400e;
}

.section-shell {
    margin: 0.18rem 0 0.9rem;
}

.section-kicker {
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    color: #2563eb;
}

.section-title {
    margin: 0.18rem 0 0;
    font-size: 1.16rem;
    font-weight: 800;
    color: var(--text);
}

.section-desc {
    margin: 0.32rem 0 0;
    color: #64748b;
    line-height: 1.65;
}

.surface-card {
    background: var(--panel-strong);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1rem 1.05rem;
    box-shadow: var(--shadow-soft);
}

.surface-card + .surface-card {
    margin-top: 0.9rem;
}

.job-card-title {
    margin: 0;
    font-size: 1.12rem;
    font-weight: 800;
    color: var(--text);
}

.job-card-company {
    margin-top: 0.24rem;
    color: #475569;
    font-weight: 600;
}

.job-card-summary {
    margin: 0.9rem 0 0;
    line-height: 1.7;
    color: #334155;
}

.job-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.7rem;
    margin-top: 1rem;
}

.job-card-block {
    background: rgba(248, 250, 252, 0.9);
    border: 1px solid rgba(15, 23, 42, 0.07);
    border-radius: 16px;
    padding: 0.78rem 0.84rem;
}

.job-card-block-title,
.info-card-title {
    font-size: 0.86rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #64748b;
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

.job-link {
    margin-top: 0.95rem;
}

.job-link a {
    color: #2563eb;
    font-weight: 700;
    text-decoration: none;
}

.info-card {
    background: var(--panel-strong);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1rem 1.05rem;
    box-shadow: var(--shadow-soft);
    min-height: 100%;
}

.summary-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(244,247,255,0.96) 100%);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1rem 1.05rem;
    box-shadow: var(--shadow-soft);
    margin-bottom: 0.95rem;
}

.summary-card-text {
    margin-top: 0.55rem;
    color: #334155;
    line-height: 1.75;
}

.board-card-shell {
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(246,249,255,0.96) 100%);
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 20px;
    padding: 0.95rem 1rem;
    min-height: 23.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
    box-shadow: var(--shadow-soft);
}

.board-card-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 800;
    color: var(--text);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.board-card-company {
    color: #475569;
    font-weight: 600;
    margin-top: -0.2rem;
}

.board-card-meta,
.board-card-timeline {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
}

.board-card-section {
    background: rgba(248, 250, 252, 0.92);
    border: 1px solid rgba(15, 23, 42, 0.06);
    border-radius: 14px;
    padding: 0.68rem 0.78rem;
}

.board-card-section-title {
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 0.38rem;
}

.board-card-copy {
    color: #334155;
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

.board-card-footer a {
    color: #2563eb;
    font-weight: 700;
    text-decoration: none;
}

.empty-chip {
    opacity: 0.78;
}

@media (max-width: 960px) {
    .hero-shell {
        padding: 1.2rem 1.15rem;
        border-radius: 18px;
    }

    .hero-title {
        font-size: 1.9rem;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )
