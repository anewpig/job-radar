"""提供手機客服式 AI launcher 樣式。"""

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
    box-sizing: border-box !important;
    background: #ffffff !important;
    border-radius: 2rem !important;
    overflow: visible !important;
}

.st-key-assistant-launcher-card-shell > div,
.st-key-assistant-launcher-card-shell [data-testid="stElementContainer"] {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    background: #ffffff !important;
}

.st-key-assistant-launcher-mobile-shell {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
}

.st-key-assistant-launcher-mobile-shell [data-testid="stVerticalBlockBorderWrapper"] {
    height: var(--launcher-shell-height) !important;
    border-radius: 2rem !important;
    border: 1px solid rgba(123, 97, 255, 0.12) !important;
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.995) 0%, rgba(251, 249, 255, 0.985) 100%),
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.14), transparent 32%) !important;
    box-shadow:
        0 26px 52px rgba(31, 27, 77, 0.18),
        0 10px 22px rgba(123, 97, 255, 0.10),
        inset 0 1px 0 rgba(255, 255, 255, 0.7) !important;
    backdrop-filter: blur(24px);
    overflow: hidden !important;
}

.st-key-assistant-launcher-mobile-shell [data-testid="stVerticalBlockBorderWrapper"] > div {
    height: 100% !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}

.st-key-assistant-launcher-mobile-shell [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    gap: 0 !important;
    background: transparent !important;
}

.st-key-assistant-launcher-mobile-shell [data-testid="stElementContainer"] {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

.st-key-assistant-launcher-mobile-header {
    flex: 0 0 auto;
    padding: 1rem 1rem 0.85rem;
    border-bottom: 1px solid rgba(123, 97, 255, 0.09);
    background:
        linear-gradient(180deg, rgba(248, 243, 255, 0.96) 0%, rgba(255, 255, 255, 0.90) 100%),
        radial-gradient(circle at top left, rgba(123, 97, 255, 0.10), transparent 45%);
}

.st-key-assistant-launcher-mobile-header [data-testid="stHorizontalBlock"] {
    align-items: center !important;
    gap: 0.75rem !important;
}

.assistant-launcher-header-brand {
    width: 2.65rem;
    height: 2.65rem;
    border-radius: 1rem;
    background:
        linear-gradient(160deg, rgba(123, 97, 255, 0.92) 0%, rgba(98, 74, 205, 0.96) 100%),
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.24), transparent 38%);
    box-shadow: 0 12px 24px rgba(96, 74, 180, 0.18);
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.assistant-launcher-header-brand span {
    font-size: 0.95rem;
    line-height: 1;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: 0.04em;
}

.assistant-launcher-header-kicker {
    font-size: 0.68rem;
    line-height: 1.15;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #938bbd;
}

.assistant-launcher-header-title {
    margin-top: 0.22rem;
    font-size: 1.08rem;
    line-height: 1.12;
    font-weight: 900;
    color: var(--text);
}

.assistant-launcher-header-subtitle {
    margin-top: 0.2rem;
    font-size: 0.78rem;
    line-height: 1.35;
    color: var(--muted);
}

.st-key-assistant-launcher-panel-close .stButton > button {
    width: 2.35rem;
    min-width: 2.35rem;
    height: 2.35rem;
    min-height: 2.35rem;
    padding: 0 !important;
    border-radius: 999px !important;
    border: 1px solid rgba(123, 97, 255, 0.12) !important;
    background: rgba(255, 255, 255, 0.9) !important;
    color: #5a518d !important;
    box-shadow: none !important;
    font-size: 0.92rem !important;
    font-weight: 900 !important;
}

.st-key-assistant-launcher-mobile-body {
    flex: 1 1 auto;
    min-height: 0 !important;
    background:
        linear-gradient(180deg, rgba(253, 252, 255, 0.98) 0%, rgba(249, 246, 255, 0.94) 100%);
}

.st-key-assistant-launcher-mobile-body,
.st-key-assistant-launcher-mobile-body > div,
.st-key-assistant-launcher-mobile-body [data-testid="stElementContainer"] {
    height: 100% !important;
}

