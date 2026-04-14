"""提供資料庫報告頁的資料讀取與整理 helper。"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

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

