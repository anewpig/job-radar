"""Crawl runtime 的啟動與 finalize flow。"""

from __future__ import annotations

import streamlit as st

from ..application.crawl import (
    CrawlApplication,
    CrawlFinalizeRequest,
    CrawlPollRequest,
    CrawlStartRequest,
)
from ..crawl_application_service import PendingCrawlState
from ..crawl_tuning import apply_crawl_preset
from ..models import MarketSnapshot, NotificationPreference
from .crawl_runtime_state import (
    apply_pending_crawl_state,
    build_crawl_queries,
    clear_pending_crawl_state,
    sync_saved_search_results,
)
from .crawl_runtime_status import estimate_crawl_eta_label
from .search import build_role_targets, get_committed_search_rows
from .search_setup import SearchSetupState


def _poll_cached_crawl_job(*, settings) -> None:
    """在其他 worker 負責刷新時，輪詢背景 job 並同步最新快照。"""
    crawl_app = CrawlApplication()
    result = crawl_app.poll_cached(
        CrawlPollRequest(
            settings=settings,
            query_signature=str(st.session_state.get("crawl_query_signature") or ""),
            active_job_id=int(st.session_state.get("crawl_active_job_id") or 0),
            current_snapshot=st.session_state.get("snapshot"),
        )
    )
    if result.snapshot is not None:
        st.session_state.snapshot = result.snapshot
        st.session_state.last_crawl_signature = str(
            st.session_state.get("crawl_query_signature") or ""
        )
    if result.status == "cleared":
        clear_pending_crawl_state()
        return
    if result.status == "completed":
        clear_pending_crawl_state()
        st.rerun(scope="fragment")
    if result.status == "failed":
        clear_pending_crawl_state()


def _run_finalize_batch(
    *,
    settings,
    snapshot: MarketSnapshot,
    product_store,
    notification_service,
    current_user_id: int,
    current_user_is_guest: bool,
    notification_preferences: NotificationPreference,
) -> None:
    """補完一批職缺原文與分析，並更新 session 中的分階段快照。"""
    if st.session_state.get("crawl_phase") != "finalizing":
        return
    pending_state = PendingCrawlState(
        query_signature=str(st.session_state.get("crawl_query_signature") or ""),
        active_job_id=int(st.session_state.get("crawl_active_job_id") or 0),
        pending_queries=list(st.session_state.get("crawl_pending_queries", [])),
        pending_jobs=list(st.session_state.get("crawl_pending_jobs", [])),
        pending_errors=list(st.session_state.get("crawl_pending_errors", [])),
        partial_ready_at=str(st.session_state.get("crawl_partial_ready_at") or ""),
        detail_cursor=int(st.session_state.get("crawl_detail_cursor", 0)),
        detail_total=int(st.session_state.get("crawl_detail_total", 0)),
        remaining_page_cursor=int(st.session_state.get("crawl_remaining_page_cursor", 1)),
        initial_wave_sources=list(st.session_state.get("crawl_initial_wave_sources", [])),
    )
    if not pending_state.pending_queries or not pending_state.pending_jobs:
        clear_pending_crawl_state()
        return

    crawl_app = CrawlApplication()
    finalize_result = crawl_app.advance_finalize(
        CrawlFinalizeRequest(
            settings=settings,
            snapshot=snapshot,
            pending_state=pending_state,
            crawl_preset_label=st.session_state.crawl_preset_label,
            force_refresh=st.session_state.crawl_refresh_mode == "強制更新",
        )
    )
    if finalize_result.status == "cleared":
        clear_pending_crawl_state()
        return
    if finalize_result.snapshot is not None:
        st.session_state.snapshot = finalize_result.snapshot
    if finalize_result.pending_state is not None:
        apply_pending_crawl_state(
            phase="finalizing",
            pending_state=finalize_result.pending_state,
        )
    if finalize_result.status == "completed":
        st.session_state.favorite_feedback = sync_saved_search_results(
            product_store=product_store,
            notification_service=notification_service,
            snapshot=finalize_result.snapshot or snapshot,
            current_user_id=current_user_id,
            current_user_is_guest=current_user_is_guest,
            notification_preferences=notification_preferences,
        )
        clear_pending_crawl_state()
        st.rerun()
    st.rerun(scope="fragment")