.st-key-assistant-launcher-mobile-body [data-testid="stVerticalBlock"] {
    height: 100% !important;
    min-height: 0 !important;
    overflow-y: auto !important;
    padding: 1rem 1rem 0.85rem !important;
    gap: 0.9rem !important;
    scrollbar-width: thin;
    scrollbar-color: rgba(123, 97, 255, 0.22) transparent;
}

.st-key-assistant-launcher-mobile-body [data-testid="stVerticalBlock"]::-webkit-scrollbar {
    width: 0.45rem;
}

.st-key-assistant-launcher-mobile-body [data-testid="stVerticalBlock"]::-webkit-scrollbar-thumb {
    background: rgba(123, 97, 255, 0.18);
    border-radius: 999px;
}

.st-key-assistant-launcher-mobile-tabbar {
    flex: 0 0 auto;
    padding: 0.5rem 0.65rem calc(0.6rem + env(safe-area-inset-bottom, 0px));
    border-top: 1px solid rgba(123, 97, 255, 0.08);
    background: rgba(255, 255, 255, 0.98);
}

.st-key-assistant-launcher-mobile-tabbar [data-testid="stHorizontalBlock"] {
    gap: 0.38rem !important;
    align-items: stretch !important;
}

[class*="st-key-assistant-launcher-tab-"] .stButton {
    width: 100%;
}

[class*="st-key-assistant-launcher-tab-"] .stButton > button {
    min-height: 3.25rem !important;
    height: 3.25rem !important;
    padding: 0.32rem 0.4rem !important;
    border-radius: 1rem !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    color: #7a739f !important;
    box-shadow: none !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0.18rem !important;
    font-size: 0.74rem !important;
    font-weight: 800 !important;
    line-height: 1.08 !important;
}

[class*="st-key-assistant-launcher-tab-"] .stButton > button::before {
    display: block;
    font-size: 1rem;
    line-height: 1;
    font-weight: 800;
}

.st-key-assistant-launcher-tab-assistant .stButton > button::before {
    content: "✦";
}

.st-key-assistant-launcher-tab-guide .stButton > button::before {
    content: "⌕";
}

.st-key-assistant-launcher-tab-notifications .stButton > button::before {
    content: "◎";
}

[class*="st-key-assistant-launcher-tab-"] .stButton > button:hover {
    background: rgba(123, 97, 255, 0.06) !important;
    color: #514587 !important;
}

[class*="st-key-assistant-launcher-tab-"] .stButton > button[kind="primary"] {
    border-color: rgba(123, 97, 255, 0.12) !important;
    background: linear-gradient(180deg, rgba(123, 97, 255, 0.14) 0%, rgba(123, 97, 255, 0.08) 100%) !important;
    color: #40356f !important;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.44) !important;
}

.st-key-assistant-launcher-assistant-body [data-testid="stVerticalBlock"],
.st-key-assistant-launcher-guide-body [data-testid="stVerticalBlock"],
.st-key-assistant-launcher-notifications-body [data-testid="stVerticalBlock"] {
    gap: 0.9rem !important;
}

.assistant-launcher-hero-card {
    padding: 1rem 1rem 0.95rem;
    border-radius: 1.35rem;
    background:
        linear-gradient(180deg, rgba(123, 97, 255, 0.12) 0%, rgba(255, 255, 255, 0.96) 100%),
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.18), transparent 38%);
    border: 1px solid rgba(123, 97, 255, 0.10);
    box-shadow: 0 16px 32px rgba(96, 74, 180, 0.10);
}

.assistant-launcher-hero-kicker,
.assistant-launcher-section-kicker,
.assistant-launcher-guide-section-label,
.assistant-launcher-notification-summary-label {
    font-size: 0.68rem;
    line-height: 1.2;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #9088ba;
}

.assistant-launcher-hero-title {
    margin-top: 0.3rem;
    font-size: 1.02rem;
    line-height: 1.26;
    font-weight: 900;
    color: #2a2358;
}

