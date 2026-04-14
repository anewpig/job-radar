"""使用者切換與通知偏好相關的 session helpers。"""

from __future__ import annotations

import streamlit as st

from ..models import NotificationPreference
from ..product_store import ProductStore


def notification_state_defaults(
    preferences: NotificationPreference,
) -> dict[str, str | bool | int]:
    """把通知偏好物件轉成可直接寫入 session state 的基本型別。"""
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
    """把指定使用者的通知設定同步到目前 session。"""
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
    login_method: str | None = None,
    oidc_provider: str = "",
    oidc_subject: str = "",
) -> None:
    """切換目前 session 到指定使用者，並重建使用者相關狀態。"""
    st.session_state.auth_user_id = int(user.id)
    st.session_state.auth_user_email = user.email
    st.session_state.auth_user_display_name = user.display_name
    st.session_state.auth_user_is_guest = bool(user.is_guest)
    st.session_state.auth_login_method = (
        "guest" if bool(user.is_guest) else (login_method or "password")
    )
    st.session_state.auth_oidc_provider = "" if bool(user.is_guest) else oidc_provider
    st.session_state.auth_oidc_subject = "" if bool(user.is_guest) else oidc_subject
    st.session_state.auth_pending_oidc_link_user_id = 0
    st.session_state.auth_pending_oidc_provider = ""
    st.session_state.active_saved_search_id = None
    st.session_state.pending_saved_search_refresh_id = None
    st.session_state.resume_matches = []
    st.session_state.resume_notes = []
    st.session_state.assistant_profile = None
    st.session_state.assistant_history = []
    st.session_state.assistant_report = None
    st.session_state.assistant_question_draft = ""
    st.session_state.assistant_question_input = ""
    st.session_state.assistant_launcher_question_input = ""
    st.session_state.assistant_launcher_submit_pending = False
    st.session_state.assistant_suggestion_page = 0
    st.session_state.assistant_agent_mode = "assistant"
    st.session_state.assistant_agent_task = None
    st.session_state.assistant_agent_pending_confirmation = None
    st.session_state.assistant_agent_last_result = None

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
