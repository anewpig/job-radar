"""提供搜尋設定區塊的 CSS 片段。"""

SEARCH_SETUP_STYLES = """
.st-key-search-setup-shell {
    position: relative;
    overflow: hidden;
    isolation: isolate;
    width: 100%;
    border-radius: 28px !important;
    border: 1px solid rgba(123, 97, 255, 0.08) !important;
    background:
        linear-gradient(128deg, transparent 0 76.8%, rgba(255, 255, 255, 0.32) 77%, rgba(255, 255, 255, 0.32) 77.24%, transparent 77.46%) top right / 18rem 9rem no-repeat,
        linear-gradient(146deg, transparent 0 68.8%, rgba(255, 255, 255, 0.26) 69%, rgba(255, 255, 255, 0.26) 69.22%, transparent 69.44%) top right / 20rem 11rem no-repeat,
        linear-gradient(112deg, transparent 0 61.8%, rgba(255, 255, 255, 0.22) 62%, rgba(255, 255, 255, 0.22) 62.2%, transparent 62.42%) top right / 16rem 8rem no-repeat,
        linear-gradient(138deg, transparent 0 54.8%, rgba(255, 255, 255, 0.18) 55%, rgba(255, 255, 255, 0.18) 55.18%, transparent 55.38%) top right / 22rem 12rem no-repeat,
        linear-gradient(135deg, transparent 0 82.8%, rgba(255, 215, 126, 0.14) 83%, rgba(255, 215, 126, 0.14) 83.35%, transparent 83.55%) top right / 15rem 9rem no-repeat,
        linear-gradient(135deg, transparent 0 72.8%, rgba(255, 215, 126, 0.11) 73%, rgba(255, 215, 126, 0.11) 73.3%, transparent 73.5%) top right / 17rem 10.5rem no-repeat,
        repeating-linear-gradient(118deg, transparent 0 20px, rgba(123, 97, 255, 0.028) 20px 21px, transparent 21px 44px) top right / 24rem 13rem no-repeat,
        repeating-linear-gradient(90deg, transparent 0 34px, rgba(255, 215, 126, 0.024) 34px 35px, transparent 35px 68px) top right / 16rem 10rem no-repeat,
        radial-gradient(circle at 12% 14%, rgba(123, 97, 255, 0.07) 0%, rgba(123, 97, 255, 0.018) 18%, transparent 34%),
        radial-gradient(circle at 72% 18%, rgba(255, 215, 126, 0.14) 0%, rgba(255, 215, 126, 0.032) 20%, transparent 38%),
        radial-gradient(circle at 92% 12%, rgba(255, 215, 126, 0.08) 0%, rgba(255, 215, 126, 0.018) 20%, transparent 34%),
        repeating-linear-gradient(118deg, transparent 0 26px, rgba(123, 97, 255, 0.018) 26px 27px, transparent 27px 60px),
        linear-gradient(180deg, rgba(255,255,255,0.58) 0%, rgba(248,245,255,0.40) 100%),
        linear-gradient(132deg, transparent 0 69%, rgba(123, 97, 255, 0.030) 69.2%, rgba(123, 97, 255, 0.030) 69.55%, transparent 69.9%, transparent 75.2%, rgba(255, 215, 126, 0.026) 75.45%, rgba(255, 215, 126, 0.026) 75.82%, transparent 76.15%) !important;
    box-shadow: 0 8px 18px rgba(116, 86, 204, 0.04);
}

.st-key-search-setup-shell::before {
    content: "";
    position: absolute;
    right: -28px;
    top: -24px;
    width: 132px;
    height: 132px;
    border-radius: 999px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background:
        repeating-linear-gradient(135deg, transparent 0 17px, rgba(123, 97, 255, 0.05) 17px 18px, transparent 18px 36px),
        radial-gradient(circle, rgba(123, 97, 255, 0.10) 0%, rgba(123, 97, 255, 0.020) 52%, transparent 72%);
    box-shadow:
        0 0 0 18px rgba(123, 97, 255, 0.024),
        0 0 0 38px rgba(123, 97, 255, 0.012);
    pointer-events: none;
    opacity: 0.9;
}

.st-key-search-setup-shell::after {
    content: "";
    position: absolute;
    left: -22px;
    bottom: -28px;
    width: 120px;
    height: 120px;
    border-radius: 30px;
    transform: rotate(18deg);
    border: 1px solid rgba(255, 215, 126, 0.16);
    background: linear-gradient(180deg, rgba(255, 215, 126, 0.10) 0%, rgba(255, 255, 255, 0) 100%);
    box-shadow:
        0 0 0 16px rgba(255, 215, 126, 0.020),
        0 0 0 34px rgba(123, 97, 255, 0.010);
    pointer-events: none;
    opacity: 0.82;
}

.st-key-search-setup-shell > div {
    position: relative;
    z-index: 1;
    padding: var(--space-1) var(--space-6) var(--space-6) !important;
}

.search-setup-intro {
    text-align: left;
    margin-top: 0 !important;
    margin-bottom: var(--space-2) !important;
    padding: 0;
}

.search-setup-intro .section-title {
    text-align: left;
    margin-top: var(--space-3);
    font-size: 1.46rem;
    line-height: 1.16;
}

.search-setup-intro .section-kicker {
    text-align: left;
    letter-spacing: 0.12em;
    color: #7b61ff;
}

.search-setup-intro .section-desc {
    max-width: 30rem;
    margin: var(--space-2) 0 0;
    font-size: 0.92rem;
    line-height: 1.6;
    color: rgba(86, 81, 124, 0.88);
    text-align: left;
}

.st-key-search-setup-shell [data-testid="stHorizontalBlock"] {
    align-items: flex-start;
}

.st-key-search-setup-shell [data-testid="column"] {
    display: flex;
}

.st-key-search-setup-shell [data-testid="column"] > div {
    width: 100%;
}

.st-key-search-setup-main {
    display: flex;
    flex-direction: column;
}

.st-key-search-setup-main [data-testid="stVerticalBlock"] {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.st-key-search-setup-cta {
    padding-top: 0;
    display: flex;
    flex-direction: column;
    margin-top: calc(var(--space-4) * -1);
}

.st-key-search-setup-cta [data-testid="stVerticalBlock"] {
    height: auto;
    gap: 0 !important;
}

.st-key-search-setup-body {
    padding-left: 0;
    padding-right: 0;
}

.st-key-search-setup-body [data-testid="stCaptionContainer"] {
    text-align: left;
}

.st-key-search-setup-main-panel {
    position: relative;
    overflow: hidden;
    border-radius: 26px !important;
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    background:
        radial-gradient(circle at 86% 14%, rgba(123, 97, 255, 0.045) 0%, rgba(123, 97, 255, 0.014) 18%, transparent 34%),
        linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(248,245,255,0.97) 100%) !important;
    box-shadow: 0 12px 24px rgba(116, 86, 204, 0.07);
}

.st-key-search-setup-main-panel::before {
    content: "";
    position: absolute;
    right: -4.25rem;
    top: -3rem;
    width: 16rem;
    height: 16rem;
    border-radius: 999px;
    background:
        radial-gradient(circle, transparent 54%, rgba(123, 97, 255, 0.085) 55%, rgba(123, 97, 255, 0.085) 56%, transparent 57%),
        radial-gradient(circle, transparent 69%, rgba(123, 97, 255, 0.058) 70%, rgba(123, 97, 255, 0.058) 71%, transparent 72%),
        radial-gradient(circle, transparent 82%, rgba(255, 215, 126, 0.08) 83%, rgba(255, 215, 126, 0.08) 84%, transparent 85%),
        radial-gradient(circle, rgba(123, 97, 255, 0.085) 0%, rgba(123, 97, 255, 0.022) 32%, transparent 58%);
    opacity: 0.72;
    pointer-events: none;
}

.st-key-search-setup-main-panel::after {
    content: "";
    position: absolute;
    left: -2.5rem;
    bottom: -1.9rem;
    width: 14rem;
    height: 8rem;
    border-radius: 2rem;
    background:
        repeating-linear-gradient(0deg, transparent 0 12px, rgba(123, 97, 255, 0.03) 12px 13px),
        linear-gradient(135deg, rgba(255, 215, 126, 0.085) 0%, rgba(123, 97, 255, 0.02) 52%, transparent 88%);
    transform: rotate(-8deg);
    opacity: 0.5;
    pointer-events: none;
}

.st-key-search-setup-main-panel > div {
    position: relative;
    z-index: 1;
    padding: 0 var(--space-4) var(--space-4) !important;
}

.st-key-search-setup-main-panel [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

.st-key-search-fields-group-shell,
.st-key-search-controls-group-shell {
    width: 100%;
}

.st-key-search-fields-group-shell [data-testid="stVerticalBlock"],
.st-key-search-controls-group-shell [data-testid="stVerticalBlock"] {
    gap: var(--space-2);
}

.st-key-search-fields-group-shell,
.st-key-search-controls-group-shell {
    margin-top: 0;
}

.search-card-head {
    display: block;
    padding: 0;
    position: relative;
    z-index: 2;
    margin-bottom: var(--space-2);
}

.search-card-head-copy {
    min-width: 0;
}

.search-card-title {
    margin-top: 0;
    font-size: 0.82rem;
    line-height: 1.2;
    letter-spacing: 0.02em;
    font-weight: 800;
    color: #7f79a3;
}

.search-card-copy {
    margin-top: var(--space-1);
    max-width: 34rem;
    color: #6f688f;
    font-size: 0.88rem;
    line-height: 1.52;
}

.st-key-search-row-headers-shell {
    position: relative;
    z-index: 2;
    margin-bottom: var(--space-2);
}

.search-row-header-label {
    padding: 0 0 0 var(--space-1);
    font-size: 0.82rem;
    line-height: 1.2;
    letter-spacing: 0.02em;
    font-weight: 800;
    color: #7f79a3;
}

.search-row-header-label--action {
    padding-left: 0;
    text-align: center;
}

.st-key-search-role-rows-shell [data-testid="stVerticalBlock"] {
    gap: var(--space-2);
}

[class*="st-key-search-row-shell-"] {
    padding: var(--space-2);
    border-radius: 22px;
    border: 1px solid rgba(123, 97, 255, 0.12);
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(250,248,255,0.97) 100%);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.84), 0 8px 18px rgba(111, 86, 201, 0.05);
}

[class*="st-key-search-row-shell-"] [data-testid="stHorizontalBlock"] {
    align-items: stretch;
}

.search-row-inline-label {
    display: none;
    margin: 0 0 var(--space-1);
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    color: #857faf;
}

[class*="st-key-search-row-role-shell-"] [data-baseweb="base-input"],
[class*="st-key-search-row-keywords-shell-"] [data-baseweb="base-input"] {
    min-height: 3rem !important;
    border-radius: 16px !important;
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
    align-items: stretch;
}

[class*="st-key-search-row-add-action-shell-"] .stButton > button {
    min-height: 3rem;
    height: 3rem;
    padding-top: 0;
    padding-bottom: 0;
    border-radius: 16px !important;
    line-height: 1;
    border: 1px solid rgba(123, 97, 255, 0.14) !important;
    background: linear-gradient(180deg, rgba(123, 97, 255, 0.10) 0%, rgba(123, 97, 255, 0.06) 100%) !important;
    color: #3f338b !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.72), 0 6px 14px rgba(123, 97, 255, 0.07) !important;
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
    margin-top: var(--space-2) !important;
}

.st-key-search-role-tags-shell [data-testid="stVerticalBlock"] {
    gap: var(--space-3) !important;
}

[class*="st-key-search-role-tag-shell-"] {
    padding: 0;
}

[class*="st-key-search-role-tag-shell-"] [data-testid="stHorizontalBlock"] {
    align-items: flex-start;
}

[class*="st-key-search-role-tag-shell-"] [data-testid="stElementContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}

[class*="st-key-search-role-tag-shell-"] [data-testid="stMarkdownContainer"] {
    width: 100%;
}

.search-role-badge-cluster {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-2);
    padding: 0;
    width: 100%;
}

.search-role-badge-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-1);
    width: 100%;
}

.search-role-badge-row--keywords {
    row-gap: var(--space-2);
}

.search-role-badge-cluster .ui-chip {
    padding: 0.34rem 0.64rem;
    font-size: 0.76rem;
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
    min-height: 2rem;
    border-radius: 12px !important;
    box-shadow: none !important;
    font-weight: 700 !important;
    font-size: 0.76rem !important;
    padding: 0.08rem 0.2rem !important;
}

[class*="st-key-search-role-tag-edit-shell-"] .stButton > button {
    border: 1px solid transparent !important;
    background: transparent !important;
    color: #5547b8 !important;
}

[class*="st-key-search-role-tag-remove-shell-"] .stButton > button {
    border: 1px solid transparent !important;
    background: transparent !important;
    color: #757091 !important;
}

[class*="st-key-search-role-tag-edit-shell-"] .stButton > button:hover,
[class*="st-key-search-role-tag-remove-shell-"] .stButton > button:hover {
    background: rgba(123, 97, 255, 0.05) !important;
    border-color: rgba(123, 97, 255, 0.06) !important;
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
    align-items: stretch;
}

.st-key-crawl-preset-control-shell,
.st-key-crawl-refresh-control-shell {
    position: relative;
}

.st-key-crawl-preset-control-shell [data-testid="stWidgetLabel"],
.st-key-crawl-refresh-control-shell [data-testid="stWidgetLabel"] {
    margin-bottom: var(--space-2);
}

.st-key-crawl-preset-control-shell [data-testid="stWidgetLabel"] p,
.st-key-crawl-refresh-control-shell [data-testid="stWidgetLabel"] p {
    font-size: 0.78rem;
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
    gap: var(--space-1) !important;
    padding: var(--space-1) !important;
    border-radius: 18px !important;
    border: 1px solid rgba(123, 97, 255, 0.12) !important;
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(251,249,255,0.95) 100%) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.82) !important;
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

.st-key-search-setup-run-shell {
    margin-top: var(--space-3);
}

.st-key-search-setup-run-shell .stButton {
    display: flex;
    justify-content: center;
}

.st-key-search-setup-run-shell .stButton > button {
    min-height: 3.18rem;
    border-radius: 18px !important;
    font-size: 0.96rem;
    font-weight: 800;
    box-shadow: 0 12px 20px rgba(123, 97, 255, 0.16) !important;
    width: min(100%, 20rem);
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

@media (max-width: 960px) {
    .search-card-head {
        flex-direction: column;
        align-items: flex-start;
    }

    .st-key-search-setup-main-panel > div {
        padding: var(--space-3) !important;
    }

    .st-key-search-setup-body {
        padding-left: 0;
        padding-right: 0;
    }

    .st-key-search-setup-cta {
        padding-top: var(--space-3);
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

    .st-key-search-setup-run-shell .stButton > button {
        width: 100%;
    }
}
"""