.assistant-launcher-hero-copy {
    margin-top: 0.36rem;
    font-size: 0.82rem;
    line-height: 1.42;
    color: #6a648d;
}

.assistant-launcher-hero-list {
    margin: 0.7rem 0 0;
    padding: 0 0 0 1rem;
    color: #483f7f;
}

.assistant-launcher-hero-list li {
    margin: 0.18rem 0;
    font-size: 0.78rem;
    line-height: 1.38;
    font-weight: 700;
}

.st-key-assistant-launcher-quick-chip-grid [data-testid="stHorizontalBlock"] {
    gap: 0.5rem !important;
}

[class*="st-key-assistant-launcher-chip-"] .stButton > button {
    min-height: 2.6rem !important;
    height: auto !important;
    padding: 0.7rem 0.85rem !important;
    border-radius: 999px !important;
    border: 1px solid rgba(123, 97, 255, 0.12) !important;
    background: rgba(255, 255, 255, 0.94) !important;
    color: #4c437d !important;
    box-shadow: 0 10px 20px rgba(96, 74, 180, 0.06) !important;
    font-size: 0.79rem !important;
    font-weight: 800 !important;
    line-height: 1.25 !important;
}

[class*="st-key-assistant-launcher-chip-"] .stButton > button:hover {
    background: rgba(123, 97, 255, 0.07) !important;
}

.st-key-assistant-launcher-composer-shell [data-testid="stHorizontalBlock"] {
    align-items: center !important;
    gap: 0.5rem !important;
}

.st-key-assistant_launcher_question_input input,
.st-key-assistant-launcher-guide-search input {
    min-height: 3rem !important;
    border-radius: 1rem !important;
    border: 1px solid rgba(123, 97, 255, 0.12) !important;
    background: rgba(255, 255, 255, 0.96) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
    color: var(--text) !important;
}

.st-key-assistant-launcher-guide-search [data-testid="stTextInput"] {
    margin-bottom: 0.1rem !important;
}

.st-key-assistant-launcher-send .stButton > button {
    width: 3rem !important;
    min-width: 3rem !important;
    height: 3rem !important;
    min-height: 3rem !important;
    padding: 0 !important;
    border-radius: 1rem !important;
    background: linear-gradient(180deg, rgba(123, 97, 255, 0.98) 0%, rgba(101, 76, 213, 0.98) 100%) !important;
    border: 1px solid rgba(90, 66, 202, 0.24) !important;
    color: #ffffff !important;
    box-shadow: 0 14px 24px rgba(96, 74, 180, 0.18) !important;
    font-size: 1rem !important;
    font-weight: 900 !important;
}

.st-key-assistant-launcher-open-page .stButton > button,
.st-key-assistant-launcher-open-notifications .stButton > button {
    min-height: 2.9rem !important;
    border-radius: 1rem !important;
    border: 1px solid rgba(123, 97, 255, 0.12) !important;
    background: rgba(255, 255, 255, 0.95) !important;
    color: #4b407d !important;
    box-shadow: 0 10px 22px rgba(96, 74, 180, 0.06) !important;
    font-size: 0.82rem !important;
    font-weight: 800 !important;
}

[class*="st-key-assistant-launcher-guide-row-"] {
    padding: 0.88rem 0.95rem;
    border-radius: 1.15rem;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: rgba(255, 255, 255, 0.94);
    box-shadow: 0 10px 20px rgba(96, 74, 180, 0.05);
}

[class*="st-key-assistant-launcher-guide-row-"] [data-testid="stHorizontalBlock"] {
    align-items: center !important;
    gap: 0.7rem !important;
}

.assistant-launcher-guide-title {
    font-size: 0.9rem;
    line-height: 1.22;
    font-weight: 800;
    color: #241f52;
}

.assistant-launcher-guide-copy {
    margin-top: 0.22rem;
    font-size: 0.8rem;
    line-height: 1.4;
    color: #6d6795;
}