def maybe_start_crawl(
    *,
    settings,
    search_setup_state: SearchSetupState,
    product_store,
    notification_service,
    current_user_id: int,
    current_user_is_guest: bool,
    notification_preferences: NotificationPreference,
    current_signature: str,
) -> None:
    """當搜尋設定觸發新一輪抓取時，啟動分階段爬取流程。"""
    pending_saved_search_refresh_id = st.session_state.pop(
        "pending_saved_search_refresh_id",
        None,
    )
    if not (search_setup_state.run_crawl or pending_saved_search_refresh_id):
        return

    effective_search_rows = get_committed_search_rows(
        st.session_state.search_role_rows,
        draft_index=st.session_state.get("search_role_draft_index"),
    )
    role_targets = build_role_targets(effective_search_rows)
    runtime_settings = apply_crawl_preset(settings, search_setup_state.crawl_preset)
    queries = build_crawl_queries(
        role_targets=role_targets,
        crawl_preset=search_setup_state.crawl_preset,
        custom_queries=search_setup_state.custom_queries,
    )
    eta_label = estimate_crawl_eta_label(
        query_count=len(queries),
        preset_label=search_setup_state.crawl_preset.label,
        force_refresh=search_setup_state.force_refresh,
        execution_mode=settings.crawl_execution_mode,
        max_pages_per_source=runtime_settings.max_pages_per_source,
        max_detail_jobs_per_source=runtime_settings.max_detail_jobs_per_source,
    )

    crawl_status = None
    try:
        crawl_status = st.status("正在抓取並分析職缺...", expanded=True)
        crawl_status.write(f"預計時間：{eta_label}")
        crawl_status.write("1. 整理搜尋條件與查詢字詞")
        crawl_app = CrawlApplication()
        start_result = crawl_app.start(
            CrawlStartRequest(
                settings=runtime_settings,
                role_targets=role_targets,
                queries=queries,
                query_signature=current_signature,
                force_refresh=search_setup_state.force_refresh,
                crawl_preset_label=st.session_state.crawl_preset_label,
                worker_id=str(st.session_state.crawl_worker_id),
                execution_mode=settings.crawl_execution_mode,
                rows=effective_search_rows,
                custom_queries_text=st.session_state.custom_queries_text,
                user_id=None if current_user_is_guest else current_user_id,
                active_saved_search_id=(
                    int(st.session_state.active_saved_search_id)
                    if st.session_state.active_saved_search_id
                    else None
                ),
            )
        )
        if start_result.snapshot is not None:
            st.session_state.snapshot = start_result.snapshot
            st.session_state.last_crawl_signature = current_signature
        if start_result.status == "invalid":
            crawl_status.update(label="搜尋條件不足", state="error", expanded=False)
            st.warning(start_result.warning_message)
            return
        if start_result.status == "used_fresh_cache":
            clear_pending_crawl_state()
            crawl_status.update(label="已使用最新快照", state="complete", expanded=False)
            return
        if start_result.status == "awaiting_snapshot":
            if start_result.pending_state is not None:
                apply_pending_crawl_state(
                    phase="awaiting_snapshot",
                    pending_state=start_result.pending_state,
                )
            crawl_status.update(
                label="其他 worker 正在刷新相同查詢，等待最新快照",
                state="running",
                expanded=False,
            )
            return
        if start_result.status == "completed":
            st.session_state.favorite_feedback = sync_saved_search_results(
                product_store=product_store,
                notification_service=notification_service,
                snapshot=start_result.snapshot or st.session_state.snapshot,
                current_user_id=current_user_id,
                current_user_is_guest=current_user_is_guest,
                notification_preferences=notification_preferences,
            )
            clear_pending_crawl_state()
            crawl_status.update(label="抓取與分析完成", state="complete", expanded=False)
            st.rerun()

        if start_result.pending_state is not None:
            apply_pending_crawl_state(
                phase="finalizing",
                pending_state=start_result.pending_state,
            )
        crawl_status.write("2. 抓各來源首波結果並建立初步列表")
        crawl_status.write("3. 已建立初步職缺列表，畫面會先顯示搜尋結果")
        crawl_status.update(
            label="已取得初步職缺列表，正在追加搜尋波次與補完整分析",
            state="complete",
            expanded=False,
        )
        st.rerun()
    except Exception:
        crawl_status_label = crawl_status
        if crawl_status_label is not None:
            crawl_status_label.update(label="抓取與分析失敗", state="error", expanded=True)
        raise


@st.fragment(run_every=1.0)
def render_finalize_worker_fragment(
    *,
    settings,
    snapshot: MarketSnapshot | None,
    product_store,
    notification_service,
    current_user_id: int,
    current_user_is_guest: bool,
    notification_preferences: NotificationPreference,
) -> None:
    """在畫面仍可互動時，持續推進後續的補分析批次。"""
    if st.session_state.get("crawl_phase") == "awaiting_snapshot":
        _poll_cached_crawl_job(settings=settings)
        return
    if snapshot is None or st.session_state.get("crawl_phase") != "finalizing":
        return
    _run_finalize_batch(
        settings=settings,
        snapshot=snapshot,
        product_store=product_store,
        notification_service=notification_service,
        current_user_id=current_user_id,
        current_user_is_guest=current_user_is_guest,
        notification_preferences=notification_preferences,
    )
