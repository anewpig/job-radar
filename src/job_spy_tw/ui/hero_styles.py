"""提供首頁 Hero 區塊的 CSS 片段。"""

HERO_STYLES = """
.hero-shell {
    position: relative;
    overflow: hidden;
    width: 100%;
    box-sizing: border-box;
    margin-left: auto;
    margin-right: auto;
    margin-top: -3.4rem;
    margin-bottom: 1.5rem;
    padding: 1.6rem 1.5rem;
    border-radius: 30px;
    border: 1px solid rgba(123, 97, 255, 0.12);
    background:
        radial-gradient(circle at top right, rgba(255, 215, 126, 0.18), transparent 22%),
        linear-gradient(135deg, #ffffff 0%, #f8f4ff 68%, #f3edff 100%);
    box-shadow: var(--shadow-soft);
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
    gap: 2.4rem;
    align-items: stretch;
}

.hero-copy {
    align-self: stretch;
    display: flex;
    flex-direction: column;
    margin-top: 0.1rem;
    max-width: 32rem;
    min-height: 100%;
    padding-left: 1.1rem;
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
    font-size: 1.7rem;
    line-height: 1.15;
    font-weight: 900;
    letter-spacing: 0.02em;
    color: var(--text);
}

.hero-title {
    margin: 0.3rem 0 0;
    font-size: 2.8rem;
    line-height: 1.08;
    font-weight: 800;
    color: #27234e;
}

.hero-subtitle {
    margin: 1.75rem 0 0;
    max-width: 30rem;
    font-size: 1.02rem;
    line-height: 1.65;
    color: #5f587e;
    font-weight: 700;
}

.hero-description {
    margin: 2rem 0 0;
    max-width: 31rem;
    font-size: 0.96rem;
    line-height: 1.82;
    color: #6f6990;
}

.hero-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-top: 1.1rem;
}

.hero-actions {
    display: flex;
    flex-direction: row;
    align-items: flex-end;
    gap: 1rem;
    margin-top: auto;
    margin-bottom: 0.85rem;
    padding-top: 1.75rem;
    flex-wrap: wrap;
}

.hero-action-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 9.6rem;
    min-height: 3.2rem;
    padding: 0 1.35rem;
    border-radius: 18px;
    background: linear-gradient(135deg, #6f56f6 0%, #7b61ff 55%, #9672ff 100%);
    box-shadow: 0 16px 28px rgba(123, 97, 255, 0.18);
    color: #ffffff !important;
    font-size: 1rem;
    font-weight: 800;
    text-decoration: none;
    transform: translateY(0.125rem);
}

.hero-shell a.hero-action-button,
.hero-shell a.hero-action-button:link,
.hero-shell a.hero-action-button:visited,
.hero-shell a.hero-action-button:hover,
.hero-shell a.hero-action-button:focus,
.hero-action-button--link,
.hero-action-button--link:link,
.hero-action-button--link:visited,
.hero-action-button--link:hover,
.hero-action-button--link:focus {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff;
    text-decoration: none;
}

.hero-action-note {
    color: #756f97;
    font-size: 0.92rem;
    line-height: 1.45;
    font-weight: 700;
    padding-bottom: 0.22rem;
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
    gap: 0.85rem;
    margin-top: 1.25rem;
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
    padding: 0.95rem 1rem;
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
    margin-top: 0.34rem;
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

.hero-mockup-radar-ring {
    position: absolute;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.16);
    pointer-events: none;
    z-index: 0;
}

.hero-mockup-radar-ring--one {
    right: -3.8rem;
    bottom: -5.4rem;
    width: 17rem;
    height: 17rem;
    opacity: 0.3;
}

.hero-mockup-radar-ring--two {
    right: 0.4rem;
    bottom: -2.2rem;
    width: 11.8rem;
    height: 11.8rem;
    opacity: 0.24;
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
    padding: 0.82rem 1rem;
    min-width: 7.8rem;
    justify-content: center;
    font-size: 0.82rem;
    letter-spacing: 0.04em;
}

.hero-mockup-card {
    position: absolute;
    border-radius: 26px;
    background: rgba(255, 255, 255, 0.97);
    border: 1px solid rgba(123, 97, 255, 0.08);
    box-shadow: 0 18px 34px rgba(56, 35, 145, 0.16);
    backdrop-filter: blur(12px);
}

.hero-mockup-card--main {
    top: 4rem;
    left: 4.5rem;
    right: 2rem;
    min-height: 13.4rem;
    padding: 1rem 1rem 0.95rem;
    z-index: 1;
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

.hero-mockup-board-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.75rem;
}

.hero-mockup-board-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 2rem;
    padding: 0 0.72rem;
    border-radius: 999px;
    background: rgba(123, 97, 255, 0.10);
    color: #5e49cf;
    font-size: 0.76rem;
    font-weight: 800;
    white-space: nowrap;
}

.hero-mockup-job-list {
    display: flex;
    flex-direction: column;
    gap: 0.72rem;
    margin-top: 0.85rem;
}

.hero-mockup-job-card {
    border-radius: 22px;
    background: linear-gradient(180deg, rgba(247, 243, 255, 0.96) 0%, rgba(255, 255, 255, 0.96) 100%);
    border: 1px solid rgba(123, 97, 255, 0.08);
    padding: 0.76rem 0.82rem 0.78rem;
}

.hero-mockup-job-card--active {
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.99) 0%, rgba(242, 237, 255, 0.98) 100%);
    border-color: rgba(111, 86, 246, 0.22);
    box-shadow: 0 16px 28px rgba(111, 86, 246, 0.14);
}

.hero-mockup-job-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.7rem;
}

.hero-mockup-job-title {
    font-size: 0.92rem;
    line-height: 1.35;
    font-weight: 800;
    color: #2f285f;
}

.hero-mockup-job-card--active .hero-mockup-job-title {
    font-size: 1rem;
    color: #2a215e;
}

.hero-mockup-job-meta {
    margin-top: 0.2rem;
    font-size: 0.74rem;
    line-height: 1.4;
    color: #8b84af;
    font-weight: 700;
}

.hero-mockup-job-score {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 2rem;
    padding: 0 0.72rem;
    border-radius: 999px;
    background: rgba(123, 97, 255, 0.08);
    color: #5f4cc8;
    font-size: 0.78rem;
    font-weight: 800;
    white-space: nowrap;
}

.hero-mockup-job-score--active {
    background: linear-gradient(135deg, #6f56f6 0%, #8a6dff 100%);
    color: #ffffff;
    box-shadow: 0 10px 18px rgba(111, 86, 246, 0.18);
}

.hero-mockup-job-card .hero-mini-tags {
    margin-top: 0.5rem;
}

.hero-mockup-job-card .hero-mini-tag {
    background: rgba(123, 97, 255, 0.07);
    border: 1px solid rgba(123, 97, 255, 0.08);
    color: #6653d3;
}

.hero-mockup-job-card--active .hero-mini-tag {
    background: rgba(111, 86, 246, 0.10);
    border-color: rgba(111, 86, 246, 0.14);
    color: #5a45cc;
}

.hero-mockup-job-footer {
    margin-top: 0.52rem;
    color: #766f98;
    font-size: 0.78rem;
    line-height: 1.4;
    font-weight: 700;
}

.hero-mockup-card--overlay {
    left: 1.15rem;
    top: 8rem;
    width: 11.9rem;
    padding: 0.9rem 0.9rem;
    background: linear-gradient(180deg, rgba(255, 248, 235, 0.96) 0%, rgba(255, 255, 255, 0.98) 100%);
    z-index: 3;
}

.hero-mockup-card--assistant {
    right: 1.15rem;
    bottom: 1rem;
    width: 13.2rem;
    padding: 0.9rem 0.92rem;
    background: linear-gradient(180deg, rgba(246, 242, 255, 0.98) 0%, rgba(255, 255, 255, 0.98) 100%);
    z-index: 3;
}

.hero-mockup-copy {
    margin-top: 0.28rem;
    color: #676083;
    font-size: 0.84rem;
    line-height: 1.6;
    font-weight: 700;
}

.hero-mockup-progress-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.48rem;
    margin-top: 0.58rem;
}

.hero-mockup-progress-item {
    border-radius: 18px;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 240, 255, 0.98) 100%);
    border: 1px solid rgba(123, 97, 255, 0.08);
    padding: 0.58rem 0.42rem 0.56rem;
    text-align: center;
}

.hero-mockup-progress-item span {
    display: block;
    font-size: 0.66rem;
    line-height: 1.3;
    color: #938bb7;
    font-weight: 800;
}

.hero-mockup-progress-item strong {
    display: block;
    margin-top: 0.24rem;
    font-size: 1rem;
    line-height: 1;
    color: #32296f;
    font-weight: 900;
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

    .hero-copy {
        align-self: start;
        display: block;
        min-height: auto;
    }

    .hero-shell {
        margin-top: -2.8rem;
    }

    .hero-mockup {
        min-height: 20.2rem;
    }

    .hero-mockup-card--main {
        left: 4rem;
        right: 1rem;
        top: 3.8rem;
        min-height: 12rem;
        padding: 0.88rem;
    }

    .hero-mockup-card--overlay {
        left: 0.85rem;
        top: 8.6rem;
        width: 10.1rem;
    }

    .hero-mockup-card--assistant {
        right: 0.85rem;
        width: 11.1rem;
        bottom: 0.75rem;
    }

    .hero-mockup-badge--label,
    .hero-mockup-badge--stat {
        transform: scale(0.94);
        transform-origin: top left;
    }

    .hero-mockup-board-pill {
        min-height: 1.8rem;
        padding: 0 0.58rem;
        font-size: 0.7rem;
    }

    .hero-mockup-job-title {
        font-size: 0.82rem;
    }

    .hero-mockup-job-card--active .hero-mockup-job-title {
        font-size: 0.88rem;
    }

    .hero-mockup-job-meta,
    .hero-mockup-job-footer {
        font-size: 0.7rem;
    }

    .hero-mockup-job-score {
        min-height: 1.76rem;
        padding: 0 0.56rem;
        font-size: 0.7rem;
    }

    .hero-mockup-progress-grid {
        gap: 0.34rem;
    }

    .hero-mockup-progress-item {
        padding: 0.5rem 0.3rem;
    }

    .hero-title {
        font-size: 2.2rem;
    }

    .hero-brand-title {
        font-size: 2.05rem;
    }

    .hero-subtitle {
        font-size: 1.02rem;
    }

    .hero-description {
        font-size: 0.94rem;
        line-height: 1.75;
    }

    .hero-actions {
        margin-top: 1.75rem;
        padding-top: 0;
    }
}
"""
