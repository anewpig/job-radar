"""提供導覽抽屜與漢堡按鈕的 CSS 片段。"""

NAVIGATION_STYLES = """
.st-key-nav-sticky-row-shell {
    position: sticky;
    top: var(--sticky-nav-top);
    width: var(--shared-surface-width);
    max-width: var(--shared-surface-width);
    box-sizing: border-box;
    margin: calc(var(--space-4) * -1) auto var(--surface-stack-gap);
    z-index: 995;
}

.st-key-nav-sticky-row-shell [data-testid="stHorizontalBlock"] {
    align-items: stretch;
}

.st-key-nav-sticky-row-shell [data-testid="column"] {
    display: flex;
}

.st-key-nav-sticky-row-shell [data-testid="column"] > div {
    width: 100%;
}

.st-key-nav-drawer-toggle-shell {
    display: flex;
    align-items: stretch;
    justify-content: flex-start;
    width: 100%;
    min-width: 0;
    margin: 0 !important;
    min-height: 100%;
    padding: 0 !important;
    border-radius: var(--surface-radius-lg);
    border: 1px solid var(--surface-primary-border);
    background:
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.12), transparent 24%),
        var(--surface-primary-bg);
    box-shadow: var(--surface-primary-shadow);
    backdrop-filter: blur(18px);
}

.st-key-nav-drawer-toggle-shell .stButton {
    display: flex;
    align-items: stretch;
    justify-content: flex-start;
    width: 100%;
    min-height: 100%;
    padding: 0;
}

.st-key-nav-drawer-toggle-shell .stButton > button {
    width: 100%;
    min-width: 100%;
    min-height: 100%;
    height: 100%;
    padding: var(--space-3) 0;
    border-radius: calc(var(--surface-radius-lg) - 1px);
    border: none;
    background: transparent;
    color: var(--control-text);
    box-shadow: none;
    font-size: 0.92rem;
    font-weight: 800;
}

.st-key-nav-drawer-toggle-shell .stButton > button:hover {
    border: none;
    background: rgba(123, 97, 255, 0.06);
    color: #4f4685;
}

.st-key-nav-drawer-panel-shell {
    position: fixed;
    top: calc(var(--sticky-nav-top) + 4rem);
    right: calc((100vw - var(--shared-surface-width)) / 2);
    width: 13.8rem;
    max-width: 13.8rem;
    margin: 0 !important;
    padding: 0 !important;
    background: var(--surface-floating-bg) !important;
    border-radius: var(--surface-radius-lg) !important;
    overflow: hidden;
    z-index: 1001;
}

.st-key-nav-drawer-panel-shell [data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: var(--surface-radius-lg) !important;
    border: 1px solid var(--surface-floating-border) !important;
    background: var(--surface-floating-bg) !important;
    box-shadow: var(--surface-floating-shadow);
}

.st-key-nav-drawer-panel-shell [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: var(--space-2) 0 !important;
}

.st-key-nav-drawer-panel-shell [data-testid="stVerticalBlock"] {
    background: #ffffff !important;
    gap: 0 !important;
}

.st-key-nav-drawer-panel-shell [data-testid="stElementContainer"] {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    max-width: none !important;
}

.st-key-nav-drawer-panel-shell .stButton {
    display: block !important;
    width: 100% !important;
    max-width: none !important;
    margin: 0 !important;
    padding: 0 !important;
    min-height: 0 !important;
}

.st-key-nav-drawer-panel-shell .stButton > button {
    display: flex !important;
    align-items: center;
    width: 100% !important;
    max-width: none !important;
    justify-content: flex-start !important;
    min-height: 3.35rem;
    height: 3.35rem;
    padding: 0 var(--space-5);
    border-radius: 0 !important;
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    color: #6f737a !important;
    font-size: 0.98rem;
    font-weight: 500;
    line-height: 1.1 !important;
    letter-spacing: 0;
    text-align: left;
}

.st-key-nav-drawer-panel-shell .stButton > button[kind="secondary"]:hover {
    background: rgba(247, 248, 250, 0.96) !important;
    color: #525861 !important;
}

.st-key-nav-drawer-panel-shell .stButton > button[kind="primary"] {
    background: rgba(246, 247, 249, 0.98) !important;
    color: #505661 !important;
    font-weight: 600;
}

.st-key-nav-drawer-panel-shell .stButton > button[kind="primary"]:hover {
    background: rgba(242, 244, 247, 0.98) !important;
    color: #474d57 !important;
}

.st-key-nav-tab-list-shell {
    min-width: 0;
}

.st-key-nav-tab-bar-shell {
    position: relative;
    overflow: hidden;
    width: 100%;
    max-width: none;
    box-sizing: border-box;
    margin: 0;
    border-radius: var(--surface-radius-lg) !important;
    border: 1px solid var(--surface-primary-border) !important;
    background:
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.12), transparent 24%),
        var(--surface-primary-bg) !important;
    box-shadow: var(--surface-primary-shadow);
    backdrop-filter: blur(18px);
    z-index: 1;
}

.st-key-nav-tab-bar-shell::before {
    content: "";
    position: absolute;
    right: -28px;
    top: -28px;
    width: 120px;
    height: 120px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123, 97, 255, 0.10) 0%, rgba(123, 97, 255, 0.02) 70%, transparent 100%);
    pointer-events: none;
}

.st-key-nav-tab-bar-shell [data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    border-radius: 24px !important;
}

.st-key-nav-tab-bar-shell [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: var(--space-3) var(--space-4) !important;
}

.st-key-nav-tab-bar-shell [data-testid="stHorizontalBlock"] {
    align-items: center;
}

.st-key-nav-tab-list-shell [data-testid="stPills"] {
    width: 100%;
}
"""
