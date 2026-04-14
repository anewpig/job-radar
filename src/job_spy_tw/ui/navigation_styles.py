"""提供導覽抽屜與漢堡按鈕的 CSS 片段。"""

NAVIGATION_STYLES = """
.st-key-nav-sticky-row-shell {
    position: sticky;
    top: var(--sticky-nav-top);
    width: var(--shared-surface-width);
    max-width: var(--shared-surface-width);
    box-sizing: border-box;
    margin: var(--space-3) auto var(--space-3);
    z-index: 995;
}

.st-key-nav-sticky-row-shell [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

.st-key-nav-drawer-toggle-shell {
    position: fixed !important;
    right: var(--floating-fab-right) !important;
    bottom:
        calc(
            var(--floating-fab-stack-base-bottom)
            + var(--floating-fab-size)
            + var(--floating-fab-gap)
            + var(--assistant-launcher-active-offset)
        ) !important;
    z-index: 1002;
    width: var(--floating-fab-size) !important;
    min-width: var(--floating-fab-size) !important;
    max-width: var(--floating-fab-size) !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
    box-sizing: border-box !important;
}

.st-key-nav-drawer-toggle-button-shell,
.st-key-nav-drawer-toggle-button-shell [data-testid="stElementContainer"],
.st-key-nav-drawer-toggle-button-shell [data-testid="stVerticalBlock"],
.st-key-nav-drawer-toggle-button-shell .stButton {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
}

.st-key-nav-drawer-toggle-button-shell .stButton > button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: var(--floating-fab-size) !important;
    min-width: var(--floating-fab-size) !important;
    max-width: var(--floating-fab-size) !important;
    min-height: var(--floating-fab-size) !important;
    height: var(--floating-fab-size) !important;
    padding: 0 !important;
    border-radius: var(--floating-fab-radius) !important;
    border: var(--floating-fab-border) !important;
    background: var(--floating-fab-bg) !important;
    color: var(--floating-fab-text) !important;
    box-shadow: var(--floating-fab-shadow) !important;
    backdrop-filter: blur(18px) !important;
    font-size: 1rem !important;
    font-weight: 800 !important;
    letter-spacing: 0 !important;
    line-height: 1;
    text-align: center;
    position: relative;
    z-index: 1;
    aspect-ratio: 1 / 1;
    transition:
        background 160ms ease,
        color 160ms ease,
        box-shadow 160ms ease,
        transform 160ms ease;
}

.st-key-nav-drawer-toggle-button-shell .stButton > button:hover,
.st-key-nav-drawer-toggle-button-shell .stButton > button:focus {
    border: var(--floating-fab-border) !important;
    background: var(--floating-fab-hover-bg) !important;
    color: var(--floating-fab-text-hover) !important;
    box-shadow: var(--floating-fab-shadow) !important;
}

.st-key-nav-drawer-toggle-button-shell .stButton > button[kind="primary"] {
    border: var(--floating-fab-border) !important;
    background: var(--floating-fab-bg) !important;
    color: var(--floating-fab-text) !important;
    box-shadow: var(--floating-fab-shadow) !important;
}

.st-key-nav-drawer-panel-shell {
    position: fixed;
    right: var(--floating-fab-right);
    bottom:
        calc(
            var(--floating-fab-stack-base-bottom)
            + (var(--floating-fab-size) * 2)
            + var(--floating-fab-gap)
            + 1.05rem
            + var(--assistant-launcher-active-offset)
        );
    width: min(18rem, calc(100vw - 1rem));
    max-width: calc(100vw - 1rem);
    margin: 0 !important;
    padding: 0 !important;
    background: #ffffff !important;
    border-radius: 28px !important;
    overflow: hidden;
    z-index: 1001;
}

.st-key-nav-drawer-panel-shell [data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 28px !important;
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.995) 0%, rgba(255, 255, 255, 0.975) 100%) !important;
    box-shadow:
        0 26px 52px rgba(31, 27, 77, 0.16),
        0 10px 22px rgba(123, 97, 255, 0.08),
        inset 0 1px 0 rgba(255, 255, 255, 0.56);
    backdrop-filter: blur(24px);
}

.st-key-nav-drawer-panel-shell [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 0 !important;
}

.st-key-nav-drawer-panel-shell [data-testid="stVerticalBlock"] {
    background: #ffffff !important;
    gap: 0 !important;
    padding: 0 !important;
    max-height: min(36rem, calc(100vh - 7rem));
    overflow-y: auto !important;
    scrollbar-width: thin;
    scrollbar-color: rgba(123, 97, 255, 0.22) transparent;
}

.st-key-nav-drawer-panel-shell [data-testid="stElementContainer"] {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
    max-width: none !important;
}

.nav-drawer-panel-header {
    position: relative;
    padding: var(--space-5) var(--space-5) var(--space-4);
}

.nav-drawer-panel-header::after {
    content: "";
    position: absolute;
    right: 1.25rem;
    top: 1rem;
    width: 4.4rem;
    height: 4.4rem;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123, 97, 255, 0.14) 0%, rgba(123, 97, 255, 0.02) 68%, transparent 100%);
    pointer-events: none;
}

.nav-drawer-panel-kicker {
    font-size: 0.68rem;
    line-height: 1.2;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8e87b6;
}

.nav-drawer-panel-title {
    margin-top: 0.35rem;
    font-size: 1.34rem;
    line-height: 1.08;
    font-weight: 900;
    color: #241d5a;
}

.nav-drawer-panel-desc {
    margin-top: 0.45rem;
    font-size: 0.88rem;
    line-height: 1.55;
    font-weight: 600;
    color: #736c9a;
    max-width: 13rem;
}

[class*="st-key-nav-drawer-section-"] {
    position: relative;
    padding: 0 0 var(--space-2);
}

[class*="st-key-nav-drawer-section-"] + [class*="st-key-nav-drawer-section-"] {
    margin-top: var(--space-2);
    padding-top: var(--space-3);
}

[class*="st-key-nav-drawer-section-"] + [class*="st-key-nav-drawer-section-"]::before {
    content: "";
    position: absolute;
    top: 0;
    left: var(--space-5);
    right: var(--space-5);
    height: 1px;
    background: linear-gradient(90deg, rgba(123, 97, 255, 0.18), rgba(123, 97, 255, 0.05), transparent);
}

[class*="st-key-nav-drawer-section-"] [data-testid="stVerticalBlock"] {
    gap: var(--space-1) !important;
}

.nav-drawer-section-label {
    padding: 0 var(--space-5) var(--space-2);
    font-size: 0.68rem;
    line-height: 1.2;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #867eaf;
}

[class*="st-key-nav-drawer-item-shell-"] {
    position: relative;
    margin: 0 var(--space-3) !important;
}

[class*="st-key-nav-drawer-item-shell-"]::before {
    position: absolute;
    left: var(--space-3);
    top: 50%;
    transform: translateY(-50%);
    width: 2rem;
    height: 2rem;
    border-radius: 0.8rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(123, 97, 255, 0.08);
    background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(247,243,255,0.95) 100%);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.58);
    color: #6a6197;
    font-size: 0.92rem;
    font-weight: 900;
    pointer-events: none;
    z-index: 2;
}

[class*="st-key-nav-drawer-item-shell-"]:has(.stButton > button[kind="primary"])::before {
    border-color: rgba(123, 97, 255, 0.14);
    background: linear-gradient(180deg, rgba(123, 97, 255, 0.14) 0%, rgba(123, 97, 255, 0.08) 100%);
    color: #4434b2;
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.28),
        0 10px 18px rgba(123, 97, 255, 0.08);
}

.st-key-nav-drawer-item-shell-overview::before {
    content: "◌";
}

.st-key-nav-drawer-item-shell-assistant::before {
    content: "✦";
}

.st-key-nav-drawer-item-shell-resume::before {
    content: "▣";
}

.st-key-nav-drawer-item-shell-tasks::before {
    content: "≣";
}

.st-key-nav-drawer-item-shell-tracking::before {
    content: "●";
}

.st-key-nav-drawer-item-shell-board::before {
    content: "▤";
}

.st-key-nav-drawer-item-shell-sources::before {
    content: "◎";
}

.st-key-nav-drawer-item-shell-notifications::before {
    content: "◍";
}

.st-key-nav-drawer-item-shell-database::before {
    content: "⌘";
}

.st-key-nav-drawer-item-shell-export::before {
    content: "↧";
}

.st-key-nav-drawer-item-shell-backend_console::before {
    content: "⋯";
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
    min-height: 3.05rem;
    height: auto;
    padding: 0.72rem 4rem 0.72rem 4rem;
    border-radius: 18px !important;
    border: 1px solid transparent !important;
    box-shadow: none !important;
    background: transparent !important;
    color: #5a537e !important;
    font-size: 0.95rem;
    font-weight: 650;
    line-height: 1.18 !important;
    letter-spacing: -0.01em;
    text-align: left;
    position: relative;
    transition:
        background 160ms ease,
        border-color 160ms ease,
        color 160ms ease,
        box-shadow 160ms ease,
        transform 160ms ease;
}

.st-key-nav-drawer-panel-shell .stButton > button[kind="secondary"]:hover {
    background: rgba(123, 97, 255, 0.06) !important;
    border-color: rgba(123, 97, 255, 0.08) !important;
    color: #3d356d !important;
    box-shadow: 0 10px 18px rgba(123, 97, 255, 0.08) !important;
    transform: translateY(-1px);
}

.st-key-nav-drawer-panel-shell .stButton > button[kind="primary"] {
    background: linear-gradient(180deg, rgba(123, 97, 255, 0.14) 0%, rgba(123, 97, 255, 0.07) 100%) !important;
    border-color: rgba(123, 97, 255, 0.10) !important;
    color: #30295f !important;
    font-weight: 800;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.22),
        0 12px 22px rgba(123, 97, 255, 0.10) !important;
}

.st-key-nav-drawer-panel-shell .stButton > button[kind="primary"]:hover {
    background: linear-gradient(180deg, rgba(123, 97, 255, 0.16) 0%, rgba(123, 97, 255, 0.08) 100%) !important;
    color: #281f63 !important;
    transform: translateY(-1px);
}

.st-key-nav-drawer-panel-shell .stButton > button[kind="primary"]::after {
    content: "目前";
    position: absolute;
    right: var(--space-4);
    top: 50%;
    transform: translateY(-50%);
    padding: 0.18rem 0.48rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.62);
    border: 1px solid rgba(123, 97, 255, 0.10);
    color: #4637b8;
    font-size: 0.66rem;
    line-height: 1;
    font-weight: 900;
    letter-spacing: 0.08em;
}

@media (max-width: 640px) {
    .st-key-nav-drawer-panel-shell {
        width: min(18rem, calc(100vw - 1rem));
    }

    .nav-drawer-panel-header {
        padding: var(--space-4) var(--space-4) var(--space-3);
    }

    .nav-drawer-section-label {
        padding: 0 var(--space-4) var(--space-2);
    }

    [class*="st-key-nav-drawer-section-"] + [class*="st-key-nav-drawer-section-"]::before {
        left: var(--space-4);
        right: var(--space-4);
    }

    [class*="st-key-nav-drawer-item-shell-"] {
        margin: 0 var(--space-2) !important;
    }

    [class*="st-key-nav-drawer-item-shell-"]::before {
        left: 0.8rem;
        width: 1.9rem;
        height: 1.9rem;
    }

    .st-key-nav-drawer-panel-shell .stButton > button {
        padding: 0.68rem 3.8rem 0.68rem 3.55rem;
    }
}

.st-key-nav-tab-list-shell {
    min-width: 0;
}

.st-key-nav-tab-list-shell [data-testid="stElementContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}

.st-key-nav-tab-list-shell [data-testid="stWidgetLabel"],
.st-key-nav-tab-list-shell [data-testid="stWidgetLabelHelp"] {
    display: none !important;
    margin: 0 !important;
    padding: 0 !important;
    min-height: 0 !important;
}

.st-key-nav-tab-bar-shell {
    position: relative;
    overflow: hidden;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
    margin: 0;
    border-radius: 24px !important;
    border: 1px solid rgba(123, 97, 255, 0.09) !important;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.985) 0%, rgba(248,245,255,0.95) 100%),
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.12), transparent 24%),
        repeating-linear-gradient(135deg, transparent 0 22px, rgba(123, 97, 255, 0.018) 22px 23px, transparent 23px 48px) !important;
    box-shadow: 0 10px 22px rgba(96, 74, 180, 0.06);
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

.st-key-nav-tab-bar-shell::after {
    content: "";
    position: absolute;
    top: 0;
    right: 0;
    width: 13rem;
    height: 100%;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.0) 0%, rgba(255,255,255,0.0) 100%),
        repeating-linear-gradient(118deg, transparent 0 18px, rgba(123, 97, 255, 0.02) 18px 19px, transparent 19px 40px);
    opacity: 0.72;
    pointer-events: none;
}

.st-key-nav-tab-bar-shell [data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    border-radius: 24px !important;
}

.st-key-nav-tab-bar-shell [data-testid="stVerticalBlock"] {
    display: flex;
    align-items: center;
    gap: 0 !important;
}

.st-key-nav-tab-bar-shell [data-testid="stVerticalBlockBorderWrapper"] > div {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 2.58rem;
    padding: 0 var(--space-2) !important;
}

.st-key-nav-tab-bar-shell [data-testid="stHorizontalBlock"] {
    align-items: center;
}

.st-key-nav-tab-list-shell [data-testid="stPills"] {
    display: flex;
    align-items: center;
    height: 100%;
    margin: 0 !important;
    padding: 0 !important;
    width: 100%;
    transform: none;
}

.st-key-nav-tab-list-shell [data-testid="stPills"] [role="radiogroup"] {
    display: flex !important;
    flex-wrap: nowrap;
    align-items: center;
    height: 100%;
    gap: var(--space-1) !important;
    width: 100%;
    padding: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    transform: none;
}

.st-key-nav-tab-list-shell [data-testid="stPills"] button {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 2.58rem !important;
    height: 2.58rem !important;
    padding: 0 calc(var(--space-3) + 0.1rem) !important;
    border-radius: 16px !important;
    border: 1px solid rgba(123, 97, 255, 0.05) !important;
    background: rgba(255, 255, 255, 0.42) !important;
    color: #69638f !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    line-height: 1 !important;
    letter-spacing: 0.01em;
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.82),
        0 1px 0 rgba(255,255,255,0.45) !important;
    transform: translateY(-0.0625rem);
    transition:
        background 160ms ease,
        border-color 160ms ease,
        color 160ms ease,
        box-shadow 160ms ease,
        transform 160ms ease;
}

.st-key-nav-tab-list-shell [data-testid="stPills"] button:hover {
    border-color: rgba(123, 97, 255, 0.09) !important;
    background: rgba(123, 97, 255, 0.075) !important;
    color: #463c86 !important;
}

.st-key-nav-tab-list-shell [data-testid="stPills"] [aria-checked="true"],
.st-key-nav-tab-list-shell [data-testid="stPills"] button[kind="primary"] {
    border-color: rgba(123, 97, 255, 0.13) !important;
    background: linear-gradient(180deg, rgba(123, 97, 255, 0.17) 0%, rgba(123, 97, 255, 0.095) 100%) !important;
    color: #241f54 !important;
    box-shadow:
        inset 0 0 0 1px rgba(123, 97, 255, 0.14),
        inset 0 1px 0 rgba(255,255,255,0.34),
        0 8px 14px rgba(123, 97, 255, 0.07) !important;
}

.st-key-nav-tab-list-shell [data-testid="stPills"] [aria-checked="true"]:hover,
.st-key-nav-tab-list-shell [data-testid="stPills"] button[kind="primary"]:hover {
    background: linear-gradient(180deg, rgba(123, 97, 255, 0.20) 0%, rgba(123, 97, 255, 0.11) 100%) !important;
    color: #1f1a4d !important;
}
"""
