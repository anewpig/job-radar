"""提供 Header、Hero 與 HTML 輔助片段等共用 UI 元件。"""

from __future__ import annotations

import html

import streamlit as st

from ..models import MarketSnapshot, TargetRole
from .dev_annotations import render_dev_card_annotation


def _escape(text: object) -> str:
    """把任意文字轉成可安全嵌入 HTML 的內容。"""
    return html.escape(str(text))


def _escape_multiline(text: object) -> str:
    """轉義文字並保留換行，方便直接輸出到 HTML 片段。"""
    return _escape(text).replace("\n", "<br>")


def build_chip_row(
    items: list[str],
    *,
    empty_text: str = "未設定",
    tone: str = "accent",
    limit: int | None = None,
) -> str:
    """把字串清單渲染成一排扁平的 HTML chip。"""
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
    """把資料渲染成簡單的 HTML 清單，並處理空狀態。"""
    cleaned = [str(item).strip() for item in items if str(item).strip()][:limit]
    if not cleaned:
        return f'<li class="empty-chip">{_escape(empty_text)}</li>'
    return "".join(f"<li>{_escape(item)}</li>" for item in cleaned)


def mask_identifier(value: str, *, prefix: int = 3, suffix: int = 3) -> str:
    """遮罩使用者識別字串，只保留少量前後綴。"""
    cleaned = str(value or "").strip()
    if not cleaned:
        return ""
    if len(cleaned) <= prefix + suffix:
        return cleaned[:1] + "***"
    return f"{cleaned[:prefix]}***{cleaned[-suffix:]}"


def render_top_header(total_visit_count: int) -> None:
    """渲染全站共用的吸頂 Header。"""
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


def render_hero(snapshot: MarketSnapshot | None, role_targets: list[TargetRole]) -> None:
    """渲染首頁 Hero 區塊，包含快照摘要與產品 mockup。"""
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
        "搜尋摘要 CTA 卡",
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
    cards = "".join(
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
  <div class="cta-stat-grid">{cards}</div>
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


def _format_ranked_terms(items: list[tuple[str, int]], tone: str) -> str:
    """把排序後的詞項整理成保留次數標記的 chip 列。"""
    if not items:
        return build_chip_row([], tone=tone)
    labels = [f"{label} ×{count}" for label, count in items]
    return build_chip_row(labels, tone=tone, limit=8)
