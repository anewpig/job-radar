"""將執行期狀態整理成 PageContext 的輔助函式。"""

from __future__ import annotations

import streamlit as st

from .page_context import PageContext


def build_page_context(
    *,
    settings,
    snapshot,
    job_frame,
    skill_frame,
    task_frame,
    jobs_by_url,
    product_store,
    user_data_store,
    notification_service,
    current_user_id: int,
    current_user_is_guest: bool,
    active_saved_search,
    favorite_jobs,
    favorite_urls,
    notifications,
    unread_notification_count: int,
    saved_searches,
    notification_preferences,
    default_rows,
    current_signature: str,
    current_search_name: str,
) -> PageContext:
    """建立所有頁面共用的型別化渲染上下文。"""
    return PageContext(
        settings=settings,
        snapshot=snapshot,
        crawl_phase=str(st.session_state.get("crawl_phase", "idle")),
        crawl_detail_cursor=int(st.session_state.get("crawl_detail_cursor", 0)),
        crawl_detail_total=int(st.session_state.get("crawl_detail_total", 0)),
        job_frame=job_frame,
        skill_frame=skill_frame,
        task_frame=task_frame,
        jobs_by_url=jobs_by_url,
        product_store=product_store,
        user_data_store=user_data_store,
        notification_service=notification_service,
        current_user_id=current_user_id,
        current_user_is_guest=current_user_is_guest,
        active_saved_search=active_saved_search,
        favorite_jobs=favorite_jobs,
        favorite_urls=favorite_urls,
        notifications=notifications,
        unread_notification_count=unread_notification_count,
        saved_searches=saved_searches,
        notification_preferences=notification_preferences,
        default_rows=default_rows,
        current_signature=current_signature,
        current_search_name=current_search_name,
    )
