from __future__ import annotations

import pandas as pd
import streamlit as st

from ..models import MarketSnapshot, NotificationPreference
from ..product_store import ProductStore
from .frames import jobs_to_frame, skills_to_frame, task_insights_to_frame
from .search import _default_search_row


def notification_state_defaults(
    preferences: NotificationPreference,
) -> dict[str, str | bool | int]:
    return {
        "notify_site_enabled": preferences.site_enabled,
        "notify_email_enabled": preferences.email_enabled,
        "notify_line_enabled": preferences.line_enabled,
        "notify_email_recipients": preferences.email_recipients,
        "notify_line_target": preferences.line_target,
        "notify_min_score": int(preferences.min_relevance_score),
        "notify_max_jobs": int(preferences.max_jobs_per_alert),
    }


def apply_notification_session_state(
    *,
    user_id: int,
    preferences: NotificationPreference,
) -> None:
    defaults = notification_state_defaults(preferences)
    same_user = st.session_state.get("notification_state_user_id") == int(user_id)
    missing_keys = [key for key in defaults if key not in st.session_state]
    if same_user and not missing_keys:
        return
    for key, value in defaults.items():
        st.session_state[key] = value
    st.session_state.notification_state_user_id = int(user_id)


def activate_user_session(
    *,
    user,
    product_store: ProductStore,
    success_message: str = "",
) -> None:
    st.session_state.auth_user_id = int(user.id)
    st.session_state.auth_user_email = user.email
    st.session_state.auth_user_display_name = user.display_name
    st.session_state.auth_user_is_guest = bool(user.is_guest)
    st.session_state.active_saved_search_id = None
    st.session_state.pending_saved_search_refresh_id = None
    st.session_state.resume_matches = []
    st.session_state.resume_notes = []
    st.session_state.assistant_profile = None
    st.session_state.assistant_history = []
    st.session_state.assistant_report = None
    st.session_state.assistant_question_draft = ""
    st.session_state.assistant_question_input = ""
    st.session_state.assistant_suggestion_page = 0

    stored_profile = None
    if not bool(user.is_guest):
        stored_resume = product_store.get_resume_profile(user_id=int(user.id))
        if stored_resume is not None:
            stored_profile = stored_resume.profile
        preferences = product_store.get_notification_preferences(user_id=int(user.id))
    else:
        preferences = NotificationPreference()
    st.session_state.resume_profile = stored_profile
    apply_notification_session_state(user_id=int(user.id), preferences=preferences)

    if success_message:
        st.session_state.favorite_feedback = success_message


def assistant_question_batches(
    questions: list[str],
    batch_size: int = 4,
) -> list[list[str]]:
    cleaned = [str(question).strip() for question in questions if str(question).strip()]
    if not cleaned:
        return [[]]
    return [
        cleaned[index : index + batch_size]
        for index in range(0, len(cleaned), batch_size)
    ]


def render_top_limit_control(
    container,
    *,
    label: str,
    total_count: int,
    key: str,
    default_value: int,
    min_slider_value: int = 8,
    max_slider_value: int = 30,
) -> int:
    total_count = max(0, int(total_count))
    if total_count == 0:
        return 0
    if total_count <= min_slider_value:
        container.caption(f"{label}：目前共 {total_count} 項")
        return total_count
    return int(
        container.slider(
            label,
            min_value=min_slider_value,
            max_value=min(max_slider_value, total_count),
            value=min(default_value, total_count),
            step=1,
            key=key,
        )
    )


def set_main_tab(tab_id: str) -> None:
    st.session_state.main_tab_selection = tab_id
    st.session_state.pending_main_tab_selection = tab_id


def cache_snapshot_views(snapshot: MarketSnapshot) -> None:
    snapshot_key = (
        f"{snapshot.generated_at}|{len(snapshot.jobs)}|"
        f"{len(snapshot.skills)}|{len(snapshot.task_insights)}"
    )
    if st.session_state.get("snapshot_view_cache_key") == snapshot_key:
        return
    st.session_state.snapshot_job_frame = jobs_to_frame(snapshot)
    st.session_state.snapshot_skill_frame = skills_to_frame(snapshot.skills)
    st.session_state.snapshot_task_frame = task_insights_to_frame(snapshot.task_insights)
    st.session_state.snapshot_jobs_by_url = {
        job.url: job for job in snapshot.jobs if job.url
    }
    st.session_state.snapshot_view_cache_key = snapshot_key


def initialize_session_state(*, guest_user) -> list[dict[str, object]]:
    default_rows = [_default_search_row()]
    defaults: dict[str, object] = {
        "search_role_rows": default_rows,
        "custom_queries_text": "",
        "crawl_preset_label": "快速",
        "snapshot": None,
        "resume_profile": None,
        "resume_matches": [],
        "resume_notes": [],
        "assistant_history": [],
        "assistant_report": None,
        "assistant_question_draft": "",
        "assistant_question_input": "",
        "assistant_profile": None,
        "assistant_suggestion_page": 0,
        "active_saved_search_id": None,
        "favorite_feedback": "",
        "last_crawl_signature": "",
        "search_role_autofilled_notice": False,
        "main_tab_selection": "overview",
        "main_tab_control": "overview",
        "pending_main_tab_selection": "",
        "pending_saved_search_refresh_id": None,
        "snapshot_view_cache_key": "",
        "snapshot_job_frame": pd.DataFrame(),
        "snapshot_skill_frame": pd.DataFrame(),
        "snapshot_task_frame": pd.DataFrame(),
        "snapshot_jobs_by_url": {},
        "auth_user_id": int(guest_user.id),
        "auth_user_email": guest_user.email,
        "auth_user_display_name": guest_user.display_name,
        "auth_user_is_guest": True,
        "visit_count_recorded": False,
        "total_visit_count": 0,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    return default_rows
