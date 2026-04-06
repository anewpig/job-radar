"""提供浮動 AI 助理啟動器的 CSS 片段。"""

ASSISTANT_LAUNCHER_STYLES = """
.st-key-assistant-launcher-trigger-shell {
    position: fixed;
    right: 1.15rem;
    bottom: 1.15rem;
    z-index: 1002;
    width: auto;
    margin: 0 !important;
    padding: 0 !important;
}

.st-key-assistant-launcher-trigger-shell .stButton > button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.9rem;
    min-width: 2.9rem;
    height: 2.9rem;
    min-height: 2.9rem;
    padding: 0 !important;
    border-radius: 999px !important;
    border: 1px solid var(--control-border);
    background: var(--surface-floating-bg) !important;
    color: var(--control-text) !important;
    font-size: 1.05rem;
    font-weight: 900;
    line-height: 1;
    box-shadow: var(--surface-floating-shadow);
    text-decoration: none;
    cursor: pointer;
}

.st-key-assistant-launcher-trigger-shell .stButton > button:hover,
.st-key-assistant-launcher-trigger-shell .stButton > button:focus {
    border: 1px solid rgba(123, 97, 255, 0.20);
    background: var(--control-hover-bg) !important;
    color: #5f4dd2 !important;
    box-shadow: var(--surface-floating-shadow);
    text-decoration: none;
}

.st-key-assistant-launcher-card-shell {
    position: fixed;
    right: 1.15rem;
    bottom: 5.2rem;
    z-index: 1002;
    width: 25rem;
    margin: 0 !important;
    padding: 0 !important;
    background: var(--surface-floating-bg) !important;
    border-radius: var(--surface-radius-xl) !important;
    overflow: hidden;
}

.st-key-assistant-launcher-card-shell [data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface-floating-bg) !important;
    border-radius: var(--surface-radius-xl) !important;
    border: 1px solid var(--surface-floating-border) !important;
    box-shadow: var(--surface-floating-shadow);
}

.st-key-assistant-launcher-card-shell [data-testid="stVerticalBlock"] {
    gap: 0 !important;
    background: #ffffff !important;
}

.st-key-assistant-launcher-close-top .stButton > button {
    width: 2.6rem;
    min-width: 2.6rem;
    height: 2.6rem;
    min-height: 2.6rem;
    padding: 0 !important;
    border-radius: 999px !important;
    border: none !important;
    background: rgba(255, 255, 255, 0.34) !important;
    color: #4f3408 !important;
    box-shadow: none;
    font-size: 1.15rem;
    font-weight: 800;
}

.st-key-assistant-launcher-form-shell {
    margin: 0 0 0.2rem;
    padding: 0.95rem;
    border-radius: var(--surface-radius-lg);
    background: var(--surface-secondary-bg);
    border: 1px solid var(--surface-secondary-border);
    box-shadow: var(--surface-primary-shadow);
}

.assistant-launcher-form-label {
    font-size: 0.98rem;
    line-height: 1.3;
    font-weight: 800;
    color: #24342a;
}

.st-key-assistant-launcher-form-shell [data-testid="stTextInput"] {
    margin-top: 0.65rem;
}

.st-key-assistant-launcher-form-shell input {
    border-radius: var(--control-radius) !important;
    border: 1px solid var(--control-border) !important;
    background: var(--control-bg) !important;
}

.st-key-assistant-launcher-form-shell [data-testid="stHorizontalBlock"] {
    gap: 0.55rem;
    margin-top: 0.7rem;
}

.assistant-launcher-faq-item {
    display: flex;
    align-items: center;
    min-height: 2.9rem;
    color: #314339;
    font-size: 0.98rem;
    font-weight: 700;
    border-top: 1px solid rgba(180, 133, 32, 0.12);
}

.st-key-assistant-launcher-form-shell [data-testid="stHorizontalBlock"] + [data-testid="stHorizontalBlock"] {
    margin-top: 0;
}

.st-key-assistant-launcher-form-shell .stButton > button[kind="primary"] {
    background: var(--control-primary-bg) !important;
    box-shadow: var(--control-primary-shadow);
}

.st-key-assistant-launcher-form-shell .stButton > button {
    min-height: var(--control-height);
    border-radius: var(--control-radius);
}

.st-key-assistant-launcher-faq-1 .stButton > button,
.st-key-assistant-launcher-faq-2 .stButton > button {
    min-width: 2.4rem;
    width: 2.4rem;
    height: 2.4rem;
    min-height: 2.4rem;
    padding: 0 !important;
    border-radius: 999px !important;
    background: rgba(237, 196, 82, 0.16) !important;
    border: none !important;
    box-shadow: none;
    color: #9a6e17 !important;
    font-size: 1.2rem;
    font-weight: 900;
}
"""
