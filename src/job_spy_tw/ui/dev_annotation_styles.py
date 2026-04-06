"""提供開發標註區塊的 CSS 片段。"""

DEV_ANNOTATION_STYLES = """
.dev-card-annotation-shell {
    margin: 0 0 0.7rem;
    padding: 0.55rem 0.7rem;
    border-radius: 18px;
    border: 1px dashed rgba(79, 70, 229, 0.24);
    background: linear-gradient(180deg, rgba(248, 247, 255, 0.98) 0%, rgba(242, 240, 255, 0.96) 100%);
}

.dev-card-annotation-shell--compact {
    margin-bottom: 0.45rem;
    padding: 0.48rem 0.6rem;
}

.dev-card-annotation-row {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.7rem;
}

.dev-card-annotation-row--compact {
    gap: 0.5rem;
}

.dev-card-annotation-left {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.45rem;
}

.dev-card-annotation__pill,
.dev-card-annotation__id {
    display: inline-flex;
    align-items: center;
    min-height: 1.75rem;
    padding: 0.22rem 0.6rem;
    border-radius: 999px;
    font-size: 0.76rem;
    line-height: 1.3;
}

.dev-card-annotation__pill {
    background: rgba(79, 70, 229, 0.12);
    color: #3f33a1;
    font-weight: 800;
}

.dev-card-annotation__id {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(79, 70, 229, 0.14);
    color: #5e5690;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

details.dev-card-annotation-details {
    margin: 0;
    padding: 0;
    border: none !important;
    background: transparent;
    box-shadow: none;
}

.dev-card-annotation-details__summary {
    cursor: pointer;
    list-style: none;
    border-radius: 999px;
    border: 1px solid rgba(79, 70, 229, 0.16);
    background: rgba(255, 255, 255, 0.94);
    color: #4338ca;
    padding: 0.32rem 0.72rem;
    font-size: 0.76rem;
    font-weight: 700;
}

.dev-card-annotation-details__summary::-webkit-details-marker {
    display: none;
}

.dev-card-annotation-details__summary:hover {
    border-color: rgba(79, 70, 229, 0.28);
    background: rgba(255, 255, 255, 0.98);
}

.dev-card-annotation-details__panel {
    margin-top: 0.6rem;
    padding: 0.78rem 0.9rem;
    border-radius: 16px;
    border: 1px solid rgba(79, 70, 229, 0.12);
    background: rgba(255, 255, 255, 0.95);
}

.dev-card-annotation-details__title {
    color: #231c63;
    font-size: 0.96rem;
    font-weight: 900;
}

.dev-card-annotation-details__meta {
    margin-top: 0.42rem;
    color: #5e5690;
    font-size: 0.78rem;
}

.dev-card-annotation-details__meta code,
.dev-card-annotation-details__list code {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 0.74rem;
}

.dev-card-annotation-details__copy {
    margin-top: 0.55rem;
    color: #3e3865;
    font-size: 0.84rem;
    line-height: 1.6;
}

.dev-card-annotation-details__section-title {
    margin-top: 0.8rem;
    color: #4338ca;
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.dev-card-annotation-details__list {
    margin: 0.45rem 0 0;
    padding-left: 1.1rem;
    color: #3e3865;
}

.dev-card-annotation-details__list li + li {
    margin-top: 0.38rem;
}

.dev-card-annotation-details__list--named {
    padding-left: 0;
    list-style: none;
}

.dev-card-annotation-details__named-item {
    display: grid;
    grid-template-columns: minmax(9rem, max-content) 1fr;
    gap: 0.55rem;
    align-items: start;
}

.dev-card-annotation-details__named-item code {
    display: inline-flex;
    width: fit-content;
    padding: 0.14rem 0.38rem;
    border-radius: 8px;
    background: rgba(79, 70, 229, 0.08);
    color: #392f92;
}

.dev-card-annotation-details__named-item span {
    color: #4d476f;
    font-size: 0.8rem;
    line-height: 1.55;
}

@media (max-width: 960px) {
    .dev-card-annotation-row {
        flex-direction: column;
        align-items: stretch;
    }

    .dev-card-annotation-details__named-item {
        grid-template-columns: 1fr;
        gap: 0.25rem;
    }
}
"""