[class*="st-key-assistant-launcher-guide-action-"] .stButton > button {
    width: 2.4rem !important;
    min-width: 2.4rem !important;
    height: 2.4rem !important;
    min-height: 2.4rem !important;
    padding: 0 !important;
    border-radius: 999px !important;
    border: none !important;
    background: rgba(123, 97, 255, 0.12) !important;
    color: #5a4b97 !important;
    box-shadow: none !important;
    font-size: 1rem !important;
    font-weight: 900 !important;
}

.assistant-launcher-notification-summary {
    padding: 0.95rem 1rem;
    border-radius: 1.2rem;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.97) 0%, rgba(244, 239, 255, 0.94) 100%),
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.12), transparent 42%);
    box-shadow: 0 14px 28px rgba(96, 74, 180, 0.07);
}

.assistant-launcher-notification-summary-title {
    margin-top: 0.28rem;
    font-size: 1rem;
    line-height: 1.2;
    font-weight: 900;
    color: #2a2459;
}

.assistant-launcher-notification-summary-copy {
    margin-top: 0.22rem;
    font-size: 0.8rem;
    line-height: 1.4;
    color: #6e6796;
}

.st-key-assistant-launcher-notification-feed [data-testid="stVerticalBlock"] {
    gap: 0.7rem !important;
}

.assistant-launcher-notification-card {
    padding: 0.92rem 0.95rem;
    border-radius: 1.15rem;
    border: 1px solid rgba(123, 97, 255, 0.09);
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 10px 20px rgba(96, 74, 180, 0.05);
}

.assistant-launcher-notification-card-topline {
    font-size: 0.68rem;
    line-height: 1.15;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9189ba;
}

.assistant-launcher-notification-title {
    margin-top: 0.28rem;
    font-size: 0.9rem;
    line-height: 1.25;
    font-weight: 900;
    color: #241f52;
}

.assistant-launcher-notification-meta {
    margin-top: 0.18rem;
    font-size: 0.76rem;
    line-height: 1.36;
    color: #726b9d;
}

.assistant-launcher-notification-note {
    margin-top: 0.34rem;
    font-size: 0.79rem;
    line-height: 1.38;
    color: #625c89;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.assistant-launcher-empty-state {
    padding: 1rem;
    border-radius: 1.25rem;
    border: 1px dashed rgba(123, 97, 255, 0.18);
    background: rgba(255, 255, 255, 0.78);
}

.assistant-launcher-empty-state-centered {
    min-height: 15rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
}

.assistant-launcher-empty-icon {
    width: 3rem;
    height: 3rem;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(123, 97, 255, 0.10);
    color: #5a4d95;
    font-size: 1.1rem;
    font-weight: 900;
}

.assistant-launcher-empty-title {
    margin-top: 0.75rem;
    font-size: 0.92rem;
    line-height: 1.2;
    font-weight: 900;
    color: #272255;
}

.assistant-launcher-empty-copy {
    margin-top: 0.28rem;
    font-size: 0.8rem;
    line-height: 1.45;
    color: #6f6998;
}

.assistant-launcher-inline-link {
    color: #6f56f6;
    text-decoration: none;
    font-weight: 800;
}

.assistant-launcher-inline-link:hover {
    text-decoration: underline;
}

@media (max-width: 960px) {
    .st-key-assistant-launcher-card-shell {
        right: calc(env(safe-area-inset-right, 0px) + 0.5rem) !important;
        left: calc(env(safe-area-inset-left, 0px) + 0.5rem) !important;
        width: auto !important;
        max-width: none !important;
    }

    .st-key-assistant-launcher-mobile-shell [data-testid="stVerticalBlockBorderWrapper"] {
        height: min(var(--launcher-shell-height), calc(100vh - 5.25rem)) !important;
        border-radius: 1.7rem !important;
    }

    .st-key-assistant-launcher-mobile-header {
        padding: 0.95rem 0.9rem 0.8rem;
    }

    .st-key-assistant-launcher-mobile-body [data-testid="stVerticalBlock"] {
        padding: 0.9rem 0.9rem 0.8rem !important;
    }

    .st-key-assistant-launcher-mobile-tabbar {
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
}
"""
