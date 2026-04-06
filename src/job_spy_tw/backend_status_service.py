"""CLI-friendly backend status report helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .backend_operations_service import (
    BackendOperationsSnapshot,
    RuntimeComponentStatus,
    collect_backend_operations_snapshot,
)
from .product_store import ProductStore
from .settings import Settings


@dataclass(slots=True)
class SQLiteBackupStatus:
    backup_root: str
    backup_count: int = 0
    latest_backup_id: str = ""
    latest_manifest_path: str = ""
    latest_created_at: str = ""
    latest_database_keys: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BackendStatusReport:
    execution_mode: str
    operations: BackendOperationsSnapshot
    backups: SQLiteBackupStatus
    issues: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_mode": self.execution_mode,
            "operations": asdict(self.operations),
            "backups": asdict(self.backups),
            "issues": list(self.issues),
        }


def collect_backend_status_report(
    *,
    settings: Settings,
    product_store: ProductStore,
) -> BackendStatusReport:
    operations = collect_backend_operations_snapshot(
        settings=settings,
        product_store=product_store,
    )
    backups = _collect_backup_status(settings.data_dir / "backups" / "sqlite")
    issues = _collect_backend_issues(operations, backups)
    return BackendStatusReport(
        execution_mode=operations.execution_mode,
        operations=operations,
        backups=backups,
        issues=issues,
    )


def _collect_backup_status(backup_root: Path) -> SQLiteBackupStatus:
    manifests: list[tuple[str, Path, dict[str, Any]]] = []
    if backup_root.exists():
        for entry in backup_root.iterdir():
            manifest_path = entry / "manifest.json"
            if not entry.is_dir() or not manifest_path.exists():
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            created_at = str(manifest.get("created_at", "")).strip()
            manifests.append((created_at or entry.name, entry, manifest))
    manifests.sort(key=lambda item: item[0], reverse=True)
    if not manifests:
        return SQLiteBackupStatus(
            backup_root=str(backup_root),
            backup_count=0,
        )

    _sort_key, latest_dir, latest_manifest = manifests[0]
    latest_database_keys = [
        str(entry.get("database_key", "")).strip()
        for entry in latest_manifest.get("databases", [])
        if isinstance(entry, dict) and str(entry.get("database_key", "")).strip()
    ]
    return SQLiteBackupStatus(
        backup_root=str(backup_root),
        backup_count=len(manifests),
        latest_backup_id=latest_dir.name,
        latest_manifest_path=str(latest_dir / "manifest.json"),
        latest_created_at=str(latest_manifest.get("created_at", "")).strip(),
        latest_database_keys=latest_database_keys,
    )


def _collect_backend_issues(
    operations: BackendOperationsSnapshot,
    backups: SQLiteBackupStatus,
) -> list[str]:
    issues: list[str] = []
    if operations.execution_mode == "worker":
        scheduler_status = _latest_component_status(
            operations.runtime_components,
            component_kind="scheduler",
        )
        worker_status = _latest_component_status(
            operations.runtime_components,
            component_kind="worker",
        )
        if scheduler_status is None:
            issues.append("scheduler heartbeat missing")
        elif scheduler_status.is_stale:
            issues.append("scheduler heartbeat stale")
        if worker_status is None:
            issues.append("worker heartbeat missing")
        elif worker_status.is_stale:
            issues.append("worker heartbeat stale")

    if operations.failed_job_count > 0:
        issues.append(f"failed jobs present: {operations.failed_job_count}")
    if backups.backup_count <= 0:
        issues.append("sqlite backup missing")
    return issues


def _latest_component_status(
    runtime_components: list[RuntimeComponentStatus],
    *,
    component_kind: str,
) -> RuntimeComponentStatus | None:
    for component in runtime_components:
        if component.component_kind == component_kind:
            return component
    return None
