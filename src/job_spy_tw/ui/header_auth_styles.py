"""提供 Header 與 auth dialog 的 CSS 片段。"""

HEADER_AUTH_STYLES = """
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

[data-testid="stDialog"] {
    backdrop-filter: blur(14px);
}

[data-testid="stDialog"] [role="dialog"] {
    border-radius: 32px !important;
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(249,246,255,0.98) 100%) !important;
    box-shadow: 0 34px 80px rgba(31, 27, 77, 0.20) !important;
    overflow: hidden !important;
}

[data-testid="stDialog"] [role="dialog"]:has(.st-key-auth-page-shell) {
    width: min(68rem, calc(100vw - 2rem)) !important;
    max-width: 68rem !important;
}

[data-testid="stDialog"] [role="dialog"]:has(.auth-dialog-shell--account) {
    width: min(31rem, calc(100vw - 2rem)) !important;
    max-width: 31rem !important;
}

[data-testid="stDialog"] [role="dialog"]:has(.st-key-auth-page-shell) [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

.st-key-auth-page-shell {
    position: relative;
    padding: 0.35rem 0.2rem 0.25rem;
}

.st-key-auth-page-shell::before {
    content: "";
    position: absolute;
    left: 1.2rem;
    top: 1rem;
    width: 15rem;
    height: 15rem;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(255, 215, 126, 0.18) 0%, rgba(255, 215, 126, 0.02) 72%, transparent 100%);
    pointer-events: none;
}

.st-key-auth-page-shell::after {
    content: "";
    position: absolute;
    right: 1.2rem;
    bottom: 1rem;
    width: 17rem;
    height: 17rem;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123, 97, 255, 0.14) 0%, rgba(123, 97, 255, 0.02) 74%, transparent 100%);
    pointer-events: none;
}

.st-key-auth-page-shell [data-testid="stHorizontalBlock"] {
    align-items: stretch;
    gap: var(--space-4) !important;
}

.st-key-auth-page-brand-shell,
.st-key-auth-page-form-shell {
    position: relative;
    z-index: 1;
}

.st-key-auth-page-brand-shell > div,
.st-key-auth-page-form-shell > div {
    height: 100%;
    padding: 1.45rem;
    border-radius: 28px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    box-shadow: 0 20px 42px rgba(88, 72, 160, 0.10);
}

.st-key-auth-page-brand-shell > div {
    background:
        radial-gradient(circle at top left, rgba(255, 215, 126, 0.22), transparent 34%),
        linear-gradient(135deg, rgba(255,255,255,0.96) 0%, rgba(247,242,255,0.92) 62%, rgba(242,236,255,0.96) 100%);
}

.st-key-auth-page-form-shell > div {
    background: linear-gradient(180deg, rgba(255,255,255,0.995) 0%, rgba(251,249,255,0.99) 100%);
}

.auth-page-pane,
.auth-dialog-shell {
    position: relative;
}

.auth-page-kicker,
.auth-pane-kicker {
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-weight: 800;
    color: var(--accent);
}

.auth-page-brand-row,
.auth-dialog-brand {
    display: flex;
    align-items: center;
    gap: var(--space-3);
}

.auth-page-brand-row {
    margin-top: var(--space-3);
}

.auth-dialog-logo {
    width: 3.2rem;
    height: 3.2rem;
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6f56f6 0%, #7b61ff 55%, #9672ff 100%);
    color: #ffffff;
    font-size: 1rem;
    font-weight: 900;
    box-shadow: 0 16px 28px rgba(123, 97, 255, 0.22);
    flex-shrink: 0;
}

.auth-page-title,
.auth-dialog-title {
    font-size: 2.02rem;
    line-height: 1.08;
    font-weight: 900;
    color: var(--text);
}

.auth-page-subtitle,
.auth-dialog-subtitle {
    margin-top: 0.18rem;
    color: #6f6990;
    font-size: 0.96rem;
    line-height: 1.45;
    font-weight: 700;
}

.auth-page-copy,
.auth-pane-copy,
.auth-account-copy {
    margin-top: var(--space-3);
    color: #645d85;
    font-size: 0.95rem;
    line-height: 1.75;
}

.auth-page-trust-row,
.auth-account-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-top: var(--space-4);
}

.auth-page-trust-pill,
.auth-account-pill {
    display: inline-flex;
    align-items: center;
    min-height: 2rem;
    padding: 0 0.78rem;
    border-radius: 999px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: rgba(255,255,255,0.72);
    color: #534a82;
    font-size: 0.82rem;
    font-weight: 700;
}

.st-key-dialog-google-login-shell,
.st-key-dialog-facebook-login-shell {
    margin-top: var(--space-3);
}

.auth-social-card {
    padding: 1rem 1rem 0.88rem;
    border-radius: 22px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: rgba(255,255,255,0.82);
    box-shadow: 0 14px 28px rgba(88, 72, 160, 0.08);
}

.auth-social-title {
    font-size: 1rem;
    line-height: 1.35;
    font-weight: 800;
    color: var(--text);
}

.auth-social-desc {
    margin-top: 0.28rem;
    color: #6d668d;
    font-size: 0.88rem;
    line-height: 1.6;
}

.st-key-dialog-google-login-shell .stButton,
.st-key-dialog-facebook-login-shell .stButton {
    margin-top: 0.78rem;
}

.st-key-dialog-google-login-shell .stButton > button,
.st-key-dialog-facebook-login-shell .stButton > button {
    min-height: 3.15rem;
    border-radius: 18px;
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(247,242,255,0.96) 100%);
    border: 1px solid rgba(123, 97, 255, 0.14);
    color: #463a86;
    box-shadow: 0 12px 24px rgba(116, 86, 204, 0.08);
}

.st-key-dialog-google-login-shell .stButton > button:disabled,
.st-key-dialog-facebook-login-shell .stButton > button:disabled {
    opacity: 0.62;
    box-shadow: none;
}

.auth-pane-title {
    margin-top: var(--space-2);
    font-size: 1.34rem;
    line-height: 1.24;
    font-weight: 850;
    color: var(--text);
}

.auth-feedback {
    margin: var(--space-3) 0 0;
    padding: 0.92rem 1rem;
    border-radius: 18px;
    font-size: 0.9rem;
    line-height: 1.6;
    font-weight: 700;
}

.auth-feedback--error {
    border: 1px solid rgba(226, 83, 103, 0.18);
    background: rgba(255, 241, 244, 0.96);
    color: #a53a4d;
}

.auth-feedback--success {
    border: 1px solid rgba(62, 157, 104, 0.18);
    background: rgba(239, 251, 244, 0.96);
    color: #2b7c52;
}

.auth-form-label {
    margin-top: var(--space-3);
    font-size: 0.82rem;
    line-height: 1.3;
    font-weight: 800;
    color: #585078;
}

.st-key-auth-page-form-shell form {
    margin-top: var(--space-2);
}

.st-key-auth-page-form-shell [data-testid="stTextInput"] {
    margin-top: 0.34rem;
}

[data-testid="stDialog"] [role="dialog"]:has(.st-key-auth-page-shell) .stTextInput input,
[data-testid="stDialog"] [role="dialog"]:has(.st-key-auth-page-shell) [data-baseweb="base-input"] input {
    min-height: 3.15rem;
    border-radius: 18px !important;
    border: 1px solid rgba(123, 97, 255, 0.14) !important;
    background: rgba(255, 255, 255, 0.98) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.85);
}

[data-testid="stDialog"] [role="dialog"]:has(.st-key-auth-page-shell) .stTextInput input:focus,
[data-testid="stDialog"] [role="dialog"]:has(.st-key-auth-page-shell) [data-baseweb="base-input"] input:focus {
    border-color: rgba(123, 97, 255, 0.28) !important;
    box-shadow: 0 0 0 4px rgba(123, 97, 255, 0.10) !important;
}

.auth-field-error {
    margin-top: 0.38rem;
    color: #b23f56;
    font-size: 0.82rem;
    line-height: 1.45;
    font-weight: 700;
}

.st-key-dialog-auth-tab-login .stButton > button,
.st-key-dialog-auth-tab-register .stButton > button {
    min-height: 3rem;
    border-radius: 18px;
}

.st-key-dialog-open-forgot-password .stButton > button,
.st-key-dialog-switch-register-link .stButton > button,
.st-key-dialog-back-to-login-from-forgot-request .stButton > button,
.st-key-dialog-back-to-login-from-forgot-confirm .stButton > button {
    min-height: 2.8rem;
    border-radius: 16px;
    box-shadow: none;
}

.auth-step-shell {
    margin-top: var(--space-3);
    padding: 1rem 1rem 0.95rem;
    border-radius: 20px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(180deg, rgba(248,245,255,0.96) 0%, rgba(255,255,255,0.92) 100%);
}

.auth-step-kicker {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-weight: 800;
    color: var(--accent);
}

.auth-step-title {
    margin-top: 0.45rem;
    font-size: 1.12rem;
    line-height: 1.3;
    font-weight: 850;
    color: var(--text);
}

.auth-step-copy,
.auth-inline-note {
    margin-top: 0.45rem;
    color: #6c658c;
    font-size: 0.88rem;
    line-height: 1.62;
}

.auth-inline-note--muted {
    padding: 0.82rem 0.9rem;
    border-radius: 16px;
    border: 1px dashed rgba(123, 97, 255, 0.16);
    background: rgba(248, 245, 255, 0.9);
}

.auth-dialog-shell {
    padding: 0.25rem 0.05rem 0.12rem;
}

.auth-dialog-shell--account {
    text-align: left;
}

.auth-dialog-shell--account .auth-dialog-title {
    font-size: 1.55rem;
}

.st-key-dialog-logout-button .stButton {
    margin-top: var(--space-4);
}

.st-key-dialog-logout-button .stButton > button {
    min-height: 3.1rem;
    border-radius: 18px;
}

@media (max-width: 960px) {
    [data-testid="stDialog"] [role="dialog"]:has(.st-key-auth-page-shell) {
        width: min(calc(100vw - 1rem), 42rem) !important;
        max-width: min(calc(100vw - 1rem), 42rem) !important;
    }

    .st-key-auth-page-shell {
        padding: 0.1rem 0 0.1rem;
    }

    .st-key-auth-page-shell [data-testid="stHorizontalBlock"] {
        flex-direction: column;
        align-items: stretch;
        gap: var(--space-3) !important;
    }

    .st-key-auth-page-brand-shell > div,
    .st-key-auth-page-form-shell > div {
        padding: 1.15rem;
    }

    .auth-page-title,
    .auth-dialog-title {
        font-size: 1.68rem;
    }

    .auth-page-trust-row,
    .auth-account-pill-row {
        gap: 0.5rem;
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
"""
