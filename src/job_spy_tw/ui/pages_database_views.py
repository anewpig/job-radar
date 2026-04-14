"""提供資料庫報告頁的樣式與視覺 render helper。"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from .common import _escape, build_chip_row


def _inject_database_report_styles() -> None:
    st.markdown(
        """
<style>
.database-intro {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    text-align: left;
    margin: 0 0 0.35rem;
    padding: 0 1.45rem 0 2.3rem;
}

.database-intro .section-kicker,
.database-intro .section-title,
.database-intro .section-desc {
    text-align: left;
}

.database-intro-meta {
    min-width: 13rem;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
    padding-top: 0.3rem;
}

.database-meta-card {
    border-radius: 18px;
    padding: 0.95rem 1rem;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,245,255,0.97) 100%);
    box-shadow: 0 10px 24px rgba(116, 86, 204, 0.08);
}

.database-meta-kicker {
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 800;
    color: #8a84ab;
}

.database-meta-value {
    margin-top: 0.35rem;
    font-size: 1.15rem;
    font-weight: 800;
    color: #342f67;
}

.database-body-note {
    margin: 0.2rem 0 1rem;
}

.database-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
    margin-top: 0.35rem;
}

.database-card {
    border-radius: 22px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(247,242,255,0.96) 100%);
    box-shadow: 0 12px 26px rgba(116, 86, 204, 0.08);
    padding: 1rem 1.05rem;
}

.database-card-eyebrow {
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8a84ab;
}

.database-card-title {
    margin-top: 0.3rem;
    font-size: 1.05rem;
    font-weight: 800;
    color: #2f295c;
}

.database-card-copy {
    margin-top: 0.55rem;
    color: #60587f;
    line-height: 1.7;
}

.database-architecture {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
    margin-top: 0.35rem;
}

.database-lane {
    position: relative;
    border-radius: 24px;
    padding: 1.05rem;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(135deg, rgba(255,255,255,0.99) 0%, rgba(245,241,255,0.96) 100%);
    box-shadow: 0 14px 30px rgba(116, 86, 204, 0.08);
}

.database-lane-title {
    font-size: 0.8rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #7b61ff;
}

.database-lane-subtitle {
    margin-top: 0.25rem;
    font-size: 1.2rem;
    font-weight: 800;
    color: #2f295c;
}

.database-node-list {
    display: grid;
    gap: 0.8rem;
    margin-top: 0.95rem;
}

.database-node {
    border-radius: 18px;
    padding: 0.9rem 0.95rem;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: rgba(255, 255, 255, 0.92);
}

.database-node-kicker {
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 800;
    color: #948cb5;
}

.database-node-title {
    margin-top: 0.28rem;
    font-size: 0.98rem;
    font-weight: 800;
    color: #37306d;
}

.database-node-copy {
    margin-top: 0.45rem;
    color: #61597f;
    line-height: 1.65;
}

.database-risk-grid,
.database-learn-grid,
.database-roadmap-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
    margin-top: 0.35rem;
}

.database-risk-card,
.database-learn-card,
.database-roadmap-card {
    border-radius: 22px;
    border: 1px solid rgba(123, 97, 255, 0.10);
    background: linear-gradient(180deg, rgba(255,255,255,0.99) 0%, rgba(247,242,255,0.96) 100%);
    box-shadow: 0 12px 26px rgba(116, 86, 204, 0.08);
    padding: 1rem 1.05rem;
}

.database-risk-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.28rem 0.7rem;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.04em;
}

.database-risk-badge--high {
    background: rgba(255, 232, 182, 0.92);
    color: #8a5e00;
}

.database-risk-badge--midhigh {
    background: rgba(231, 240, 255, 0.95);
    color: #3157c2;
}

.database-risk-badge--mid {
    background: rgba(243, 239, 255, 0.98);
    color: #654dde;
}

