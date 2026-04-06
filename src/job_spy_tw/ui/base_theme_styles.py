"""提供全站基礎主題、版面與通用元件的 CSS 片段。"""

BASE_THEME_STYLES = """
:root {
    --space-1: 0.25rem;
    --space-2: 0.5rem;
    --space-3: 0.75rem;
    --space-4: 1rem;
    --space-5: 1.25rem;
    --space-6: 1.5rem;
    --space-7: 1.75rem;
    --space-8: 2rem;
    --space-9: 2.25rem;
    --space-10: 2.5rem;
    --space-11: 2.75rem;
    --space-12: 3rem;
    --space-13: 3.25rem;
    --space-14: 3.5rem;
    --space-15: 3.75rem;
    --space-16: 4rem;
    --space-17: 4.25rem;
    --space-18: 4.5rem;
    --bg-start: #faf7ff;
    --bg-end: #f3efff;
    --page-shell-max: 1240px;
    --page-shell-gutter: var(--space-4);
    --shared-surface-width: min(1240px, calc(100vw - 2rem));
    --surface-stack-gap: var(--space-4);
    --header-shell-max: calc(var(--page-shell-max) + (var(--page-shell-gutter) * 2));
    --surface-radius-xl: 30px;
    --surface-radius-lg: 24px;
    --surface-radius-md: 18px;
    --top-header-height: var(--space-14);
    --sticky-nav-top: calc(var(--top-header-height) + var(--space-2));
    --surface-content-inline: var(--space-6);
    --surface-content-inline-wide: var(--space-10);
    --surface-content-block: var(--space-6);
    --surface-content-gap-tight: var(--space-3);
    --surface-content-gap: var(--space-4);
    --surface-content-gap-loose: var(--space-10);
    --panel: rgba(255, 255, 255, 0.96);
    --panel-soft: rgba(248, 245, 255, 0.96);
    --border: rgba(104, 80, 188, 0.12);
    --text: #1f1b4d;
    --muted: #726c96;
    --accent: #7b61ff;
    --accent-soft: #f0ebff;
    --warm-soft: #fff6db;
    --shadow-soft: 0 10px 28px rgba(116, 86, 204, 0.08);
    --surface-primary-bg: linear-gradient(135deg, #ffffff 0%, #f8f4ff 68%, #f3edff 100%);
    --surface-primary-border: rgba(123, 97, 255, 0.12);
    --surface-primary-shadow: 0 10px 28px rgba(116, 86, 204, 0.08);
    --surface-secondary-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(249, 246, 255, 0.96) 100%);
    --surface-secondary-border: rgba(123, 97, 255, 0.10);
    --surface-floating-bg: #ffffff;
    --surface-floating-border: rgba(123, 97, 255, 0.12);
    --surface-floating-shadow: 0 18px 36px rgba(31, 27, 77, 0.14);
    --control-height: 3.08rem;
    --control-radius: 16px;
    --control-padding-inline: 0.92rem;
    --control-border: rgba(123, 97, 255, 0.14);
    --control-bg: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(247,242,255,0.96) 100%);
    --control-hover-bg: linear-gradient(180deg, rgba(250,248,255,0.99) 0%, rgba(244,239,255,0.97) 100%);
    --control-text: #4a3f86;
    --control-shadow: 0 10px 22px rgba(116, 86, 204, 0.08);
    --control-primary-bg: linear-gradient(135deg, #6f56f6 0%, #7b61ff 55%, #9672ff 100%);
    --control-primary-hover-bg: linear-gradient(135deg, #654cf0 0%, #7459fa 55%, #8f69fb 100%);
    --control-primary-shadow: 0 16px 28px rgba(123, 97, 255, 0.20);
    --search-row-control-height: var(--control-height);
    --search-row-action-offset: 0.24rem;
    --search-row-action-height: 2.6rem;
    --search-row-action-radius: var(--control-radius);
    --search-row-action-gap: 0.0rem;
    --search-row-add-offset: 0.22rem;
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
    border-radius: var(--control-radius);
    border: 1px solid var(--control-border);
    min-height: var(--control-height);
    padding: 0.08rem var(--control-padding-inline);
    font-weight: 700;
    background: var(--control-bg);
    color: var(--control-text);
    box-shadow: var(--control-shadow);
}

.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    border-color: rgba(123, 97, 255, 0.26);
    background: var(--control-hover-bg);
}

[data-testid="stPopover"] > button {
    width: auto;
    min-width: fit-content;
    min-height: var(--control-height);
    padding: 0.08rem var(--control-padding-inline);
    border-radius: var(--control-radius);
    border: 1px solid var(--control-border);
    background: var(--control-bg);
    color: var(--control-text);
    box-shadow: var(--control-shadow);
    font-weight: 700;
    justify-content: center;
}

[data-testid="stPopover"] > button:hover {
    border-color: rgba(123, 97, 255, 0.20);
    background: var(--control-hover-bg);
    color: #312a5f;
    box-shadow: var(--control-shadow);
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    color: #ffffff;
    border: none;
    background: var(--control-primary-bg);
    box-shadow: var(--control-primary-shadow);
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

@media (max-width: 960px) {
    [data-testid="stAppViewContainer"] > .main .block-container {
        padding-top: 0.0rem;
    }
}

.st-key-finalize-worker-shell,
.st-key-finalize-worker-shell > div,
.st-key-finalize-worker-shell [data-testid="stVerticalBlock"],
.st-key-finalize-worker-shell [data-testid="stElementContainer"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}

/* 背景補分析仍會觸發 Streamlit 的 stale/loading 樣式，這裡直接關掉灰化效果。 */
[data-stale="true"],
[data-stale="true"] *,
.stale-element,
.stale-element *,
[aria-busy="true"],
[aria-busy="true"] * {
    opacity: 1 !important;
    filter: none !important;
}

.stSpinner,
[data-testid="stSpinner"],
[data-testid="stSkeleton"],
[data-testid="stStatusWidget"] {
    display: none !important;
}
"""
