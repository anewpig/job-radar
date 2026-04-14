"""提供職缺總覽頁的專屬 CSS 片段。"""

OVERVIEW_STYLES = """
.st-key-overview-shell {
    position: relative;
    z-index: 0;
    overflow: hidden;
    isolation: isolate;
    width: var(--shared-surface-width);
    max-width: var(--shared-surface-width);
    box-sizing: border-box;
    margin-left: auto;
    margin-right: auto;
    margin-top: 0;
    margin-bottom: var(--surface-stack-gap);
    border-radius: var(--surface-radius-xl) !important;
    border: 1px solid rgba(123, 97, 255, 0.08) !important;
    background:
        radial-gradient(circle at 85% 16%, rgba(255, 215, 126, 0.16) 0%, rgba(255, 215, 126, 0.04) 18%, transparent 40%),
        radial-gradient(circle at 78% 10%, rgba(123, 97, 255, 0.10) 0%, rgba(123, 97, 255, 0.024) 22%, transparent 44%),
        radial-gradient(circle at 94% 12%, rgba(255, 255, 255, 0.32) 0%, rgba(255, 255, 255, 0.0) 28%, transparent 56%),
        linear-gradient(128deg, transparent 0 71.8%, rgba(255, 255, 255, 0.36) 72%, rgba(255, 255, 255, 0.36) 72.22%, transparent 72.46%) top right / 29rem 13rem no-repeat,
        linear-gradient(142deg, transparent 0 64.8%, rgba(255, 255, 255, 0.26) 65%, rgba(255, 255, 255, 0.26) 65.22%, transparent 65.46%) top right / 26rem 12rem no-repeat,
        linear-gradient(108deg, transparent 0 57.8%, rgba(123, 97, 255, 0.07) 58%, rgba(123, 97, 255, 0.07) 58.18%, transparent 58.36%) top right / 24rem 11rem no-repeat,
        linear-gradient(118deg, transparent 0 69.6%, rgba(255, 215, 126, 0.10) 69.8%, rgba(255, 215, 126, 0.10) 70%, transparent 70.22%) top right / 25rem 11.4rem no-repeat,
        linear-gradient(94deg, transparent 0 68.6%, rgba(255, 255, 255, 0.20) 68.8%, rgba(255, 255, 255, 0.20) 69.02%, transparent 69.26%) top right / 18rem 10rem no-repeat,
        repeating-linear-gradient(132deg, transparent 0 28px, rgba(255,255,255,0.18) 28px 29px, transparent 29px 58px) top right / 28rem 13rem no-repeat,
        repeating-linear-gradient(116deg, transparent 0 34px, rgba(123,97,255,0.035) 34px 35px, transparent 35px 68px) top right / 26rem 12rem no-repeat,
        linear-gradient(126deg, transparent 0 75.2%, rgba(255, 255, 255, 0.28) 75.4%, rgba(255, 255, 255, 0.28) 75.68%, transparent 75.96%) top right / 24rem 11rem no-repeat,
        repeating-linear-gradient(118deg, transparent 0 26px, rgba(123, 97, 255, 0.018) 26px 27px, transparent 27px 60px),
        linear-gradient(180deg, rgba(255,255,255,0.58) 0%, rgba(248,245,255,0.42) 100%) !important;
    box-shadow: 0 10px 22px rgba(116, 86, 204, 0.05);
}

.st-key-overview-shell::before {
    content: "";
    position: absolute;
    right: -3rem;
    top: -2.8rem;
    width: 15rem;
    height: 15rem;
    border-radius: 999px;
    background:
        linear-gradient(132deg, transparent 0 57%, rgba(255,255,255,0.32) 57.2%, rgba(255,255,255,0.32) 57.42%, transparent 57.66%),
        linear-gradient(92deg, transparent 0 64%, rgba(255,255,255,0.20) 64.2%, rgba(255,255,255,0.20) 64.42%, transparent 64.66%),
        linear-gradient(118deg, transparent 0 68%, rgba(123,97,255,0.06) 68.2%, rgba(123,97,255,0.06) 68.4%, transparent 68.64%),
        linear-gradient(148deg, transparent 0 58%, rgba(255,215,126,0.14) 58.2%, rgba(255,215,126,0.14) 58.42%, transparent 58.66%),
        repeating-linear-gradient(130deg, transparent 0 20px, rgba(255,255,255,0.18) 20px 21px, transparent 21px 42px),
        repeating-linear-gradient(114deg, transparent 0 30px, rgba(123,97,255,0.045) 30px 31px, transparent 31px 58px),
        radial-gradient(circle, rgba(255, 215, 126, 0.14) 0%, rgba(255, 215, 126, 0.04) 34%, transparent 60%),
        radial-gradient(circle, rgba(123, 97, 255, 0.10) 0%, rgba(123, 97, 255, 0.02) 42%, transparent 72%);
    pointer-events: none;
    opacity: 0.9;
}

.st-key-overview-shell::after {
    content: "";
    position: absolute;
    left: -2.8rem;
    bottom: -3rem;
    width: 10rem;
    height: 10rem;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123, 97, 255, 0.10) 0%, rgba(123, 97, 255, 0.02) 56%, transparent 76%);
    pointer-events: none;
    opacity: 0.74;
}

.st-key-overview-shell > div {
    position: relative;
    z-index: 0;
}

.overview-intro {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: var(--space-4);
    margin: 0 0 var(--space-4);
    padding: 0 var(--surface-content-inline);
}

.overview-intro-main {
    flex: 1 1 auto;
    max-width: 42rem;
}

.overview-intro .section-kicker,
.overview-intro .section-title {
    text-align: left;
}

.overview-intro .section-title {
    margin-top: var(--space-2);
}

.overview-intro-desc {
    margin-top: var(--space-2);
    margin-left: 0;
    padding-left: 0;
    font-size: 0.96rem;
    line-height: 1.6;
    color: #716b95;
    font-weight: 600;
    text-align: left;
    align-self: flex-start;
}

.overview-intro-stats {
    display: flex;
    align-items: stretch;
    justify-content: flex-end;
    gap: var(--space-3);
    flex: 0 0 auto;
}

.overview-intro-stat {
    min-width: 8.8rem;
    padding: var(--space-3);
    border-radius: 20px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(247,243,255,0.95) 100%);
    box-shadow: 0 8px 18px rgba(116, 86, 204, 0.05);
}

.overview-intro-stat-label {
    font-size: 0.75rem;
    line-height: 1.2;
    font-weight: 800;
    letter-spacing: 0.04em;
    color: #8d86ae;
}

.overview-intro-stat-value {
    margin-top: var(--space-2);
    font-size: 1.2rem;
    line-height: 1.1;
    font-weight: 800;
    color: #221c56;
}

.st-key-overview-body {
    padding: 0 var(--surface-content-inline) var(--space-6);
}

.st-key-overview-body [data-testid="stVerticalBlock"] {
    gap: 0;
}

.st-key-overview-filter-shell {
    margin: 0;
}

.st-key-overview-filter-shell [data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,245,255,0.92) 100%);
    border: 1px solid rgba(123, 97, 255, 0.08) !important;
    border-radius: 22px !important;
    box-shadow: 0 8px 18px rgba(116, 86, 204, 0.04);
}

.st-key-overview-filter-shell [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: var(--space-3) var(--space-3) !important;
    gap: 0;
}

.st-key-overview-filter-shell [data-testid="stHorizontalBlock"] {
    align-items: flex-end;
}

.st-key-overview-filter-shell [data-testid="stWidgetLabel"] {
    margin-bottom: var(--space-2) !important;
}

.st-key-overview-filter-shell [data-testid="stWidgetLabel"] p {
    font-size: 0.8rem !important;
    line-height: 1.2 !important;
    font-weight: 800 !important;
    letter-spacing: 0.02em;
    text-transform: none;
    color: #7e789f !important;
}

.st-key-overview-filter-shell [data-baseweb="select"] {
    border-radius: 18px !important;
}

.st-key-overview-filter-shell [data-baseweb="select"] > div {
    min-height: calc(var(--control-height) - 0.18rem) !important;
    border-radius: 18px !important;
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(247,242,255,0.94) 100%) !important;
    box-shadow: none !important;
}

.st-key-overview-filter-shell [data-baseweb="select"] input,
.st-key-overview-filter-shell [data-baseweb="select"] span {
    color: #433b73 !important;
}

.st-key-overview-filter-shell .stButton > button {
    min-height: calc(var(--control-height) - 0.18rem);
    height: calc(var(--control-height) - 0.18rem);
    border-radius: 18px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: rgba(255, 255, 255, 0.58);
    box-shadow: none;
    color: #5a5380;
    font-weight: 700;
}

.st-key-overview-filter-shell .stButton > button:hover {
    border-color: rgba(123, 97, 255, 0.18);
    background: rgba(244, 241, 255, 0.9);
    box-shadow: none;
}

.overview-filter-meta {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: var(--space-2);
    margin-top: var(--space-2);
}

.overview-filter-meta .chip-row {
    gap: var(--space-2);
}

[class*="st-key-overview-job-card-shell-"] {
    margin: var(--space-3) 0 0;
}

[class*="st-key-overview-job-card-shell-"] [data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(249,247,255,0.95) 100%);
    border: 1px solid rgba(123, 97, 255, 0.08) !important;
    border-radius: 24px !important;
    box-shadow: 0 10px 22px rgba(116, 86, 204, 0.05);
}

[class*="st-key-overview-job-card-shell-"] [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: var(--space-4) var(--space-4) !important;
    gap: var(--space-3);
}

.overview-job-card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--space-3);
}

.overview-job-card-header-main {
    min-width: 0;
    flex: 1 1 auto;
}

.overview-job-card-score {
    flex: 0 0 auto;
    min-width: 4.8rem;
    padding: 0.75rem 0.9rem;
    border-radius: 18px;
    border: 1px solid rgba(123, 97, 255, 0.12);
    background: rgba(243, 238, 255, 0.94);
    text-align: center;
}

.overview-job-card-score span {
    display: block;
    font-size: 0.74rem;
    line-height: 1.1;
    font-weight: 800;
    letter-spacing: 0.04em;
    color: #877fb0;
}

.overview-job-card-score strong {
    display: block;
    margin-top: 0.32rem;
    font-size: 1.08rem;
    line-height: 1.1;
    font-weight: 800;
    color: #4d3eb3;
}

.overview-job-card-meta {
    margin-top: var(--space-2);
    gap: var(--space-2);
}

.overview-job-card-preview {
    margin-top: var(--space-2);
    padding: var(--space-3);
    border-radius: 18px;
    background: linear-gradient(180deg, rgba(247, 243, 255, 0.76) 0%, rgba(255, 255, 255, 0.68) 100%);
}

.overview-job-card-preview .job-card-list {
    margin-top: var(--space-2);
}

.overview-job-card-note,
.overview-job-card-footer-note {
    display: none;
}

.overview-job-card-detail {
    min-height: 100%;
}

[class*="st-key-overview-job-card-shell-"] [data-testid="stExpander"] {
    margin: 0;
    border-radius: 18px;
    border: 1px solid rgba(123, 97, 255, 0.09) !important;
    background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(247,243,255,0.92) 100%);
    box-shadow: none;
    padding: var(--space-1) var(--space-2);
}

[class*="st-key-overview-job-card-shell-"] [data-testid="stExpander"] summary p {
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    color: #3b346c !important;
}

[class*="st-key-overview-job-card-shell-"] .stButton > button {
    min-height: 2.7rem;
    height: 2.7rem;
    border-radius: 16px;
    box-shadow: none;
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

.overview-empty-state {
    margin-top: var(--space-3);
    padding: var(--space-4);
    border-radius: 22px;
    border: 1px solid rgba(123, 97, 255, 0.08);
    background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(247,243,255,0.92) 100%);
    color: #6a648d;
    font-size: 0.95rem;
    line-height: 1.6;
    font-weight: 600;
}

.st-key-overview-scroll-shell,
.st-key-overview-scroll-shell > div,
.st-key-overview-scroll-shell iframe,
.st-key-overview-scroll-shell [data-testid="stElementContainer"],
.st-key-overview-dedupe-shell,
.st-key-overview-dedupe-shell > div,
.st-key-overview-dedupe-shell iframe,
.st-key-overview-dedupe-shell [data-testid="stElementContainer"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}

#overview-top-anchor {
    scroll-margin-top: calc(var(--sticky-nav-top) + var(--space-10));
}

.st-key-overview-pagination-shell {
    margin: var(--space-4) 0 0;
}

.st-key-overview-pagination-shell [data-testid="stHorizontalBlock"] {
    align-items: center;
}

.overview-pagination-summary {
    font-size: 0.9rem;
    line-height: 1.55;
    font-weight: 700;
    color: #4e4671;
}

.overview-pagination-summary span {
    display: block;
    margin-top: 0.12rem;
    font-size: 0.8rem;
    color: #817aa5;
}

.st-key-overview-pagination-shell .stButton > button {
    min-width: 2.55rem;
    min-height: 2.55rem;
    height: 2.55rem;
    border-radius: 999px;
    border: none;
    background: transparent;
    box-shadow: none;
    color: #2b2750;
    font-size: 0.98rem;
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
    min-height: 2.55rem;
    color: #756f97;
    font-weight: 700;
    letter-spacing: 0.12em;
}

@media (max-width: 960px) {
    .overview-intro {
        flex-direction: column;
        align-items: flex-start;
        padding: 0 var(--space-4);
    }

    .overview-intro-stats {
        width: 100%;
        justify-content: flex-start;
        flex-wrap: wrap;
    }

    .overview-intro-stat {
        min-width: 0;
        flex: 1 1 10rem;
    }

    .st-key-overview-body {
        padding: 0 var(--space-4) var(--space-4);
    }

    .st-key-overview-filter-shell [data-testid="stVerticalBlockBorderWrapper"] > div,
    [class*="st-key-overview-job-card-shell-"] [data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: var(--space-3) !important;
    }

    .overview-job-card-header {
        flex-direction: column;
    }

    .overview-job-card-score {
        min-width: 0;
        width: fit-content;
    }

    .st-key-overview-pagination-shell [data-testid="stHorizontalBlock"] {
        flex-direction: column;
        align-items: flex-start;
        gap: var(--space-3);
    }
}
"""
