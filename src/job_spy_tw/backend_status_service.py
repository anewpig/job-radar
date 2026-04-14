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
from .build_info import BuildInfo, collect_build_info
from .product_store import ProductStore
from .schema_versions import schema_version_registry
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
    build: BuildInfo
    execution_mode: str
    operations: BackendOperationsSnapshot
    backups: SQLiteBackupStatus
    schema_versions: dict[str, Any] = field(default_factory=dict)
    ai_health: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "build": asdict(self.build),
            "execution_mode": self.execution_mode,
            "operations": asdict(self.operations),
            "backups": asdict(self.backups),
            "schema_versions": dict(self.schema_versions),
            "ai_health": dict(self.ai_health),
            "security": dict(self.security),
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
    build = collect_build_info()
    backups = _collect_backup_status(settings.data_dir / "backups" / "sqlite")
    ai_health = {
        "latency_budgets": product_store.evaluate_ai_latency_budgets(limit=500),
        "assistant_modes": product_store.summarize_assistant_modes(limit=500),
        "cache_efficiency": product_store.summarize_ai_cache_efficiency(limit=500),
    }
    security = {
        "backend_console_allowed_roles": list(settings.backend_console_allowed_roles),
        "recent_audit_events": len(product_store.list_recent_audit_events(limit=50)),
    }
    schema_versions = schema_version_registry()
    issues = _collect_backend_issues(operations, backups, ai_health)
    return BackendStatusReport(
        build=build,
        execution_mode=operations.execution_mode,
        operations=operations,
        backups=backups,
        schema_versions=schema_versions,
        ai_health=ai_health,
        security=security,
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
    ai_health: dict[str, Any],
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
    latency_budgets = (ai_health.get("latency_budgets") or {})
    ai_status = str(latency_budgets.get("status") or "")
    if ai_status == "FAIL":
        issues.append("ai latency budgets failing")
    elif ai_status == "WARN":
        issues.append("ai latency budgets warning")
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
