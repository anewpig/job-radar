"""提供共用表面元件的 CSS 片段。"""

SURFACE_STYLES = """
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
}

.ui-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.42rem 0.76rem;
    border-radius: 999px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: rgba(255, 255, 255, 0.95);
    font-size: 0.86rem;
    color: #534d73;
}

.ui-chip--accent {
    background: var(--accent-soft);
    color: #5947be;
}

.ui-chip--soft {
    background: #f7f3ff;
    color: #6a6197;
}

.ui-chip--warm {
    background: var(--warm-soft);
    color: #8a5e00;
}

.section-shell {
    margin: 0.15rem 0 1rem;
    text-align: center;
}

.section-kicker {
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    color: var(--accent);
}

.section-title {
    margin: 0.22rem 0 0;
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--text);
}

.section-desc {
    max-width: 46rem;
    margin: 0.42rem auto 0;
    color: var(--muted);
    line-height: 1.75;
}

.market-report-heading {
    margin: var(--space-4) 0 var(--space-3);
    text-align: center;
}

.market-report-heading-title {
    font-size: 1.12rem;
    font-weight: 800;
    color: var(--text);
}

.market-report-heading-copy {
    max-width: 44rem;
    margin: var(--space-1) auto 0;
    color: var(--muted);
    line-height: 1.7;
}

.surface-card,
.info-card,
.summary-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(248,245,255,0.96) 100%);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 1rem 1.05rem;
    box-shadow: var(--shadow-soft);
}

.surface-card {
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.surface-card:hover {
    transform: translateY(-2px);
    border-color: rgba(123, 97, 255, 0.20);
    box-shadow: 0 14px 30px rgba(116, 86, 204, 0.12);
}

.summary-card {
    margin-bottom: 1rem;
}

[class*="st-key-market-report-"] {
    margin-top: var(--space-3);
}

[class*="st-key-market-report-"] [data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(248,245,255,0.96) 100%);
    border: 1px solid var(--border);
    border-radius: 24px;
    box-shadow: var(--shadow-soft);
}

[class*="st-key-market-report-"] [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: var(--space-4) !important;
}

[class*="st-key-market-report-"] [data-testid="stVerticalBlock"] {
    gap: var(--space-3);
}

.report-card-head {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
}

.report-card-title {
    font-size: 0.96rem;
    font-weight: 800;
    color: var(--text);
}

.report-card-copy {
    color: #6f6990;
    font-size: 0.84rem;
    line-height: 1.6;
}

.cta-shell {
    position: relative;
    overflow: hidden;
    margin: 0;
    padding: var(--space-4);
    width: 100%;
    max-width: none;
    border-radius: 24px;
    border: 1px solid rgba(123, 97, 255, 0.07);
    background: linear-gradient(180deg, rgba(255,255,255,0.985) 0%, rgba(247,245,252,0.96) 100%);
    box-shadow: 0 8px 18px rgba(116, 86, 204, 0.05);
}

.cta-shell--search-summary {
    min-height: 0;
    height: auto;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}

.cta-shell::after {
    content: "";
    position: absolute;
    right: -66px;
    bottom: -60px;
    width: 156px;
    height: 156px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123,97,255,0.06) 0%, rgba(123,97,255,0.018) 72%, transparent 100%);
    pointer-events: none;
}

.cta-summary-head {
    display: flex;
    flex-direction: column;
}

.cta-summary-meta-wrap {
    margin-top: var(--space-1);
}

.cta-title {
    margin-top: 0;
    font-size: 1.14rem;
    line-height: 1.2;
    font-weight: 800;
    color: #1f1b4d;
    max-width: none;
}

.cta-copy {
    max-width: none;
    margin-top: var(--space-2);
    color: #6f698e;
    line-height: 1.56;
    font-size: 0.86rem;
}

.cta-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-1);
    margin-top: 0;
}

.cta-meta-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    min-height: 1.96rem;
    padding: 0 0.7rem;
    border-radius: 999px;
    background: rgba(123, 97, 255, 0.038);
    border: 1px solid rgba(123, 97, 255, 0.07);
    color: #594dbf;
    font-size: 0.76rem;
    font-weight: 800;
}

.cta-meta-label {
    color: #857ea8;
    font-weight: 700;
}

.cta-meta-pill strong {
    color: #3a2f7a;
    font-weight: 800;
}

.cta-stat-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--space-2);
    margin-top: var(--space-2);
    padding-top: 0;
}

.cta-stat-card {
    padding: var(--space-3);
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(123, 97, 255, 0.07);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.74);
}

.cta-stat-card--wide {
    grid-column: 1 / -1;
}

.cta-stat-label {
    font-size: 0.76rem;
    letter-spacing: 0.01em;
    font-weight: 800;
    color: #8a84ab;
}

.cta-stat-value {
    margin-top: var(--space-1);
    font-size: 1.12rem;
    font-weight: 800;
    color: #2a235d;
}

.info-card-title,
.job-card-block-title,
.board-card-section-title {
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #8a84ab;
}

.summary-card-text {
    margin-top: 0.55rem;
    color: #5c567e;
    line-height: 1.8;
}

.board-summary-chips {
    justify-content: center;
    row-gap: var(--space-2);
}

.board-summary-card {
    position: relative;
    overflow: hidden;
    min-height: 7rem;
    padding: 0.9rem 0.95rem;
    border-radius: 22px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(245,241,255,0.94) 100%);
    box-shadow: var(--shadow-soft);
}

.board-summary-card::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 3px;
    background: rgba(123, 97, 255, 0.16);
}

.board-summary-card-top {
    display: flex;
    align-items: center;
    gap: 0.55rem;
}

.board-summary-card-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.7rem;
    height: 1.7rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 900;
    line-height: 1;
}

.board-summary-card-label {
    color: #8a84ab;
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.board-summary-card-value {
    margin-top: 0.65rem;
    color: #251f59;
    font-size: 2rem;
    font-weight: 900;
    line-height: 1;
}

.board-summary-card-copy {
    margin-top: 0.55rem;
    color: #6f6990;
    font-size: 0.82rem;
    font-weight: 700;
    line-height: 1.45;
}

.board-summary-card--all::before {
    background: linear-gradient(90deg, #7b61ff 0%, #9a84ff 100%);
}

.board-summary-card--pending::before {
    background: linear-gradient(90deg, #e2d8ff 0%, #b9aae8 100%);
}

.board-summary-card--active::before {
    background: linear-gradient(90deg, #cfe0ff 0%, #9ebcff 100%);
}

.board-summary-card--finished::before {
    background: linear-gradient(90deg, #d8dde7 0%, #b7bfce 100%);
}

.board-summary-card-icon--all {
    background: rgba(123, 97, 255, 0.10);
    color: #6b54de;
}

.board-summary-card-icon--pending {
    background: rgba(216, 204, 255, 0.34);
    color: #6d5fa8;
}

.board-summary-card-icon--active {
    background: rgba(189, 208, 255, 0.32);
    color: #4569d6;
}

.board-summary-card-icon--finished {
    background: rgba(213, 219, 228, 0.34);
    color: #6d7485;
}

.job-card-title {
    margin: 0;
    font-size: 1.12rem;
    font-weight: 800;
    color: var(--text);
}

.job-card-company {
    margin-top: 0.24rem;
    color: #6f6990;
    font-weight: 600;
}

.job-card-block {
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(244,240,255,0.92) 100%);
    border: 1px solid rgba(123, 97, 255, 0.09);
    border-radius: 18px;
    padding: 0.85rem 0.9rem;
}

.job-card-list {
    margin: 0.55rem 0 0;
    padding-left: 1rem;
    color: #334155;
}

.job-card-list li {
    margin: 0.3rem 0;
    line-height: 1.55;
}

[class*="st-key-board-card-container-"] {
    margin-top: var(--space-2);
}

[class*="st-key-board-status-shell-"] {
    margin-bottom: var(--space-2);
}

[class*="st-key-board-status-shell-"] [data-testid="stVerticalBlock"],
[class*="st-key-board-empty-shell-"] [data-testid="stVerticalBlock"] {
    gap: 0;
}

.board-status-heading {
    min-height: 5.4rem;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--space-2);
    padding-top: 0.15rem;
    border-top: 4px solid rgba(123, 97, 255, 0.12);
}

.board-status-copy {
    display: flex;
    flex-direction: column;
    gap: 0.32rem;
}

.board-status-label {
    color: var(--text);
    font-size: 1rem;
    font-weight: 900;
    line-height: 1.2;
}

.board-status-heading--pending {
    border-top-color: #d8ccff;
}

.board-status-heading--preparing {
    border-top-color: #f4d58d;
}

.board-status-heading--applied {
    border-top-color: #bdd0ff;
}

.board-status-heading--interview {
    border-top-color: #f6c5a8;
}

.board-status-heading--offer {
    border-top-color: #bfe4cc;
}

.board-status-heading--declined {
    border-top-color: #d5dbe4;
}

.board-status-label--pending {
    color: #6d5fa8;
}

.board-status-label--preparing {
    color: #9a6a12;
}

.board-status-label--applied {
    color: #4569d6;
}

.board-status-label--interview {
    color: #b86a2e;
}

.board-status-label--offer {
    color: #2e8a5f;
}

.board-status-label--declined {
    color: #6d7485;
}

.board-status-desc {
    color: #736c97;
    font-size: 0.84rem;
    line-height: 1.55;
}

.board-status-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 4.4rem;
    padding: 0.5rem 0.7rem;
    border-radius: 999px;
    background: rgba(245, 241, 255, 0.96);
    border: 1px solid rgba(123, 97, 255, 0.10);
    color: #695f96;
    font-size: 0.82rem;
    font-weight: 800;
    line-height: 1;
    white-space: nowrap;
}

.board-status-count--pending {
    background: #f1ecff;
    border-color: #d8ccff;
    color: #6d5fa8;
}

.board-status-count--preparing {
    background: #fff4d9;
    border-color: #f4d58d;
    color: #9a6a12;
}

.board-status-count--applied {
    background: #eaf1ff;
    border-color: #bdd0ff;
    color: #4569d6;
}

.board-status-count--interview {
    background: #ffe9dd;
    border-color: #f6c5a8;
    color: #b86a2e;
}

.board-status-count--offer {
    background: #e8f7ee;
    border-color: #bfe4cc;
    color: #2e8a5f;
}

.board-status-count--declined {
    background: #eef1f5;
    border-color: #d5dbe4;
    color: #6d7485;
}

.board-empty-shell {
    min-height: 7.4rem;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}

.board-empty-copy {
    width: 100%;
    max-width: 14rem;
    margin: 0 auto;
    color: #736c97;
    line-height: 1.6;
}

.st-key-tasks-shell {
    position: relative;
    z-index: 0;
    overflow: hidden;
    isolation: isolate;
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

.st-key-tasks-shell::before {
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

.st-key-tasks-shell::after {
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

.st-key-tasks-shell > div {
    position: relative;
    z-index: 0;
}

.tasks-intro {
    margin: 0 0 var(--space-4);
    padding: 0 var(--surface-content-inline);
    text-align: left;
}

.tasks-intro-main {
    max-width: 42rem;
}

.tasks-intro .section-kicker,
.tasks-intro .section-title,
.tasks-intro .section-desc {
    text-align: left;
}

.tasks-intro .section-title {
    margin-top: var(--space-2);
}

.tasks-intro .section-desc {
    max-width: 42rem;
    margin: var(--space-2) 0 0;
    color: #716b95;
    font-weight: 600;
    line-height: 1.6;
}

.board-card-shell,
[class*="st-key-board-card-shell-"] {
    position: relative;
    overflow: hidden;
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(247,242,255,0.96) 100%);
    border: 1px solid rgba(123, 97, 255, 0.10);
    border-radius: 24px;
    padding: 0.92rem 0.92rem;
    height: 18rem;
    min-height: 18rem;
    display: flex;
    flex-direction: column;
    gap: 0.58rem;
    box-shadow: var(--shadow-soft);
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.board-card-shell [data-testid="stVerticalBlock"],
[class*="st-key-board-card-shell-"] [data-testid="stVerticalBlock"] {
    gap: 0.58rem;
}

[class*="st-key-board-card-summary-row-"] {
    margin-bottom: var(--space-2);
}

[class*="st-key-board-card-summary-row-"] [data-testid="stHorizontalBlock"] {
    align-items: stretch;
}

.board-card-summary-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(13rem, 14rem);
    gap: var(--space-3);
    align-items: start;
}

.board-card-main {
    display: flex;
    gap: 0.85rem;
    align-items: flex-start;
}

.board-card-shell::before,
[class*="st-key-board-card-shell-"]::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, #ffbe3d 0%, #7b61ff 55%, #9672ff 100%);
}

[class*="st-key-board-card-shell-pending-"]::before,
.board-card-shell--pending::before {
    background: linear-gradient(90deg, #d8ccff 0%, #a897df 100%);
}

[class*="st-key-board-card-shell-preparing-"]::before,
.board-card-shell--preparing::before {
    background: linear-gradient(90deg, #fae6b5 0%, #f4d58d 100%);
}

[class*="st-key-board-card-shell-applied-"]::before,
.board-card-shell--applied::before {
    background: linear-gradient(90deg, #d4e3ff 0%, #95b4ff 100%);
}

[class*="st-key-board-card-shell-interview-"]::before,
.board-card-shell--interview::before {
    background: linear-gradient(90deg, #fbd8c5 0%, #f0b693 100%);
}

[class*="st-key-board-card-shell-offer-"]::before,
.board-card-shell--offer::before {
    background: linear-gradient(90deg, #d4efdd 0%, #96cdaf 100%);
}

[class*="st-key-board-card-shell-declined-"]::before,
.board-card-shell--declined::before {
    background: linear-gradient(90deg, #e0e5ec 0%, #b5bcc9 100%);
}

.board-card-shell:hover,
[class*="st-key-board-card-shell-"]:hover {
    transform: translateY(-2px);
    border-color: rgba(123, 97, 255, 0.18);
    box-shadow: 0 16px 30px rgba(116, 86, 204, 0.12);
}

.board-card-icon {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(255, 190, 61, 0.24) 0%, rgba(123, 97, 255, 0.16) 100%);
    color: #6e55e2;
    font-size: 1rem;
    font-weight: 900;
}

.board-card-title {
    margin: 0;
    font-size: 1.02rem;
    font-weight: 800;
    color: var(--text);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.board-card-company {
    color: #6f6990;
    font-weight: 600;
    margin-top: 0.15rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.board-card-signal-panel {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 0.75rem 0.85rem;
    border-radius: 20px;
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(241,236,255,0.92) 100%);
    border: 1px solid rgba(123, 97, 255, 0.10);
}

.board-card-signal-panel--pending {
    background: linear-gradient(180deg, #f7f3ff 0%, #f1ecff 100%);
    border-color: #d8ccff;
}

.board-card-signal-panel--preparing {
    background: linear-gradient(180deg, #fff8e7 0%, #fff4d9 100%);
    border-color: #f4d58d;
}

.board-card-signal-panel--applied {
    background: linear-gradient(180deg, #f3f7ff 0%, #eaf1ff 100%);
    border-color: #bdd0ff;
}

.board-card-signal-panel--interview {
    background: linear-gradient(180deg, #fff3ec 0%, #ffe9dd 100%);
    border-color: #f6c5a8;
}

.board-card-signal-panel--offer {
    background: linear-gradient(180deg, #f1fbf5 0%, #e8f7ee 100%);
    border-color: #bfe4cc;
}

.board-card-signal-panel--declined {
    background: linear-gradient(180deg, #f5f7fa 0%, #eef1f5 100%);
    border-color: #d5dbe4;
}

.board-card-signal-label {
    color: #8b83ae;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.board-card-signal-value {
    color: var(--text);
    font-size: 1.05rem;
    font-weight: 900;
    line-height: 1.2;
}

.board-status-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: fit-content;
    padding: 0.42rem 0.72rem;
    border-radius: 999px;
    font-size: 0.88rem;
    font-weight: 900;
    line-height: 1;
    border: 1px solid rgba(123, 97, 255, 0.10);
}

.board-status-pill--pending {
    background: #f1ecff;
    border-color: #d8ccff;
    color: #6d5fa8;
}

.board-status-pill--preparing {
    background: #fff4d9;
    border-color: #f4d58d;
    color: #9a6a12;
}

.board-status-pill--applied {
    background: #eaf1ff;
    border-color: #bdd0ff;
    color: #4569d6;
}

.board-status-pill--interview {
    background: #ffe9dd;
    border-color: #f6c5a8;
    color: #b86a2e;
}

.board-status-pill--offer {
    background: #e8f7ee;
    border-color: #bfe4cc;
    color: #2e8a5f;
}

.board-status-pill--declined {
    background: #eef1f5;
    border-color: #d5dbe4;
    color: #6d7485;
}

.board-card-signal-meta {
    color: #685f93;
    font-size: 0.9rem;
    font-weight: 700;
}

.board-card-signal-flags {
    display: flex;
    flex-direction: column;
    gap: 0.32rem;
}

.board-card-flag {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: fit-content;
    padding: 0.32rem 0.62rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    line-height: 1.15;
    border: 1px solid rgba(123, 97, 255, 0.10);
}

.board-card-flag.is-filled {
    background: rgba(255, 244, 207, 0.85);
    color: #8e6312;
}

.board-card-flag.is-empty {
    background: rgba(245, 241, 255, 0.92);
    color: #756b9d;
}

.board-card-meta,
.board-card-timeline {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    align-content: flex-start;
}

.board-card-meta {
    min-height: 2.7rem;
    max-height: 5.25rem;
    overflow: hidden;
    margin-top: 0;
}

.board-card-timeline {
    min-height: 2.35rem;
}

.board-card-section {
    background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(244,240,255,0.90) 100%);
    border: 1px solid rgba(123, 97, 255, 0.08);
    border-radius: 18px;
    padding: 0.62rem 0.74rem;
}

.board-card-copy {
    color: #5d587f;
    line-height: 1.6;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 0;
}

.board-card-footer {
    margin-top: auto;
    padding-top: 0.45rem;
    padding-left: 0.76rem;
}

[class*="st-key-board-card-toggle-inline-shell-"] {
    width: fit-content;
    max-width: calc(100% - 3.35rem);
    margin-top: var(--space-2);
    margin-left: 3.35rem;
}

[class*="st-key-board-card-toggle-inline-shell-"] [data-testid="stButton"] {
    margin: 0;
    width: fit-content;
}

[class*="st-key-board-card-toggle-inline-shell-"] button {
    min-height: 2.3rem;
    min-width: 7.6rem;
    padding: 0 0.95rem !important;
    border-radius: 999px !important;
    border: 1px solid rgba(123, 97, 255, 0.12) !important;
    background: linear-gradient(180deg, rgba(250,247,255,0.98) 0%, rgba(243,238,255,0.94) 100%) !important;
    color: #5d4ec3 !important;
    box-shadow: none !important;
    font-weight: 800 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.01em;
}

[class*="st-key-board-card-toggle-inline-shell-"] button:hover {
    border-color: rgba(123, 97, 255, 0.20) !important;
    background: linear-gradient(180deg, rgba(247,243,255,0.99) 0%, rgba(239,234,255,0.96) 100%) !important;
    color: #5142ba !important;
    box-shadow: 0 8px 16px rgba(123, 97, 255, 0.08) !important;
}

[class*="st-key-board-editor-shell-"] {
    margin-top: var(--space-2);
    padding: 0.9rem 0.95rem 0.95rem;
    border-radius: 22px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(244,240,255,0.94) 100%);
    box-shadow: var(--shadow-soft);
}

[class*="st-key-board-editor-shell-"] [data-testid="stForm"] {
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
}

[class*="st-key-board-editor-shell-"] [data-testid="stTextInput"] {
    margin-top: 0.2rem;
}

.board-card-footer a,
.job-link a {
    color: #6850dc;
    font-weight: 700;
    text-decoration: none;
}

.newsletter-shell {
    position: relative;
    overflow: hidden;
    margin-top: 0;
    padding: 1.55rem 1.4rem 1.2rem;
    border-radius: 30px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(180deg, rgba(252,250,255,0.98) 0%, rgba(245,241,255,0.98) 100%);
    box-shadow: var(--shadow-soft);
    text-align: center;
}

.st-key-board-shell {
    position: relative;
    z-index: 0;
    overflow: hidden;
    isolation: isolate;
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

.st-key-board-shell::before {
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

.st-key-board-shell::after {
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

.st-key-board-shell > div {
    position: relative;
    z-index: 0;
}

.hero-shell,
.newsletter-shell,
.st-key-nav-sticky-row-shell,
.st-key-search-setup-shell,
.st-key-overview-shell,
.st-key-resume-shell,
.st-key-assistant-shell,
.st-key-tasks-shell,
.st-key-sources-shell,
.st-key-tracking-shell,
.st-key-board-shell,
.st-key-backend-shell,
.st-key-backend-ops-shell,
.st-key-backend-console-shell,
.st-key-notifications-shell,
.st-key-database-shell,
.st-key-export-shell {
    width: var(--shared-surface-width) !important;
    max-width: var(--shared-surface-width) !important;
    box-sizing: border-box;
    margin-left: auto !important;
    margin-right: auto !important;
}

.newsletter-shell::before {
    content: "";
    position: absolute;
    left: -42px;
    top: -32px;
    width: 160px;
    height: 160px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(123, 97, 255, 0.10) 0%, rgba(123, 97, 255, 0.02) 72%, transparent 100%);
    pointer-events: none;
}

.newsletter-kicker {
    font-size: 0.76rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 800;
    color: #7b61ff;
}

.newsletter-title {
    margin-top: 0.35rem;
    font-size: 1.7rem;
    line-height: 1.2;
    font-weight: 800;
    color: var(--text);
}

.newsletter-copy {
    max-width: 46rem;
    margin: 0.6rem auto 0;
    color: #6f6990;
    line-height: 1.8;
}

.newsletter-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    justify-content: center;
    margin-top: 1rem;
}

.newsletter-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.48rem 0.8rem;
    border-radius: 999px;
    background: rgba(123, 97, 255, 0.08);
    border: 1px solid rgba(123, 97, 255, 0.10);
    color: #614ed0;
    font-size: 0.85rem;
    font-weight: 700;
}

.newsletter-footer-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 0.9rem 1rem;
    margin-top: 1.1rem;
    color: #8f88b0;
    font-size: 0.84rem;
}

.newsletter-footer-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.9rem 1rem;
    align-items: center;
    justify-content: center;
}

.newsletter-footer-visit {
    white-space: nowrap;
    font-weight: 700;
}

@media (max-width: 960px) {
    .cta-copy {
        max-width: none;
    }

    .cta-shell {
        width: 100%;
        max-width: none;
    }

    .section-title {
        font-size: 1.35rem;
    }

    .board-card-shell,
    [class*="st-key-board-card-shell-"] {
        height: auto;
        min-height: auto;
    }

    .board-card-summary-grid {
        grid-template-columns: 1fr;
    }

    .board-status-heading {
        min-height: auto;
    }

    .newsletter-footer-row {
        justify-content: center;
    }
}
"""
