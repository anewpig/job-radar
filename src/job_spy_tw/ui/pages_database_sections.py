"""提供資料庫報告頁各分頁 section 的渲染 helper。"""

from __future__ import annotations

import streamlit as st

from .common import build_chip_row
from .pages_database_data import _format_bytes
from .pages_database_views import (
    _render_architecture_map,
    _render_learning_cards,
    _render_risk_cards,
    _render_risk_chart,
    _render_roadmap,
    _render_storage_chart,
    _render_table_chart,
)


def _render_status_chips(report: dict[str, object]) -> None:
    pragmas = report["pragmas"]
    status_chips = [
        f"cache backend: {report['cache_backend']}",
        f"queue backend: {report['queue_backend']}",
        f"database backend: {report['database_backend']}",
        f"foreign_keys: {pragmas['foreign_keys']}",
        f"journal_mode: {pragmas['journal_mode']}",
        (
            "query runtime: 已落地"
            if report["query_runtime_live"]
            else "query runtime: 程式已支援，但 data/ 尚未落地"
        ),
    ]
    st.markdown(
        f"<div class='database-body-note chip-row'>{build_chip_row(status_chips, tone='soft', limit=6)}</div>",
        unsafe_allow_html=True,
    )


def _render_overview_section(report: dict[str, object]) -> None:
    storage_frame = report["storage_frame"]
    table_frame = report["table_frame"]
    snapshot_summary = report["snapshot_summary"]

    metrics = st.columns(4, gap="medium")
    metrics[0].metric("data/ 總容量", _format_bytes(int(report["total_size"])))
    metrics[1].metric("cache 佔比", f"{report['cache_share']:.1f}%")
    metrics[2].metric("主要結構化列數", int(report["structured_row_total"]))
    metrics[3].metric("最新 snapshot jobs", int(snapshot_summary["job_count"]))

    st.markdown(
        """
<div class="database-grid">
  <div class="database-card">
    <div class="database-card-eyebrow">Current status</div>
    <div class="database-card-title">目前這個專案的資料核心不是單一 DB</div>
    <div class="database-card-copy">市場資料以 JSON snapshot 和檔案 cache 為主，使用者與產品狀態才主要進 SQLite。這代表你之後會遇到兩種不同瓶頸：檔案型資料膨脹，以及產品狀態表的併發與查詢壓力。</div>
  </div>
  <div class="database-card">
    <div class="database-card-eyebrow">Most loaded area</div>
    <div class="database-card-title">真正最重的是 cache，不是 product_state.sqlite3</div>
    <div class="database-card-copy">目前 data/ 的容量幾乎都由 cache 吃掉。反而產品狀態 DB 還很小，說明你現在還在原型階段，先要管理的是資料邊界與儲存策略，而不是過早做分散式資料庫。</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    chart_cols = st.columns(2, gap="large")
    with chart_cols[0]:
        st.markdown(
            """
<div class="summary-card">
  <div class="info-card-title">儲存容量分布</div>
  <div class="summary-card-text">這張圖回答的是「現在 data/ 的重量主要壓在哪裡」。如果快取一路長大，後面會先卡在磁碟、同步與備份，不會先卡在產品資料表。</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        _render_storage_chart(storage_frame)
    with chart_cols[1]:
        st.markdown(
            """
<div class="summary-card">
  <div class="info-card-title">主要資料表列數</div>
  <div class="summary-card-text">這張圖回答的是「現在真正進資料庫的資料量有多少」。目前仍是很小的產品原型資料量，還沒進入重型 OLTP 階段。</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        _render_table_chart(table_frame)

    st.markdown(
        """
<div class="summary-card" style="margin-top:1rem;">
  <div class="info-card-title">系統儲存架構地圖</div>
  <div class="summary-card-text">下面把目前系統實際分成兩條 lane 來看：一條處理市場資料與分析，一條處理使用者與產品狀態。這也是你未來思考 database 時最重要的邊界。</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    _render_architecture_map(report)

    with st.expander("查看原始儲存與資料表明細"):
        raw_storage = storage_frame[["label", "category", "size_label", "share"]].copy()
        raw_storage = raw_storage.rename(
            columns={
                "label": "項目",
                "category": "類型",
                "size_label": "容量",
                "share": "占比 (%)",
            }
        )
        raw_storage["占比 (%)"] = raw_storage["占比 (%)"].map(lambda value: f"{value:.1f}")
        st.dataframe(raw_storage, use_container_width=True, hide_index=True)

        raw_tables = table_frame[["database", "label", "rows", "available"]].copy()
        raw_tables = raw_tables.rename(
            columns={
                "database": "檔案",
                "label": "資料表",
                "rows": "列數",
                "available": "已存在",
            }
        )
        st.dataframe(raw_tables, use_container_width=True, hide_index=True)


def _render_learning_section(report: dict[str, object]) -> None:
    st.markdown(
        """
<div class="summary-card">
  <div class="info-card-title">先用這個專案學 Database</div>
  <div class="summary-card-text">不要先背一堆理論名詞，先把它對到你自己的專案。你現在最該建立的是三個判斷：什麼資料要長期保存、什麼資料只是快照、什麼時候該從 JSON/檔案走向正規化資料表。</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    _render_learning_cards()

    explain_cols = st.columns(2, gap="large")
    with explain_cols[0]:
        st.markdown(
            f"""
<div class="summary-card">
  <div class="info-card-title">目前哪些資料進 SQLite</div>
  <div class="summary-card-text">這些資料有一個共同點：它們都是產品狀態或使用者狀態，必須跨 session 保留，而且會被 UI 直接更新。</div>
  <div class="chip-row" style="margin-top:0.8rem;">{build_chip_row(['users', 'saved_searches', 'favorite_jobs', 'notification_preferences', 'user_submissions'], tone='accent', limit=6)}</div>
</div>
            """,
            unsafe_allow_html=True,
        )
    with explain_cols[1]:
        st.markdown(
            f"""
<div class="summary-card">
  <div class="info-card-title">目前哪些資料還在檔案系統</div>
  <div class="summary-card-text">市場快照與抓取快取偏向衍生資料或中間結果，所以現在主要放在檔案。這做法在原型期很快，但之後不利於歷史分析。</div>
  <div class="chip-row" style="margin-top:0.8rem;">{build_chip_row(['jobs_latest.json', 'data/cache', 'future snapshots dir', 'HTML cache payloads'], tone='warm', limit=6)}</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
<div class="summary-card" style="margin-top:1rem;">
  <div class="info-card-title">這個專案的資料庫閱讀順序</div>
  <div class="summary-card-text">如果你之後要自己看 schema，最好的順序是：先看 <code>users / saved_searches / favorite_jobs</code>，再看 <code>notifications</code>，最後才看履歷與查詢 runtime。因為前者最直接對應到你的產品操作。</div>
  <div class="chip-row" style="margin-top:0.8rem;">{build_chip_row(['1. users', '2. saved_searches', '3. favorite_jobs', '4. notifications', '5. resume / query runtime'], tone='soft', limit=6)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    json_areas = list(report["json_heavy_areas"])
    st.markdown(
        f"""
<div class="summary-card">
  <div class="info-card-title">你現在最該有的資料庫觀念</div>
  <div class="summary-card-text">目前 schema 已經出現多個 JSON-heavy 欄位，這是典型原型期設計。它的優點是快，缺點是資料成長後不容易做 join、條件查詢與報表。這通常就是正規化的起點。</div>
  <div class="chip-row" style="margin-top:0.8rem;">{build_chip_row(json_areas, tone='warm', limit=6)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _render_risk_section(report: dict[str, object]) -> None:
    pragmas = report["pragmas"]
    risk_metrics = st.columns(4, gap="medium")
    risk_metrics[0].metric("最大儲存來源", "cache")
    risk_metrics[1].metric("journal_mode", str(pragmas["journal_mode"]))
    risk_metrics[2].metric("foreign_keys", str(pragmas["foreign_keys"]))
    risk_metrics[3].metric("JSON-heavy 區域", len(report["json_heavy_areas"]))

    st.caption("下面的風險分數是根據目前程式碼與 data/ 狀態做的工程估計，不是壓測結果。")

    st.markdown(
        """
<div class="summary-card">
  <div class="info-card-title">資料量放大後的風險矩陣</div>
  <div class="summary-card-text">這張圖不是在看「今天有沒有壞」，而是在看「如果資料量、使用者數、背景工作都變多，哪裡會最先出問題」。越靠右上角，越值得先處理。</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    _render_risk_chart(report["risk_frame"])

    _render_risk_cards()

    st.markdown(
        """
<div class="summary-card" style="margin-top:1rem;">
  <div class="info-card-title">建議的演進路線</div>
  <div class="summary-card-text">現在不用急著全面換資料庫。先把當前的 SQLite 與 schema 用對，再根據產品型態決定哪些資料真的值得搬到更重的後端。</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    _render_roadmap()
