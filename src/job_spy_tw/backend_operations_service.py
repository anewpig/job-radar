"""Backend operations snapshot helpers for scheduler/worker monitoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .crawl_application_service import build_query_runtime, collect_due_saved_searches
from .models import UserAccount
from .product_store import ProductStore
from .query_runtime import RuntimeSignalStore
from .settings import Settings
from .storage import load_snapshot


@dataclass(slots=True)
class DueSavedSearchStatus:
    user_id: int
    user_label: str
    search_id: int
    search_name: str
    frequency: str
    last_run_at: str
    role_labels: list[str] = field(default_factory=list)
    custom_query_count: int = 0


@dataclass(slots=True)
class QueueJobStatus:
    job_id: int
    status: str
    priority: int
    query_signature: str
    query_labels: list[str] = field(default_factory=list)
    subscriber_count: int = 0
    attempt_count: int = 0
    max_attempts: int = 0
    created_at: str = ""
    updated_at: str = ""
    lease_owner: str = ""
    lease_expires_at: str = ""
    next_retry_at: str = ""
    error_message: str = ""


@dataclass(slots=True)
class SnapshotCacheStatus:
    query_signature: str
    status: str
    is_partial: bool
    generated_at: str
    updated_at: str
    fresh_until: str
    job_count: int = 0
    query_count: int = 0
    error_message: str = ""


@dataclass(slots=True)
class RuntimeComponentStatus:
    component_kind: str
    component_id: str
    status: str
    message: str
    updated_at: str
    is_stale: bool = False
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BackendOperationsSnapshot:
    execution_mode: str
    due_saved_search_count: int = 0
    pending_job_count: int = 0
    leased_job_count: int = 0
    failed_job_count: int = 0
    ready_snapshot_count: int = 0
    partial_snapshot_count: int = 0
    last_saved_search_refresh_at: str = ""
    last_scheduler_pass_at: str = ""
    last_worker_activity_at: str = ""
    last_job_activity_at: str = ""
    last_snapshot_update_at: str = ""
    due_saved_searches: list[DueSavedSearchStatus] = field(default_factory=list)
    recent_jobs: list[QueueJobStatus] = field(default_factory=list)
    recent_snapshots: list[SnapshotCacheStatus] = field(default_factory=list)
    runtime_components: list[RuntimeComponentStatus] = field(default_factory=list)


def collect_backend_operations_snapshot(
    *,
    settings: Settings,
    product_store: ProductStore,
    due_limit: int = 12,
    job_limit: int = 12,
    snapshot_limit: int = 12,
    signal_limit: int = 8,
) -> BackendOperationsSnapshot:
    """Collect one developer-facing operations snapshot for the backend runtime."""
    users = product_store.list_users(include_guest=False)
    users_by_id = {int(user.id): user for user in users}
    due_candidates = collect_due_saved_searches(
        product_store=product_store,
        settings=settings,
    )
    registry, queue = build_query_runtime(settings)
    signal_store = RuntimeSignalStore(db_path=settings.query_state_db_path)

    all_saved_searches_last_run_at = _collect_last_saved_search_refresh(users, product_store)
    recent_jobs = queue.list_jobs(limit=job_limit)
    recent_snapshots = registry.list_snapshots(limit=snapshot_limit)
    signals = signal_store.list_signals(limit=signal_limit)

    scheduler_updates = [
        signal.updated_at for signal in signals if signal.component_kind == "scheduler"
    ]
    worker_updates = [
        signal.updated_at for signal in signals if signal.component_kind == "worker"
    ]

    return BackendOperationsSnapshot(
        execution_mode=str(settings.crawl_execution_mode).strip().lower() or "inline",
        due_saved_search_count=len(due_candidates),
        pending_job_count=queue.count_jobs(status="pending"),
        leased_job_count=queue.count_jobs(status="leased"),
        failed_job_count=queue.count_jobs(status="failed"),
        ready_snapshot_count=registry.count_snapshots(status="ready", is_partial=False),
        partial_snapshot_count=registry.count_snapshots(is_partial=True),
        last_saved_search_refresh_at=all_saved_searches_last_run_at,
        last_scheduler_pass_at=_latest_timestamp(scheduler_updates),
        last_worker_activity_at=_latest_timestamp(worker_updates),
        last_job_activity_at=recent_jobs[0].updated_at if recent_jobs else "",
        last_snapshot_update_at=recent_snapshots[0].updated_at if recent_snapshots else "",
        due_saved_searches=[
            DueSavedSearchStatus(
                user_id=int(candidate.user_id),
                user_label=_format_user_label(users_by_id.get(int(candidate.user_id))),
                search_id=int(candidate.search_id),
                search_name=candidate.search_name,
                frequency=candidate.frequency,
                last_run_at=candidate.last_run_at,
                role_labels=_extract_role_labels(candidate.rows),
                custom_query_count=_count_custom_queries(candidate.custom_queries_text),
            )
            for candidate in due_candidates[: max(1, int(due_limit))]
        ],
        recent_jobs=[
            QueueJobStatus(
                job_id=int(job.id),
                status=job.status,
                priority=int(job.priority),
                query_signature=job.query_signature,
                query_labels=_extract_query_labels(job.payload()),
                subscriber_count=len(
                    product_store.list_saved_search_subscribers(
                        signature=job.query_signature
                    )
                ),
                attempt_count=int(job.attempt_count),
                max_attempts=int(job.max_attempts),
                created_at=job.created_at,
                updated_at=job.updated_at,
                lease_owner=job.lease_owner,
                lease_expires_at=job.lease_expires_at,
                next_retry_at=job.next_retry_at,
                error_message=job.error_message,
            )
            for job in recent_jobs
        ],
        recent_snapshots=[
            SnapshotCacheStatus(
                query_signature=record.query_signature,
                status=record.status,
                is_partial=bool(record.is_partial),
                generated_at=record.generated_at,
                updated_at=record.updated_at,
                fresh_until=record.fresh_until,
                job_count=len(record.snapshot.jobs) if record.snapshot is not None else 0,
                query_count=len(record.snapshot.queries) if record.snapshot is not None else 0,
                error_message=record.error_message,
            )
            for record in _hydrate_recent_snapshots(registry, recent_snapshots)
        ],
        runtime_components=[
            RuntimeComponentStatus(
                component_kind=signal.component_kind,
                component_id=signal.component_id,
                status=signal.status,
                message=signal.message,
                updated_at=signal.updated_at,
                is_stale=_is_signal_stale(signal.updated_at, signal.payload()),
                payload=signal.payload(),
            )
            for signal in signals
        ],
    )


def _collect_last_saved_search_refresh(
    users: list[UserAccount],
    product_store: ProductStore,
) -> str:
    timestamps: list[str] = []
    for user in users:
        for saved_search in product_store.list_saved_searches(user_id=int(user.id)):
            if str(saved_search.last_run_at).strip():
                timestamps.append(saved_search.last_run_at)
    return _latest_timestamp(timestamps)


def _hydrate_recent_snapshots(registry, recent_snapshots):
    hydrated = []
    for record in recent_snapshots:
        if record.snapshot is None and record.storage_key:
            snapshot_path = registry.snapshot_dir / record.storage_key
            if snapshot_path.exists():
                record.snapshot = load_snapshot(snapshot_path)
        hydrated.append(record)
    return hydrated


def _extract_role_labels(rows: list[dict[str, Any]]) -> list[str]:
    labels = [
        str(row.get("role", "")).strip()
        for row in rows
        if bool(row.get("enabled", True)) and str(row.get("role", "")).strip()
    ]
    return list(dict.fromkeys(labels))


def _extract_query_labels(payload: dict[str, Any]) -> list[str]:
    queries = [
        str(query).strip()
        for query in payload.get("queries", [])
        if str(query).strip()
    ]
    if queries:
        return list(dict.fromkeys(queries))[:4]
    role_targets = payload.get("role_targets") or []
    labels: list[str] = []
    for item in role_targets:
        if not isinstance(item, dict):
            continue
        role_name = str(item.get("name", "")).strip()
        if role_name:
            labels.append(role_name)
    return list(dict.fromkeys(labels))[:4]


def _count_custom_queries(custom_queries_text: str) -> int:
    return len(
        [line.strip() for line in str(custom_queries_text).splitlines() if line.strip()]
    )


def _format_user_label(user: UserAccount | None) -> str:
    if user is None:
        return "未知使用者"
    if user.display_name.strip():
        return user.display_name.strip()
    email = user.email.strip()
    if "@" not in email:
        return email or f"user-{user.id}"
    local, domain = email.split("@", 1)
    masked_local = local[:2] + "***" if len(local) > 2 else local[:1] + "***"
    return f"{masked_local}@{domain}"


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).strip())
    except Exception:  # noqa: BLE001
        return None


def _latest_timestamp(values: list[str]) -> str:
    parsed = [
        (parsed_value, original)
        for original in values
        if (parsed_value := _parse_iso(original)) is not None
    ]
    if not parsed:
        return ""
    parsed.sort(key=lambda item: item[0], reverse=True)
    return parsed[0][1]


def _is_signal_stale(updated_at: str, payload: dict[str, Any]) -> bool:
    parsed = _parse_iso(updated_at)
    if parsed is None:
        return True
    if bool(payload.get("once", False)):
        return False
    poll_interval = max(1.0, float(payload.get("poll_interval", 60.0) or 60.0))
    stale_seconds = max(120.0, poll_interval * 2.5)
    return (datetime.now() - parsed).total_seconds() > stale_seconds
