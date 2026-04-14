"""Crawl runtime 的狀態面板與 ETA 顯示。"""

from __future__ import annotations

import streamlit as st

from ..application.crawl import CrawlApplication, CrawlStatusRequest
from .common import build_chip_row
from .search import get_committed_search_rows


def format_runtime_status_label(status: str, *, kind: str) -> str:
    """把 runtime / snapshot 狀態轉成中文標籤。"""
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


def format_eta_seconds(seconds: int) -> str:
    """把秒數整理成適合顯示在 UI 的中文時間。"""
    rounded_seconds = max(5, int(round(seconds / 5) * 5))
    if rounded_seconds < 60:
        return f"{rounded_seconds} 秒"
    minutes, remain_seconds = divmod(rounded_seconds, 60)
    if remain_seconds == 0 or minutes >= 4:
        return f"{minutes} 分鐘"
    return f"{minutes} 分 {remain_seconds} 秒"


def estimate_crawl_eta_label(
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
            f"約 {format_eta_seconds(lower_seconds)} 到 {format_eta_seconds(upper_seconds)}"
            "，若背景佇列繁忙會再更久"
        )

    return f"約 {format_eta_seconds(lower_seconds)} 到 {format_eta_seconds(upper_seconds)}"


def should_render_runtime_panel() -> bool:
    """判斷目前是否需要顯示 runtime panel。"""
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
    if not should_render_runtime_panel():
        return

    runtime_status = CrawlApplication().inspect_status(
        CrawlStatusRequest(
            settings=settings,
            query_signature=query_signature,
        )
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
        f"Job：{format_runtime_status_label(runtime_status.job_status, kind='job')}",
        f"快照：{format_runtime_status_label(runtime_status.snapshot_status, kind='snapshot')}",
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
            format_runtime_status_label(runtime_status.job_status, kind="job"),
        )
        metric_cols[2].metric(
            "Snapshot",
            format_runtime_status_label(runtime_status.snapshot_status, kind="snapshot"),
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