@media (max-width: 960px) {
    .database-intro,
    .database-grid,
    .database-architecture,
    .database-risk-grid,
    .database-learn-grid,
    .database-roadmap-grid {
        grid-template-columns: 1fr;
    }

    .database-intro {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _render_storage_chart(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("目前沒有可視覺化的儲存資料。")
        return
    chart_frame = frame[frame["size_bytes"] > 0].copy()
    if chart_frame.empty:
        st.info("目前資料目錄中沒有可計算大小的項目。")
        return
    chart_frame = chart_frame.sort_values("size_mb", ascending=True)
    chart = (
        alt.Chart(chart_frame)
        .mark_bar(cornerRadius=10, size=26)
        .encode(
            x=alt.X(
                "size_mb:Q",
                title="容量 (MB)",
                axis=alt.Axis(grid=True, gridColor="#e2e8f0"),
            ),
            y=alt.Y(
                "label:N",
                sort=chart_frame["label"].tolist(),
                title=None,
                axis=alt.Axis(labelLimit=220),
            ),
            color=alt.Color(
                "category:N",
                title="類型",
                scale=alt.Scale(
                    domain=["快取", "快照", "資料庫", "查詢快照", "其他"],
                    range=["#7b61ff", "#38bdf8", "#22c55e", "#f59e0b", "#94a3b8"],
                ),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("label:N", title="項目"),
                alt.Tooltip("category:N", title="類型"),
                alt.Tooltip("size_mb:Q", title="容量 (MB)", format=".2f"),
                alt.Tooltip("share:Q", title="占比 (%)", format=".1f"),
                alt.Tooltip("size_label:N", title="格式化容量"),
            ],
        )
        .properties(height=320)
        .configure_view(strokeWidth=0)
        .configure_axis(domain=False, labelColor="#0f172a", titleColor="#334155")
        .configure_legend(labelColor="#0f172a", titleColor="#334155")
    )
    st.altair_chart(chart, use_container_width=True)


def _render_table_chart(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("目前沒有可視覺化的資料表資料。")
        return
    chart_frame = frame.copy().sort_values(["rows", "label"], ascending=[True, True])
    chart = (
        alt.Chart(chart_frame)
        .mark_bar(cornerRadius=10, size=22)
        .encode(
            x=alt.X(
                "rows:Q",
                title="列數",
                axis=alt.Axis(grid=True, gridColor="#e2e8f0", tickMinStep=1),
            ),
            y=alt.Y(
                "display_label:N",
                sort=chart_frame["display_label"].tolist(),
                title=None,
                axis=alt.Axis(labelLimit=280),
            ),
            color=alt.Color(
                "database:N",
                title="檔案",
                scale=alt.Scale(
                    domain=[
                        "product_state.sqlite3",
                        "user_submissions.sqlite3",
                        "query_runtime.sqlite3",
                    ],
                    range=["#16a34a", "#0ea5e9", "#f59e0b"],
                ),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("label:N", title="資料表"),
                alt.Tooltip("database:N", title="檔案"),
                alt.Tooltip("rows:Q", title="列數"),
                alt.Tooltip("available:N", title="已存在"),
            ],
        )
        .properties(height=360)
        .configure_view(strokeWidth=0)
        .configure_axis(domain=False, labelColor="#0f172a", titleColor="#334155")
        .configure_legend(labelColor="#0f172a", titleColor="#334155")
    )
    st.altair_chart(chart, use_container_width=True)


def _render_risk_chart(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("目前沒有風險評估資料。")
        return
    chart = (
        alt.Chart(frame)
        .mark_circle(opacity=0.86, stroke="#ffffff", strokeWidth=1.5)
        .encode(
            x=alt.X(
                "likelihood:Q",
                title="發生機率",
                scale=alt.Scale(domain=[0, 10]),
                axis=alt.Axis(grid=True, gridColor="#e2e8f0"),
            ),
            y=alt.Y(
                "impact:Q",
                title="影響程度",
                scale=alt.Scale(domain=[0, 10]),
                axis=alt.Axis(grid=True, gridColor="#e2e8f0"),
            ),
            size=alt.Size(
                "score:Q",
                title="風險分數",
                scale=alt.Scale(range=[350, 1600]),
                legend=None,
            ),
            color=alt.Color(
                "category:N",
                title="類型",
                scale=alt.Scale(
                    domain=["儲存", "併發", "Schema", "分析", "演進"],
                    range=["#7b61ff", "#38bdf8", "#22c55e", "#f59e0b", "#ef4444"],
                ),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("risk:N", title="風險"),
                alt.Tooltip("category:N", title="類型"),
                alt.Tooltip("likelihood:Q", title="機率"),
                alt.Tooltip("impact:Q", title="影響"),
                alt.Tooltip("priority:N", title="優先級"),
            ],
        )
        .properties(height=360)
        .configure_view(strokeWidth=0)
        .configure_axis(domain=False, labelColor="#0f172a", titleColor="#334155")
        .configure_legend(labelColor="#0f172a", titleColor="#334155")
    )
    labels = (
        alt.Chart(frame)
        .mark_text(dx=10, dy=-10, align="left", color="#1f1b4d", fontWeight=700)
        .encode(x="likelihood:Q", y="impact:Q", text="risk:N")
    )
    st.altair_chart(chart + labels, use_container_width=True)


def _render_intro(report: dict[str, object]) -> None:
    snapshot_summary = report["snapshot_summary"]
    st.markdown(
        f"""
<div class="section-shell database-intro">
  <div>
    <div class="section-kicker">{_escape("Database Report")}</div>
    <div class="section-title">{_escape("資料庫與儲存架構報告")}</div>
    <div class="section-desc">{_escape("這頁直接讀取目前專案 data/ 內的實際資料，拆出市場快照、檔案快取、產品狀態 SQLite 與履歷資料 SQLite，讓你用同一頁看懂現在的資料結構與未來的風險。")}</div>
  </div>
  <div class="database-intro-meta">
    <div class="database-meta-card">
      <div class="database-meta-kicker">{_escape("Data Root")}</div>
      <div class="database-meta-value">{_escape(str(report["data_root"]))}</div>
    </div>
    <div class="database-meta-card">
      <div class="database-meta-kicker">{_escape("Latest Snapshot")}</div>
      <div class="database-meta-value">{_escape(str(snapshot_summary["generated_at"] or "尚未產生"))}</div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _render_architecture_map(report: dict[str, object]) -> None:
    snapshot_summary = report["snapshot_summary"]
    query_runtime_note = (
        "query runtime 檔案已存在，代表查詢快照 registry 開始落地。"
        if report["query_runtime_live"]
        else "程式碼已有 query registry / crawl queue 設計，但目前 data/ 下還沒看到實際落地檔案。"
    )
    market_lane = [
        {
            "kicker": "入口層",
            "title": "Streamlit UI + session state",
            "copy": "畫面先讀目前快照，再用 staged crawl 逐步補完整職缺與分析結果。",
            "chips": ["snapshot", "crawl_phase", "partial -> final"],
        },
        {
            "kicker": "抓取與分析",
            "title": "JobMarketPipeline",
            "copy": "負責抓取、去重、補 detail、重算 relevance、整理技能與工作內容統計。",
            "chips": ["collect_initial_wave", "complete_snapshot", "skills/tasks"],
        },
        {
            "kicker": "持久化",
            "title": "JSON snapshot + filesystem cache",
            "copy": (
                f"目前最新 snapshot 有 {snapshot_summary['job_count']} 筆 jobs，"
                f"cache 佔 data/ 約 {report['cache_share']:.1f}% ，是現在最大的儲存來源。"
            ),
            "chips": [
                f"jobs_latest.json {report['storage_frame'].iloc[1]['size_label']}",
                f"cache {report['storage_frame'].iloc[0]['size_label']}",
                f"errors {snapshot_summary['error_count']}",
            ],
        },
    ]
    product_lane = [
        {
            "kicker": "產品狀態",
            "title": "product_state.sqlite3",
            "copy": "放帳號、已儲存搜尋、收藏、通知偏好、站內通知與產品級履歷摘要。",
            "chips": ["users", "saved_searches", "favorite_jobs", "notifications"],
        },
        {
            "kicker": "履歷歷史",
            "title": "user_submissions.sqlite3",
            "copy": "保存匿名化後的履歷提交歷史，偏向資料收集與分析用途，不是主產品狀態表。",
            "chips": ["user_submissions", "masked text", "history"],
        },
        {
            "kicker": "查詢 runtime",
            "title": "query snapshot / crawl queue",
            "copy": query_runtime_note,
            "chips": ["query_snapshots", "crawl_jobs", "sqlite queue"],
        },
    ]

    def build_lane(title: str, subtitle: str, nodes: list[dict[str, object]]) -> str:
        markup = []
        for node in nodes:
            markup.append(
                f"""
<div class="database-node">
  <div class="database-node-kicker">{_escape(node["kicker"])}</div>
  <div class="database-node-title">{_escape(node["title"])}</div>
  <div class="database-node-copy">{_escape(node["copy"])}</div>
  <div class="chip-row" style="margin-top:0.7rem;">{build_chip_row(list(node["chips"]), tone="soft", limit=6)}</div>
</div>
                """
            )
        return (
            f"""
<div class="database-lane">
  <div class="database-lane-title">{_escape(title)}</div>
  <div class="database-lane-subtitle">{_escape(subtitle)}</div>
  <div class="database-node-list">{''.join(markup)}</div>
</div>
            """
        )

    st.markdown(
        "<div class='database-architecture'>"
        + build_lane("Lane A", "市場資料與分析流", market_lane)
        + build_lane("Lane B", "產品資料與使用者狀態流", product_lane)
        + "</div>",
        unsafe_allow_html=True,
    )


def _render_learning_cards() -> None:
    learning_cards = [
        (
            "Table",
            "資料表",
            "在這個專案裡，一個 table 就是一種業務實體。像 users、saved_searches、favorite_jobs 都是在回答『我們要長期記住什麼』。",
        ),
        (
            "Row",
            "資料列",
            "一列就是一筆資料。例如一筆收藏職缺、一個使用者、一組通知偏好。你平常在 UI 點一次收藏，背後通常就是新增或更新一列。",
        ),
        (
            "Index",
            "索引",
            "索引的功能是讓查詢不要每次都把整張表掃完。現在這個專案已經有 user_id + signature、user_id + application_status 等二級索引。",
        ),
        (
            "Boundary",
            "資料邊界",
            "不是所有東西都要先進 database。這個專案目前把市場快照放 JSON，把產品狀態放 SQLite，這就是一種儲存邊界設計。",
        ),
        (
            "Normalization",
            "正規化",
            "資料少的時候，用 JSON 欄位很快；資料變大後，就會想把它拆成獨立表，讓查詢、統計、通知和報表都更好做。",
        ),
        (
            "Migration",
            "遷移",
            "schema 不會永遠正確，所以要能從舊表搬到新表。這個專案目前的 store/database.py 已經有多段 migration 與補欄位邏輯。",
        ),
    ]
    card_markup = []
    for eyebrow, title, copy in learning_cards:
        card_markup.append(
            f"""
<div class="database-learn-card">
  <div class="database-card-eyebrow">{_escape(eyebrow)}</div>
  <div class="database-card-title">{_escape(title)}</div>
  <div class="database-card-copy">{_escape(copy)}</div>
</div>
            """
        )
    st.markdown(
        f"<div class='database-learn-grid'>{''.join(card_markup)}</div>",
        unsafe_allow_html=True,
    )


def _render_risk_cards() -> None:
    risk_cards = [
        (
            "高",
            "快取與 HTML 檔案膨脹",
            "現在 data/ 容量幾乎都在 cache。資料量上來後，先遇到的通常是磁碟、備份和 I/O 壓力，不是產品狀態表本身。",
            "先做 cache retention、大小上限與清理策略。",
        ),
        (
            "中高",
            "SQLite 寫入競爭",
            "目前 product_state 與其他 SQLite 檔案都是 journal_mode=delete，而且大量操作採每次即開即關。多使用者或多程序後會更容易遇到 lock。",
            "先開 WAL，再評估 product_state/query_runtime 遷到 PostgreSQL。",
        ),
        (
            "高",
            "JSON 欄位長大後難查",
            "known_job_urls、new_jobs_json、profile_json 這類欄位適合原型，但不適合成長後的條件查詢、趨勢報表與 join。",
            "先把 seen jobs、job notifications payload、歷史職缺主體逐步正規化。",
        ),
        (
            "高",
            "缺少歷史職缺主表",
            "目前 finalize 後主要是覆寫最新 snapshot，不是建立完整的 job_posts / crawl_runs / job_skills 歷史資料層。",
            "若要做趨勢、比對平台品質、技能變化，下一版 schema 應補核心分析表。",
        ),
        (
            "中",
            "設定看似可換 backend，實際仍是 SQLite-only",
            "settings 有 database_backend / queue_backend，但 queue_backend 不是 sqlite 就會直接報錯，代表抽象層還沒完整落地。",
            "未來要不就真的做 interface，要不就先把設定收斂，避免誤判可擴充性。",
        ),
        (
            "中高",
            "關聯完整性主要靠程式碼",
            "目前 foreign_keys 是關閉的，schema 也沒有用 FK 明確描述 users 與 saved_searches / favorites / notifications 的關聯。",
            "先開 foreign_keys，再補外鍵與刪除策略。",
        ),
    ]
    badge_classes = {
        "高": "database-risk-badge database-risk-badge--high",
        "中高": "database-risk-badge database-risk-badge--midhigh",
        "中": "database-risk-badge database-risk-badge--mid",
    }
    card_markup = []
    for severity, title, detail, action in risk_cards:
        card_markup.append(
            f"""
<div class="database-risk-card">
  <div class="{badge_classes.get(severity, 'database-risk-badge database-risk-badge--mid')}">{_escape(severity)}優先</div>
  <div class="database-card-title" style="margin-top:0.7rem;">{_escape(title)}</div>
  <div class="database-card-copy">{_escape(detail)}</div>
  <div class="chip-row" style="margin-top:0.8rem;">{build_chip_row([action], tone="warm", limit=1)}</div>
</div>
            """
        )
    st.markdown(
        f"<div class='database-risk-grid'>{''.join(card_markup)}</div>",
        unsafe_allow_html=True,
    )


def _render_roadmap() -> None:
    roadmap_cards = [
        (
            "Now",
            "先把 SQLite 用對",
            "開 WAL、開 foreign_keys、補 cache 清理、把 Python 過濾改成 SQL，這是最划算的一步。",
        ),
        (
            "Next",
            "把核心資料正規化",
            "至少拆出 crawl_runs、job_posts、job_skills、job_tasks、saved_search_seen_jobs，之後統計和通知才會順。",
        ),
        (
            "Later",
            "多實例再上 PostgreSQL",
            "等你要多人使用、背景 worker、雲端部署與長期趨勢分析時，再把 product_state / query_runtime 移出去。",
        ),
    ]
    markup = []
    for eyebrow, title, copy in roadmap_cards:
        markup.append(
            f"""
<div class="database-roadmap-card">
  <div class="database-card-eyebrow">{_escape(eyebrow)}</div>
  <div class="database-card-title">{_escape(title)}</div>
  <div class="database-card-copy">{_escape(copy)}</div>
</div>
            """
        )
    st.markdown(
        f"<div class='database-roadmap-grid'>{''.join(markup)}</div>",
        unsafe_allow_html=True,
    )
