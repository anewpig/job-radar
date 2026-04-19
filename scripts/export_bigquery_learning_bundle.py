#!/usr/bin/env python3
"""Export a BigQuery-friendly learning bundle from local Job Radar data."""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_TABLE_SPECS: tuple[tuple[str, str, str, bool], ...] = (
    ("market_history.sqlite3", "crawl_runs", "raw_market_history_crawl_runs", False),
    ("market_history.sqlite3", "job_posts", "raw_market_history_job_posts", False),
    ("market_history.sqlite3", "crawl_run_jobs", "raw_market_history_crawl_run_jobs", False),
    ("product_state.sqlite3", "ai_monitoring_events", "raw_product_ai_monitoring_events", False),
    ("product_state.sqlite3", "audit_events", "raw_product_audit_events", False),
    ("product_state.sqlite3", "feedback_events", "raw_product_feedback_events", False),
    ("product_state.sqlite3", "agent_memories", "raw_product_agent_memories", False),
    ("product_state.sqlite3", "saved_searches", "raw_product_saved_searches", False),
    ("product_state.sqlite3", "job_notifications", "raw_product_job_notifications", False),
    ("product_state.sqlite3", "notification_preferences", "raw_product_notification_preferences", False),
    ("query_runtime.sqlite3", "query_snapshots", "raw_query_runtime_query_snapshots", False),
    ("query_runtime.sqlite3", "crawl_jobs", "raw_query_runtime_crawl_jobs", False),
    ("query_runtime.sqlite3", "runtime_signals", "raw_query_runtime_runtime_signals", False),
    ("user_submissions.sqlite3", "user_submissions", "raw_user_submissions", True),
)

JSON_LIKE_COLUMNS: dict[str, set[str]] = {
    "crawl_runs": {
        "queries_json",
        "role_targets_json",
        "skills_json",
        "task_insights_json",
        "errors_json",
    },
    "job_posts": {"latest_payload_json"},
    "crawl_run_jobs": {"job_snapshot_json"},
    "ai_monitoring_events": {"metadata_json"},
    "audit_events": {"details_json"},
    "feedback_events": {"tags_json", "metadata_json"},
    "agent_memories": {"value_json"},
    "saved_searches": {
        "rows_json",
        "filters_json",
        "stats_json",
        "known_job_urls_json",
        "metadata_json",
        "delivery_channels_json",
    },
    "job_notifications": {"new_jobs_json", "delivery_notes_json", "metadata_json"},
    "notification_preferences": {"channels_json", "keywords_json"},
    "crawl_jobs": {"payload_json"},
    "runtime_signals": {"payload_json"},
    "user_submissions": {
        "target_roles",
        "core_skills",
        "tool_skills",
        "domain_keywords",
        "preferred_tasks",
        "generated_prompts",
        "match_keywords",
        "notes",
    },
}


@dataclass(slots=True)
class ExportTarget:
    db_filename: str
    table_name: str
    export_name: str
    sensitive: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export local Job Radar data into NDJSON files suitable for BigQuery learning.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing local SQLite files and snapshot JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/bigquery_exports"),
        help="Directory where the export bundle should be created.",
    )
    parser.add_argument(
        "--include-sensitive",
        action="store_true",
        help="Also export masked user_submissions for learning purposes.",
    )
    return parser.parse_args()


