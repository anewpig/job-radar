"""Render a backend architecture dashboard inside the Streamlit app."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3

import streamlit as st

from ..storage import load_snapshot
from .common import _escape, build_chip_row, render_section_header
from .page_context import PageContext


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).strip())
    except Exception:  # noqa: BLE001
        return None


def _format_relative_time(value: str) -> str:
    parsed = _parse_iso(value)
    if parsed is None:
        return "尚未建立"
    delta = datetime.now() - parsed
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 60:
        return f"{seconds} 秒前"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} 分鐘前"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} 小時前"
    days = hours // 24
    return f"{days} 天前"


def _format_timestamp(value: str) -> str:
    parsed = _parse_iso(value)
    if parsed is None:
        return "尚未建立"
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _format_size(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return "0 B"
    size = path.stat().st_size
    units = ["B", "KB", "MB", "GB"]
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return bool(row)


def _count_rows(db_path: Path, table_name: str) -> int | None:
    if not db_path.exists():
        return None
    try:
        with sqlite3.connect(db_path) as connection:
            if not _table_exists(connection, table_name):
                return None
            row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    except sqlite3.Error:
        return None
    return int(row[0]) if row else 0


def _collect_tables(db_path: Path) -> list[str]:
    if not db_path.exists():
        return []
    try:
        with sqlite3.connect(db_path) as connection:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            ).fetchall()
    except sqlite3.Error:
        return []
    return [str(row[0]) for row in rows]


def _count_snapshot_files(snapshot_dir: Path) -> int:
    if not snapshot_dir.exists():
        return 0
    return sum(1 for path in snapshot_dir.glob("*.json") if path.is_file())


def _load_effective_snapshot(ctx: PageContext):
    if ctx.snapshot.generated_at:
        return ctx.snapshot
    return load_snapshot(ctx.settings.snapshot_path)


def _metric_card(label: str, value: str, detail: str) -> str:
    return f"""
<div class="backend-metric-card">
  <div class="backend-metric-label">{_escape(label)}</div>
  <div class="backend-metric-value">{_escape(value)}</div>
  <div class="backend-metric-detail">{_escape(detail)}</div>
</div>
"""


def _layer_card(title: str, subtitle: str, items: list[str]) -> str:
    return f"""
<div class="backend-layer-card">
  <div class="backend-layer-title">{_escape(title)}</div>
  <div class="backend-layer-subtitle">{_escape(subtitle)}</div>
  <div class="backend-layer-chips">{build_chip_row(items, tone="soft", limit=8)}</div>
</div>
"""


def _flow_card(title: str, description: str, nodes: list[str]) -> str:
    nodes_html = "".join(
        (
            f'<span class="backend-flow-node">{_escape(node)}</span>'
            if index == len(nodes) - 1
            else (
                f'<span class="backend-flow-node">{_escape(node)}</span>'
                '<span class="backend-flow-arrow">→</span>'
            )
        )
        for index, node in enumerate(nodes)
    )
    return f"""
<div class="backend-flow-card">
  <div class="backend-flow-head">
    <div class="backend-flow-title">{_escape(title)}</div>
    <div class="backend-flow-desc">{_escape(description)}</div>
  </div>
  <div class="backend-flow-track">{nodes_html}</div>
</div>
"""


def _status_card(title: str, rows: list[tuple[str, str]]) -> str:
    row_html = "".join(
        f"""
<div class="backend-status-row">
  <span class="backend-status-key">{_escape(label)}</span>
  <span class="backend-status-value">{_escape(value)}</span>
</div>
"""
        for label, value in rows
    )
    return f"""
<div class="backend-status-card">
  <div class="backend-status-title">{_escape(title)}</div>
  <div class="backend-status-table">{row_html}</div>
</div>
"""


def _finding_card(title: str, body: str, tone: str = "neutral") -> str:
    return f"""
<div class="backend-finding-card backend-finding-card--{_escape(tone)}">
  <div class="backend-finding-title">{_escape(title)}</div>
  <div class="backend-finding-body">{_escape(body)}</div>
