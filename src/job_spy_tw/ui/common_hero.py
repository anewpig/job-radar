"""Hero section renderer."""

from __future__ import annotations

import streamlit as st

from ..models import MarketSnapshot, TargetRole
from .common_html import _escape
from .dev_annotations import render_dev_card_annotation


def render_hero(snapshot: MarketSnapshot | None, role_targets: list[TargetRole]) -> None:
    """渲染首頁 Hero 區塊，包含快照摘要與產品 mockup。"""
    _ = role_targets
    total_jobs = len(snapshot.jobs) if snapshot is not None else 0
    headline = "四個求職網站的職缺，一次整合"
    subtitle = (
        "整合 104、1111、Cake 和 LinkedIn 的職缺內容，統一呈現市場需求、技能趨勢與投遞進度，"
        "幫你省下反覆切換網站與整理資訊的時間，讓你更快看懂市場、篩出適合機會並安排下一步，"
        "也能更清楚掌握企業正在找什麼樣的技能與人才，提升每一次投遞與準備的效率。"
    )
    secondary_line = "原文解析｜履歷匹配｜AI 助理｜投遞看板"
    synced_jobs_label = f"{total_jobs} 筆職缺" if total_jobs else "本日精選"
    with st.container(key="hero-dev-annotation-shell"):
        render_dev_card_annotation(
            "首頁 Hero 卡",
            element_id="hero-shell",
            description="首頁最上方的品牌與產品展示區，左側是價值主張，右側是產品 mockup。",
            layers=[
                "hero-copy",
                "hero-actions",
                "hero-visual",
                "hero-mockup-card--main",
                "hero-mockup-card--overlay",
                "hero-mockup-card--assistant",
            ],
            text_nodes=[
                ("hero-kicker", "Hero 左上角英文小標。"),
                ("hero-brand-title", "產品中文品牌名稱。"),
                ("hero-headline", "Hero 主標題文字。"),
                ("hero-description", "主敘述段落。"),
                ("hero-action-button", "主要 CTA 按鈕文字。"),
                ("hero-action-note", "CTA 旁的功能摘要小字。"),
                ("hero-mockup-kicker", "右側 mockup 卡片上方的小標。"),
                ("hero-mockup-title", "右側主卡的大標文字。"),
                ("hero-mockup-job-title", "模擬職缺卡的職稱文字。"),
                ("hero-mockup-job-meta", "模擬職缺卡的來源 / 團隊資訊。"),
                ("hero-mini-tag", "Hero mockup 內的小技能 tag。"),
                ("hero-mockup-job-footer", "模擬職缺卡底部地點文字。"),
                ("hero-mockup-copy", "浮層 AI 建議內容文字。"),
            ],
            notes=[
                "如果你想再細拆每一個 mockup badge 或分數 tag，可再從這張 Hero 卡往下拆子標註。",
            ],
            show_popover=True,
            popover_key="hero-shell",
        )
    st.markdown(
        f"""
<div class="hero-shell">
  <div class="hero-grid">
    <div class="hero-copy">
      <div class="hero-kicker">Job Search Workspace</div>
      <div class="hero-brand-title">職缺雷達</div>
      <div class="hero-headline">{_escape(headline)}</div>
      <div class="hero-description">{_escape(subtitle)}</div>
      <div class="hero-actions">
        <a class="hero-action-button hero-action-button--link" href="?auth=start">立即開始</a>
        <span class="hero-action-note">{_escape(secondary_line)}</span>
      </div>
    </div>
    <div class="hero-visual">
      <div class="hero-mockup">
        <div class="hero-mockup-radar-ring hero-mockup-radar-ring--one"></div>
        <div class="hero-mockup-radar-ring hero-mockup-radar-ring--two"></div>
        <div class="hero-mockup-orb hero-mockup-orb--one"></div>
        <div class="hero-mockup-orb hero-mockup-orb--two"></div>
        <div class="hero-mockup-badge hero-mockup-badge--label">Job Radar</div>
        <div class="hero-mockup-badge hero-mockup-badge--stat">四站同步</div>
        <div class="hero-mockup-card hero-mockup-card--main">
          <div class="hero-mockup-board-head">
            <div>
              <div class="hero-mockup-kicker">職缺總覽</div>
              <div class="hero-mockup-title">今天值得優先看的職缺</div>
            </div>
            <div class="hero-mockup-board-pill">{_escape(synced_jobs_label)}</div>
          </div>
          <div class="hero-mockup-job-list">
            <div class="hero-mockup-job-card">
              <div class="hero-mockup-job-top">
                <div>
                  <div class="hero-mockup-job-title">生成式 AI 後端工程師</div>
                  <div class="hero-mockup-job-meta">LinkedIn｜技術產品團隊</div>
                </div>
                <div class="hero-mockup-job-score">78</div>
              </div>
              <div class="hero-mini-tags">
                <span class="hero-mini-tag">Python</span>
                <span class="hero-mini-tag">API</span>
                <span class="hero-mini-tag">Prompt</span>
              </div>
              <div class="hero-mockup-job-footer">新北 / 混合辦公</div>
            </div>
            <div class="hero-mockup-job-card hero-mockup-job-card--active">
              <div class="hero-mockup-job-top">
                <div>
                  <div class="hero-mockup-job-title">AI 應用工程師</div>
                  <div class="hero-mockup-job-meta">104｜AI Product Team</div>
                </div>
                <div class="hero-mockup-job-score hero-mockup-job-score--active">Match 86</div>
              </div>
              <div class="hero-mini-tags">
                <span class="hero-mini-tag">Python</span>
                <span class="hero-mini-tag">LLM</span>
                <span class="hero-mini-tag">RAG</span>
              </div>
              <div class="hero-mockup-job-footer">台北 / 遠端</div>
            </div>
            <div class="hero-mockup-job-card">
              <div class="hero-mockup-job-top">
                <div>
                  <div class="hero-mockup-job-title">資料產品經理</div>
                  <div class="hero-mockup-job-meta">Cake｜成長數據團隊</div>
                </div>
                <div class="hero-mockup-job-score">74</div>
              </div>
              <div class="hero-mini-tags">
                <span class="hero-mini-tag">SQL</span>
                <span class="hero-mini-tag">GA4</span>
                <span class="hero-mini-tag">Dashboard</span>
              </div>
              <div class="hero-mockup-job-footer">台北 / 混合辦公</div>
            </div>
          </div>
        </div>
        <div class="hero-mockup-card hero-mockup-card--overlay">
          <div class="hero-mockup-kicker">AI 建議</div>
          <div class="hero-mockup-copy">先投遞這 3 筆，原因是技能命中高。</div>
        </div>
        <div class="hero-mockup-card hero-mockup-card--assistant">
          <div class="hero-mockup-kicker">投遞進度</div>
          <div class="hero-mockup-progress-grid">
            <div class="hero-mockup-progress-item">
              <span>已收藏</span>
              <strong>18</strong>
            </div>
            <div class="hero-mockup-progress-item">
              <span>已投遞</span>
              <strong>6</strong>
            </div>
            <div class="hero-mockup-progress-item">
              <span>面試中</span>
              <strong>2</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
