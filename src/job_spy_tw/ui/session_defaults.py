"""Session defaults 與初始化 helpers。"""

from __future__ import annotations

from uuid import uuid4

import pandas as pd
import streamlit as st

from .search import _default_search_row


def build_default_search_rows() -> list[dict[str, object]]:
    """建立搜尋設定的預設列。"""
    return [_default_search_row()]


def build_session_defaults(*, guest_user) -> dict[str, object]:
    """建立應用程式首次載入需要的 session 預設值。"""
    default_rows = build_default_search_rows()
    return {
        # 搜尋設定與爬取模式
        "search_role_rows": default_rows,
        "custom_queries_text": "",
        "crawl_preset_label": "快速",
        "crawl_refresh_mode": "使用快取",

        # 快照與履歷 / AI 助理結果
        "snapshot": None,
        "resume_profile": None,
        "resume_matches": [],
        "resume_notes": [],
        "assistant_history": [],
        "assistant_report": None,
        "assistant_question_draft": "",
        "assistant_question_input": "",
        "assistant_launcher_question_input": "",
        "assistant_launcher_submit_pending": False,
        "launcher_bottom_tab": "assistant",
        "assistant_profile": None,
        "assistant_suggestion_page": 0,
        "assistant_launcher_open": False,
        "assistant_agent_mode": "assistant",
        "assistant_agent_task": None,
        "assistant_agent_pending_confirmation": None,
        "assistant_agent_last_result": None,
        "nav_drawer_open": False,

        # 搜尋與收藏等產品狀態
        "active_saved_search_id": None,
        "favorite_feedback": "",
        "last_crawl_signature": "",
        "search_role_autofilled_notice": False,

        # 分階段爬蟲狀態
        "crawl_phase": "idle",
        "crawl_pending_queries": [],
        "crawl_pending_jobs": [],
        "crawl_pending_errors": [],
        "crawl_partial_ready_at": "",
        "crawl_detail_cursor": 0,
        "crawl_detail_total": 0,
        "crawl_remaining_page_cursor": 1,
        "crawl_initial_wave_sources": [],
        "crawl_query_signature": "",
        "crawl_active_job_id": 0,
        "crawl_worker_id": str(uuid4()),

        # 導覽與列表分頁
        "main_tab_selection": "overview",
        "main_tab_control": "overview",
        "pending_main_tab_selection": "",
        "pending_saved_search_refresh_id": None,
        "overview_page": 1,
        "overview_filter_signature": "",
        "overview_sort_mode": "relevance",

        # 目前快照對應的 DataFrame 快取
        "snapshot_view_cache_key": "",
        "snapshot_job_frame": pd.DataFrame(),
        "snapshot_skill_frame": pd.DataFrame(),
        "snapshot_task_frame": pd.DataFrame(),
        "snapshot_jobs_by_url": {},

        # 認證與訪客預設狀態
        "auth_user_id": int(guest_user.id),
        "auth_user_email": guest_user.email,
        "auth_user_display_name": guest_user.display_name,
        "auth_user_is_guest": True,
        "auth_login_method": "guest",
        "auth_oidc_provider": "",
        "auth_oidc_subject": "",
        "auth_pending_oidc_link_user_id": 0,
        "auth_pending_oidc_provider": "",
        "show_auth_dialog": False,
        "auth_view_mode": "login",
        "auth_form_error": "",
        "auth_form_success": "",
        "auth_form_field_errors": {},
        "auth_reset_email_prefill": "",

        # 來訪次數統計
        "visit_count_recorded": False,
        "total_visit_count": 0,
    }


def initialize_session_state(*, guest_user) -> list[dict[str, object]]:
    """建立應用程式預期會存在的所有 session key。"""
    defaults = build_session_defaults(guest_user=guest_user)
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    return defaults["search_role_rows"]
