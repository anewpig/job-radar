"""Restore drill helper that verifies backup recovery on disposable scratch data."""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings, load_settings
from .sqlite_backup_service import run_sqlite_restore


RESTORE_DRILL_MARKER_TABLE = "restore_drill_marker"


@dataclass(slots=True)
class SQLiteRestoreDrillResult:
    backup_path: Path
    report_path: Path
    restored_databases: list[str]
    verified_databases: list[str]
    safety_backup_manifest_path: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a restore drill against a disposable scratch data dir.")
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Project base directory for loading .env and data paths.",
    )
    parser.add_argument(
        "--backup",
        default="",
        help="Backup directory or manifest path. Defaults to the latest backup set.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(args.base_dir)
    result = run_sqlite_restore_drill(
        settings=settings,
        backup_path=Path(args.backup).expanduser() if str(args.backup).strip() else None,
    )
    print(
        "SQLite restore drill: "
        f"backup={result.backup_path} "
        f"restored={','.join(result.restored_databases) or '-'} "
        f"verified={','.join(result.verified_databases) or '-'} "
        f"report={result.report_path}"
    )
    if result.safety_backup_manifest_path:
        print(f"Safety backup: {result.safety_backup_manifest_path}")


def run_sqlite_restore_drill(
    *,
    settings: Settings,
    backup_path: Path | None = None,
) -> SQLiteRestoreDrillResult:
    selected_backup_path = backup_path or _latest_backup_path(settings.data_dir / "backups" / "sqlite")
    if selected_backup_path is None:
        raise FileNotFoundError("No SQLite backup set available for restore drill.")

    drill_root = settings.data_dir / "restore_drills" / _timestamp_slug()
    scratch_data_dir = drill_root / "scratch" / "data"
    scratch_data_dir.mkdir(parents=True, exist_ok=True)
    scratch_settings = replace(settings, data_dir=scratch_data_dir)

    placeholder_paths = {
        "product_state": scratch_settings.product_state_db_path,
        "user_submissions": scratch_settings.user_data_db_path,
        "market_history": scratch_settings.market_history_db_path,
        "query_runtime": scratch_settings.query_state_db_path,
    }
    for path in placeholder_paths.values():
        _write_placeholder_database(path)

    restore_result = run_sqlite_restore(
        settings=scratch_settings,
        backup_path=selected_backup_path,
        include_runtime=False,
        create_safety_backup=True,
    )

    verified_databases = []
    for database_key in restore_result.restored_databases:
        restored_path = placeholder_paths[database_key]
        if _marker_table_exists(restored_path):
            raise RuntimeError(f"Restore drill failed for {database_key}: marker table still exists.")
        verified_databases.append(database_key)

    report = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "backup_path": str(selected_backup_path),
        "restored_databases": restore_result.restored_databases,
        "verified_databases": verified_databases,
        "safety_backup_manifest_path": (
            str(restore_result.safety_backup_manifest_path)
            if restore_result.safety_backup_manifest_path is not None
            else ""
        ),
    }
    report_path = drill_root / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    scratch_root = drill_root / "scratch"
    if scratch_root.exists():
        shutil.rmtree(scratch_root)

    return SQLiteRestoreDrillResult(
        backup_path=selected_backup_path,
        report_path=report_path,
        restored_databases=list(restore_result.restored_databases),
        verified_databases=verified_databases,
        safety_backup_manifest_path=str(restore_result.safety_backup_manifest_path or ""),
    )


def _latest_backup_path(backup_root: Path) -> Path | None:
    backup_dirs = [entry for entry in backup_root.iterdir()] if backup_root.exists() else []
    valid_dirs = [entry for entry in backup_dirs if entry.is_dir() and (entry / "manifest.json").exists()]
    if not valid_dirs:
        return None
    valid_dirs.sort(key=lambda path: path.name, reverse=True)
    return valid_dirs[0]


def _write_placeholder_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            f"CREATE TABLE IF NOT EXISTS {RESTORE_DRILL_MARKER_TABLE} (value TEXT NOT NULL)"
        )
        connection.execute(f"DELETE FROM {RESTORE_DRILL_MARKER_TABLE}")
        connection.execute(
            f"INSERT INTO {RESTORE_DRILL_MARKER_TABLE}(value) VALUES ('before-restore')"
        )
        connection.commit()


def _marker_table_exists(db_path: Path) -> bool:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            """,
            (RESTORE_DRILL_MARKER_TABLE,),
        ).fetchone()
    return row is not None


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


if __name__ == "__main__":
    main()
