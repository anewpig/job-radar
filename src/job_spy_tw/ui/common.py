from __future__ import annotations

import html

import streamlit as st

from ..models import MarketSnapshot, TargetRole


def _escape(text: object) -> str:
    return html.escape(str(text))


def _escape_multiline(text: object) -> str:
    return _escape(text).replace("\n", "<br>")


def build_chip_row(
    items: list[str],
    *,
    empty_text: str = "未設定",
    tone: str = "accent",
    limit: int | None = None,
) -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if limit is not None:
        cleaned = cleaned[:limit]
    if not cleaned:
        return f'<span class="ui-chip empty-chip">{_escape(empty_text)}</span>'
    tone_class = {
        "accent": "ui-chip ui-chip--accent",
        "soft": "ui-chip ui-chip--soft",
        "warm": "ui-chip ui-chip--warm",
    }.get(tone, "ui-chip")
    return "".join(
        f'<span class="{tone_class}">{_escape(item)}</span>' for item in cleaned
    )


def build_html_list(items: list[str], *, empty_text: str, limit: int) -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()][:limit]
    if not cleaned:
        return f'<li class="empty-chip">{_escape(empty_text)}</li>'
    return "".join(f"<li>{_escape(item)}</li>" for item in cleaned)


def mask_identifier(value: str, *, prefix: int = 3, suffix: int = 3) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        return ""
    if len(cleaned) <= prefix + suffix:
        return cleaned[:1] + "***"
    return f"{cleaned[:prefix]}***{cleaned[-suffix:]}"


def render_hero(snapshot: MarketSnapshot | None, role_targets: list[TargetRole]) -> None:
    role_names = [role.name for role in role_targets if role.name.strip()]
    if role_names:
        pill_markup = "".join(
            f'<span class="hero-pill">{_escape(role_name)}</span>'
            for role_name in role_names[:6]
        )
    else:
        pill_markup = "".join(
            f'<span class="hero-pill">{label}</span>'
            for label in (
                "原文職缺解析",
                "履歷匹配",
                "技能地圖",
            )
        )

    snapshot_meta = (
        f"最新快照 {snapshot.generated_at}"
        if snapshot is not None
        else "設定搜尋條件後即可建立市場快照"
    )
    subtitle = (
        "把 104、1111、LinkedIn 的職缺原文拆成工作內容、技能需求與條件，"
        "再用履歷匹配、技能統計與 AI 問答幫你快速看懂市場。"
    )
    st.markdown(
        f"""
<div class="hero-shell">
  <div class="hero-kicker">Taiwan Job Intelligence</div>
  <h1 class="hero-title">職缺雷達</h1>
  <p class="hero-subtitle">{subtitle}</p>
  <div class="hero-pill-row">
    {pill_markup}
    <span class="hero-pill">{_escape(snapshot_meta)}</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, description: str, kicker: str) -> None:
    st.markdown(
        f"""
<div class="section-shell">
  <div class="section-kicker">{_escape(kicker)}</div>
  <div class="section-title">{_escape(title)}</div>
  <div class="section-desc">{_escape(description)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _format_ranked_terms(items: list[tuple[str, int]], tone: str) -> str:
    if not items:
        return build_chip_row([], tone=tone)
    labels = [f"{label} ×{count}" for label, count in items]
    return build_chip_row(labels, tone=tone, limit=8)