</div>
"""


def _inject_backend_styles() -> None:
    st.markdown(
        """
<style>
.backend-metric-grid,
.backend-layer-grid,
.backend-status-grid,
.backend-finding-grid {
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:0.9rem;
}
.backend-metric-card,
.backend-layer-card,
.backend-status-card,
.backend-flow-card,
.backend-finding-card {
  border:1px solid rgba(27, 59, 74, 0.12);
  border-radius:20px;
  background:
    radial-gradient(circle at top right, rgba(196, 223, 230, 0.45), transparent 40%),
    linear-gradient(180deg, rgba(255,255,255,0.98), rgba(246,249,250,0.98));
  padding:1rem 1.05rem;
  box-shadow:0 16px 30px rgba(22, 42, 51, 0.06);
}
.backend-metric-label,
.backend-status-key,
.backend-layer-subtitle,
.backend-flow-desc {
  color:rgba(64, 78, 86, 0.82);
  font-size:0.84rem;
}
.backend-metric-value,
.backend-layer-title,
.backend-status-title,
.backend-flow-title,
.backend-finding-title {
  color:#16333d;
  font-weight:700;
}
.backend-metric-value {
  font-size:1.45rem;
  margin:0.18rem 0 0.4rem;
}
.backend-metric-detail {
  color:rgba(64, 78, 86, 0.88);
  font-size:0.88rem;
  line-height:1.45;
}
.backend-layer-title {
  font-size:1.02rem;
  margin-bottom:0.25rem;
}
.backend-layer-chips {
  margin-top:0.85rem;
}
.backend-flow-stack {
  display:grid;
  gap:0.9rem;
}
.backend-flow-head {
  margin-bottom:0.85rem;
}
.backend-flow-track {
  display:flex;
  flex-wrap:wrap;
  gap:0.5rem;
  align-items:center;
}
.backend-flow-node {
  border-radius:999px;
  background:#17333d;
  color:#fff;
  font-size:0.84rem;
  padding:0.38rem 0.78rem;
  line-height:1.3;
}
.backend-flow-arrow {
  color:#52707c;
  font-weight:700;
  font-size:1rem;
}
.backend-status-title {
  font-size:1rem;
  margin-bottom:0.8rem;
}
.backend-status-table {
  display:grid;
  gap:0.62rem;
}
.backend-status-row {
  display:flex;
  justify-content:space-between;
  gap:1rem;
  padding-bottom:0.55rem;
  border-bottom:1px solid rgba(27, 59, 74, 0.08);
}
.backend-status-row:last-child {
  border-bottom:none;
  padding-bottom:0;
}
.backend-status-key {
  flex:1 1 auto;
}
.backend-status-value {
  flex:0 0 auto;
  text-align:right;
  color:#17333d;
  font-weight:600;
}
.backend-path-card {
  border:1px dashed rgba(27, 59, 74, 0.18);
  border-radius:18px;
  padding:1rem 1.05rem;
  background:rgba(249, 252, 252, 0.94);
}
.backend-path-card code {
  white-space:pre-wrap;
}
.backend-finding-grid {
  margin-top:0.2rem;
}
.backend-finding-card--risk {
  border-color:rgba(155, 89, 62, 0.16);
  background:
    radial-gradient(circle at top right, rgba(246, 215, 205, 0.5), transparent 42%),
    linear-gradient(180deg, rgba(255,255,255,0.98), rgba(252,247,244,0.98));
}
.backend-finding-card--good {
  border-color:rgba(44, 110, 73, 0.16);
  background:
    radial-gradient(circle at top right, rgba(209, 236, 220, 0.48), transparent 42%),
    linear-gradient(180deg, rgba(255,255,255,0.98), rgba(245,250,247,0.98));
}
.backend-finding-body {
  margin-top:0.35rem;
  color:rgba(55, 68, 75, 0.9);
  line-height:1.52;
  font-size:0.9rem;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_backend_architecture_page(ctx: PageContext) -> None:
    """Render the current backend architecture and runtime state."""
    _inject_backend_styles()
    snapshot = _load_effective_snapshot(ctx)
    snapshot_generated_at = snapshot.generated_at if snapshot is not None else ""
    snapshot_job_count = len(snapshot.jobs) if snapshot is not None else 0
    snapshot_skill_count = len(snapshot.skills) if snapshot is not None else 0
    snapshot_task_count = len(snapshot.task_insights) if snapshot is not None else 0
    snapshot_error_count = len(snapshot.errors) if snapshot is not None else 0

    product_db_path = ctx.settings.product_state_db_path
    user_db_path = ctx.settings.user_data_db_path
    query_db_path = ctx.settings.query_state_db_path
    snapshot_path = ctx.settings.snapshot_path
    snapshot_store_dir = ctx.settings.snapshot_store_dir
    cache_dir = ctx.settings.cache_dir

    product_counts = {
        "users": _count_rows(product_db_path, "users"),
        "saved_searches": _count_rows(product_db_path, "saved_searches"),
        "favorite_jobs": _count_rows(product_db_path, "favorite_jobs"),
        "job_notifications": _count_rows(product_db_path, "job_notifications"),
        "notification_preferences": _count_rows(product_db_path, "notification_preferences"),
    }
    user_submission_count = _count_rows(user_db_path, "user_submissions")
    query_runtime_counts = {
        "query_snapshots": _count_rows(query_db_path, "query_snapshots"),
        "crawl_jobs": _count_rows(query_db_path, "crawl_jobs"),
    }

    connectors = ["104", "1111"]
    if ctx.settings.enable_cake:
        connectors.append("Cake")
    if ctx.settings.enable_linkedin:
        connectors.append("LinkedIn")

    summary_cards = [
        ("架構型態", "Streamlit 單體應用", "UI 與後端模組目前仍在同一個 Python 進程"),
        ("抓取模式", "Staged Crawl", "先回 partial snapshot，再補 detail enrich 與完整分析"),
        (
            "最近快照",
            _format_relative_time(snapshot_generated_at),
            f"{_format_timestamp(snapshot_generated_at)}｜{snapshot_job_count} 筆職缺",
        ),
        (
            "持久化主體",
            "SQLite + JSON Snapshot",
            "產品狀態、履歷投稿與市場快照分開存放",
        ),
    ]

    layer_cards = [
        (
            "入口與協調層",
            "Streamlit app shell 與 session-driven orchestration",
            ["app.py", "ui/bootstrap.py", "ui/router.py", "ui/crawl_runtime.py"],
        ),
        (
            "核心服務層",
            "實際後端能力集中在 service / pipeline",
            ["pipeline.py", "resume/service.py", "assistant/service.py", "notifications/service.py"],
        ),
        (
            "整合與邊界層",
            "外部網站、LLM 與訊息通道的 adapter",
            ["connectors/", "line_webhook.py", "OpenAI", "SMTP / LINE Bot"],
        ),
        (
            "資料與狀態層",
            "本地快照、SQLite 與 query runtime registry",
            ["jobs_latest.json", "product_state.sqlite3", "user_submissions.sqlite3", "query_runtime.sqlite3"],
        ),
    ]

    flow_cards = [
        (
            "職缺抓取資料流",
            "目前後端的主幹流程，透過 staged crawl 讓 UI 可以先看到初步結果。",
            [
                "搜尋設定",
                "crawl_runtime",
                "JobMarketPipeline.collect_initial_wave",
                "partial snapshot",
                "finalize / enrich",
                "jobs_latest.json + saved search sync",
            ],
        ),
        (
            "履歷與 AI 資料流",
            "履歷分析與 RAG 助理都依賴目前市場快照，沒有獨立模型服務層。",
            [
                "履歷上傳 / 貼上文字",
                "ResumeAnalysisService",
                "user_submissions / resume profile",
                "JobMarketRAGAssistant",
                "OpenAI Responses / Embeddings",
            ],
        ),
        (
            "通知與綁定資料流",
            "LINE 綁定是分離式 webhook process，通知發送則在 app runtime 內觸發。",
            [
                "通知設定頁",
                "notification_preferences",
                "job_notifications",
                "NotificationService",
                "LINE webhook / Email",
            ],
        ),
    ]

    product_status_rows = [
        ("資料庫檔案", "存在" if product_db_path.exists() else "不存在"),
        ("users", str(product_counts["users"] or 0)),
        ("saved_searches", str(product_counts["saved_searches"] or 0)),
        ("favorite_jobs", str(product_counts["favorite_jobs"] or 0)),
        ("job_notifications", str(product_counts["job_notifications"] or 0)),
        ("notification_preferences", str(product_counts["notification_preferences"] or 0)),
    ]
    user_data_rows = [
        ("履歷投稿 DB", "存在" if user_db_path.exists() else "不存在"),
        ("user_submissions", str(user_submission_count or 0)),
        ("目前 session crawl_phase", str(ctx.crawl_phase or "idle")),
        ("目前 detail cursor", f"{ctx.crawl_detail_cursor} / {ctx.crawl_detail_total}"),
    ]
    snapshot_rows = [
        ("jobs_latest.json", f"{_format_size(snapshot_path)}｜{'存在' if snapshot_path.exists() else '不存在'}"),
        ("最近快照時間", _format_timestamp(snapshot_generated_at)),
        ("快照內容", f"{snapshot_job_count} jobs / {snapshot_skill_count} skills / {snapshot_task_count} tasks"),
        ("快照錯誤數", str(snapshot_error_count)),
    ]
    runtime_rows = [
        ("query runtime DB", "存在" if query_db_path.exists() else "尚未初始化"),
        ("query_snapshots", str(query_runtime_counts["query_snapshots"] or 0)),
        ("crawl_jobs", str(query_runtime_counts["crawl_jobs"] or 0)),
        ("snapshot store files", str(_count_snapshot_files(snapshot_store_dir))),
        ("queue backend", ctx.settings.queue_backend),
        ("database backend", ctx.settings.database_backend),
        ("cache backend", ctx.settings.cache_backend),
    ]
    feature_rows = [
        ("啟用來源", ", ".join(connectors)),
        ("OpenAI", "已設定" if ctx.settings.openai_api_key else "未設定"),
        ("Email 通知", "已設定" if ctx.notification_service.email_service_configured else "未設定"),
        ("LINE 通知", "已設定" if ctx.notification_service.line_service_configured else "未設定"),
        ("最大並發請求", str(ctx.settings.max_concurrent_requests)),
        ("每來源最大頁數", str(ctx.settings.max_pages_per_source)),
    ]

    findings = [
        (
            "目前不是前後端分離架構",
            "所有後端能力目前都被 Streamlit 頁面直接呼叫，沒有 REST / GraphQL API，也沒有獨立 application server。",
            "risk",
        ),
        (
            "抓取體驗有刻意做 staged 設計",
            "這個專案已把抓取拆成 initial wave 與 finalize wave，先顯示 partial snapshot，再補齊 detail 與統計，對互動體驗是加分。",
            "good",
        ),
        (
            "資料已經分流，但仍是單機型儲存",
            "產品狀態、履歷投稿、市場快照與 query runtime 已分檔，但核心仍是 SQLite + 本地檔案，適合原型與小量使用，不適合高併發寫入。",
            "risk",
        ),
        (
            "query runtime 有雛形，但未完全獨立化",
            "佇列與 snapshot registry 已做出來，不過 worker 仍由 app 內的 fragment/polling 推進，還不是獨立背景作業系統。",
            "risk",
        ),
    ]
    if query_runtime_counts["query_snapshots"] is None and query_runtime_counts["crawl_jobs"] is None:
        findings.append(
            (
                "目前環境尚未建立 query runtime DB",
                "代表這個工作區雖然已經有 queue/registry 程式碼，但這份資料庫在目前環境還沒有真正被建立或持久化。",
                "risk",
            )
        )

    render_section_header(
        "後端架構總覽",
        "這頁面直接讀目前程式結構與 data 目錄狀態，讓你看的是現在這個專案的後端，而不是抽象示意圖。",
        "Backend",
    )
    st.markdown(
        f'<div class="backend-metric-grid">{"".join(_metric_card(*card) for card in summary_cards)}</div>',
        unsafe_allow_html=True,
    )

    render_section_header(
        "服務分層",
        "目前後端邏輯已經有模組化，但仍維持在同一個單體應用內。",
        "Layers",
    )
    st.markdown(
        f'<div class="backend-layer-grid">{"".join(_layer_card(*card) for card in layer_cards)}</div>',
        unsafe_allow_html=True,
    )

    render_section_header(
        "主要資料流",
        "下面三條是現在專案中最重要的後端執行路徑。",
        "Flow",
    )
    st.markdown(
        f'<div class="backend-flow-stack">{"".join(_flow_card(*card) for card in flow_cards)}</div>',
        unsafe_allow_html=True,
    )

    render_section_header(
        "執行期狀態",
        "這裡是從目前 `data/` 讀到的真實狀態，不是寫死的數字。",
        "Runtime",
    )
    st.markdown(
        (
            '<div class="backend-status-grid">'
            f'{_status_card("產品狀態 DB", product_status_rows)}'
            f'{_status_card("履歷 / Session 狀態", user_data_rows)}'
            f'{_status_card("快照與檔案", snapshot_rows)}'
            f'{_status_card("Query Runtime", runtime_rows)}'
            f'{_status_card("功能與外部服務", feature_rows)}'
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    render_section_header(
        "資料落點",
        "目前後端狀態分散在幾個明確位置，這也是之後拆服務時最需要先收斂的地方。",
        "Storage",
    )
    st.markdown(
        f"""
<div class="backend-path-card">
  <div class="backend-status-table">
    <div class="backend-status-row"><span class="backend-status-key">市場快照</span><span class="backend-status-value"><code>{_escape(str(snapshot_path))}</code></span></div>
    <div class="backend-status-row"><span class="backend-status-key">產品狀態 DB</span><span class="backend-status-value"><code>{_escape(str(product_db_path))}</code></span></div>
    <div class="backend-status-row"><span class="backend-status-key">履歷投稿 DB</span><span class="backend-status-value"><code>{_escape(str(user_db_path))}</code></span></div>
    <div class="backend-status-row"><span class="backend-status-key">Query Runtime DB</span><span class="backend-status-value"><code>{_escape(str(query_db_path))}</code></span></div>
    <div class="backend-status-row"><span class="backend-status-key">快照快取目錄</span><span class="backend-status-value"><code>{_escape(str(snapshot_store_dir))}</code></span></div>
    <div class="backend-status-row"><span class="backend-status-key">HTTP 快取目錄</span><span class="backend-status-value"><code>{_escape(str(cache_dir))}</code></span></div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    render_section_header(
        "目前判讀",
        "這是根據實際程式與資料狀態整理出的後端評估。",
        "Assessment",
    )
    st.markdown(
        f'<div class="backend-finding-grid">{"".join(_finding_card(*finding) for finding in findings)}</div>',
        unsafe_allow_html=True,
    )

    with st.expander("查看目前 SQLite tables", expanded=False):
        st.write("`product_state.sqlite3`")
        st.code("\n".join(_collect_tables(product_db_path)) or "尚未建立")
        st.write("`user_submissions.sqlite3`")
        st.code("\n".join(_collect_tables(user_db_path)) or "尚未建立")
        st.write("`query_runtime.sqlite3`")
        st.code("\n".join(_collect_tables(query_db_path)) or "尚未建立")
