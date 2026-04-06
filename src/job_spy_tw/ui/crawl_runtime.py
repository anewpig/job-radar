"""提供 Streamlit 入口使用的分階段爬取協調輔助函式。"""

from __future__ import annotations

import streamlit as st

from ..crawl_tuning import apply_crawl_preset
from ..crawl_application_service import (
    PendingCrawlState,
    advance_finalize_batch,
    build_crawl_queries as build_crawl_queries_service,
    inspect_query_runtime_status,
    poll_cached_crawl_job,
    start_crawl,
    sync_saved_search_results as sync_saved_search_results_service,
)
from ..models import MarketSnapshot, NotificationPreference
from .common import build_chip_row
from .search import build_role_targets, get_committed_search_rows
from .search_setup import SearchSetupState


def build_crawl_queries(*, role_targets, crawl_preset, custom_queries: str) -> list[str]:
    """依目標職缺與額外自訂查詢字詞建立最終查詢清單。"""
    return build_crawl_queries_service(
        role_targets=role_targets,
        crawl_preset=crawl_preset,
        custom_queries=custom_queries,
    )


def clear_pending_crawl_state() -> None:
    """在補分析完成或中止後清除所有分階段爬取狀態。"""
    st.session_state.crawl_phase = "idle"
    st.session_state.crawl_pending_queries = []
    st.session_state.crawl_pending_jobs = []
    st.session_state.crawl_pending_errors = []
    st.session_state.crawl_partial_ready_at = ""
    st.session_state.crawl_detail_cursor = 0
    st.session_state.crawl_detail_total = 0
    st.session_state.crawl_remaining_page_cursor = 1
    st.session_state.crawl_initial_wave_sources = []
    st.session_state.crawl_query_signature = ""
    st.session_state.crawl_active_job_id = 0


def _apply_pending_crawl_state(*, phase: str, pending_state: PendingCrawlState) -> None:
    """把 backend service 回傳的 crawl state 寫回 Streamlit session。"""
    st.session_state.crawl_phase = phase
    st.session_state.crawl_pending_queries = list(pending_state.pending_queries)
    st.session_state.crawl_pending_jobs = list(pending_state.pending_jobs)
    st.session_state.crawl_pending_errors = list(pending_state.pending_errors)
    st.session_state.crawl_partial_ready_at = pending_state.partial_ready_at
    st.session_state.crawl_detail_cursor = int(pending_state.detail_cursor)
    st.session_state.crawl_detail_total = int(pending_state.detail_total)
    st.session_state.crawl_remaining_page_cursor = int(pending_state.remaining_page_cursor)
    st.session_state.crawl_initial_wave_sources = list(pending_state.initial_wave_sources)
    st.session_state.crawl_query_signature = pending_state.query_signature
    st.session_state.crawl_active_job_id = int(pending_state.active_job_id)


def _format_runtime_status_label(status: str, *, kind: str) -> str:
    if kind == "job":
        return {
            "missing": "未排入佇列",
            "pending": "佇列等待中",
            "leased": "worker 執行中",
            "completed": "背景工作完成",
            "failed": "背景工作失敗",
        }.get(status, status)
    return {
        "missing": "尚未建立快照",
        "pending": "partial snapshot",
        "ready": "final snapshot",
        "stale": "快照已過期",
    }.get(status, status)


def _format_eta_seconds(seconds: int) -> str:
    """把秒數整理成適合顯示在 UI 的中文時間。"""
    rounded_seconds = max(5, int(round(seconds / 5) * 5))
    if rounded_seconds < 60:
        return f"{rounded_seconds} 秒"
    minutes, remain_seconds = divmod(rounded_seconds, 60)
    if remain_seconds == 0 or minutes >= 4:
        return f"{minutes} 分鐘"
    return f"{minutes} 分 {remain_seconds} 秒"


