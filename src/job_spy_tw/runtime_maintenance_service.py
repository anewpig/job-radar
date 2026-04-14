"""Runtime cleanup helpers for query queue, snapshot cache, and signals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .crawl_application_service import build_query_runtime
from .query_runtime import RuntimeSignalStore
from .settings import Settings
from .utils import CachedFetcher, purge_nested_cache_files


MAINTENANCE_COMPONENT_KIND = "cleanup"
MAINTENANCE_COMPONENT_ID = "runtime-maintenance"


@dataclass(slots=True)
class RuntimeCleanupResult:
    status: str
    trigger: str
    skipped_reason: str = ""
    deleted_jobs: int = 0
    deleted_snapshot_rows: int = 0
    deleted_snapshot_files: int = 0
    deleted_orphan_snapshot_files: int = 0
    deleted_signals: int = 0
    deleted_cache_files: int = 0
    deleted_cache_bytes: int = 0
    retained_cache_files: int = 0
    retained_cache_bytes: int = 0
    ran_at: str = ""


def run_runtime_cleanup(
    *,
    settings: Settings,
    trigger: str,
    force: bool = False,
) -> RuntimeCleanupResult:
    """Prune old runtime artifacts on an interval so SQLite state stays bounded."""
    signal_store = RuntimeSignalStore(db_path=settings.query_state_db_path)
    current_time = datetime.now().isoformat(timespec="seconds")
    if not force:
        latest_cleanup = _latest_cleanup_signal(signal_store)
        if latest_cleanup is not None and not _cleanup_due(
            latest_cleanup.updated_at,
            interval_seconds=settings.runtime_cleanup_interval_seconds,
        ):
            return RuntimeCleanupResult(
                status="skipped",
                trigger=trigger,
                skipped_reason="cleanup interval not elapsed",
                ran_at=current_time,
            )

    registry, queue = build_query_runtime(settings)
    try:
        deleted_jobs = queue.prune_jobs(
            retention_days=settings.runtime_job_retention_days
        )
        snapshot_result = registry.prune_snapshots(
            ready_retention_days=settings.runtime_snapshot_retention_days,
            partial_retention_hours=settings.runtime_partial_snapshot_retention_hours,
        )
        deleted_signals = signal_store.prune_signals(
            retention_days=settings.runtime_signal_retention_days
        )
        cache_result = CachedFetcher(
            cache_dir=settings.cache_dir,
            timeout=settings.request_timeout,
            delay_seconds=settings.request_delay,
            user_agent=settings.user_agent,
            allow_insecure_ssl_fallback=settings.allow_insecure_ssl_fallback,
            backend=settings.cache_backend,
        ).purge_cache(
            max_bytes=settings.cache_max_bytes,
            max_files=settings.cache_max_files,
        )
        root_cache_entries = sum(
            1 for path in settings.cache_dir.glob("*.html") if path.is_file()
        ) if settings.cache_dir.exists() else 0
        root_cache_bytes = sum(
            path.stat().st_size for path in settings.cache_dir.iterdir() if path.is_file()
        ) if settings.cache_dir.exists() else 0
        nested_cache_result = purge_nested_cache_files(
            settings.cache_dir,
            max_bytes=max(0, settings.cache_max_bytes - int(root_cache_bytes)),
            max_files=max(0, settings.cache_max_files - int(root_cache_entries)),
        )
        result = RuntimeCleanupResult(
            status="completed",
            trigger=trigger,
            deleted_jobs=deleted_jobs,
            deleted_snapshot_rows=int(snapshot_result["deleted_rows"]),
            deleted_snapshot_files=int(snapshot_result["deleted_files"]),
            deleted_orphan_snapshot_files=int(snapshot_result["deleted_orphan_files"]),
            deleted_signals=deleted_signals,
            deleted_cache_files=int(cache_result.deleted_files + nested_cache_result.deleted_files),
            deleted_cache_bytes=int(cache_result.deleted_bytes + nested_cache_result.deleted_bytes),
            retained_cache_files=int(root_cache_entries + nested_cache_result.retained_files),
            retained_cache_bytes=int(root_cache_bytes + nested_cache_result.retained_bytes),
            ran_at=current_time,
        )
        signal_store.put_signal(
            component_kind=MAINTENANCE_COMPONENT_KIND,
            component_id=MAINTENANCE_COMPONENT_ID,
            status="completed",
            message=_format_cleanup_message(result),
            payload={
                "trigger": trigger,
                "interval_seconds": int(settings.runtime_cleanup_interval_seconds),
                "deleted_jobs": int(result.deleted_jobs),
                "deleted_snapshot_rows": int(result.deleted_snapshot_rows),
                "deleted_snapshot_files": int(result.deleted_snapshot_files),
                "deleted_orphan_snapshot_files": int(result.deleted_orphan_snapshot_files),
                "deleted_signals": int(result.deleted_signals),
                "deleted_cache_files": int(result.deleted_cache_files),
                "deleted_cache_bytes": int(result.deleted_cache_bytes),
                "retained_cache_files": int(result.retained_cache_files),
                "retained_cache_bytes": int(result.retained_cache_bytes),
            },
        )
        return result
    except Exception as exc:
        signal_store.put_signal(
            component_kind=MAINTENANCE_COMPONENT_KIND,
            component_id=MAINTENANCE_COMPONENT_ID,
            status="failed",
            message=str(exc),
            payload={
                "trigger": trigger,
                "interval_seconds": int(settings.runtime_cleanup_interval_seconds),
            },
        )
        raise


def _latest_cleanup_signal(signal_store: RuntimeSignalStore):
    signals = signal_store.list_signals(
        component_kind=MAINTENANCE_COMPONENT_KIND,
        limit=10,
    )
    for signal in signals:
        if signal.component_id == MAINTENANCE_COMPONENT_ID:
            return signal
    return None


def _cleanup_due(updated_at: str, *, interval_seconds: int) -> bool:
    try:
        previous_run = datetime.fromisoformat(str(updated_at).strip())
    except Exception:  # noqa: BLE001
        return True
    return (datetime.now() - previous_run).total_seconds() >= max(
        0,
        int(interval_seconds),
    )


def _format_cleanup_message(result: RuntimeCleanupResult) -> str:
    return (
        f"Cleanup via {result.trigger}: "
        f"jobs={result.deleted_jobs}, "
        f"snapshots={result.deleted_snapshot_rows}, "
        f"snapshot_files={result.deleted_snapshot_files}, "
        f"orphans={result.deleted_orphan_snapshot_files}, "
        f"signals={result.deleted_signals}, "
        f"cache_files={result.deleted_cache_files}"
    )
