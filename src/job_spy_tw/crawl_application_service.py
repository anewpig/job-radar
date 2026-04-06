"""Pure backend helpers for staged crawl orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import sqlite3
from typing import Any

from .crawl_tuning import CrawlPreset, apply_crawl_preset, get_crawl_preset
from .models import (
    JobListing,
    MarketSnapshot,
    NotificationPreference,
    TargetRole,
)
from .notification_service import NotificationService
from .pipeline import JobMarketPipeline
from .product_store import ProductStore
from .query_runtime import CrawlJobQueue, CrawlJobRecord, QuerySnapshotRegistry
from .settings import Settings
from .targets import build_default_queries


@dataclass(slots=True)
class PendingCrawlState:
    """Serializable crawl state that the UI can store in session state."""

    query_signature: str = ""
    active_job_id: int = 0
    pending_queries: list[str] = field(default_factory=list)
    pending_jobs: list[JobListing] = field(default_factory=list)
    pending_errors: list[str] = field(default_factory=list)
    partial_ready_at: str = ""
    detail_cursor: int = 0
    detail_total: int = 0
    remaining_page_cursor: int = 1
    initial_wave_sources: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SavedSearchSyncResult:
    """Result of syncing one crawl snapshot back to saved-search state."""

    feedback: str = ""
    active_saved_search_id: int | None = None


@dataclass(slots=True)
class CrawlStartResult:
    """Outcome of attempting to start one staged crawl job."""

    status: str
    snapshot: MarketSnapshot | None = None
    pending_state: PendingCrawlState | None = None
    warning_message: str = ""


@dataclass(slots=True)
class FinalizeBatchResult:
    """Outcome of advancing one finalize batch."""

    status: str
    snapshot: MarketSnapshot | None = None
    pending_state: PendingCrawlState | None = None


@dataclass(slots=True)
class CachedJobPollResult:
    """Outcome of polling a crawl job owned by another worker."""

    status: str
    snapshot: MarketSnapshot | None = None


@dataclass(slots=True)
class ProcessQueuedJobResult:
    """Outcome of letting a background worker process one leased job."""

    status: str
    snapshot: MarketSnapshot | None = None
    error_message: str = ""
    attempt_count: int = 0
    max_attempts: int = 0
    next_retry_at: str = ""


@dataclass(slots=True)
class QueryRuntimeStatus:
    """Combined view of queue and snapshot state for one logical query."""

    query_signature: str
    execution_mode: str
    snapshot_status: str = "missing"
    snapshot_generated_at: str = ""
    snapshot_is_partial: bool = False
    snapshot_is_fresh: bool = False
    snapshot_error_message: str = ""
    job_id: int = 0
    job_status: str = "missing"
    attempt_count: int = 0
    max_attempts: int = 0
    lease_owner: str = ""
    lease_expires_at: str = ""
    next_retry_at: str = ""
    job_error_message: str = ""


@dataclass(slots=True)
class ScheduledRefreshCandidate:
    """One saved search that should be refreshed by the scheduler."""

    user_id: int
    search_id: int
    search_name: str
    rows: list[dict[str, Any]]
    custom_queries_text: str
    crawl_preset_label: str
    frequency: str
    last_run_at: str


@dataclass(slots=True)
class ScheduledRefreshRunResult:
    """Summary of one scheduler pass over saved searches."""

    checked_count: int = 0
    enqueued_count: int = 0
    skipped_count: int = 0
    invalid_count: int = 0
    details: list[str] = field(default_factory=list)


def build_crawl_queries(
    *,
    role_targets: list[TargetRole],
    crawl_preset: CrawlPreset,
    custom_queries: str,
) -> list[str]:
    """Build the stable query list for one crawl request."""
    queries = build_default_queries(
        role_targets,
        keywords_per_role=crawl_preset.keywords_per_role,
    )
    queries.extend(
        [line.strip() for line in custom_queries.splitlines() if line.strip()]
    )
    return list(dict.fromkeys(queries))


def build_query_runtime(
    settings: Settings,
) -> tuple[QuerySnapshotRegistry, CrawlJobQueue]:
    """Build the query snapshot registry and crawl queue for one environment."""
    if settings.queue_backend != "sqlite":
        raise ValueError(f"Unsupported queue backend: {settings.queue_backend}")
    return (
        QuerySnapshotRegistry(
            db_path=settings.query_state_db_path,
            snapshot_dir=settings.snapshot_store_dir,
            snapshot_ttl_seconds=settings.snapshot_ttl_seconds,
        ),
        CrawlJobQueue(
            db_path=settings.query_state_db_path,
            lease_seconds=settings.crawl_job_lease_seconds,
        ),
    )


def build_role_targets_from_rows(rows: list[dict[str, Any]]) -> list[TargetRole]:
    """Convert normalized saved-search rows into stable target-role models."""
    roles: list[TargetRole] = []
    for row in rows:
        enabled = bool(row.get("enabled", True))
        role_name = str(row.get("role", "")).strip()
        if not enabled or not role_name or role_name.lower() in {"none", "null"}:
            continue
        keywords = [
            keyword.strip()
            for keyword in str(row.get("keywords", "")).split(",")
            if keyword.strip()
        ]
        roles.append(
            TargetRole(
                name=role_name,
                priority=int(row.get("priority", len(roles) + 1) or (len(roles) + 1)),
                keywords=keywords,
            )
        )
    roles.sort(key=lambda role: role.priority)
    return roles


def inspect_query_runtime_status(
    *,
    settings: Settings,
    query_signature: str,
) -> QueryRuntimeStatus:
    """Read the current queue and snapshot state for one query signature."""
    status = QueryRuntimeStatus(
        query_signature=query_signature,
        execution_mode=str(settings.crawl_execution_mode).strip().lower() or "inline",
    )
    if not query_signature:
        return status

    registry, job_queue = build_query_runtime(settings)
    snapshot_entry = registry.get_snapshot(query_signature)
    if snapshot_entry is not None:
        status.snapshot_status = snapshot_entry.status
        status.snapshot_generated_at = snapshot_entry.generated_at
        status.snapshot_is_partial = bool(snapshot_entry.is_partial)
        status.snapshot_is_fresh = snapshot_entry.is_fresh()
        status.snapshot_error_message = snapshot_entry.error_message

    job = job_queue.get_active_job_for_signature(query_signature)
    if job is not None:
        status.job_id = int(job.id)
        status.job_status = job.status
        status.attempt_count = int(job.attempt_count)
        status.max_attempts = int(job.max_attempts)
        status.lease_owner = job.lease_owner
        status.lease_expires_at = job.lease_expires_at
        status.next_retry_at = job.next_retry_at
        status.job_error_message = job.error_message
    return status


def build_crawl_job_payload(
    *,
    queries: list[str],
    role_targets: list[TargetRole],
    crawl_preset_label: str,
    force_refresh: bool,
    rows: list[dict[str, Any]] | None = None,
    custom_queries_text: str = "",
    user_id: int | None = None,
    active_saved_search_id: int | None = None,
) -> str:
    """Serialize one crawl request so a detached worker can execute it later."""
    return json.dumps(
        {
            "queries": list(queries),
            "role_targets": [
                {
                    "name": role.name,
                    "priority": int(role.priority),
                    "keywords": list(role.keywords),
                }
                for role in role_targets
            ],
            "crawl_preset_label": crawl_preset_label,
            "force_refresh": bool(force_refresh),
            "rows": list(rows or []),
            "custom_queries_text": custom_queries_text,
            "user_id": user_id,
            "active_saved_search_id": active_saved_search_id,
        },
        ensure_ascii=False,
    )


def parse_role_targets(payload: dict[str, Any]) -> list[TargetRole]:
    """Decode role targets from queue payload with a best-effort fallback."""
    encoded_roles = payload.get("role_targets") or []
    if isinstance(encoded_roles, list) and encoded_roles:
        roles: list[TargetRole] = []
        for index, item in enumerate(encoded_roles):
            if not isinstance(item, dict):
                continue
            role_name = str(item.get("name", "")).strip()
            if not role_name:
                continue
            roles.append(
                TargetRole(
                    name=role_name,
                    priority=int(item.get("priority", index + 1) or (index + 1)),
                    keywords=[
                        str(keyword).strip()
                        for keyword in item.get("keywords", [])
                        if str(keyword).strip()
                    ],
                )
            )
        if roles:
            roles.sort(key=lambda role: role.priority)
            return roles

    queries = [
        str(query).strip()
        for query in payload.get("queries", [])
        if str(query).strip()
    ]
    return [
        TargetRole(name=query, priority=index + 1, keywords=[])
        for index, query in enumerate(dict.fromkeys(queries))
    ]


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).strip())
    except Exception:  # noqa: BLE001
        return None


def _frequency_interval(frequency: str) -> timedelta:
    cleaned = str(frequency or "").strip()
    if cleaned == "每週":
        return timedelta(days=7)
    if cleaned == "每日":
        return timedelta(days=1)
    return timedelta(hours=1)


def is_saved_search_due(*, last_run_at: str, frequency: str, now: datetime | None = None) -> bool:
    """Return whether one saved search should be refreshed by the scheduler."""
    current_time = now or datetime.now()
    if not str(last_run_at).strip():
        return True
    parsed = _parse_iso(last_run_at)
    if parsed is None:
        return True
    return current_time >= parsed + _frequency_interval(frequency)


def collect_due_saved_searches(*, product_store: ProductStore) -> list[ScheduledRefreshCandidate]:
    """Collect all saved searches whose refresh window has elapsed."""
    candidates: list[ScheduledRefreshCandidate] = []
    for user in product_store.list_users(include_guest=False):
        preferences = product_store.get_notification_preferences(user_id=int(user.id))
        for saved_search in product_store.list_saved_searches(user_id=int(user.id)):
            if not is_saved_search_due(
                last_run_at=saved_search.last_run_at,
                frequency=preferences.frequency,
            ):
                continue
            candidates.append(
                ScheduledRefreshCandidate(
                    user_id=int(user.id),
                    search_id=int(saved_search.id),
                    search_name=saved_search.name,
                    rows=list(saved_search.rows or []),
                    custom_queries_text=saved_search.custom_queries_text,
                    crawl_preset_label=saved_search.crawl_preset_label,
                    frequency=preferences.frequency,
                    last_run_at=saved_search.last_run_at,
                )
            )
    return candidates


def schedule_due_saved_searches(
    *,
    settings: Settings,
    product_store: ProductStore,
    worker_id: str,
) -> ScheduledRefreshRunResult:
    """Enqueue all saved searches whose scheduler window has elapsed."""
    candidates = collect_due_saved_searches(product_store=product_store)
    result = ScheduledRefreshRunResult(checked_count=len(candidates))
    for candidate in candidates:
        role_targets = build_role_targets_from_rows(candidate.rows)
        queries = build_crawl_queries(
            role_targets=role_targets,
            crawl_preset=get_crawl_preset(candidate.crawl_preset_label),
            custom_queries=candidate.custom_queries_text,
        )
        query_signature = product_store.build_signature(
            candidate.rows,
            candidate.custom_queries_text,
            candidate.crawl_preset_label,
        )
        start_result = start_crawl(
            settings=settings,
            role_targets=role_targets,
            queries=queries,
            query_signature=query_signature,
            force_refresh=False,
            crawl_preset_label=candidate.crawl_preset_label,
            worker_id=worker_id,
            execution_mode="worker",
            rows=candidate.rows,
            custom_queries_text=candidate.custom_queries_text,
            user_id=candidate.user_id,
            active_saved_search_id=candidate.search_id,
        )
        if start_result.status == "awaiting_snapshot":
            result.enqueued_count += 1
            result.details.append(
                f"Enqueued {candidate.search_name} (user={candidate.user_id}, search={candidate.search_id})."
            )
        elif start_result.status == "used_fresh_cache":
            result.skipped_count += 1
            result.details.append(
                f"Skipped {candidate.search_name}: fresh snapshot still valid."
            )
        elif start_result.status == "invalid":
            result.invalid_count += 1
            result.details.append(
                f"Invalid {candidate.search_name}: {start_result.warning_message}"
            )
        else:
            result.skipped_count += 1
            result.details.append(
                f"Skipped {candidate.search_name}: start result = {start_result.status}."
            )
    return result


def sync_saved_search_results(
    *,
    product_store: ProductStore,
    notification_service: NotificationService,
    snapshot: MarketSnapshot,
    current_user_id: int,
    current_user_is_guest: bool,
    notification_preferences: NotificationPreference,
    rows: list[dict[str, Any]],
    custom_queries_text: str,
    crawl_preset_label: str,
    active_saved_search_id: int | None = None,
) -> SavedSearchSyncResult:
    """Sync the latest snapshot back to a saved search and trigger notifications."""
    if current_user_is_guest:
        return SavedSearchSyncResult(feedback="", active_saved_search_id=None)

    saved_search = None
    if active_saved_search_id:
        saved_search = product_store.get_saved_search(
            int(active_saved_search_id),
            user_id=current_user_id,
        )
    if saved_search is None:
        saved_search = product_store.find_saved_search_by_signature(
            rows,
            custom_queries_text,
            crawl_preset_label,
            user_id=current_user_id,
        )
        if saved_search is not None:
            active_saved_search_id = saved_search.id

    if saved_search is None:
        return SavedSearchSyncResult(feedback="", active_saved_search_id=None)

    sync_result = product_store.sync_saved_search_results(
        user_id=current_user_id,
        search_id=saved_search.id,
        rows=rows,
        custom_queries_text=custom_queries_text,
        crawl_preset_label=crawl_preset_label,
        snapshot=snapshot,
        min_relevance_score=notification_preferences.min_relevance_score,
        max_jobs=notification_preferences.max_jobs_per_alert,
        create_notification=notification_preferences.site_enabled,
    )
    if sync_result["baseline_created"]:
        return SavedSearchSyncResult(
            feedback=(
                f"已更新追蹤搜尋「{sync_result['search_name']}」，"
                "目前先建立基準，下一次會開始通知新職缺。"
            ),
            active_saved_search_id=saved_search.id,
        )
    if sync_result["new_jobs"]:
        notification_notes: list[str] = []
        if notification_preferences.email_enabled or notification_preferences.line_enabled:
            delivery_result = notification_service.send_new_job_alert(
                search_name=sync_result["search_name"],
                new_jobs=sync_result["new_jobs"],
                email_enabled=notification_preferences.email_enabled,
                line_enabled=notification_preferences.line_enabled,
                email_recipients_text=notification_preferences.email_recipients,
                line_target=notification_preferences.line_target,
                max_jobs=notification_preferences.max_jobs_per_alert,
            )
            notification_notes = list(delivery_result["notes"])
            if sync_result["notification_id"]:
                product_store.update_notification_delivery(
                    int(sync_result["notification_id"]),
                    user_id=current_user_id,
                    email_sent=bool(delivery_result["email_sent"]),
                    line_sent=bool(delivery_result["line_sent"]),
                    delivery_notes=list(delivery_result["notes"]),
                )
        feedback = (
            f"追蹤搜尋「{sync_result['search_name']}」有 "
            f"{len(sync_result['new_jobs'])} 筆新職缺。"
        )
        if notification_notes:
            feedback += " " + " ".join(notification_notes)
        return SavedSearchSyncResult(
            feedback=feedback,
            active_saved_search_id=saved_search.id,
        )
    return SavedSearchSyncResult(
        feedback=f"追蹤搜尋「{sync_result['search_name']}」本次沒有新職缺。",
        active_saved_search_id=saved_search.id,
    )


def collect_saved_search_sync_targets(
    *,
    product_store: ProductStore,
    query_signature: str,
    fallback_user_id: int | None = None,
    fallback_search_id: int | None = None,
) -> list[tuple[int, int]]:
    """Resolve all saved-search subscribers that should receive one snapshot update."""
    targets: list[tuple[int, int]] = []
    seen_pairs: set[tuple[int, int]] = set()

    for target_user_id, saved_search in product_store.list_saved_search_subscribers(
        signature=query_signature
    ):
        pair = (int(target_user_id), int(saved_search.id))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        targets.append(pair)

    if fallback_user_id not in {None, "", 0, "0"} and fallback_search_id not in {
        None,
        "",
        0,
        "0",
    }:
        fallback_pair = (int(fallback_user_id), int(fallback_search_id))
        if fallback_pair not in seen_pairs:
            targets.append(fallback_pair)
    return targets


def poll_cached_crawl_job(
    *,
    settings: Settings,
    query_signature: str,
    active_job_id: int,
    current_snapshot: MarketSnapshot | None = None,
) -> CachedJobPollResult:
    """Poll a leased crawl job and return the latest snapshot when available."""
    if not query_signature or not active_job_id:
        return CachedJobPollResult(status="cleared")

    registry, job_queue = build_query_runtime(settings)
    snapshot = _load_registry_snapshot(
        registry=registry,
        query_signature=query_signature,
        current_snapshot=current_snapshot,
    )
    job = job_queue.get_job(active_job_id)
    if job is None:
        return CachedJobPollResult(status="cleared", snapshot=snapshot)
    if job.status == "completed":
        completed_snapshot = _load_registry_snapshot(
            registry=registry,
            query_signature=query_signature,
            current_snapshot=None,
        )
        return CachedJobPollResult(status="completed", snapshot=completed_snapshot or snapshot)
    if job.status == "failed":
        return CachedJobPollResult(status="failed", snapshot=snapshot)
    return CachedJobPollResult(status="waiting", snapshot=snapshot)


def start_crawl(
    *,
    settings: Settings,
    role_targets: list[TargetRole],
    queries: list[str],
    query_signature: str,
    force_refresh: bool,
    crawl_preset_label: str,
    worker_id: str,
    execution_mode: str = "inline",
    rows: list[dict[str, Any]] | None = None,
    custom_queries_text: str = "",
    user_id: int | None = None,
    active_saved_search_id: int | None = None,
) -> CrawlStartResult:
    """Acquire or start one staged crawl job without touching UI state."""
    registry, job_queue = build_query_runtime(settings)
    cached_entry = registry.get_snapshot(query_signature)
    cached_snapshot = cached_entry.snapshot if cached_entry is not None else None

    if not role_targets and not queries:
        return CrawlStartResult(
            status="invalid",
            snapshot=cached_snapshot,
            warning_message="請先勾選並填寫至少一筆目標職缺，或輸入額外查詢字詞。",
        )
    if (
        cached_entry is not None
        and cached_snapshot is not None
        and cached_entry.status == "ready"
        and cached_entry.is_fresh()
        and not force_refresh
    ):
        return CrawlStartResult(status="used_fresh_cache", snapshot=cached_snapshot)

    if cached_entry is not None:
        registry.mark_snapshot_stale(query_signature)

    job_payload = build_crawl_job_payload(
        queries=queries,
        role_targets=role_targets,
        crawl_preset_label=crawl_preset_label,
        force_refresh=force_refresh,
        rows=rows,
        custom_queries_text=custom_queries_text,
        user_id=user_id,
        active_saved_search_id=active_saved_search_id,
    )
    enqueued_job = job_queue.enqueue_crawl(
        query_signature,
        priority=100 if force_refresh else 50,
        max_attempts=max(1, int(settings.runtime_job_max_retries) + 1),
        payload_json=job_payload,
    )
    if str(execution_mode).strip().lower() == "worker":
        return CrawlStartResult(
            status="awaiting_snapshot",
            snapshot=cached_snapshot,
            pending_state=PendingCrawlState(
                query_signature=query_signature,
                active_job_id=enqueued_job.id,
            ),
        )
    leased_job = job_queue.lease_job_for_signature(
        query_signature,
        worker_id=worker_id,
    )
    if leased_job is None:
        return CrawlStartResult(
            status="awaiting_snapshot",
            snapshot=cached_snapshot,
            pending_state=PendingCrawlState(
                query_signature=query_signature,
                active_job_id=enqueued_job.id,
            ),
        )

    try:
        pipeline = JobMarketPipeline(
            settings=settings,
            role_targets=role_targets,
            force_refresh=force_refresh,
            perform_cache_maintenance=True,
        )
        collected_jobs, crawl_errors, initial_wave_sources = pipeline.collect_initial_wave(
            queries=queries,
        )
        initial_detail_cursor, initial_detail_total = pipeline.enrich_job_batch(
            collected_jobs,
            crawl_errors,
            start_index=0,
            batch_size=10,
        )
        partial_snapshot = pipeline.build_partial_snapshot(
            queries=queries,
            jobs=collected_jobs,
            errors=crawl_errors,
        )
        next_page_cursor = 2 if len(initial_wave_sources) >= len(pipeline.connectors) else 1
        registry.put_snapshot(
            query_signature,
            partial_snapshot,
            status="pending",
            fresh_until=registry.compute_fresh_until(),
            is_partial=True,
        )

        if settings.max_pages_per_source <= 1 and initial_detail_total <= initial_detail_cursor:
            final_snapshot = pipeline.complete_snapshot(
                queries=queries,
                jobs=collected_jobs,
                errors=crawl_errors,
            )
            snapshot_record = registry.put_snapshot(
                query_signature,
                final_snapshot,
                status="ready",
                fresh_until=registry.compute_fresh_until(),
                is_partial=False,
            )
            job_queue.complete_job(leased_job.id, snapshot_record.storage_key)
            return CrawlStartResult(status="completed", snapshot=final_snapshot)

        return CrawlStartResult(
            status="partial_ready",
            snapshot=partial_snapshot,
            pending_state=PendingCrawlState(
                query_signature=query_signature,
                active_job_id=leased_job.id,
                pending_queries=list(queries),
                pending_jobs=collected_jobs,
                pending_errors=list(crawl_errors),
                partial_ready_at=partial_snapshot.generated_at,
                detail_cursor=0,
                detail_total=0,
                remaining_page_cursor=next_page_cursor,
                initial_wave_sources=list(initial_wave_sources),
            ),
        )
    except Exception as exc:
        job_queue.fail_job(leased_job.id, str(exc))
        raise


def advance_finalize_batch(
    *,
    settings: Settings,
    snapshot: MarketSnapshot,
    pending_state: PendingCrawlState,
    crawl_preset_label: str,
    force_refresh: bool,
) -> FinalizeBatchResult:
    """Advance one finalize step for an in-flight staged crawl."""
    if not pending_state.pending_queries or not pending_state.pending_jobs:
        return FinalizeBatchResult(status="cleared")

    registry, job_queue = build_query_runtime(settings)
    finalize_settings = apply_crawl_preset(
        settings,
        get_crawl_preset(crawl_preset_label),
    )
    finalize_pipeline = JobMarketPipeline(
        settings=finalize_settings,
        role_targets=snapshot.role_targets,
        force_refresh=force_refresh,
    )
    pending_jobs = list(pending_state.pending_jobs)
    pending_errors = list(pending_state.pending_errors)

    if pending_state.remaining_page_cursor <= finalize_settings.max_pages_per_source:
        merged_jobs, search_errors, next_page_cursor = finalize_pipeline.collect_remaining_waves(
            pending_state.pending_queries,
            pending_jobs,
            page_cursor=pending_state.remaining_page_cursor,
            completed_initial_sources=pending_state.initial_wave_sources,
        )
        pending_jobs = merged_jobs
        pending_errors.extend(search_errors)
        next_state = PendingCrawlState(
            query_signature=pending_state.query_signature,
            active_job_id=pending_state.active_job_id,
            pending_queries=list(pending_state.pending_queries),
            pending_jobs=pending_jobs,
            pending_errors=pending_errors,
            partial_ready_at=pending_state.partial_ready_at or snapshot.generated_at,
            detail_cursor=pending_state.detail_cursor,
            detail_total=pending_state.detail_total,
            remaining_page_cursor=next_page_cursor,
            initial_wave_sources=list(pending_state.initial_wave_sources),
        )
        partial_snapshot = finalize_pipeline.build_partial_snapshot(
            queries=next_state.pending_queries,
            jobs=next_state.pending_jobs,
            errors=next_state.pending_errors,
            generated_at=next_state.partial_ready_at,
        )
        _put_partial_snapshot(
            registry=registry,
            query_signature=next_state.query_signature,
            snapshot=partial_snapshot,
        )
        return FinalizeBatchResult(
            status="partial_updated",
            snapshot=partial_snapshot,
            pending_state=next_state,
        )

    next_cursor, total_candidates = finalize_pipeline.enrich_job_batch(
        pending_jobs,
        pending_errors,
        start_index=pending_state.detail_cursor,
        batch_size=20,
    )
    next_state = PendingCrawlState(
        query_signature=pending_state.query_signature,
        active_job_id=pending_state.active_job_id,
        pending_queries=list(pending_state.pending_queries),
        pending_jobs=pending_jobs,
        pending_errors=pending_errors,
        partial_ready_at=pending_state.partial_ready_at or snapshot.generated_at,
        detail_cursor=next_cursor,
        detail_total=total_candidates,
        remaining_page_cursor=pending_state.remaining_page_cursor,
        initial_wave_sources=list(pending_state.initial_wave_sources),
    )

    if next_cursor >= total_candidates:
        final_snapshot = finalize_pipeline.complete_snapshot(
            queries=next_state.pending_queries,
            jobs=next_state.pending_jobs,
            errors=next_state.pending_errors,
        )
        snapshot_record = None
        if next_state.query_signature:
            snapshot_record = registry.put_snapshot(
                next_state.query_signature,
                final_snapshot,
                status="ready",
                fresh_until=registry.compute_fresh_until(),
                is_partial=False,
            )
        if next_state.active_job_id:
            job_queue.complete_job(
                next_state.active_job_id,
                snapshot_ref=snapshot_record.storage_key if snapshot_record else "",
            )
        return FinalizeBatchResult(status="completed", snapshot=final_snapshot)

    partial_snapshot = finalize_pipeline.build_partial_snapshot(
        queries=next_state.pending_queries,
        jobs=next_state.pending_jobs,
        errors=next_state.pending_errors,
        generated_at=next_state.partial_ready_at,
    )
    _put_partial_snapshot(
        registry=registry,
        query_signature=next_state.query_signature,
        snapshot=partial_snapshot,
    )
    return FinalizeBatchResult(
        status="partial_updated",
        snapshot=partial_snapshot,
        pending_state=next_state,
    )


def is_retryable_crawl_job_error(exc: Exception) -> bool:
    """Return whether one worker failure looks transient enough to retry once."""
    if isinstance(exc, (TimeoutError, ConnectionError, sqlite3.OperationalError)):
        return True
    lowered = str(exc).strip().lower()
    if not lowered:
        return False
    retryable_tokens = (
        "timed out",
        "timeout",
        "temporary failure",
        "temporarily unavailable",
        "connection reset",
        "connection aborted",
        "connection refused",
        "connection closed",
        "remote disconnected",
        "name or service not known",
        "429",
        "403",
        "449",
        "999",
        "rate limit",
        "too many requests",
        "request denied",
        "forbidden",
        "database is locked",
        "database table is locked",
        "database busy",
    )
    return any(token in lowered for token in retryable_tokens)


def process_queued_crawl_job(
    *,
    settings: Settings,
    job: CrawlJobRecord,
) -> ProcessQueuedJobResult:
    """Let a detached worker process one leased crawl job end-to-end."""
    registry, job_queue = build_query_runtime(settings)
    payload = job.payload()
    queries = [
        str(query).strip()
        for query in payload.get("queries", [])
        if str(query).strip()
    ]
    role_targets = parse_role_targets(payload)
    crawl_preset_label = str(payload.get("crawl_preset_label", "快速") or "快速")
    force_refresh = bool(payload.get("force_refresh", False))
    runtime_settings = apply_crawl_preset(settings, get_crawl_preset(crawl_preset_label))
    rows = list(payload.get("rows") or [])
    custom_queries_text = str(payload.get("custom_queries_text", "") or "")
    user_id = payload.get("user_id")
    active_saved_search_id = payload.get("active_saved_search_id")

    try:
        pipeline = JobMarketPipeline(
            settings=runtime_settings,
            role_targets=role_targets,
            force_refresh=force_refresh,
            perform_cache_maintenance=True,
        )
        collected_jobs, crawl_errors, initial_wave_sources = pipeline.collect_initial_wave(
            queries=queries
        )
        partial_snapshot = pipeline.build_partial_snapshot(
            queries=queries,
            jobs=collected_jobs,
            errors=crawl_errors,
        )
        _put_partial_snapshot(
            registry=registry,
            query_signature=job.query_signature,
            snapshot=partial_snapshot,
        )

        page_cursor = 2 if len(initial_wave_sources) >= len(pipeline.connectors) else 1
        working_jobs = collected_jobs
        working_errors = list(crawl_errors)
        while page_cursor <= runtime_settings.max_pages_per_source:
            working_jobs, search_errors, page_cursor = pipeline.collect_remaining_waves(
                queries,
                working_jobs,
                page_cursor=page_cursor,
                completed_initial_sources=initial_wave_sources,
            )
            working_errors.extend(search_errors)
            partial_snapshot = pipeline.build_partial_snapshot(
                queries=queries,
                jobs=working_jobs,
                errors=working_errors,
                generated_at=partial_snapshot.generated_at,
            )
            _put_partial_snapshot(
                registry=registry,
                query_signature=job.query_signature,
                snapshot=partial_snapshot,
            )

        final_snapshot = pipeline.finalize_snapshot(
            queries=queries,
            jobs=working_jobs,
            errors=working_errors,
        )
        snapshot_record = registry.put_snapshot(
            job.query_signature,
            final_snapshot,
            status="ready",
            fresh_until=registry.compute_fresh_until(),
            is_partial=False,
        )
        job_queue.complete_job(job.id, snapshot_record.storage_key)

        if user_id not in {None, "", 0, "0"}:
            product_store = ProductStore(settings.product_state_db_path)
            notification_service = NotificationService(settings)
            sync_targets = collect_saved_search_sync_targets(
                product_store=product_store,
                query_signature=job.query_signature,
                fallback_user_id=(
                    int(user_id) if user_id not in {None, "", 0, "0"} else None
                ),
                fallback_search_id=(
                    int(active_saved_search_id)
                    if active_saved_search_id not in {None, "", 0, "0"}
                    else None
                ),
            )
            for target_user_id, target_search_id in sync_targets:
                notification_preferences = product_store.get_notification_preferences(
                    user_id=target_user_id
                )
                sync_saved_search_results(
                    product_store=product_store,
                    notification_service=notification_service,
                    snapshot=final_snapshot,
                    current_user_id=target_user_id,
                    current_user_is_guest=False,
                    notification_preferences=notification_preferences,
                    rows=rows,
                    custom_queries_text=custom_queries_text,
                    crawl_preset_label=crawl_preset_label,
                    active_saved_search_id=target_search_id,
                )
        return ProcessQueuedJobResult(status="completed", snapshot=final_snapshot)
    except Exception as exc:
        updated_job = job_queue.record_attempt_failure(
            job.id,
            str(exc),
            allow_retry=is_retryable_crawl_job_error(exc),
            retry_backoff_seconds=settings.runtime_job_retry_backoff_seconds,
        )
        if updated_job.status == "pending" and updated_job.next_retry_at:
            return ProcessQueuedJobResult(
                status="retry_scheduled",
                error_message=str(exc),
                attempt_count=int(updated_job.attempt_count),
                max_attempts=int(updated_job.max_attempts),
                next_retry_at=updated_job.next_retry_at,
            )
        return ProcessQueuedJobResult(
            status="failed",
            error_message=str(exc),
            attempt_count=int(updated_job.attempt_count),
            max_attempts=int(updated_job.max_attempts),
        )


def _load_registry_snapshot(
    *,
    registry: QuerySnapshotRegistry,
    query_signature: str,
    current_snapshot: MarketSnapshot | None,
) -> MarketSnapshot | None:
    if not query_signature:
        return None
    cached_entry = registry.get_snapshot(query_signature)
    if cached_entry is None or cached_entry.snapshot is None:
        return None
    if (
        current_snapshot is not None
        and current_snapshot.generated_at == cached_entry.snapshot.generated_at
    ):
        return None
    return cached_entry.snapshot


def _put_partial_snapshot(
    *,
    registry: QuerySnapshotRegistry,
    query_signature: str,
    snapshot: MarketSnapshot,
) -> None:
    if not query_signature:
        return
    registry.put_snapshot(
        query_signature,
        snapshot,
        status="pending",
        fresh_until=registry.compute_fresh_until(),
        is_partial=True,
    )
