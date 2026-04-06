"""提供首頁 Hero 區塊的 CSS 片段。"""

HERO_STYLES = """
.hero-shell {
    position: relative;
    overflow: hidden;
    width: var(--shared-surface-width);
    box-sizing: border-box;
    margin-left: auto;
    margin-right: auto;
    margin-top: calc(var(--space-14) * -1);
    margin-bottom: var(--surface-stack-gap);
    padding: var(--surface-content-block) var(--surface-content-inline);
    border-radius: var(--surface-radius-xl);
    border: 1px solid var(--surface-primary-border);
    background:
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.18), transparent 22%),
        var(--surface-primary-bg);
    box-shadow: var(--surface-primary-shadow);
}

.hero-shell::before {
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

.hero-shell::after {
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

.hero-grid {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: minmax(0, 0.98fr) minmax(390px, 1.02fr);
    gap: var(--surface-content-gap-loose);
    align-items: stretch;
}

.hero-copy {
    align-self: stretch;
    display: flex;
    flex-direction: column;
    margin-top: var(--space-1);
    max-width: 34rem;
    min-height: 100%;
    padding-left: var(--space-5);
}

.hero-kicker {
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-weight: 800;
    color: var(--accent);
}

.hero-brand-title {
    margin: var(--space-3) 0 0;
    font-size: 2.4rem;
    line-height: 1.15;
    font-weight: 900;
    letter-spacing: 0.02em;
    color: #5f49d6;
}

.hero-headline {
    margin: var(--space-4) 0 0;
    max-width: 34rem;
    font-size: 1.2rem;
    line-height: 1.14;
    font-weight: 800;
    letter-spacing: -0.01em;
    color: #27234e;
    text-wrap: balance;
}

.hero-subtitle {
    margin: var(--space-7) 0 0;
    max-width: 30rem;
    font-size: 1.02rem;
    line-height: 1.65;
    color: #5f587e;
    font-weight: 700;
}

.hero-description {
    margin: var(--space-6) 0 0;
    max-width: 32rem;
    font-size: 1rem;
    line-height: 1.76;
    color: #6f6990;
}

.hero-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
    margin-top: var(--space-5);
}

.hero-actions {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: var(--space-5);
    margin-top: auto;
    margin-bottom: calc(var(--space-5) + 1.625rem);
    padding-top: var(--space-8);
    flex-wrap: wrap;
}

.hero-action-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 9.6rem;
    min-height: 3.2rem;
    padding: 0 var(--space-5);
    border-radius: 18px;
    background: linear-gradient(135deg, #6f56f6 0%, #7b61ff 55%, #9672ff 100%);
    box-shadow: 0 16px 28px rgba(123, 97, 255, 0.18);
    color: #ffffff !important;
    font-size: 1rem;
    font-weight: 800;
    text-decoration: none;
}

.hero-shell a.hero-action-button,
.hero-shell a.hero-action-button:link,
.hero-action-button--link,
.hero-action-button--link:hover,
.hero-action-button--link:focus,
.hero-action-button--link:visited {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff;
    text-decoration: none;
}

.hero-action-note {
    color: #756f97;
    font-size: 0.92rem;
    line-height: 1.45;
    font-weight: 700;
    max-width: 24rem;
    padding-bottom: 0;
}

.hero-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.42rem 0.76rem;
    border-radius: 999px;
    background: rgba(123, 97, 255, 0.08);
    border: 1px solid rgba(123, 97, 255, 0.10);
    color: #5d4cc4;
    font-size: 0.86rem;
    font-weight: 700;
}

.hero-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--surface-content-gap-tight);
    margin-top: var(--space-5);
}

.hero-meta-card,
.hero-note-card,
.hero-stat-card {
    border-radius: 22px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: rgba(255, 255, 255, 0.92);
    box-shadow: var(--shadow-soft);
}

.hero-meta-card,
.hero-note-card {
    padding: var(--space-4);
    min-width: 13rem;
}

.hero-meta-label,
.hero-stat-label {
    font-size: 0.74rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 800;
    color: #8a84ab;
}

.hero-meta-value {
    margin-top: var(--space-1);
    font-size: 0.98rem;
    font-weight: 700;
    color: var(--text);
}

.hero-visual {
    position: relative;
    align-self: start;
}

.hero-mockup {
    position: relative;
    min-height: 21.8rem;
    border-radius: 30px;
    overflow: hidden;
    background:
        radial-gradient(circle at 18% 20%, rgba(255, 255, 255, 0.34), transparent 18%),
        radial-gradient(circle at 88% 12%, rgba(255, 255, 255, 0.24), transparent 18%),
        linear-gradient(135deg, #a987ff 0%, #8b6cff 40%, #7759ec 70%, #6949d8 100%);
    box-shadow: 0 24px 46px rgba(108, 79, 210, 0.22);
}

.hero-mockup::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 0% 68%, rgba(255, 255, 255, 0.28) 0%, rgba(255, 255, 255, 0.08) 20%, transparent 22%),
        radial-gradient(circle at 18% 78%, rgba(255, 255, 255, 0.16) 0%, rgba(255, 255, 255, 0.04) 28%, transparent 30%),
        radial-gradient(circle at 82% 94%, rgba(255, 255, 255, 0.10) 0%, transparent 18%);
    pointer-events: none;
}

.hero-mockup::after {
    content: "";
    position: absolute;
    left: 36%;
    top: 10%;
    width: 10rem;
    height: 10rem;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.34) 0%, rgba(255, 255, 255, 0.08) 62%, transparent 66%);
    pointer-events: none;
}

.hero-mockup-orb {
    position: absolute;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.34) 0%, rgba(255, 255, 255, 0.10) 62%, transparent 68%);
    pointer-events: none;
}

.hero-mockup-orb--one {
    left: -2.8rem;
    bottom: 1rem;
    width: 12rem;
    height: 12rem;
}

.hero-mockup-orb--two {
    right: -2rem;
    top: 1.2rem;
    width: 8.5rem;
    height: 8.5rem;
}

.hero-mockup-badge {
    position: absolute;
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.96);
    box-shadow: 0 12px 26px rgba(65, 44, 153, 0.16);
    color: #352a77;
    font-weight: 700;
    z-index: 2;
}

.hero-mockup-badge--label {
    top: 1.45rem;
    left: 1.3rem;
    padding: 0.7rem 1rem;
    gap: 0.65rem;
    font-size: 0.88rem;
}

.hero-mockup-badge--label::before {
    content: "";
    width: 2.1rem;
    height: 2.1rem;
    border-radius: 999px;
    background: linear-gradient(135deg, #6f56f6 0%, #8d74ff 100%);
    box-shadow: inset 0 0 0 6px rgba(255, 255, 255, 0.18);
}

.hero-mockup-badge--stat {
    top: 1.2rem;
    right: 1.3rem;
    padding: 0.85rem 1.15rem;
    min-width: 11.6rem;
    justify-content: center;
    font-size: 0.9rem;
}

.hero-mockup-card {
    position: absolute;
    border-radius: 26px;
    background: rgba(255, 255, 255, 0.97);
    border: 1px solid rgba(123, 97, 255, 0.08);
    box-shadow: 0 18px 34px rgba(56, 35, 145, 0.16);
}

.hero-mockup-card--main {
    top: 4.2rem;
    left: 11.6rem;
    right: 2.4rem;
    min-height: 11.5rem;
    padding: 0.95rem 1rem 0.9rem;
}

.hero-mockup-card-head {
    display: flex;
    align-items: flex-start;
    gap: 0.85rem;
}

.hero-mockup-appmark {
    width: 3.2rem;
    height: 3.2rem;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #6f56f6 0%, #8b6cff 100%);
    color: #ffffff;
    font-size: 1.02rem;
    font-weight: 900;
    box-shadow: 0 14px 24px rgba(123, 97, 255, 0.18);
    flex-shrink: 0;
}

.hero-mockup-kicker {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-weight: 800;
    color: #9f97c2;
}

.hero-mockup-title {
    margin-top: 0.28rem;
    font-size: 1rem;
    line-height: 1.55;
    font-weight: 800;
    color: #2d275f;
}

.hero-mockup-chart {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    align-items: end;
    gap: 0.7rem;
    height: 4.35rem;
    margin-top: 0.7rem;
}

.hero-mockup-chart-bar {
    border-radius: 18px 18px 10px 10px;
    background: linear-gradient(180deg, rgba(155, 132, 255, 0.95) 0%, rgba(114, 91, 231, 0.98) 100%);
}

.hero-mockup-chart-bar--one {
    height: 62%;
}

.hero-mockup-chart-bar--two {
    height: 86%;
}

.hero-mockup-chart-bar--three {
    height: 74%;
}

.hero-mockup-chart-bar--four {
    height: 100%;
}

.hero-mockup-mini-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.7rem;
    margin-top: 0.7rem;
}

.hero-mockup-mini-card {
    border-radius: 20px;
    background: linear-gradient(180deg, rgba(246, 242, 255, 0.98) 0%, rgba(255, 255, 255, 0.98) 100%);
    border: 1px solid rgba(123, 97, 255, 0.08);
    padding: 0.65rem 0.72rem;
}

.hero-mockup-mini-card span {
    display: block;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 800;
    color: #9a92bf;
}

.hero-mockup-mini-card strong {
    display: block;
    margin-top: 0.32rem;
    font-size: 1.18rem;
    line-height: 1;
    color: #362b79;
}

.hero-mockup-card--overlay {
    left: 1.4rem;
    top: 7rem;
    width: 11.5rem;
    padding: 0.85rem 0.85rem;
}

.hero-mockup-card--assistant {
    right: 1.35rem;
    bottom: 0.95rem;
    width: 13rem;
    padding: 0.85rem 0.9rem;
}

.hero-mockup-copy {
    margin-top: 0.28rem;
    color: #676083;
    font-size: 0.82rem;
    line-height: 1.55;
    font-weight: 700;
}

.hero-mockup-action {
    position: absolute;
    left: 4.5rem;
    bottom: 2.4rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 6.2rem;
    padding: 0.78rem 1rem;
    border-radius: 18px;
    background: linear-gradient(135deg, #6f56f6 0%, #7b61ff 75%, #9672ff 100%);
    color: #ffffff;
    font-size: 1rem;
    font-weight: 800;
    box-shadow: 0 18px 28px rgba(86, 61, 191, 0.22);
    z-index: 2;
}

.hero-mini-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 0.42rem;
}

.hero-mini-tag {
    display: inline-flex;
    align-items: center;
    padding: 0.3rem 0.58rem;
    border-radius: 999px;
    background: rgba(123, 97, 255, 0.08);
    color: #6653d3;
    font-size: 0.79rem;
    font-weight: 700;
}

.hero-stat-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.7rem;
}

.hero-stat-card {
    padding: 0.78rem 0.8rem;
}

.hero-stat-value {
    margin-top: 0.34rem;
    font-size: 1.26rem;
    font-weight: 800;
    color: #3a2f7a;
}

@media (max-width: 960px) {
    .hero-grid {
        grid-template-columns: 1fr;
        align-items: start;
    }

    .hero-shell {
        margin-top: calc(var(--space-11) * -1);
    }

    .hero-mockup {
        min-height: 19rem;
    }

    .hero-mockup-card--main {
        left: 9.8rem;
        right: 1.1rem;
        top: 3.8rem;
        min-height: 10.4rem;
        padding: 0.9rem;
    }

    .hero-mockup-card--overlay {
        left: 0.95rem;
        top: 11.9rem;
        width: 10.9rem;
    }

    .hero-mockup-card--assistant {
        right: 0.95rem;
        width: 11.4rem;
        bottom: 0.65rem;
    }

    .hero-mockup-action {
        left: 9.8rem;
        bottom: 0.75rem;
        min-width: 5.2rem;
        padding: 0.68rem 0.9rem;
    }

    .hero-mockup-badge--label,
    .hero-mockup-badge--stat {
        transform: scale(0.94);
        transform-origin: top left;
    }

    .hero-brand-title {
        font-size: 2.05rem;
        margin-top: var(--space-2);
    }

    .hero-headline {
        font-size: 1.05rem;
        margin-top: var(--space-3);
    }

    .hero-description {
        font-size: 0.94rem;
        line-height: 1.75;
        margin-top: var(--space-5);
    }

    .hero-actions {
        margin-top: var(--space-6);
        gap: var(--surface-content-gap);
        padding-top: 0;
    }
}
"""
