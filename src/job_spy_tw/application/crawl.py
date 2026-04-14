"""Application-layer boundary for crawl runtime operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..crawl_application_service import (
    CachedJobPollResult,
    CrawlStartResult,
    FinalizeBatchResult,
    PendingCrawlState,
    QueryRuntimeStatus,
    SavedSearchSyncResult,
    ScheduledRefreshRunResult,
    advance_finalize_batch,
    inspect_query_runtime_status,
    poll_cached_crawl_job,
    schedule_due_saved_searches,
    sync_saved_search_results,
    start_crawl,
)
from ..models import MarketSnapshot, NotificationPreference, TargetRole
from ..notification_service import NotificationService
from ..product_store import ProductStore
from ..settings import Settings


@dataclass(slots=True)
class CrawlStartRequest:
    settings: Settings
    role_targets: list[TargetRole]
    queries: list[str]
    query_signature: str
    force_refresh: bool
    crawl_preset_label: str
    worker_id: str
    execution_mode: str
    rows: list[dict[str, Any]] | None = None
    custom_queries_text: str = ""
    user_id: int | None = None
    active_saved_search_id: int | None = None


@dataclass(slots=True)
class CrawlFinalizeRequest:
    settings: Settings
    snapshot: MarketSnapshot
    pending_state: PendingCrawlState
    crawl_preset_label: str
    force_refresh: bool


@dataclass(slots=True)
class CrawlPollRequest:
    settings: Settings
    query_signature: str
    active_job_id: int
    current_snapshot: MarketSnapshot | None


@dataclass(slots=True)
class CrawlStatusRequest:
    settings: Settings
    query_signature: str


@dataclass(slots=True)
class SavedSearchScheduleRequest:
    settings: Settings
    product_store: ProductStore
    worker_id: str


@dataclass(slots=True)
class SavedSearchSyncRequest:
    product_store: ProductStore
    notification_service: NotificationService
    snapshot: MarketSnapshot
    current_user_id: int
    current_user_is_guest: bool
    notification_preferences: NotificationPreference
    rows: list[dict[str, Any]]
    custom_queries_text: str
    crawl_preset_label: str
    active_saved_search_id: int | None = None


class CrawlApplication:
    """Application-level API for crawl lifecycle."""

    def start(self, request: CrawlStartRequest) -> CrawlStartResult:
        return start_crawl(
            settings=request.settings,
            role_targets=request.role_targets,
            queries=request.queries,
            query_signature=request.query_signature,
            force_refresh=request.force_refresh,
            crawl_preset_label=request.crawl_preset_label,
            worker_id=request.worker_id,
            execution_mode=request.execution_mode,
            rows=request.rows,
            custom_queries_text=request.custom_queries_text,
            user_id=request.user_id,
            active_saved_search_id=request.active_saved_search_id,
        )

    def advance_finalize(self, request: CrawlFinalizeRequest) -> FinalizeBatchResult:
        return advance_finalize_batch(
            settings=request.settings,
            snapshot=request.snapshot,
            pending_state=request.pending_state,
            crawl_preset_label=request.crawl_preset_label,
            force_refresh=request.force_refresh,
        )

    def poll_cached(self, request: CrawlPollRequest) -> CachedJobPollResult:
        return poll_cached_crawl_job(
            settings=request.settings,
            query_signature=request.query_signature,
            active_job_id=request.active_job_id,
            current_snapshot=request.current_snapshot,
        )

    def inspect_status(self, request: CrawlStatusRequest) -> QueryRuntimeStatus:
        return inspect_query_runtime_status(
            settings=request.settings,
            query_signature=request.query_signature,
        )

    def schedule_due_saved_searches(
        self, request: SavedSearchScheduleRequest
    ) -> ScheduledRefreshRunResult:
        return schedule_due_saved_searches(
            settings=request.settings,
            product_store=request.product_store,
            worker_id=request.worker_id,
        )

    def sync_saved_search_results(self, request: SavedSearchSyncRequest) -> SavedSearchSyncResult:
        return sync_saved_search_results(
            product_store=request.product_store,
            notification_service=request.notification_service,
            snapshot=request.snapshot,
            current_user_id=request.current_user_id,
            current_user_is_guest=request.current_user_is_guest,
            notification_preferences=request.notification_preferences,
            rows=request.rows,
            custom_queries_text=request.custom_queries_text,
            crawl_preset_label=request.crawl_preset_label,
            active_saved_search_id=request.active_saved_search_id,
        )
