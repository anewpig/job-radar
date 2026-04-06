"""提供職缺總覽頁卡片外框的 CSS 片段。"""

OVERVIEW_STYLES = """
.st-key-overview-shell,
.st-key-resume-shell,
.st-key-assistant-shell,
.st-key-tasks-shell,
.st-key-skills-shell,
.st-key-sources-shell,
.st-key-tracking-shell,
.st-key-board-shell {
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

.st-key-export-shell,
.st-key-notifications-shell,
.st-key-database-shell {
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

.st-key-overview-shell::before,
.st-key-resume-shell::before,
.st-key-assistant-shell::before,
.st-key-tasks-shell::before,
.st-key-skills-shell::before,
.st-key-sources-shell::before,
.st-key-tracking-shell::before,
.st-key-board-shell::before {
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

.st-key-export-shell::before,
.st-key-notifications-shell::before,
.st-key-database-shell::before {
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

.st-key-overview-shell::after,
.st-key-resume-shell::after,
.st-key-assistant-shell::after,
.st-key-tasks-shell::after,
.st-key-skills-shell::after,
.st-key-sources-shell::after,
.st-key-tracking-shell::after,
.st-key-board-shell::after {
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

.st-key-export-shell::after,
.st-key-notifications-shell::after,
.st-key-database-shell::after {
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

.overview-intro {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--surface-content-gap);
    text-align: left;
    margin: 0 0 var(--space-1);
    padding: 0 var(--surface-content-inline) 0 var(--surface-content-inline-wide);
}

.overview-intro .section-kicker,
.overview-intro .section-title {
    text-align: left;
}

.overview-intro .section-title {
    margin-top: var(--space-1);
}

.overview-updated-at {
    padding-top: var(--space-1);
    text-align: right;
    font-size: 0.84rem;
    line-height: 1.45;
    color: #7a7498;
    font-weight: 600;
    white-space: nowrap;
}

.st-key-overview-body {
    padding-left: var(--surface-content-inline-wide);
    padding-right: var(--surface-content-inline);
    padding-bottom: var(--space-1);
}

.st-key-overview-body [data-testid="stVerticalBlock"] {
    gap: var(--surface-content-gap);
}

.overview-status-banner {
    margin-bottom: var(--space-1);
    padding: var(--space-3) var(--space-4);
    border-radius: 18px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(180deg, rgba(239, 244, 255, 0.98) 0%, rgba(232, 238, 255, 0.96) 100%);
    color: #5c648b;
    font-size: 0.9rem;
    line-height: 1.55;
    font-weight: 600;
}

.st-key-overview-filter-shell {
    margin: 0 0 var(--space-1);
}

.st-key-overview-filter-shell [data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(248,245,255,0.97) 100%);
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    border-radius: 24px !important;
    box-shadow: 0 10px 26px rgba(116, 86, 204, 0.08);
}

.st-key-overview-filter-shell [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: var(--space-4) var(--space-4) var(--space-3) !important;
    gap: var(--surface-content-gap-tight);
}

.st-key-overview-filter-shell [data-testid="stWidgetLabel"] {
    margin-bottom: var(--space-2) !important;
}

.st-key-overview-filter-shell [data-testid="stWidgetLabel"] p {
    font-size: 0.8rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #8a84ab !important;
}

.st-key-overview-filter-shell [data-baseweb="select"] {
    border-radius: 18px !important;
}

.st-key-overview-filter-shell [data-baseweb="select"] > div {
    min-height: var(--control-height) !important;
    border-radius: 18px !important;
    border: 1px solid rgba(123, 97, 255, 0.12) !important;
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(247,242,255,0.96) 100%) !important;
    box-shadow: 0 10px 22px rgba(116, 86, 204, 0.06) !important;
}

.st-key-overview-filter-shell [data-baseweb="select"] input,
.st-key-overview-filter-shell [data-baseweb="select"] span {
    color: #4d4670 !important;
}

.overview-filter-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-3);
    padding-top: var(--space-1);
}

.overview-filter-meta .chip-row {
    gap: var(--space-2);
}

[class*="st-key-overview-job-card-shell-"] {
    margin: 0 0 var(--space-4);
}

[class*="st-key-overview-job-card-shell-"] [data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(248,245,255,0.97) 100%);
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    border-radius: 28px !important;
    box-shadow: 0 14px 30px rgba(116, 86, 204, 0.08);
}

[class*="st-key-overview-job-card-shell-"] [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: var(--space-5) var(--space-5) var(--space-4) !important;
    gap: var(--space-3);
}

.overview-job-card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--surface-content-gap);
}

.overview-job-card-meta {
    margin-top: var(--space-3);
}

.overview-job-card-preview {
    margin-top: var(--space-4);
    padding: var(--space-4);
    border-radius: 20px;
}

.overview-job-card-note,
.overview-job-card-footer-note {
    color: #7a7399;
    font-size: 0.86rem;
    line-height: 1.55;
}

.overview-job-card-note {
    margin-top: var(--space-2);
}

.st-key-overview-scroll-shell,
.st-key-overview-scroll-shell > div,
.st-key-overview-scroll-shell iframe,
.st-key-overview-scroll-shell [data-testid="stElementContainer"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}

.overview-job-card-footer-note {
    padding-top: var(--space-1);
}

.overview-job-card-detail {
    min-height: 100%;
}

[class*="st-key-overview-job-card-shell-"] [data-testid="stExpander"] {
    margin: var(--space-1) 0 0;
    border-radius: 20px;
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(246,242,255,0.95) 100%);
    box-shadow: none;
    padding: var(--space-1) var(--space-2);
}

[class*="st-key-overview-job-card-shell-"] [data-testid="stExpander"] summary p {
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    color: #39336a !important;
}

[class*="st-key-overview-job-card-shell-"] .stButton > button {
    min-height: 2.9rem;
    height: 2.9rem;
}

.overview-chip--priority {
    background: rgba(123, 97, 255, 0.12);
    color: #5845be;
    border-color: rgba(123, 97, 255, 0.18);
}

.overview-chip--warm {
    background: rgba(255, 239, 196, 0.92);
    color: #8a5e00;
    border-color: rgba(234, 190, 78, 0.24);
}

.overview-chip--link {
    background: rgba(242, 239, 255, 0.98);
    color: #5644bc;
    border-color: rgba(123, 97, 255, 0.18);
}

.st-key-resume-body,
.st-key-assistant-body,
.st-key-tasks-body,
.st-key-skills-body,
.st-key-sources-body,
.st-key-tracking-body,
.st-key-board-body,
.st-key-database-body {
    padding-left: var(--surface-content-inline);
    padding-right: var(--surface-content-inline);
    padding-bottom: var(--space-1);
}

.st-key-assistant-profile-card-shell,
.st-key-assistant-quick-ask-card-shell {
    position: relative;
}

.st-key-assistant-profile-card-shell [data-testid="stVerticalBlockBorderWrapper"],
.st-key-assistant-quick-ask-card-shell [data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: calc(var(--surface-radius-lg) + 2px) !important;
    border: 1px solid rgba(123, 97, 255, 0.12) !important;
    background:
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.10), transparent 26%),
        rgba(255, 255, 255, 0.92) !important;
    box-shadow: 0 18px 44px rgba(90, 76, 167, 0.08) !important;
}

.st-key-assistant-profile-card-shell [data-testid="stVerticalBlockBorderWrapper"] > div,
.st-key-assistant-quick-ask-card-shell [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: var(--space-4) var(--space-4) var(--space-4) !important;
}

.st-key-assistant-profile-card-shell [data-testid="stVerticalBlock"],
.st-key-assistant-quick-ask-card-shell [data-testid="stVerticalBlock"] {
    gap: var(--space-3);
}

.export-intro {
    text-align: left;
    margin: 0 0 var(--space-1);
    padding: 0 var(--space-5);
}

.export-intro .section-kicker,
.export-intro .section-title,
.export-intro .section-desc {
    text-align: left;
}

.export-intro .section-title {
    margin-top: var(--space-1);
}

.export-intro .section-desc {
    max-width: 40rem;
    margin: var(--space-2) 0 0;
}

.st-key-export-body {
    padding-left: var(--space-5);
    padding-right: var(--space-5);
    padding-bottom: 0;
}

.st-key-export-body [data-testid="stVerticalBlock"] {
    gap: var(--space-2);
}

.st-key-export-body [data-testid="stExpander"] {
    margin-bottom: var(--space-1);
}

.notifications-intro {
    text-align: left;
    margin: 0 0 var(--space-1);
    padding: 0 var(--space-5);
}

.notifications-intro .section-kicker,
.notifications-intro .section-title,
.notifications-intro .section-desc {
    text-align: left;
}

.notifications-intro .section-title {
    margin-top: var(--space-1);
}

.notifications-intro .section-desc {
    max-width: 40rem;
    margin: var(--space-2) 0 0;
}

.st-key-notifications-body {
    padding-left: var(--space-5);
    padding-right: var(--space-5);
    padding-bottom: var(--space-1);
}

#overview-top-anchor {
    scroll-margin-top: calc(var(--sticky-nav-top) + var(--space-10));
}

.st-key-overview-pagination-shell {
    margin: var(--surface-content-gap) 0 var(--space-1);
}

.st-key-overview-pagination-shell [data-testid="stHorizontalBlock"] {
    align-items: center;
}

.st-key-overview-pagination-shell .stButton > button {
    min-width: 2.7rem;
    min-height: 2.7rem;
    height: 2.7rem;
    border-radius: 999px;
    border: none;
    background: transparent;
    box-shadow: none;
    color: #2b2750;
    font-size: 1rem;
    font-weight: 700;
    padding: var(--space-1);
}

.st-key-overview-pagination-shell .stButton > button:hover {
    border: none;
    background: rgba(31, 27, 77, 0.05);
    box-shadow: none;
    color: #1f1b4d;
}

.st-key-overview-pagination-shell .stButton > button[kind="primary"] {
    border: none;
    background: rgba(31, 27, 77, 0.08);
    box-shadow: none;
    color: #1f1b4d;
}

.st-key-overview-pagination-shell .stButton > button[kind="primary"]:hover {
    border: none;
    background: rgba(31, 27, 77, 0.08);
    box-shadow: none;
    color: #1f1b4d;
}

.overview-pagination-ellipsis {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 2.7rem;
    color: #756f97;
    font-weight: 700;
    letter-spacing: 0.12em;
}
"""
