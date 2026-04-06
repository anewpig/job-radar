"""SQLite backup and restore helpers for operational use."""

from __future__ import annotations

import json
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .settings import Settings


MANIFEST_VERSION = 1
PERSISTENT_DATABASE_KEYS = ("product_state", "user_submissions", "market_history")
RUNTIME_DATABASE_KEYS = ("query_runtime",)
DEFAULT_BACKUP_ROOT_PARTS = ("backups", "sqlite")


@dataclass(slots=True, frozen=True)
class SQLiteDatabaseTarget:
    key: str
    filename: str
    path: Path
    category: str


@dataclass(slots=True)
class SQLiteBackupEntry:
    database_key: str
    filename: str
    backup_file: str
    source_path: str
    size_bytes: int
    category: str


@dataclass(slots=True)
class SQLiteBackupResult:
    backup_dir: Path
    manifest_path: Path
    created_at: str
    entries: list[SQLiteBackupEntry]
    skipped_databases: list[str]
    pruned_backup_dirs: list[Path]


@dataclass(slots=True)
class SQLiteRestoreResult:
    restored_databases: list[str]
    skipped_databases: list[str]
    manifest_path: Path
    safety_backup_manifest_path: Path | None


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _open_sqlite_connection(db_path: Path, *, readonly: bool) -> sqlite3.Connection:
    if readonly:
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    else:
        connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def _copy_sqlite_database(source_path: Path, destination_path: Path) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with _open_sqlite_connection(source_path, readonly=True) as source_connection:
        with _open_sqlite_connection(destination_path, readonly=False) as destination_connection:
            source_connection.backup(destination_connection)


def _build_target_map(settings: Settings) -> dict[str, SQLiteDatabaseTarget]:
    return {
        "product_state": SQLiteDatabaseTarget(
            key="product_state",
            filename=settings.product_state_db_path.name,
            path=settings.product_state_db_path,
            category="persistent",
        ),
        "user_submissions": SQLiteDatabaseTarget(
            key="user_submissions",
            filename=settings.user_data_db_path.name,
            path=settings.user_data_db_path,
            category="persistent",
        ),
        "market_history": SQLiteDatabaseTarget(
            key="market_history",
            filename=settings.market_history_db_path.name,
            path=settings.market_history_db_path,
            category="persistent",
        ),
        "query_runtime": SQLiteDatabaseTarget(
            key="query_runtime",
            filename=settings.query_state_db_path.name,
            path=settings.query_state_db_path,
            category="runtime",
        ),
    }


def _resolve_selected_targets(
    settings: Settings,
    *,
    include_runtime: bool,
    database_keys: Iterable[str] | None,
) -> list[SQLiteDatabaseTarget]:
    target_map = _build_target_map(settings)
    allowed_keys = set(PERSISTENT_DATABASE_KEYS)
    if include_runtime:
        allowed_keys.update(RUNTIME_DATABASE_KEYS)
    if database_keys is None:
        selected_keys = allowed_keys
    else:
        selected_keys = set(database_keys) & allowed_keys
    return [target_map[key] for key in target_map if key in selected_keys]


def _default_backup_root(settings: Settings) -> Path:
    return settings.data_dir.joinpath(*DEFAULT_BACKUP_ROOT_PARTS)


