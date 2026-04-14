"""Shared layout/shell components."""

from __future__ import annotations

import streamlit as st

from ..models import MarketSnapshot
from .common_html import _escape
from .dev_annotations import render_dev_card_annotation


def render_top_header(total_visit_count: int) -> None:
    """渲染全站共用的吸頂 Header。"""
    _ = total_visit_count
    st.markdown(
        f"""
<div id="page-top-anchor" class="top-header-host">
  <div class="top-header-fixed">
    <div class="top-header-shell">
      <div class="top-header-brand">
        <div class="top-header-logo">JR</div>
        <div>
          <div class="top-header-title">職缺雷達</div>
          <div class="top-header-subtitle">用職缺原文、履歷匹配與 AI 助理整理你的求職工作台</div>
        </div>
      </div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, description: str, kicker: str) -> None:
    """渲染可重複使用的區塊標題。"""
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


def render_metrics_cta(
    *,
    row_count: int,
    crawl_preset_label: str,
    refresh_mode: str,
    snapshot: MarketSnapshot | None,
) -> None:
    """渲染搜尋設定右側的即時摘要卡。"""
    render_dev_card_annotation(
        "搜尋摘要卡",
        element_id="metrics-cta-card",
        description="搜尋設定右側的摘要卡，集中顯示本次抓取設定與主要統計。",
        layers=[
            "cta-summary-head",
            "cta-summary-meta-wrap",
            "cta-meta-row",
            "cta-stat-grid",
        ],
        text_nodes=[
            ("cta-title", "摘要卡主標題。"),
            ("cta-copy", "摘要卡的說明文字。"),
            ("cta-meta-label", "抓取速度 / 更新模式的小標文字。"),
            ("cta-stat-label", "統計卡的小標文字。"),
            ("cta-stat-value", "統計卡的大數字。"),
        ],
        notes=[
            "這張卡主要用來幫你對照右側資訊，不是操作區。",
        ],
        show_popover=True,
        popover_key="metrics-cta-card",
    )
    has_snapshot = snapshot is not None
    total_jobs = f"{len(snapshot.jobs):,}" if has_snapshot else "尚未分析"
    total_skills = f"{len(snapshot.skills):,}" if has_snapshot else "尚未分析"
    cards = [
        ("目標職缺數", f"{row_count} 項", False),
        ("總職缺數", total_jobs, False),
        ("技能數", total_skills, True),
    ]
    cards_html = "".join(
        f"""
<div class="cta-stat-card{' cta-stat-card--wide' if is_wide else ''}">
  <div class="cta-stat-label">{_escape(label)}</div>
  <div class="cta-stat-value">{_escape(value)}</div>
</div>
        """
        for label, value, is_wide in cards
    )
    st.markdown(
        f"""
<div class="cta-shell cta-shell--search-summary">
  <div class="cta-summary-head">
    <div class="cta-title">本次搜尋摘要</div>
    <div class="cta-copy">快速確認這次要抓的職缺與設定。</div>
  </div>
  <div class="cta-summary-meta-wrap">
    <div class="cta-meta-row">
      <div class="cta-meta-pill">
        <span class="cta-meta-label">抓取速度</span>
        <strong>{_escape(crawl_preset_label)}</strong>
      </div>
      <div class="cta-meta-pill">
        <span class="cta-meta-label">更新模式</span>
        <strong>{_escape(refresh_mode)}</strong>
      </div>
    </div>
  </div>
  <div class="cta-stat-grid">{cards_html}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_newsletter_footer(total_visit_count: int) -> None:
    """渲染頁尾外框與累計來訪次數。"""
    render_dev_card_annotation(
        "頁尾 CTA 卡",
        element_id="newsletter-shell",
        description="頁面最底部的品牌收尾區塊，包含功能摘要與累計來訪數。",
        layers=[
            "newsletter-actions",
            "newsletter-footer-row",
            "newsletter-footer-meta",
        ],
        text_nodes=[
            ("newsletter-kicker", "頁尾上方小標。"),
            ("newsletter-title", "頁尾主標題。"),
            ("newsletter-copy", "頁尾說明段落。"),
            ("newsletter-pill", "頁尾功能 tag。"),
            ("newsletter-footer-visit", "右側累計來訪文字。"),
        ],
        show_popover=True,
        popover_key="newsletter-shell",
    )
    st.markdown(
        f"""
<div class="newsletter-shell">
  <div class="newsletter-kicker">Newsletter / Footer</div>
  <div class="newsletter-title">Want to keep your job search workspace organized?</div>
  <div class="newsletter-copy">把搜尋、履歷匹配、AI 助理、追蹤中心和投遞看板整合在同一個介面，之後無論是自用或公開展示都更像完整產品。</div>
  <div class="newsletter-actions">
    <span class="newsletter-pill">職缺總覽</span>
    <span class="newsletter-pill">履歷匹配</span>
    <span class="newsletter-pill">AI 助理</span>
    <span class="newsletter-pill">投遞看板</span>
  </div>
  <div class="newsletter-footer-row">
    <div class="newsletter-footer-meta">
      <span>Job Radar Workspace</span>
      <span>104 / 1111 / Cake / LinkedIn</span>
      <span>Built with Streamlit</span>
    </div>
    <div class="newsletter-footer-visit">累計來訪 {total_visit_count:,} 人次</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
