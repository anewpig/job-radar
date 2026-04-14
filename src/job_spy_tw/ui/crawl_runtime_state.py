"""Crawl runtime 的查詢與 session state helpers。"""

from __future__ import annotations

import streamlit as st

from ..application.crawl import CrawlApplication, SavedSearchSyncRequest
from ..application.query import BuildQueriesRequest, QueryApplication
from ..crawl_application_service import PendingCrawlState
from ..models import MarketSnapshot, NotificationPreference
from .search import get_committed_search_rows


def build_crawl_queries(*, role_targets, crawl_preset, custom_queries: str) -> list[str]:
    """依目標職缺與額外自訂查詢字詞建立最終查詢清單。"""
    return QueryApplication().build_queries(
        BuildQueriesRequest(
            role_targets=role_targets,
            crawl_preset=crawl_preset,
            custom_queries=custom_queries,
        )
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


def apply_pending_crawl_state(*, phase: str, pending_state: PendingCrawlState) -> None:
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
    result = CrawlApplication().sync_saved_search_results(
        SavedSearchSyncRequest(
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
    )
    if result.active_saved_search_id is not None:
        st.session_state.active_saved_search_id = result.active_saved_search_id
    return result.feedback
