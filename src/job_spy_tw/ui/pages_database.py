"""提供資料庫報告頁的視覺化渲染函式。"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from .common import _escape, build_chip_row
from .page_context import PageContext

PRODUCT_TABLES: list[tuple[str, str]] = [
    ("users", "使用者"),
    ("saved_searches", "已儲存搜尋"),
    ("favorite_jobs", "收藏 / 投遞"),
    ("job_notifications", "站內通知"),
    ("notification_preferences", "通知偏好"),
    ("user_resume_profiles", "目前履歷"),
    ("user_identities", "OIDC 身分"),
    ("password_reset_tokens", "重設密碼"),
    ("app_metrics", "站點指標"),
]

RESUME_TABLES: list[tuple[str, str]] = [
    ("user_submissions", "履歷提交歷史"),
]

QUERY_RUNTIME_TABLES: list[tuple[str, str]] = [
    ("query_snapshots", "查詢快照"),
    ("crawl_jobs", "爬蟲工作佇列"),
]

JSON_HEAVY_AREAS = [
    "saved_searches.rows_json",
    "saved_searches.known_job_urls",
    "job_notifications.new_jobs_json",
    "job_notifications.delivery_notes",
    "user_resume_profiles.profile_json",
    "user_submissions.target_roles/core_skills/tool_skills",
]


def _format_bytes(size_bytes: int) -> str:
    size = float(max(0, int(size_bytes)))
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    precision = 0 if unit_index == 0 else 1
    return f"{size:.{precision}f} {units[unit_index]}"


def _directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                continue
    return total


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size if path.exists() else 0
    except OSError:
        return 0


def _safe_share(part: int, whole: int) -> float:
    if whole <= 0:
        return 0.0
    return (float(part) / float(whole)) * 100


def _empty_summary() -> dict[str, object]:
    return {
        "generated_at": "",
        "query_count": 0,
        "role_target_count": 0,
        "job_count": 0,
        "skill_count": 0,
        "task_count": 0,
        "error_count": 0,
    }


def _load_snapshot_summary(snapshot_path: Path) -> dict[str, object]:
    if not snapshot_path.exists():
        return _empty_summary()
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_summary()
    return {
        "generated_at": str(payload.get("generated_at", "")),
        "query_count": len(payload.get("queries", [])),
        "role_target_count": len(payload.get("role_targets", [])),
        "job_count": len(payload.get("jobs", [])),
        "skill_count": len(payload.get("skills", [])),
        "task_count": len(payload.get("task_insights", [])),
        "error_count": len(payload.get("errors", [])),
    }


def _read_table_counts(
    db_path: Path,
    *,
    table_defs: list[tuple[str, str]],
    database_label: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not db_path.exists():
        for table_name, label in table_defs:
            rows.append(
                {
                    "database": database_label,
                    "table_name": table_name,
                    "label": label,
                    "rows": 0,
                    "available": False,
                }
            )
        return rows

    with sqlite3.connect(db_path) as connection:
        for table_name, label in table_defs:
            try:
                count = int(
                    connection.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0]
                )
                available = True
            except sqlite3.Error:
                count = 0
                available = False
            rows.append(
                {
                    "database": database_label,
                    "table_name": table_name,
                    "label": label,
                    "rows": count,
                    "available": available,
                }
            )
    return rows


def _read_pragmas(db_path: Path) -> dict[str, str]:
    if not db_path.exists():
        return {"foreign_keys": "missing", "journal_mode": "missing"}
    with sqlite3.connect(db_path) as connection:
        foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()
    return {
        "foreign_keys": str(foreign_keys[0]) if foreign_keys else "unknown",
        "journal_mode": str(journal_mode[0]) if journal_mode else "unknown",
    }


@st.cache_data(show_spinner=False, ttl=20)
def _load_database_report(
    *,
    data_dir: str,
    cache_backend: str,
    queue_backend: str,
    database_backend: str,
) -> dict[str, object]:
    data_root = Path(data_dir)
    cache_dir = data_root / "cache"
    snapshots_dir = data_root / "snapshots"
    product_db_path = data_root / "product_state.sqlite3"
    user_db_path = data_root / "user_submissions.sqlite3"
    query_db_path = data_root / "query_runtime.sqlite3"
    snapshot_path = data_root / "jobs_latest.json"

    total_size = _directory_size(data_root)
    cache_size = _directory_size(cache_dir)
    snapshots_size = _directory_size(snapshots_dir)
    product_db_size = _file_size(product_db_path)
    user_db_size = _file_size(user_db_path)
    query_db_size = _file_size(query_db_path)
    snapshot_size = _file_size(snapshot_path)
    known_size = (
        cache_size
        + snapshots_size
        + product_db_size
        + user_db_size
        + query_db_size
        + snapshot_size
    )
    other_size = max(0, total_size - known_size)

    snapshot_summary = _load_snapshot_summary(snapshot_path)
    pragmas = _read_pragmas(product_db_path)

    storage_frame = pd.DataFrame(
        [
            {
                "label": "Filesystem cache",
                "category": "快取",
                "size_bytes": cache_size,
                "size_label": _format_bytes(cache_size),
                "share": _safe_share(cache_size, total_size),
            },
            {
                "label": "市場快照 JSON",
                "category": "快照",
                "size_bytes": snapshot_size,
                "size_label": _format_bytes(snapshot_size),
                "share": _safe_share(snapshot_size, total_size),
            },
            {
                "label": "產品狀態 SQLite",
                "category": "資料庫",
                "size_bytes": product_db_size,
                "size_label": _format_bytes(product_db_size),
                "share": _safe_share(product_db_size, total_size),
            },
            {
                "label": "履歷提交 SQLite",
                "category": "資料庫",
                "size_bytes": user_db_size,
                "size_label": _format_bytes(user_db_size),
                "share": _safe_share(user_db_size, total_size),
            },
            {
                "label": "查詢 runtime SQLite",
                "category": "查詢快照",
                "size_bytes": query_db_size,
                "size_label": _format_bytes(query_db_size),
                "share": _safe_share(query_db_size, total_size),
            },
            {
                "label": "歷史 snapshot 目錄",
                "category": "查詢快照",
                "size_bytes": snapshots_size,
                "size_label": _format_bytes(snapshots_size),
                "share": _safe_share(snapshots_size, total_size),
            },
            {
                "label": "其他 data 檔案",
                "category": "其他",
                "size_bytes": other_size,
                "size_label": _format_bytes(other_size),
                "share": _safe_share(other_size, total_size),
            },
        ]
    )
    storage_frame["size_mb"] = storage_frame["size_bytes"] / (1024 * 1024)

    table_rows = [
        *_read_table_counts(
            product_db_path,
            table_defs=PRODUCT_TABLES,
            database_label="product_state.sqlite3",
        ),
        *_read_table_counts(
            user_db_path,
            table_defs=RESUME_TABLES,
            database_label="user_submissions.sqlite3",
        ),
        *_read_table_counts(
            query_db_path,
            table_defs=QUERY_RUNTIME_TABLES,
            database_label="query_runtime.sqlite3",
        ),
    ]
    table_frame = pd.DataFrame(table_rows)
    table_frame["display_label"] = (
        table_frame["label"] + " · " + table_frame["database"]
    )

    risk_frame = pd.DataFrame(
        [
            {
                "risk": "Filesystem cache 持續膨脹",
                "category": "儲存",
                "likelihood": 9,
                "impact": 7,
                "priority": "高",
            },
            {
                "risk": "SQLite 寫入鎖競爭",
                "category": "併發",
                "likelihood": 6,
                "impact": 7,
                "priority": "中高",
            },
            {
                "risk": "JSON 欄位讓查詢與報表變重",
                "category": "Schema",
                "likelihood": 8,
                "impact": 8,
                "priority": "高",
            },
            {
                "risk": "缺少歷史職缺主表與趨勢資料",
                "category": "分析",
                "likelihood": 8,
                "impact": 9,
                "priority": "高",
            },
            {
                "risk": "backend abstraction 與實作不一致",
                "category": "演進",
                "likelihood": 6,
                "impact": 6,
                "priority": "中",
            },
        ]
    )
    risk_frame["score"] = risk_frame["likelihood"] * risk_frame["impact"]

    structured_row_total = int(table_frame["rows"].sum()) if not table_frame.empty else 0
    available_table_count = int(table_frame["available"].sum()) if not table_frame.empty else 0
    top_table = ""
    if not table_frame.empty:
        populated = table_frame.sort_values("rows", ascending=False)
        if int(populated.iloc[0]["rows"]) > 0:
            top_table = str(populated.iloc[0]["label"])

    query_runtime_live = bool(query_db_path.exists()) and bool(snapshots_dir.exists())

    return {
        "data_root": str(data_root),
        "storage_frame": storage_frame,
        "table_frame": table_frame,
        "risk_frame": risk_frame,
        "snapshot_summary": snapshot_summary,
        "pragmas": pragmas,
        "total_size": total_size,
        "cache_size": cache_size,
        "cache_share": _safe_share(cache_size, total_size),
        "structured_row_total": structured_row_total,
        "available_table_count": available_table_count,
        "top_table": top_table,
        "query_runtime_live": query_runtime_live,
        "cache_backend": cache_backend,
        "queue_backend": queue_backend,
        "database_backend": database_backend,
        "json_heavy_areas": JSON_HEAVY_AREAS,
    }


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


def render_database_page(ctx: PageContext) -> None:
    """渲染資料庫報告頁。"""
    _inject_database_report_styles()
    report = _load_database_report(
        data_dir=str(ctx.settings.data_dir),
        cache_backend=ctx.settings.cache_backend,
        queue_backend=ctx.settings.queue_backend,
        database_backend=ctx.settings.database_backend,
    )
    storage_frame = report["storage_frame"]
    table_frame = report["table_frame"]
    snapshot_summary = report["snapshot_summary"]
    pragmas = report["pragmas"]

    with st.container(border=True, key="database-shell"):
        _render_intro(report)
        with st.container(key="database-body"):
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

            overview_tab, learning_tab, risk_tab = st.tabs(
                ["現況總覽", "Database 教學", "擴充風險"]
            )

            with overview_tab:
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
                    raw_storage = storage_frame[
                        ["label", "category", "size_label", "share"]
                    ].copy()
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

                    raw_tables = table_frame[
                        ["database", "label", "rows", "available"]
                    ].copy()
                    raw_tables = raw_tables.rename(
                        columns={
                            "database": "檔案",
                            "label": "資料表",
                            "rows": "列數",
                            "available": "已存在",
                        }
                    )
                    st.dataframe(raw_tables, use_container_width=True, hide_index=True)

            with learning_tab:
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

            with risk_tab:
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