def _estimate_crawl_eta_label(
    *,
    query_count: int,
    preset_label: str,
    force_refresh: bool,
    execution_mode: str,
    max_pages_per_source: int,
    max_detail_jobs_per_source: int,
) -> str:
    """依目前抓取設定提供保守的預估時間區間。"""
    if preset_label == "快速":
        lower_seconds, upper_seconds = 16, 36
    elif preset_label == "平衡":
        lower_seconds, upper_seconds = 28, 65
    else:
        lower_seconds, upper_seconds = 55, 160

    extra_queries = max(0, query_count - 1)
    lower_seconds += extra_queries * 4
    upper_seconds += extra_queries * 10

    if max_pages_per_source > 1:
        extra_pages = max_pages_per_source - 1
        lower_seconds += extra_pages * 8
        upper_seconds += extra_pages * 24

    detail_jobs = max_detail_jobs_per_source if max_detail_jobs_per_source > 0 else 36
    detail_overhead = max(0, detail_jobs - 12)
    lower_seconds += detail_overhead // 4
    upper_seconds += detail_overhead

    if force_refresh:
        lower_seconds += 10
        upper_seconds += 25
    else:
        lower_seconds = max(10, lower_seconds - 4)
        upper_seconds = max(lower_seconds + 10, upper_seconds - 8)

    if execution_mode == "worker":
        lower_seconds += 5
        upper_seconds += 35
        return (
            f"約 {_format_eta_seconds(lower_seconds)} 到 {_format_eta_seconds(upper_seconds)}"
            "，若背景佇列繁忙會再更久"
        )

    return f"約 {_format_eta_seconds(lower_seconds)} 到 {_format_eta_seconds(upper_seconds)}"


def _should_render_runtime_panel() -> bool:
    rows = get_committed_search_rows(
        st.session_state.search_role_rows,
        draft_index=st.session_state.get("search_role_draft_index"),
    )
    has_role = any(str(row.get("role", "")).strip() for row in rows if bool(row.get("enabled", True)))
    has_custom_query = bool(str(st.session_state.custom_queries_text).strip())
    has_active_runtime = bool(
        st.session_state.get("crawl_phase") not in {None, "", "idle"}
        or st.session_state.get("crawl_query_signature")
        or st.session_state.get("crawl_active_job_id")
        or st.session_state.get("snapshot") is not None
    )
    return has_role or has_custom_query or has_active_runtime


def render_crawl_runtime_panel(*, settings, query_signature: str) -> None:
    """Render the current crawl queue / snapshot status for the active query."""
    if not _should_render_runtime_panel():
        return

    runtime_status = inspect_query_runtime_status(
        settings=settings,
        query_signature=query_signature,
    )
    phase = str(st.session_state.get("crawl_phase", "idle") or "idle")
    phase_label = {
        "idle": "待命",
        "awaiting_snapshot": "等待背景 worker",
        "finalizing": "補完整分析中",
    }.get(phase, phase)
    summary_labels = [
        f"模式：{runtime_status.execution_mode}",
        f"目前 phase：{phase_label}",
        f"Job：{_format_runtime_status_label(runtime_status.job_status, kind='job')}",
        f"快照：{_format_runtime_status_label(runtime_status.snapshot_status, kind='snapshot')}",
    ]
    if runtime_status.snapshot_is_partial:
        summary_labels.append("目前畫面顯示 partial snapshot")
    if runtime_status.snapshot_is_fresh:
        summary_labels.append("快照仍在 fresh window")

    with st.container(border=True, key="crawl-runtime-status-shell"):
        st.markdown("**目前查詢執行狀態**")
        st.markdown(
            f'<div class="chip-row">{build_chip_row(summary_labels, tone="soft", limit=8)}</div>',
            unsafe_allow_html=True,
        )
        metric_cols = st.columns(4, gap="small")
        metric_cols[0].metric("Execution", runtime_status.execution_mode)
        metric_cols[1].metric(
            "Job",
            _format_runtime_status_label(runtime_status.job_status, kind="job"),
        )
        metric_cols[2].metric(
            "Snapshot",
            _format_runtime_status_label(runtime_status.snapshot_status, kind="snapshot"),
        )
        metric_cols[3].metric("Job ID", str(runtime_status.job_id) if runtime_status.job_id else "-")

        detail_lines: list[str] = []
        if runtime_status.snapshot_generated_at:
            detail_lines.append(f"快照時間：{runtime_status.snapshot_generated_at}")
        if runtime_status.lease_owner:
            detail_lines.append(f"目前 lease owner：{runtime_status.lease_owner}")
        if runtime_status.lease_expires_at:
            detail_lines.append(f"lease 到期：{runtime_status.lease_expires_at}")
        if runtime_status.max_attempts:
            detail_lines.append(
                f"attempt：{runtime_status.attempt_count}/{runtime_status.max_attempts}"
            )
        if runtime_status.next_retry_at:
            detail_lines.append(f"下次重試：{runtime_status.next_retry_at}")
        if detail_lines:
            st.caption("｜".join(detail_lines))

        if runtime_status.execution_mode == "worker":
            st.info("目前啟用 background worker 模式。UI 只會 enqueue job，實際抓取由獨立 worker 處理。")
        elif phase == "finalizing":
            st.info("目前使用 inline staged crawl。畫面會先顯示初步列表，再由同一個 app 逐步補完整分析。")

        if runtime_status.job_status == "failed" and runtime_status.job_error_message:
            st.error(f"背景工作失敗：{runtime_status.job_error_message}")
        elif runtime_status.next_retry_at and runtime_status.job_error_message:
            st.warning(
                "背景工作已排程重試："
                f"{runtime_status.job_error_message}"
            )
        elif runtime_status.snapshot_error_message:
            st.warning(runtime_status.snapshot_error_message)


