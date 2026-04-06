"""Combined daily maintenance helpers for backend operations."""

from __future__ import annotations

from dataclasses import dataclass

from .runtime_maintenance_service import RuntimeCleanupResult, run_runtime_cleanup
from .settings import Settings
from .sqlite_backup_service import SQLiteBackupResult, run_sqlite_backup


@dataclass(slots=True)
class BackendMaintenanceResult:
    trigger: str
    cleanup: RuntimeCleanupResult
    backup: SQLiteBackupResult


def run_backend_maintenance(
    *,
    settings: Settings,
    trigger: str,
    force_cleanup: bool = False,
    include_runtime_backup: bool = False,
    keep_last_backups: int | None = None,
) -> BackendMaintenanceResult:
    cleanup_result = run_runtime_cleanup(
        settings=settings,
        trigger=trigger,
        force=force_cleanup,
    )
    backup_result = run_sqlite_backup(
        settings=settings,
        include_runtime=include_runtime_backup,
        keep_last=keep_last_backups,
    )
    return BackendMaintenanceResult(
        trigger=trigger,
        cleanup=cleanup_result,
        backup=backup_result,
    )
