"""提供搜尋設定卡片外框的 CSS 片段。"""

SEARCH_SETUP_STYLES = """
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
    font-size: 0.9rem;
    font-weight: 800;
    color: #2b2750;
    letter-spacing: 0.015em;
}

.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"],
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"] {
    width: 100%;
}

.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"] [role="radiogroup"],
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"] [role="radiogroup"] {
    min-height: var(--control-height) !important;
    height: var(--control-height) !important;
    width: 100%;
    display: grid !important;
    align-items: stretch !important;
    gap: 0.22rem !important;
    padding: 0.18rem !important;
    border-radius: 999px !important;
    border: 1px solid rgba(123, 97, 255, 0.16) !important;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(252, 250, 255, 0.96) 100%) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 10px 24px rgba(123, 97, 255, 0.06) !important;
    transition: border-color 180ms ease, box-shadow 180ms ease !important;
}

.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"] [role="radiogroup"]:hover,
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"] [role="radiogroup"]:hover {
    border-color: rgba(123, 97, 255, 0.24) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.82), 0 12px 26px rgba(123, 97, 255, 0.09) !important;
}

.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"]:focus-within [role="radiogroup"],
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"]:focus-within [role="radiogroup"] {
    border-color: rgba(123, 97, 255, 0.34) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.84), 0 0 0 4px rgba(123, 97, 255, 0.08), 0 14px 28px rgba(123, 97, 255, 0.1) !important;
}

.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"] button,
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"] button {
    min-height: calc(var(--control-height) - 0.36rem) !important;
    height: calc(var(--control-height) - 0.36rem) !important;
    padding: 0 0.9rem !important;
    border-radius: calc(var(--control-radius) - 0.18rem) !important;
    border: none !important;
    background: transparent !important;
    color: var(--control-text) !important;
    font-weight: 700 !important;
    font-size: 0.98rem !important;
    letter-spacing: 0.01em;
    white-space: nowrap !important;
    box-shadow: none !important;
    transition: background-color 180ms ease, color 180ms ease, box-shadow 180ms ease !important;
}

.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"] button:hover,
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"] button:hover {
    background: rgba(123, 97, 255, 0.06) !important;
}

.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"] [aria-checked="true"],
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"] [aria-checked="true"],
.st-key-crawl-preset-control-shell [data-testid="stSegmentedControl"] button[kind="primary"],
.st-key-crawl-refresh-control-shell [data-testid="stSegmentedControl"] button[kind="primary"] {
    background: linear-gradient(180deg, rgba(123, 97, 255, 0.16) 0%, rgba(123, 97, 255, 0.1) 100%) !important;
    color: #312c63 !important;
    box-shadow: inset 0 0 0 1px rgba(123, 97, 255, 0.14) !important;
}

.st-key-search-setup-body [data-testid="stPopover"] > button {
    min-width: 10rem;
    min-height: var(--control-height);
    height: var(--control-height);
    padding: 0.08rem var(--control-padding-inline);
    border-radius: var(--control-radius) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    line-height: 1 !important;
    white-space: nowrap;
}

.st-key-search-setup-run-shell {
    height: 100%;
    display: flex;
    align-items: center;
}

.st-key-search-setup-run-shell .stButton > button {
    min-width: 10.8rem;
    min-height: var(--control-height);
    height: var(--control-height);
    padding: 0 var(--control-padding-inline);
    border-radius: var(--control-radius) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    line-height: 1 !important;
    border: none !important;
    background: var(--control-primary-bg) !important;
    color: #ffffff !important;
    box-shadow: var(--control-primary-shadow) !important;
    font-weight: 700;
    white-space: nowrap;
}

.st-key-search-setup-run-shell .stButton > button:hover {
    border: none !important;
    background: var(--control-primary-hover-bg) !important;
    color: #ffffff !important;
    box-shadow: 0 18px 30px rgba(123, 97, 255, 0.22) !important;
}

.st-key-search-setup-shell,
[data-testid="stAppViewContainer"] > .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"]:first-of-type {
    position: relative;
    overflow: hidden;
    width: var(--shared-surface-width);
    max-width: var(--shared-surface-width);
    box-sizing: border-box;
    margin-left: auto;
    margin-right: auto;
    margin-bottom: var(--surface-stack-gap);
    border-radius: var(--surface-radius-xl) !important;
    border: 1px solid var(--surface-primary-border) !important;
    background:
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.18), transparent 22%),
        var(--surface-primary-bg) !important;
    box-shadow: var(--surface-primary-shadow);
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

.search-setup-intro {
    text-align: left;
    margin-top: 0 !important;
    margin-bottom: 0.14rem !important;
}

.search-setup-intro .section-kicker {
    text-align: left;
    font-size: 0.76rem;
    letter-spacing: 0.12em;
    opacity: 0.78;
}

.search-setup-intro .section-title {
    text-align: left;
    margin-top: 0.16rem;
}

.search-setup-intro .section-desc {
    max-width: 29rem;
    margin: 0.34rem 0 0;
    font-size: 0.98rem;
    line-height: 1.55;
    color: rgba(86, 81, 124, 0.88);
    text-align: left;
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

.st-key-search-setup-shell [data-testid="stHorizontalBlock"] {
    align-items: stretch;
}

.st-key-search-setup-shell [data-testid="column"] {
    display: flex;
    align-items: stretch;
}

.st-key-search-setup-shell [data-testid="column"] > div {
    width: 100%;
    height: 100%;
}

.st-key-search-setup-cta {
    height: 100%;
    display: flex;
    justify-content: flex-end;
    padding-right: 0.8rem;
    box-sizing: border-box;
}

.st-key-search-setup-cta .cta-shell {
    width: 100%;
    max-width: none;
    min-height: 20.6rem;
    margin: 0.35rem 0 0.8rem auto;
    padding: 0.68rem 0.96rem 0.56rem;
    display: flex;
    flex-direction: column;
    border: 1px solid rgba(233, 195, 92, 0.22);
    background: linear-gradient(135deg, #fff6d9 0%, #ffefbf 52%, #ffe3a1 100%);
    box-shadow: 0 18px 34px rgba(220, 183, 92, 0.18);
}

.st-key-search-setup-cta .cta-shell::before {
    content: "";
    position: absolute;
    left: -2.2rem;
    bottom: -2.6rem;
    width: 9rem;
    height: 9rem;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0.10) 48%, transparent 76%);
    pointer-events: none;
}

.st-key-search-setup-cta .cta-shell::after {
    background: radial-gradient(circle, rgba(255,255,255,0.34) 0%, rgba(255,255,255,0.10) 66%, transparent 100%);
}

.st-key-search-setup-cta .cta-kicker {
    font-size: 0.7rem;
    color: rgba(102, 78, 22, 0.72);
    letter-spacing: 0.14em;
}

.st-key-search-setup-cta .cta-title {
    font-size: 1.15rem;
    max-width: none;
    color: #3b2f67;
    text-shadow: 0 1px 0 rgba(255, 255, 255, 0.22);
}

.st-key-search-setup-cta .cta-copy {
    display: block;
    max-width: none;
    margin-top: 0.42rem;
    font-size: 0.9rem;
    line-height: 1.6;
    color: rgba(72, 58, 120, 0.86);
}

.st-key-search-setup-cta .cta-helper-list {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.38rem;
    margin-top: 0.7rem;
    flex: 1 1 auto;
    align-content: stretch;
}

.st-key-search-setup-cta .cta-helper-pill {
    width: 100%;
    max-width: none;
    min-height: 2.1rem;
    height: 100%;
    padding: 0.34rem 0.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    align-self: stretch;
    text-align: center;
    border-radius: 18px;
    border: 1px solid rgba(214, 175, 72, 0.28);
    background: rgba(255, 249, 232, 0.62);
    color: rgba(98, 76, 22, 0.88);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42);
    font-size: 0.72rem;
    font-weight: 700;
    line-height: 1.2;
}

.st-key-search-setup-cta .cta-helper-line {
    display: block;
    white-space: nowrap;
}

.st-key-search-setup-cta .cta-stat-grid {
    margin-top: 0.52rem;
    gap: 0.52rem;
}

.st-key-search-setup-cta .cta-stat-card {
    padding: 0.58rem 0.72rem;
    border-radius: 18px;
    background: rgba(255, 250, 238, 0.52);
    border: 1px solid rgba(214, 175, 72, 0.22);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.32);
}

.st-key-search-setup-cta .cta-stat-label {
    color: rgba(108, 84, 24, 0.72);
}

.st-key-search-setup-cta .cta-stat-value {
    color: #4c3b88;
}

.st-key-search-setup-body {
    padding-left: 1.4rem;
    padding-right: 1.1rem;
    margin-top: 0.04rem;
    display: flex;
    flex-direction: column;
    flex: 1 1 auto;
    height: 100%;
}

.st-key-search-setup-body [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

.st-key-search-setup-body [data-testid="stElementContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}

.search-controls-group-offset {
    height: 0rem;
    flex: 0 0 0rem;
}

.st-key-search-fields-group-shell {
    position: relative;
    overflow: hidden;
    margin-top: 0.42rem;
    border-radius: var(--surface-radius-lg) !important;
    border: 1px solid var(--surface-secondary-border) !important;
    background: var(--surface-secondary-bg) !important;
    box-shadow: var(--surface-primary-shadow);
}

.st-key-search-fields-group-shell [data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    border-radius: var(--surface-radius-lg) !important;
}

.st-key-search-fields-group-shell [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 0.72rem 0.9rem 0.16rem !important;
}

.st-key-search-fields-group-shell [data-testid="stVerticalBlock"] {
    gap: 0.04rem !important;
}

.st-key-search-role-rows-shell {
    margin-top: 0.72rem;
}

.st-key-search-controls-group-shell {
    position: relative;
    overflow: hidden;
    margin-top: 0;
    transform: none;
    border-radius: var(--surface-radius-lg) !important;
    border: 1px solid var(--surface-secondary-border) !important;
    background: var(--surface-secondary-bg) !important;
    box-shadow: var(--surface-primary-shadow);
}

.st-key-search-controls-group-shell [data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    border-radius: 24px !important;
}

.st-key-search-controls-group-shell [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 0.42rem 0.9rem 0.74rem !important;
}

.st-key-search-controls-group-shell [data-testid="stVerticalBlock"] {
    gap: 0.22rem !important;
}

.search-row-header-label {
    margin: 0 0 0.4rem 0;
    font-size: 1.02rem;
    line-height: 1.1;
    font-weight: 800;
    color: #231f58;
}

.search-setup-updated-at {
    margin: 0.45rem 1.12rem 0 0;
    text-align: right;
    font-size: 0.84rem;
    line-height: 1.45;
    color: #7a7498;
    font-weight: 600;
}

[class*="st-key-search-row-role-shell-"] [data-baseweb="base-input"],
[class*="st-key-search-row-keywords-shell-"] [data-baseweb="base-input"] {
    min-height: var(--search-row-control-height) !important;
    height: var(--search-row-control-height) !important;
    display: flex;
    align-items: center;
    overflow: visible !important;
}

[class*="st-key-search-row-role-shell-"] [data-baseweb="base-input"] > div,
[class*="st-key-search-row-keywords-shell-"] [data-baseweb="base-input"] > div {
    min-height: var(--search-row-control-height) !important;
    height: var(--search-row-control-height) !important;
    position: relative !important;
    border-radius: 999px !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    padding-left: var(--control-padding-inline) !important;
    padding-right: var(--control-padding-inline) !important;
    border: 1px solid rgba(123, 97, 255, 0.14) !important;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(252, 250, 255, 0.96) 100%) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 10px 24px rgba(123, 97, 255, 0.06) !important;
}

[class*="st-key-search-row-role-shell-"] input,
[class*="st-key-search-row-keywords-shell-"] input {
    min-height: auto !important;
    height: auto !important;
    box-sizing: border-box !important;
    display: block !important;
    line-height: 1.15 !important;
    padding: 0 0 0 2.05rem !important;
    border: none !important;
    background: transparent !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='rgba(114,108,150,0.55)' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='m20 20-3.5-3.5'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: 0.82rem center !important;
    background-size: 0.92rem 0.92rem !important;
    box-shadow: none !important;
    margin: 0 !important;
    transform: none !important;
    vertical-align: middle !important;
    align-self: center !important;
}

.st-key-search-fields-group-shell input[aria-label="目標職缺"],
.st-key-search-fields-group-shell input[aria-label="關鍵字"] {
    line-height: 1.15 !important;
    padding-top: 0 !important;
    padding-left: 2.05rem !important;
    align-self: center !important;
}

[class*="st-key-search-row-delete-shell-"] .stButton > button,
.st-key-search-row-add-shell .stButton > button,
.st-key-search-row-add-shell-inline .stButton > button {
    min-height: var(--search-row-action-height);
    height: var(--search-row-action-height);
    padding: 0 1.08rem !important;
    border-radius: 999px !important;
    line-height: 1 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    border: 1px solid rgba(123, 97, 255, 0.14) !important;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(252, 250, 255, 0.96) 100%) !important;
    color: var(--control-text) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 10px 24px rgba(123, 97, 255, 0.06) !important;
}

[class*="st-key-search-row-delete-shell-"] [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-end !important;
    row-gap: 0 !important;
    gap: 0 !important;
    min-height: var(--search-row-control-height) !important;
    height: var(--search-row-control-height) !important;
}

.st-key-search-row-add-shell [data-testid="stVerticalBlock"],
.st-key-search-row-add-shell-inline [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-end !important;
    row-gap: 0 !important;
    min-height: var(--search-row-control-height) !important;
}

[class*="st-key-search-row-delete-shell-"] [data-testid="stElementContainer"],
.st-key-search-row-add-shell [data-testid="stElementContainer"],
.st-key-search-row-add-shell-inline [data-testid="stElementContainer"] {
    margin: 0 !important;
}

[class*="st-key-search-row-delete-shell-"] .stButton,
.st-key-search-row-add-shell .stButton,
.st-key-search-row-add-shell-inline .stButton {
    margin: 0 !important;
}

.st-key-search-row-add-shell,
.st-key-search-row-add-shell-inline {
    margin-top: var(--search-row-action-gap) !important;
    transform: translateY(var(--search-row-add-offset));
}

[class*="st-key-search-row-role-shell-"] input::placeholder,
[class*="st-key-search-row-role-shell-"] textarea::placeholder,
[class*="st-key-search-row-keywords-shell-"] input::placeholder,
[class*="st-key-search-row-keywords-shell-"] textarea::placeholder {
    color: rgba(114, 108, 150, 0.52) !important;
    opacity: 1 !important;
    line-height: 1.15 !important;
    position: relative !important;
    top: 0.08rem !important;
}

[class*="st-key-search-row-role-shell-"] input::-webkit-input-placeholder,
[class*="st-key-search-row-role-shell-"] textarea::-webkit-input-placeholder,
[class*="st-key-search-row-keywords-shell-"] input::-webkit-input-placeholder,
[class*="st-key-search-row-keywords-shell-"] textarea::-webkit-input-placeholder {
    color: rgba(114, 108, 150, 0.52) !important;
    opacity: 1 !important;
    line-height: 1.15 !important;
}
"""
