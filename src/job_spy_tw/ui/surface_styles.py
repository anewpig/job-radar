"""提供卡片、CTA 與頁尾等表面元件的 CSS 片段。"""

SURFACE_STYLES = """
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
}

.ui-chip {
    display: inline-flex;
    align-items: center;
    gap: var(--space-1);
    padding: var(--space-2) var(--space-3);
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

.job-card-link-chip {
    text-decoration: none;
}

.job-card-link-chip:hover,
.job-card-link-chip:focus,
.job-card-link-chip:visited {
    color: #6a6197;
    text-decoration: none;
}

.section-shell {
    margin: var(--space-1) 0 var(--surface-content-gap);
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
    margin: var(--space-1) 0 0;
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--text);
}

.section-desc {
    max-width: 46rem;
    margin: var(--space-2) auto 0;
    color: var(--muted);
    line-height: 1.75;
}

.surface-card,
.info-card,
.summary-card {
    background: var(--surface-secondary-bg);
    border: 1px solid var(--surface-secondary-border);
    border-radius: var(--surface-radius-lg);
    padding: var(--space-4) var(--space-4);
    box-shadow: var(--surface-primary-shadow);
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
    margin-bottom: var(--surface-content-gap);
}

.cta-shell {
    position: relative;
    overflow: hidden;
    margin: 1rem 0 1.1rem;
    padding: 1.35rem 1.4rem;
    width: 50%;
    max-width: 540px;
    min-width: 0;
    margin-right: auto;
    border-radius: 28px;
    border: 1px solid rgba(123, 97, 255, 0.12);
    background: linear-gradient(135deg, #8b6bff 0%, #7b61ff 54%, #6a54df 100%);
    box-shadow: 0 18px 34px rgba(123, 97, 255, 0.18);
}

.cta-shell::after {
    content: "";
    position: absolute;
    right: -48px;
    top: -36px;
    width: 180px;
    height: 180px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(255,255,255,0.20) 0%, rgba(255,255,255,0.04) 68%, transparent 100%);
    pointer-events: none;
}

.cta-kicker {
    font-size: 0.76rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 800;
    color: rgba(255, 255, 255, 0.72);
}

.cta-title {
    margin-top: 0.3rem;
    font-size: 1.55rem;
    line-height: 1.18;
    font-weight: 800;
    color: #ffffff;
    max-width: 24rem;
}

.cta-copy {
    max-width: 22rem;
    margin-top: 0.55rem;
    color: rgba(244, 240, 255, 0.92);
    line-height: 1.72;
}

.cta-stat-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.85rem;
    margin-top: 1.15rem;
}

.cta-stat-card {
    padding: 0.95rem 1rem;
    border-radius: 22px;
    background: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(255, 255, 255, 0.16);
}

.cta-stat-label {
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-weight: 800;
    color: rgba(241, 235, 255, 0.82);
}

.cta-stat-value {
    margin-top: 0.38rem;
    font-size: 1.8rem;
    font-weight: 800;
    color: #ffffff;
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

[class*="st-key-board-card-container-"] [data-testid="stVerticalBlockBorderWrapper"] {
    position: relative;
    overflow: hidden;
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(247,242,255,0.96) 100%);
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    border-radius: 24px !important;
    display: flex;
    flex-direction: column;
    box-shadow: var(--shadow-soft);
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

[class*="st-key-board-card-container-"] [data-testid="stVerticalBlockBorderWrapper"]::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, #ffbe3d 0%, #7b61ff 55%, #9672ff 100%);
}

[class*="st-key-board-card-container-"] [data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-2px);
    border-color: rgba(123, 97, 255, 0.18);
    box-shadow: 0 16px 30px rgba(116, 86, 204, 0.12);
}

[class*="st-key-board-card-container-"] [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 1rem 1rem 1rem !important;
}

[class*="st-key-board-card-container-"] [data-testid="stVerticalBlock"] {
    gap: 0.7rem;
}

.board-card-shell {
    min-height: 0;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
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
}

.board-card-meta,
.board-card-timeline {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
}

.board-card-section {
    background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(244,240,255,0.90) 100%);
    border: 1px solid rgba(123, 97, 255, 0.08);
    border-radius: 18px;
    padding: 0.75rem 0.82rem;
}

.board-card-copy {
    color: #5d587f;
    line-height: 1.6;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 4.8rem;
}

.board-card-footer {
    margin-top: auto;
}

.board-card-footer a,
.job-link a {
    color: #6850dc;
    font-weight: 700;
    text-decoration: none;
}

[class*="st-key-board-editor-shell-"] {
    margin-top: 0.15rem;
    padding-top: 0.9rem;
    border-top: 1px solid rgba(123, 97, 255, 0.10);
}

[class*="st-key-board-editor-shell-"] [data-testid="stVerticalBlock"] {
    gap: 0.75rem;
}

[class*="st-key-board-editor-shell-"] .stSelectbox label,
[class*="st-key-board-editor-shell-"] .stTextInput label,
[class*="st-key-board-editor-shell-"] .stTextArea label {
    color: #645d86 !important;
    font-weight: 700 !important;
}

[class*="st-key-board-empty-shell-"] [data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(246,243,255,0.95) 100%);
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    border-radius: 20px !important;
    box-shadow: 0 10px 24px rgba(116, 86, 204, 0.06);
}

[class*="st-key-board-status-shell-"] {
    margin-bottom: 0.7rem;
}

[class*="st-key-board-status-shell-"] [data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,246,255,0.96) 100%);
    border: 1px solid rgba(123, 97, 255, 0.10) !important;
    border-radius: 18px !important;
    box-shadow: 0 8px 20px rgba(116, 86, 204, 0.05);
}

[class*="st-key-board-status-shell-"] [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 0.9rem 0.95rem 0.8rem !important;
}

[class*="st-key-board-empty-shell-"] [data-testid="stVerticalBlockBorderWrapper"] > div {
    padding: 0.95rem 0.95rem !important;
}

.board-empty-shell {
    min-height: 7.2rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0.4rem;
}

.board-empty-title {
    font-size: 1rem;
    font-weight: 800;
    color: var(--text);
}

.board-empty-copy {
    color: #7a7399;
    line-height: 1.6;
    font-size: 0.9rem;
}

.newsletter-shell {
    position: relative;
    overflow: hidden;
    width: var(--shared-surface-width);
    max-width: var(--shared-surface-width);
    box-sizing: border-box;
    margin-left: auto;
    margin-right: auto;
    margin-top: var(--surface-stack-gap);
    padding: 1.55rem 1.4rem 1.2rem;
    border-radius: 30px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(180deg, rgba(252,250,255,0.98) 0%, rgba(245,241,255,0.98) 100%);
    box-shadow: var(--shadow-soft);
    text-align: center;
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
    .cta-shell {
        width: 100%;
        max-width: none;
    }

    .section-title {
        font-size: 1.35rem;
    }

    .board-card-shell {
        min-height: auto;
    }

    .newsletter-footer-row {
        justify-content: center;
    }
}
"""
