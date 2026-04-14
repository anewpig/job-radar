"""Sections for the full system architecture page."""

from __future__ import annotations

import streamlit as st

from .common import _escape, build_chip_row, render_section_header
from .pages_backend_architecture_helpers import (
    BackendArchitectureData,
    ComponentSpec,
    ExpansionSpec,
    FlowSpec,
    OverviewMetric,
    StoreSpec,
    TopologyCluster,
)


def inject_backend_styles() -> None:
    """Inject page-local styles for the system architecture website."""
    st.markdown(
        """
<style>
.sys-architecture-intro,
.sys-metric-card,
.sys-topology-card,
.sys-component-card,
.sys-store-card,
.sys-flow-card,
.sys-expansion-card,
.sys-runtime-card,
.sys-path-card {
  border:1px solid rgba(25, 54, 67, 0.12);
  border-radius:22px;
  background:
    radial-gradient(circle at top right, rgba(209, 227, 236, 0.42), transparent 42%),
    linear-gradient(180deg, rgba(255,255,255,0.98), rgba(247,250,251,0.98));
  box-shadow:0 18px 34px rgba(20, 38, 46, 0.06);
}
.sys-architecture-intro {
  padding:1.15rem 1.2rem;
  margin-bottom:1rem;
}
.sys-architecture-intro-title {
  font-size:1.05rem;
  font-weight:700;
  color:#18323c;
  margin-bottom:0.35rem;
}
.sys-architecture-intro-body {
  color:rgba(57, 71, 78, 0.9);
  line-height:1.62;
  font-size:0.94rem;
}
.sys-metric-grid,
.sys-topology-grid,
.sys-component-grid,
.sys-store-grid,
.sys-runtime-grid,
.sys-expansion-grid {
  display:grid;
  grid-template-columns:repeat(auto-fit, minmax(250px, 1fr));
  gap:0.95rem;
}
.sys-metric-card {
  padding:1rem 1.05rem;
}
.sys-metric-label,
.sys-card-subtitle,
.sys-block-copy,
.sys-flow-desc,
.sys-topology-summary,
.sys-expansion-stage {
  color:rgba(65, 80, 88, 0.84);
}
.sys-metric-label {
  font-size:0.82rem;
  letter-spacing:0.02em;
}
.sys-metric-value {
  font-size:1.42rem;
  color:#17303a;
  font-weight:700;
  margin:0.2rem 0 0.35rem;
}
.sys-metric-detail {
  color:rgba(65, 80, 88, 0.92);
  line-height:1.48;
  font-size:0.9rem;
}
.sys-track-shell {
  display:flex;
  flex-wrap:wrap;
  gap:0.5rem;
  align-items:center;
  margin-bottom:1rem;
}
.sys-track-node {
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-height:2.2rem;
  padding:0.42rem 0.82rem;
  border-radius:999px;
  background:#17333d;
  color:#fff;
  font-size:0.86rem;
  font-weight:600;
  line-height:1.3;
}
.sys-track-arrow {
  color:#5c7580;
  font-size:1rem;
  font-weight:700;
}
.sys-topology-card,
.sys-component-card,
.sys-store-card,
.sys-flow-card,
.sys-expansion-card,
.sys-runtime-card {
  padding:1rem 1.05rem;
}
.sys-card-head {
  display:flex;
  gap:0.82rem;
  align-items:flex-start;
  margin-bottom:0.8rem;
}
.sys-card-icon {
  flex:0 0 auto;
  min-width:3rem;
  height:3rem;
  border-radius:0.95rem;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  background:linear-gradient(180deg, rgba(24, 50, 60, 1), rgba(38, 83, 99, 0.94));
  color:#fff;
  font-size:0.82rem;
  font-weight:800;
  letter-spacing:0.04em;
  box-shadow:0 12px 24px rgba(18, 35, 41, 0.14);
}
.sys-card-title {
  color:#17303a;
  font-size:1.02rem;
  font-weight:700;
  line-height:1.35;
}
.sys-card-subtitle {
  font-size:0.88rem;
  line-height:1.48;
  margin-top:0.18rem;
}
.sys-topology-summary,
.sys-why-copy,
.sys-flow-desc,
.sys-expansion-why {
  line-height:1.58;
  font-size:0.92rem;
}
.sys-module-row,
.sys-table-row {
  margin-top:0.82rem;
}
.sys-block-grid {
  display:grid;
  grid-template-columns:repeat(2, minmax(0, 1fr));
  gap:0.72rem;
  margin-top:0.85rem;
}
.sys-block-card {
  border:1px solid rgba(24, 50, 60, 0.08);
  border-radius:16px;
  background:rgba(255, 255, 255, 0.72);
  padding:0.82rem 0.85rem;
}
.sys-block-card--good {
  background:rgba(242, 249, 245, 0.92);
  border-color:rgba(63, 123, 87, 0.15);
}
.sys-block-card--risk {
  background:rgba(252, 247, 243, 0.96);
  border-color:rgba(167, 103, 76, 0.14);
}
.sys-block-card--alt {
  background:rgba(245, 248, 251, 0.94);
  border-color:rgba(91, 120, 137, 0.14);
}
.sys-block-card--scale {
  background:rgba(247, 249, 255, 0.95);
  border-color:rgba(92, 108, 170, 0.14);
}
.sys-block-title {
  color:#17303a;
  font-size:0.84rem;
  font-weight:700;
  margin-bottom:0.4rem;
}
.sys-bullet-list {
  margin:0;
  padding-left:1.05rem;
  color:rgba(51, 65, 72, 0.92);
  line-height:1.5;
  font-size:0.88rem;
}
.sys-bullet-list li + li {
  margin-top:0.28rem;
}
.sys-fact-grid {
  display:grid;
  grid-template-columns:repeat(auto-fit, minmax(120px, 1fr));
  gap:0.55rem;
  margin-top:0.86rem;
}
.sys-fact-pill {
  border-radius:14px;
  background:rgba(244, 247, 248, 0.92);
  border:1px solid rgba(24, 50, 60, 0.08);
  padding:0.55rem 0.65rem;
}
.sys-fact-label {
  color:rgba(64, 79, 86, 0.82);
  font-size:0.74rem;
  margin-bottom:0.16rem;
}
.sys-fact-value {
  color:#17303a;
  font-size:0.9rem;
  font-weight:700;
}
.sys-store-location,
.sys-path-value code {
  display:block;
  margin-top:0.68rem;
  padding:0.72rem 0.8rem;
  border-radius:14px;
  background:rgba(247, 250, 252, 0.96);
  border:1px dashed rgba(24, 50, 60, 0.16);
  white-space:pre-wrap;
  word-break:break-word;
  color:#18323c;
  font-size:0.84rem;
}
.sys-flow-card + .sys-flow-card {
  margin-top:0.92rem;
}
.sys-flow-note-list {
  margin-top:0.82rem;
  padding-left:1.05rem;
  color:rgba(52, 66, 73, 0.92);
  line-height:1.54;
  font-size:0.89rem;
}
.sys-flow-note-list li + li {
  margin-top:0.26rem;
}
.sys-expansion-card {
  min-height:100%;
}
.sys-expansion-stage {
  font-size:0.84rem;
  line-height:1.48;
  margin-top:0.16rem;
}
.sys-expansion-why {
  margin-top:0.72rem;
  color:rgba(52, 66, 73, 0.92);
}
.sys-runtime-card-title {
  color:#17303a;
  font-size:0.98rem;
  font-weight:700;
  margin-bottom:0.72rem;
}
.sys-status-table {
  display:grid;
  gap:0.58rem;
}
.sys-status-row {
  display:flex;
  justify-content:space-between;
  gap:1rem;
  padding-bottom:0.5rem;
  border-bottom:1px solid rgba(24, 50, 60, 0.08);
}
.sys-status-row:last-child {
  border-bottom:none;
  padding-bottom:0;
}
.sys-status-key {
  color:rgba(65, 80, 88, 0.84);
  font-size:0.86rem;
}
.sys-status-value {
  color:#17303a;
  font-size:0.87rem;
  font-weight:600;
  text-align:right;
}
.sys-path-card {
  margin-top:0.95rem;
  padding:1rem 1.05rem;
}
.sys-path-grid {
  display:grid;
  gap:0.62rem;
}
.sys-path-row {
  display:grid;
  grid-template-columns:180px minmax(0, 1fr);
  gap:0.9rem;
  align-items:start;
}
.sys-path-label {
  color:rgba(65, 80, 88, 0.82);
  font-size:0.86rem;
  padding-top:0.22rem;
}
.sys-path-value code {
  margin-top:0;
}
@media (max-width: 900px) {
  .sys-block-grid {
    grid-template-columns:1fr;
  }
  .sys-path-row {
    grid-template-columns:1fr;
    gap:0.45rem;
  }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _render_list_html(items: list[str]) -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return '<ul class="sys-bullet-list"><li>目前沒有資料。</li></ul>'
    bullets = "".join(f"<li>{_escape(item)}</li>" for item in cleaned)
    return f'<ul class="sys-bullet-list">{bullets}</ul>'


def _metric_card(metric: OverviewMetric) -> str:
    return f"""
<div class="sys-metric-card">
  <div class="sys-metric-label">{_escape(metric.label)}</div>
  <div class="sys-metric-value">{_escape(metric.value)}</div>
  <div class="sys-metric-detail">{_escape(metric.detail)}</div>
</div>
"""


def _topology_card(cluster: TopologyCluster) -> str:
    return f"""
<div class="sys-topology-card">
  <div class="sys-card-head">
    <div class="sys-card-icon">{_escape(cluster.icon)}</div>
    <div>
      <div class="sys-card-title">{_escape(cluster.title)}</div>
      <div class="sys-topology-summary">{_escape(cluster.summary)}</div>
    </div>
  </div>
  {_render_list_html(cluster.items)}
</div>
"""


def _component_card(component: ComponentSpec) -> str:
    modules_html = (
        f'<div class="sys-module-row">{build_chip_row(component.modules, tone="soft")}</div>'
        if component.modules
        else ""
    )
    return f"""
<div class="sys-component-card">
  <div class="sys-card-head">
    <div class="sys-card-icon">{_escape(component.icon)}</div>
    <div>
      <div class="sys-card-title">{_escape(component.title)}</div>
      <div class="sys-card-subtitle">{_escape(component.subtitle)}</div>
    </div>
  </div>
  <div class="sys-block-card">
    <div class="sys-block-title">為什麼這樣做</div>
    <div class="sys-why-copy">{_escape(component.why)}</div>
  </div>
  <div class="sys-block-grid">
    <div class="sys-block-card sys-block-card--good">
      <div class="sys-block-title">優點</div>
      {_render_list_html(component.pros)}
    </div>
    <div class="sys-block-card sys-block-card--risk">
      <div class="sys-block-title">缺點 / 風險</div>
      {_render_list_html(component.cons)}
    </div>
    <div class="sys-block-card sys-block-card--alt">
      <div class="sys-block-title">可替代方案</div>
      {_render_list_html(component.alternatives)}
    </div>
    <div class="sys-block-card sys-block-card--scale">
      <div class="sys-block-title">要擴充時怎麼做</div>
      {_render_list_html(component.scaling)}
    </div>
  </div>
  {modules_html}
</div>
"""


def _store_card(store: StoreSpec) -> str:
    facts_html = "".join(
        f"""
<div class="sys-fact-pill">
  <div class="sys-fact-label">{_escape(label)}</div>
  <div class="sys-fact-value">{_escape(value)}</div>
</div>
"""
        for label, value in store.facts
    )
    tables_html = (
        f'<div class="sys-table-row">{build_chip_row(store.tables, tone="warm", limit=14)}</div>'
        if store.tables
        else ""
    )
    return f"""
<div class="sys-store-card">
  <div class="sys-card-head">
    <div class="sys-card-icon">{_escape(store.icon)}</div>
    <div>
      <div class="sys-card-title">{_escape(store.title)}</div>
      <div class="sys-card-subtitle">{_escape(store.purpose)}</div>
    </div>
  </div>
  <div class="sys-block-card">
    <div class="sys-block-title">為什麼這樣做</div>
    <div class="sys-why-copy">{_escape(store.why)}</div>
  </div>
  <div class="sys-store-location"><code>{_escape(store.location)}</code></div>
  <div class="sys-fact-grid">{facts_html}</div>
  <div class="sys-block-grid">
    <div class="sys-block-card sys-block-card--good">
      <div class="sys-block-title">優點</div>
      {_render_list_html(store.pros)}
    </div>
    <div class="sys-block-card sys-block-card--risk">
      <div class="sys-block-title">缺點 / 風險</div>
      {_render_list_html(store.cons)}
    </div>
    <div class="sys-block-card sys-block-card--alt">
      <div class="sys-block-title">可替代方案</div>
      {_render_list_html(store.alternatives)}
    </div>
    <div class="sys-block-card sys-block-card--scale">
      <div class="sys-block-title">要擴充時怎麼做</div>
      {_render_list_html(store.scaling)}
    </div>
  </div>
  {tables_html}
</div>
"""


def _flow_card(flow: FlowSpec) -> str:
    nodes_html = "".join(
        (
            f'<span class="sys-track-node">{_escape(node)}</span>'
            if index == len(flow.nodes) - 1
            else (
                f'<span class="sys-track-node">{_escape(node)}</span>'
                '<span class="sys-track-arrow">→</span>'
            )
        )
        for index, node in enumerate(flow.nodes)
    )
    return f"""
<div class="sys-flow-card">
  <div class="sys-card-title">{_escape(flow.title)}</div>
  <div class="sys-flow-desc">{_escape(flow.description)}</div>
  <div class="sys-track-shell" style="margin-top:0.82rem;">{nodes_html}</div>
  <ul class="sys-flow-note-list">
    {"".join(f"<li>{_escape(note)}</li>" for note in flow.notes)}
  </ul>
</div>
"""


def _expansion_card(spec: ExpansionSpec) -> str:
    return f"""
<div class="sys-expansion-card">
  <div class="sys-card-title">{_escape(spec.title)}</div>
  <div class="sys-expansion-stage">{_escape(spec.stage)}</div>
  <div class="sys-expansion-why">{_escape(spec.why)}</div>
  <div class="sys-block-grid" style="margin-top:0.82rem;">
    <div class="sys-block-card sys-block-card--scale">
      <div class="sys-block-title">建議做法</div>
      {_render_list_html(spec.actions)}
    </div>
    <div class="sys-block-card sys-block-card--risk">
      <div class="sys-block-title">代價 / 取捨</div>
      {_render_list_html(spec.tradeoffs)}
    </div>
  </div>
</div>
"""


def _runtime_card(title: str, rows: list[tuple[str, str]]) -> str:
    row_html = "".join(
        f"""
<div class="sys-status-row">
  <span class="sys-status-key">{_escape(label)}</span>
  <span class="sys-status-value">{_escape(value)}</span>
</div>
"""
        for label, value in rows
    )
    return f"""
<div class="sys-runtime-card">
  <div class="sys-runtime-card-title">{_escape(title)}</div>
  <div class="sys-status-table">{row_html}</div>
</div>
"""


def render_summary_section(data: BackendArchitectureData) -> None:
    """Render page intro and overview metrics."""
    render_section_header(
        "全系統架構",
        "把前端、後端、AI、DB、整體拓樸與資料流放進同一張系統地圖，看的不是抽象概念，而是目前這個專案的實作。",
        "System Blueprint",
    )
    st.markdown(
        f"""
<div class="sys-architecture-intro">
  <div class="sys-architecture-intro-title">這頁在看什麼</div>
  <div class="sys-architecture-intro-body">{_escape(data.overview_intro)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="sys-metric-grid">{"".join(_metric_card(metric) for metric in data.overview_metrics)}</div>',
        unsafe_allow_html=True,
    )


def render_topology_section(data: BackendArchitectureData) -> None:
    """Render the high-level system topology diagram."""
    render_section_header(
        "整體拓樸圖",
        "先看大圖：使用者互動、UI 協調、核心服務、持久化與外部系統是怎麼串起來的。",
        "Topology",
    )
    track_html = "".join(
        (
            f'<span class="sys-track-node">{_escape(cluster.title)}</span>'
            if index == len(data.topology_clusters) - 1
            else (
                f'<span class="sys-track-node">{_escape(cluster.title)}</span>'
                '<span class="sys-track-arrow">→</span>'
            )
        )
        for index, cluster in enumerate(data.topology_clusters)
    )
    st.markdown(f'<div class="sys-track-shell">{track_html}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sys-topology-grid">{"".join(_topology_card(cluster) for cluster in data.topology_clusters)}</div>',
        unsafe_allow_html=True,
    )


def _render_component_section(
    *,
    title: str,
    description: str,
    kicker: str,
    components: list[ComponentSpec],
) -> None:
    render_section_header(title, description, kicker)
    st.markdown(
        f'<div class="sys-component-grid">{"".join(_component_card(component) for component in components)}</div>',
        unsafe_allow_html=True,
    )


def render_frontend_section(data: BackendArchitectureData) -> None:
    """Render the frontend architecture section."""
    _render_component_section(
        title="前端架構",
        description="前端不是單純畫頁面，而是承接搜尋、狀態恢復、頁面切換、浮動工具與 staged feedback 的協調層。",
        kicker="Frontend",
        components=data.frontend_components,
    )


def render_backend_section(data: BackendArchitectureData) -> None:
    """Render the backend architecture section."""
    _render_component_section(
        title="後端架構",
        description="後端目前是模組化單體：沒有獨立 API server，但 service、pipeline、runtime、store 邊界已經成形。",
        kicker="Backend",
        components=data.backend_components,
    )


def render_ai_section(data: BackendArchitectureData) -> None:
    """Render the AI section."""
    _render_component_section(
        title="AI 架構",
        description="這個系統目前有兩條 AI 能力鏈：履歷分析與 RAG 助理；兩者都建立在同一份市場快照之上。",
        kicker="AI",
        components=data.ai_components,
    )


def render_database_section(data: BackendArchitectureData) -> None:
    """Render the storage/database architecture section."""
    render_section_header(
        "DB 與持久化架構",
        "現在的資料層不是只有一個 DB，而是按責任切成 product、runtime、user submissions、history，再搭配 JSON snapshot / cache。",
        "Storage",
    )
    st.markdown(
        f'<div class="sys-store-grid">{"".join(_store_card(store) for store in data.store_specs)}</div>',
        unsafe_allow_html=True,
    )


def render_flow_section(data: BackendArchitectureData) -> None:
    """Render the main data-flow diagrams."""
    render_section_header(
        "主要資料流圖",
        "這四條是這個系統最重要的執行路徑：手動查詢、自動刷新、履歷分析、AI 問答。",
        "Data Flow",
    )
    st.markdown(
        f'<div>{"".join(_flow_card(flow) for flow in data.flow_specs)}</div>',
        unsafe_allow_html=True,
    )


def render_scaling_section(data: BackendArchitectureData) -> None:
    """Render scaling and future-extension guidance."""
    render_section_header(
        "如果要擴充，下一步怎麼走",
        "這裡不是空泛的『可擴充』，而是把不同成長情境拆開來看：何時要動、先動哪一層、會付出什麼代價。",
        "Scale",
    )
    st.markdown(
        f'<div class="sys-expansion-grid">{"".join(_expansion_card(spec) for spec in data.expansion_specs)}</div>',
        unsafe_allow_html=True,
    )


def render_storage_section(data: BackendArchitectureData) -> None:
    """Render live runtime/status cards and concrete storage paths."""
    render_section_header(
        "目前環境與資料落點",
        "這裡是這個工作區目前真的在用的狀態與路徑，不是寫死的示意資料。",
        "Live State",
    )
    st.markdown(
        f'<div class="sys-runtime-grid">{"".join(_runtime_card(title, rows) for title, rows in data.runtime_cards)}</div>',
        unsafe_allow_html=True,
    )
    path_rows_html = "".join(
        f"""
<div class="sys-path-row">
  <div class="sys-path-label">{_escape(label)}</div>
  <div class="sys-path-value"><code>{_escape(path)}</code></div>
</div>
"""
        for label, path in data.storage_rows
    )
    st.markdown(
        f"""
<div class="sys-path-card">
  <div class="sys-runtime-card-title">實際檔案 / DB 路徑</div>
  <div class="sys-path-grid">{path_rows_html}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_tables_expander(data: BackendArchitectureData) -> None:
    """Render raw table names for all SQLite databases."""
    with st.expander("查看目前 SQLite tables", expanded=False):
        st.write("`product_state.sqlite3`")
        st.code("\n".join(data.product_tables) or "尚未建立")
        st.write("`user_submissions.sqlite3`")
        st.code("\n".join(data.user_tables) or "尚未建立")
        st.write("`query_runtime.sqlite3`")
        st.code("\n".join(data.query_tables) or "尚未建立")
        st.write("`market_history.sqlite3`")
        st.code("\n".join(data.history_tables) or "尚未建立")