def _write_manifest(
    *,
    manifest_path: Path,
    created_at: str,
    entries: list[SQLiteBackupEntry],
    skipped_databases: list[str],
) -> None:
    manifest_path.write_text(
        json.dumps(
            {
                "version": MANIFEST_VERSION,
                "created_at": created_at,
                "databases": [asdict(entry) for entry in entries],
                "skipped_databases": skipped_databases,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def prune_sqlite_backups(
    *,
    backup_root: Path,
    keep_last: int,
) -> list[Path]:
    if keep_last < 0:
        raise ValueError("keep_last must be >= 0")
    if not backup_root.exists():
        return []

    backup_dirs: list[tuple[str, Path]] = []
    for entry in backup_root.iterdir():
        manifest_path = entry / "manifest.json"
        if not entry.is_dir() or not manifest_path.exists():
            continue
        try:
            manifest = _load_manifest(manifest_path)
            created_at = str(manifest.get("created_at", "")).strip()
        except (OSError, ValueError, json.JSONDecodeError):
            created_at = ""
        backup_dirs.append((created_at or entry.name, entry))

    backup_dirs.sort(key=lambda item: item[0], reverse=True)
    deleted_dirs: list[Path] = []
    for _sort_key, backup_dir in backup_dirs[keep_last:]:
        shutil.rmtree(backup_dir)
        deleted_dirs.append(backup_dir)
    return deleted_dirs


def run_sqlite_backup(
    *,
    settings: Settings,
    include_runtime: bool = False,
    database_keys: Iterable[str] | None = None,
    backup_root: Path | None = None,
    backup_slug: str | None = None,
    keep_last: int | None = None,
) -> SQLiteBackupResult:
    targets = _resolve_selected_targets(
        settings,
        include_runtime=include_runtime,
        database_keys=database_keys,
    )
    created_at = datetime.now(timezone.utc).isoformat()
    backup_dir = (backup_root or _default_backup_root(settings)) / (backup_slug or _timestamp_slug())
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = backup_dir / "manifest.json"
    entries: list[SQLiteBackupEntry] = []
    skipped_databases: list[str] = []

    for target in targets:
        if not target.path.exists():
            skipped_databases.append(target.key)
            continue
        backup_file = target.filename
        backup_path = backup_dir / backup_file
        _copy_sqlite_database(target.path, backup_path)
        entries.append(
            SQLiteBackupEntry(
                database_key=target.key,
                filename=target.filename,
                backup_file=backup_file,
                source_path=str(target.path),
                size_bytes=backup_path.stat().st_size,
                category=target.category,
            )
        )

    _write_manifest(
        manifest_path=manifest_path,
        created_at=created_at,
        entries=entries,
        skipped_databases=skipped_databases,
    )
    pruned_backup_dirs = (
        prune_sqlite_backups(
            backup_root=backup_dir.parent,
            keep_last=int(keep_last),
        )
        if keep_last is not None
        else []
    )
    return SQLiteBackupResult(
        backup_dir=backup_dir,
        manifest_path=manifest_path,
        created_at=created_at,
        entries=entries,
        skipped_databases=skipped_databases,
        pruned_backup_dirs=pruned_backup_dirs,
    )


def _resolve_manifest_path(backup_path: Path) -> Path:
    return backup_path / "manifest.json" if backup_path.is_dir() else backup_path


def _load_manifest(manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if int(manifest.get("version", 0)) != MANIFEST_VERSION:
        raise ValueError(f"Unsupported manifest version: {manifest.get('version')}")
    return manifest


def run_sqlite_restore(
    *,
    settings: Settings,
    backup_path: Path,
    include_runtime: bool = False,
    create_safety_backup: bool = True,
) -> SQLiteRestoreResult:
    manifest_path = _resolve_manifest_path(backup_path)
    manifest = _load_manifest(manifest_path)
    backup_dir = manifest_path.parent
    target_map = _build_target_map(settings)
    allowed_keys = set(PERSISTENT_DATABASE_KEYS)
    if include_runtime:
        allowed_keys.update(RUNTIME_DATABASE_KEYS)

    restore_entries: list[dict[str, object]] = []
    skipped_databases: list[str] = []
    for entry in manifest.get("databases", []):
        if not isinstance(entry, dict):
            continue
        database_key = str(entry.get("database_key", "")).strip()
        if database_key not in allowed_keys:
            skipped_databases.append(database_key)
            continue
        restore_entries.append(entry)

    safety_backup_manifest_path: Path | None = None
    if create_safety_backup and restore_entries:
        safety_backup = run_sqlite_backup(
            settings=settings,
            include_runtime=include_runtime,
            database_keys=[str(entry["database_key"]) for entry in restore_entries],
            backup_slug=f"pre-restore-{_timestamp_slug()}",
        )
        safety_backup_manifest_path = safety_backup.manifest_path

    restored_databases: list[str] = []
    for entry in restore_entries:
        database_key = str(entry["database_key"])
        backup_file = str(entry["backup_file"])
        source_backup_path = backup_dir / backup_file
        if not source_backup_path.exists():
            skipped_databases.append(database_key)
            continue
        target = target_map[database_key]
        target.path.parent.mkdir(parents=True, exist_ok=True)
        _copy_sqlite_database(source_backup_path, target.path)
        restored_databases.append(database_key)

    return SQLiteRestoreResult(
        restored_databases=restored_databases,
        skipped_databases=sorted(set(skipped_databases)),
        manifest_path=manifest_path,
        safety_backup_manifest_path=safety_backup_manifest_path,
    )