def sync_saved_search_results(
    *,
    product_store,
    notification_service,
    snapshot: MarketSnapshot,
    current_user_id: int,
    current_user_is_guest: bool,
    notification_preferences: NotificationPreference,
) -> str:
    """把最新快照同步回已儲存搜尋，並在需要時發送通知。"""
    result = sync_saved_search_results_service(
        product_store=product_store,
        notification_service=notification_service,
        snapshot=snapshot,
        current_user_id=current_user_id,
        current_user_is_guest=current_user_is_guest,
        notification_preferences=notification_preferences,
        rows=get_committed_search_rows(
            st.session_state.search_role_rows,
            draft_index=st.session_state.get("search_role_draft_index"),
        ),
        custom_queries_text=st.session_state.custom_queries_text,
        crawl_preset_label=st.session_state.crawl_preset_label,
        active_saved_search_id=(
            int(st.session_state.active_saved_search_id)
            if st.session_state.active_saved_search_id
            else None
        ),
    )
    if result.active_saved_search_id is not None:
        st.session_state.active_saved_search_id = result.active_saved_search_id
    return result.feedback


def _poll_cached_crawl_job(*, settings) -> None:
    """在其他 worker 負責刷新時，輪詢背景 job 並同步最新快照。"""
    result = poll_cached_crawl_job(
        settings=settings,
        query_signature=str(st.session_state.get("crawl_query_signature") or ""),
        active_job_id=int(st.session_state.get("crawl_active_job_id") or 0),
        current_snapshot=st.session_state.get("snapshot"),
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

    finalize_result = advance_finalize_batch(
        settings=settings,
        snapshot=snapshot,
        pending_state=pending_state,
        crawl_preset_label=st.session_state.crawl_preset_label,
        force_refresh=st.session_state.crawl_refresh_mode == "強制更新",
    )
    if finalize_result.status == "cleared":
        clear_pending_crawl_state()
        return
    if finalize_result.snapshot is not None:
        st.session_state.snapshot = finalize_result.snapshot
    if finalize_result.pending_state is not None:
        _apply_pending_crawl_state(
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
    eta_label = _estimate_crawl_eta_label(
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
        start_result = start_crawl(
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
                _apply_pending_crawl_state(
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
            _apply_pending_crawl_state(
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