def now_slug() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _parse_json_like(table_name: str, column_name: str, value: Any) -> Any:
    if value in (None, ""):
        return None
    if column_name in JSON_LIKE_COLUMNS.get(table_name, set()):
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return value
    if isinstance(value, str) and value[:1] in {"{", "["}:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _read_sqlite_table(
    db_path: Path,
    table_name: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(f'SELECT * FROM "{table_name}"').fetchall()
        columns = [str(item[1]) for item in connection.execute(f'PRAGMA table_info("{table_name}")')]

    records: list[dict[str, Any]] = []
    for row in rows:
        payload: dict[str, Any] = {}
        for column in columns:
            payload[column] = _parse_json_like(table_name, column, row[column])
        records.append(payload)
    return records, columns


def _sqlite_table_exists(db_path: Path, table_name: str) -> bool:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            LIMIT 1
            """,
            (table_name,),
        ).fetchone()
    return row is not None


def _write_ndjson(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


def _guess_partition_field(columns: list[str]) -> str:
    for candidate in (
        "generated_at",
        "created_at",
        "updated_at",
        "last_seen_at",
        "first_seen_at",
    ):
        if candidate in columns:
            return candidate
    return ""


def _guess_cluster_fields(columns: list[str]) -> list[str]:
    prioritized = [
        "source",
        "matched_role",
        "query_fingerprint",
        "event_type",
        "status",
        "user_id",
        "memory_type",
    ]
    return [column for column in prioritized if column in columns][:4]


def export_sqlite_tables(
    *,
    data_dir: Path,
    bundle_dir: Path,
    include_sensitive: bool,
) -> list[dict[str, Any]]:
    exports: list[dict[str, Any]] = []
    for db_filename, table_name, export_name, sensitive in DEFAULT_TABLE_SPECS:
        if sensitive and not include_sensitive:
            continue
        db_path = data_dir / db_filename
        if not db_path.exists():
            exports.append(
                {
                    "kind": "sqlite_table",
                    "source_path": str(db_path),
                    "table_name": table_name,
                    "export_name": export_name,
                    "status": "missing",
                }
            )
            continue
        if not _sqlite_table_exists(db_path, table_name):
            exports.append(
                {
                    "kind": "sqlite_table",
                    "source_path": str(db_path),
                    "table_name": table_name,
                    "export_name": export_name,
                    "status": "missing_table",
                }
            )
            continue
        records, columns = _read_sqlite_table(db_path, table_name)
        output_path = bundle_dir / f"{export_name}.ndjson"
        _write_ndjson(output_path, records)
        exports.append(
            {
                "kind": "sqlite_table",
                "source_path": str(db_path),
                "table_name": table_name,
                "export_name": export_name,
                "output_path": str(output_path),
                "row_count": len(records),
                "partition_field": _guess_partition_field(columns),
                "cluster_fields": _guess_cluster_fields(columns),
                "status": "exported",
                "sensitive": sensitive,
            }
        )
    return exports


def export_snapshot_files(
    *,
    data_dir: Path,
    bundle_dir: Path,
) -> list[dict[str, Any]]:
    exports: list[dict[str, Any]] = []
    snapshot_path = data_dir / "jobs_latest.json"
    if snapshot_path.exists():
        output_path = bundle_dir / "raw_snapshot_jobs_latest.json"
        raw_text = snapshot_path.read_text(encoding="utf-8")
        output_path.write_text(raw_text, encoding="utf-8")
        try:
            payload = json.loads(raw_text)
            job_count = len(payload.get("jobs", []))
        except (OSError, json.JSONDecodeError):
            payload = {}
            job_count = 0
        exports.append(
            {
                "kind": "snapshot_file",
                "source_path": str(snapshot_path),
                "output_path": str(output_path),
                "export_name": "raw_snapshot_jobs_latest",
                "row_count": job_count,
                "status": "exported",
            }
        )
        jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
        if isinstance(jobs, list):
            jobs_output_path = bundle_dir / "raw_snapshot_jobs_latest_jobs.ndjson"
            _write_ndjson(jobs_output_path, [item for item in jobs if isinstance(item, dict)])
            exports.append(
                {
                    "kind": "snapshot_jobs_table",
                    "source_path": str(snapshot_path),
                    "output_path": str(jobs_output_path),
                    "export_name": "raw_snapshot_jobs_latest_jobs",
                    "row_count": len([item for item in jobs if isinstance(item, dict)]),
                    "partition_field": "generated_at" if payload.get("generated_at") else "",
                    "cluster_fields": ["source", "matched_role"],
                    "status": "exported",
                }
            )
    snapshots_dir = data_dir / "snapshots"
    if snapshots_dir.exists():
        files = sorted(item for item in snapshots_dir.glob("*.json") if item.is_file())
        manifest_rows: list[dict[str, Any]] = []
        raw_dir = bundle_dir / "snapshot_files"
        ensure_dir(raw_dir)
        for item in files[:50]:
            target = raw_dir / item.name
            target.write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
            manifest_rows.append({"filename": item.name, "source_path": str(item), "output_path": str(target)})
        if manifest_rows:
            manifest_path = bundle_dir / "snapshot_files_manifest.ndjson"
            _write_ndjson(manifest_path, manifest_rows)
            exports.append(
                {
                    "kind": "snapshot_manifest",
                    "source_path": str(snapshots_dir),
                    "output_path": str(manifest_path),
                    "export_name": "snapshot_files_manifest",
                    "row_count": len(manifest_rows),
                    "status": "exported",
                }
            )
    return exports


def write_manifest(bundle_dir: Path, exports: list[dict[str, Any]], *, data_dir: Path) -> Path:
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data_dir": str(data_dir.resolve()),
        "exports": exports,
    }
    path = bundle_dir / "bundle_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_load_guide(bundle_dir: Path, exports: list[dict[str, Any]]) -> Path:
    lines = [
        "# BigQuery 載入建議",
        "",
        "先建立 dataset，例如：`job_radar_raw`。",
        "",
        "以下是建議的 `bq load` 範例。你可以先用 `--autodetect` 練習，再逐步改成明確 schema。",
        "",
    ]
    for item in exports:
        if item.get("status") != "exported" or item.get("kind") not in {"sqlite_table", "snapshot_jobs_table"}:
            continue
        table_name = item["export_name"]
        output_path = item["output_path"]
        partition_field = str(item.get("partition_field") or "")
        cluster_fields = list(item.get("cluster_fields") or [])
        lines.append(f"## {table_name}")
        lines.append("")
        command = (
            f"bq load --source_format=NEWLINE_DELIMITED_JSON --autodetect "
            f"job_radar_raw.{table_name} '{output_path}'"
        )
        lines.append(f"```bash\n{command}\n```")
        if partition_field:
            lines.append(f"- 建議 partition 欄位：`{partition_field}`")
        if cluster_fields:
            lines.append(f"- 建議 cluster 欄位：`{', '.join(cluster_fields)}`")
        lines.append("")
    path = bundle_dir / "BIGQUERY_LOAD_GUIDE.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir.resolve()
    bundle_dir = (args.output_dir / f"job_radar_bigquery_bundle_{now_slug()}").resolve()
    ensure_dir(bundle_dir)

    exports = []
    exports.extend(
        export_sqlite_tables(
            data_dir=data_dir,
            bundle_dir=bundle_dir,
            include_sensitive=bool(args.include_sensitive),
        )
    )
    exports.extend(export_snapshot_files(data_dir=data_dir, bundle_dir=bundle_dir))
    manifest_path = write_manifest(bundle_dir, exports, data_dir=data_dir)
    guide_path = write_load_guide(bundle_dir, exports)

    print(f"Bundle ready: {bundle_dir}")
    print(f"Manifest: {manifest_path}")
    print(f"Guide: {guide_path}")
    for item in exports:
        status = item.get("status", "unknown")
        export_name = item.get("export_name") or item.get("table_name") or item.get("kind")
        row_count = item.get("row_count", "-")
        print(f"- {export_name}: {status} rows={row_count}")


if __name__ == "__main__":
    main()
