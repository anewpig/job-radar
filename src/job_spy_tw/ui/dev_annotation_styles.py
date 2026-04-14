"""提供開發標註區塊的 CSS 片段。"""

DEV_ANNOTATION_STYLES = """
.element-container:has(.dev-card-annotation-host),
[data-testid="stElementContainer"]:has(.dev-card-annotation-host),
[data-testid="stVerticalBlock"]:has(.dev-card-annotation-host),
[data-testid="stVerticalBlockBorderWrapper"]:has(.dev-card-annotation-host),
.st-key-search-setup-shell:has(.dev-card-annotation-host),
.st-key-overview-shell:has(.dev-card-annotation-host),
.st-key-resume-shell:has(.dev-card-annotation-host),
.st-key-assistant-shell:has(.dev-card-annotation-host),
.st-key-tasks-shell:has(.dev-card-annotation-host),
.st-key-skills-shell:has(.dev-card-annotation-host),
.st-key-sources-shell:has(.dev-card-annotation-host),
.st-key-tracking-shell:has(.dev-card-annotation-host),
.st-key-board-shell:has(.dev-card-annotation-host),
.st-key-export-shell:has(.dev-card-annotation-host),
.st-key-notifications-shell:has(.dev-card-annotation-host),
.st-key-database-shell:has(.dev-card-annotation-host),
.st-key-auth-page-shell:has(.dev-card-annotation-host),
.st-key-auth-account-shell:has(.dev-card-annotation-host),
.st-key-nav-tab-bar-shell:has(.dev-card-annotation-host),
.st-key-nav-drawer-toggle-shell:has(.dev-card-annotation-host),
.st-key-assistant-launcher-trigger-shell:has(.dev-card-annotation-host),
.st-key-assistant-launcher-card-shell:has(.dev-card-annotation-host),
.st-key-assistant-launcher-form-shell:has(.dev-card-annotation-host) {
    overflow: visible !important;
}

.dev-card-annotation-host {
    position: relative;
    height: 0;
    z-index: 2147483000;
    overflow: visible;
    pointer-events: none;
}

.dev-card-annotation-shell {
    position: relative;
    top: -0.4rem;
    left: 0.7rem;
    display: inline-flex;
    max-width: min(calc(100% - 1.4rem), 44rem);
    padding: 0.1rem;
    border-radius: 999px;
    border: none;
    background: transparent;
    box-shadow: none;
    backdrop-filter: none;
    pointer-events: auto;
}

.dev-card-annotation-shell--compact {
    top: -0.28rem;
    left: 0.55rem;
    padding: 0.1rem;
}

.dev-card-annotation-host[data-dev-annotation-key="search-setup-shell"] {
    display: flex;
    justify-content: flex-end;
    width: 100%;
}

.dev-card-annotation-host[data-dev-annotation-key="overview-shell"] {
    display: flex;
    justify-content: flex-end;
    width: 100%;
}

.dev-card-annotation-host[data-dev-annotation-key="auth-page-shell"] {
    display: flex;
    justify-content: flex-end;
    width: 100%;
}

.dev-card-annotation-host[data-dev-annotation-key="auth-account-shell"] {
    display: flex;
    justify-content: flex-end;
    width: 100%;
}

.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-card-shell"] {
    display: flex;
    justify-content: flex-end;
    width: 100%;
}

.dev-card-annotation-host[data-dev-annotation-key="nav-drawer-toggle-shell"] {
    display: flex;
    justify-content: flex-start;
    width: 100%;
}

.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-trigger-shell"] {
    display: flex;
    justify-content: flex-start;
    width: 100%;
}

[data-testid="stElementContainer"]:has(.dev-card-annotation-host[data-dev-annotation-key="search-setup-shell"]) {
    margin: 0 !important;
    padding: 0 !important;
}

[data-testid="stElementContainer"]:has(.dev-card-annotation-host[data-dev-annotation-key="overview-shell"]) {
    margin: 0 !important;
    padding: 0 !important;
}

[data-testid="stElementContainer"]:has(.dev-card-annotation-host[data-dev-annotation-key="auth-page-shell"]) {
    margin: 0 !important;
    padding: 0 !important;
    z-index: 2147483003 !important;
}

[data-testid="stElementContainer"]:has(.dev-card-annotation-host[data-dev-annotation-key="auth-account-shell"]) {
    margin: 0 !important;
    padding: 0 !important;
    z-index: 2147483003 !important;
}

[data-testid="stElementContainer"]:has(.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-card-shell"]) {
    margin: 0 !important;
    padding: 0 !important;
    z-index: 2147483003 !important;
}

[data-testid="stElementContainer"]:has(.dev-card-annotation-host[data-dev-annotation-key="nav-drawer-toggle-shell"]) {
    margin: 0 !important;
    padding: 0 !important;
    z-index: 2147483003 !important;
}

[data-testid="stElementContainer"]:has(.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-trigger-shell"]) {
    margin: 0 !important;
    padding: 0 !important;
    z-index: 2147483003 !important;
}

[data-testid="stVerticalBlock"]:has(.dev-card-annotation-host[data-dev-annotation-key="overview-shell"]),
[data-testid="stVerticalBlockBorderWrapper"]:has(.dev-card-annotation-host[data-dev-annotation-key="overview-shell"]) {
}

[data-testid="stVerticalBlock"]:has(.dev-card-annotation-host[data-dev-annotation-key="auth-page-shell"]),
[data-testid="stVerticalBlockBorderWrapper"]:has(.dev-card-annotation-host[data-dev-annotation-key="auth-page-shell"]) {
    z-index: 2147483003 !important;
    overflow: visible !important;
}

[data-testid="stVerticalBlock"]:has(.dev-card-annotation-host[data-dev-annotation-key="auth-account-shell"]),
[data-testid="stVerticalBlockBorderWrapper"]:has(.dev-card-annotation-host[data-dev-annotation-key="auth-account-shell"]) {
    z-index: 2147483003 !important;
    overflow: visible !important;
}

[data-testid="stVerticalBlock"]:has(.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-card-shell"]),
[data-testid="stVerticalBlockBorderWrapper"]:has(.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-card-shell"]) {
    z-index: 2147483003 !important;
    overflow: visible !important;
}

[data-testid="stVerticalBlock"]:has(.dev-card-annotation-host[data-dev-annotation-key="nav-drawer-toggle-shell"]),
[data-testid="stVerticalBlockBorderWrapper"]:has(.dev-card-annotation-host[data-dev-annotation-key="nav-drawer-toggle-shell"]) {
    z-index: 2147483003 !important;
    overflow: visible !important;
}

[data-testid="stVerticalBlock"]:has(.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-trigger-shell"]),
[data-testid="stVerticalBlockBorderWrapper"]:has(.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-trigger-shell"]) {
    z-index: 2147483003 !important;
    overflow: visible !important;
}

.dev-card-annotation-host[data-dev-annotation-key="search-setup-shell"] .dev-card-annotation-shell,
.dev-card-annotation-host[data-dev-annotation-key="search-setup-shell"] .dev-card-annotation-shell--compact {
    top: -1.1rem;
    left: auto;
    margin-right: var(--space-6);
}

.dev-card-annotation-host[data-dev-annotation-key="overview-shell"] .dev-card-annotation-shell,
.dev-card-annotation-host[data-dev-annotation-key="overview-shell"] .dev-card-annotation-shell--compact {
    top: -1.35rem;
    left: auto;
    margin-right: var(--space-6);
}

.dev-card-annotation-host[data-dev-annotation-key="auth-page-shell"] .dev-card-annotation-shell,
.dev-card-annotation-host[data-dev-annotation-key="auth-page-shell"] .dev-card-annotation-shell--compact {
    top: -0.85rem;
    left: auto;
    margin-right: var(--space-4);
}

.dev-card-annotation-host[data-dev-annotation-key="auth-account-shell"] .dev-card-annotation-shell,
.dev-card-annotation-host[data-dev-annotation-key="auth-account-shell"] .dev-card-annotation-shell--compact {
    top: -0.85rem;
    left: auto;
    margin-right: var(--space-4);
}

.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-card-shell"] .dev-card-annotation-shell,
.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-card-shell"] .dev-card-annotation-shell--compact {
    top: -1rem;
    left: auto;
    margin-right: var(--space-5);
}

.dev-card-annotation-host[data-dev-annotation-key="nav-drawer-toggle-shell"] .dev-card-annotation-shell,
.dev-card-annotation-host[data-dev-annotation-key="nav-drawer-toggle-shell"] .dev-card-annotation-shell--compact {
    top: -0.95rem;
    left: 0;
    margin-left: var(--space-4);
    margin-right: 0;
}

.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-trigger-shell"] .dev-card-annotation-shell,
.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-trigger-shell"] .dev-card-annotation-shell--compact {
    position: absolute;
    top: -0.15rem;
    left: auto;
    right: calc(100% + 0.55rem);
    margin: 0;
}

.dev-card-annotation-host[data-dev-annotation-key="search-setup-shell"] .dev-card-annotation-details__panel {
    left: auto;
    right: 0;
}

.dev-card-annotation-host[data-dev-annotation-key="overview-shell"] .dev-card-annotation-details__panel {
    left: auto;
    right: 0;
}

.dev-card-annotation-host[data-dev-annotation-key="auth-page-shell"] .dev-card-annotation-details__panel {
    left: auto;
    right: 0;
}

.dev-card-annotation-host[data-dev-annotation-key="auth-account-shell"] .dev-card-annotation-details__panel {
    left: auto;
    right: 0;
}

.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-card-shell"] .dev-card-annotation-details__panel {
    left: auto;
    right: 0;
}

.dev-card-annotation-host[data-dev-annotation-key="nav-drawer-toggle-shell"] .dev-card-annotation-details__panel {
    left: 0;
    right: auto;
}

.dev-card-annotation-host[data-dev-annotation-key="assistant-launcher-trigger-shell"] .dev-card-annotation-details__panel {
    left: auto;
    right: 0;
}

.dev-card-annotation-row {
    display: flex;
    align-items: center;
    gap: 0;
}

.dev-card-annotation-row--compact {
    gap: 0;
}

.dev-card-annotation-left {
    display: none;
}

details.dev-card-annotation-details {
    margin: 0;
    padding: 0;
    border: none !important;
    background: transparent;
    box-shadow: none;
    position: relative;
    z-index: 2147483001;
}

.dev-card-annotation-details__summary {
    cursor: pointer;
    list-style: none;
    border-radius: 999px;
    border: 1px solid rgba(79, 70, 229, 0.22);
    background: rgba(255, 255, 255, 0.78);
    color: #4338ca;
    min-width: 2.35rem;
    padding: 0.18rem 0.42rem;
    font-size: 0.66rem;
    line-height: 1.1;
    text-align: center;
    font-weight: 800;
    letter-spacing: 0.04em;
    box-shadow: 0 8px 18px rgba(45, 40, 110, 0.12);
    backdrop-filter: blur(8px);
}

.dev-card-annotation-details__summary::-webkit-details-marker {
    display: none;
}

.dev-card-annotation-details__summary:hover {
    border-color: rgba(79, 70, 229, 0.28);
    background: rgba(255, 255, 255, 0.94);
}

.dev-card-annotation-details__panel {
    position: absolute;
    top: calc(100% + 0.55rem);
    left: 0;
    z-index: 2147483002;
    width: min(42rem, calc(100vw - 3rem));
    padding: 0.78rem 0.9rem;
    border-radius: 16px;
    border: 1px solid rgba(79, 70, 229, 0.12);
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 18px 40px rgba(45, 40, 110, 0.14);
}

.dev-card-annotation-details__title {
    color: #231c63;
    font-size: 0.96rem;
    font-weight: 900;
}

.dev-card-annotation-details__meta {
    margin-top: 0.42rem;
    color: #5e5690;
    font-size: 0.78rem;
}

.dev-card-annotation-details__meta code,
.dev-card-annotation-details__list code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 0.74rem;
}

.dev-card-annotation-details__copy {
    margin-top: 0.55rem;
    color: #3e3865;
    font-size: 0.84rem;
    line-height: 1.6;
}

.dev-card-annotation-details__section-title {
    margin-top: 0.8rem;
    color: #4338ca;
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.dev-card-annotation-details__list {
    margin: 0.45rem 0 0;
    padding-left: 1.1rem;
    color: #3e3865;
}

.dev-card-annotation-details__list li + li {
    margin-top: 0.38rem;
}

.dev-card-annotation-details__list--named {
    padding-left: 0;
    list-style: none;
}

.dev-card-annotation-details__named-item {
    display: grid;
    grid-template-columns: minmax(9rem, max-content) 1fr;
    gap: 0.55rem;
    align-items: start;
}

.dev-card-annotation-details__named-item code {
    display: inline-flex;
    width: fit-content;
    padding: 0.14rem 0.38rem;
    border-radius: 8px;
    background: rgba(79, 70, 229, 0.08);
    color: #392f92;
}

.dev-card-annotation-details__named-item span {
    color: #4d476f;
    font-size: 0.8rem;
    line-height: 1.55;
}

@media (max-width: 960px) {
    .dev-card-annotation-row {
        align-items: flex-start;
    }

    .dev-card-annotation-shell,
    .dev-card-annotation-shell--compact {
        max-width: calc(100% - 1rem);
    }

    .dev-card-annotation-details__panel {
        width: min(32rem, calc(100vw - 2rem));
    }

    .dev-card-annotation-details__named-item {
        grid-template-columns: 1fr;
        gap: 0.25rem;
    }
}
"""
