"""Bootstrap 階段的 session/user context 恢復流程。"""

from __future__ import annotations

import streamlit as st

from ..models import NotificationPreference
from ..product_store import ProductStore
from ..settings import Settings
from .bootstrap_types import ActiveUserContext
from .auth_persistence import restore_persistent_login
from .session import activate_user_session, apply_notification_session_state


def hydrate_initial_snapshot(settings: Settings) -> None:
    """保留相容入口，但不再自動載入全域最新 snapshot。"""
    del settings


def ensure_visit_tracking(product_store: ProductStore) -> None:
    """在每個瀏覽器 session 中記錄或還原累計來訪次數。"""
    if not st.session_state.visit_count_recorded:
        st.session_state.total_visit_count = product_store.record_visit()
        st.session_state.visit_count_recorded = True
        return
    if not st.session_state.total_visit_count:
        st.session_state.total_visit_count = product_store.get_total_visits()


def ensure_guest_session(*, product_store: ProductStore, guest_user) -> None:
    """在訪客首次冷啟動時建立通知與 session 的預設狀態。"""
    if int(st.session_state.auth_user_id) != int(guest_user.id):
        return
    if restore_persistent_login(product_store=product_store, guest_user=guest_user):
        return
    if st.session_state.get("notification_state_user_id") is not None:
        return
    activate_user_session(user=guest_user, product_store=product_store)


def resolve_current_user(
    *,
    product_store: ProductStore,
    guest_user,
) -> ActiveUserContext:
    """解析目前有效帳號，並還原其使用者專屬的持久化狀態。"""
    current_user = product_store.get_user(int(st.session_state.auth_user_id))
    if current_user is None:
        current_user = guest_user
        activate_user_session(
            user=guest_user,
            product_store=product_store,
            success_message="找不到原本的登入狀態，已切回訪客模式。",
        )

    current_user_id = int(current_user.id)
    current_user_is_guest = bool(current_user.is_guest)
    if current_user_is_guest:
        st.session_state.active_saved_search_id = None
        saved_searches = []
        notification_preferences = NotificationPreference()
    else:
        notification_preferences = product_store.get_notification_preferences(
            user_id=current_user_id
        )
        saved_searches = product_store.list_saved_searches(user_id=current_user_id)

    apply_notification_session_state(
        user_id=current_user_id,
        preferences=notification_preferences,
    )
    return ActiveUserContext(
        user=current_user,
        current_user_id=current_user_id,
        current_user_is_guest=current_user_is_guest,
        current_user_role=str(current_user.role or "user"),
        notification_preferences=notification_preferences,
        saved_searches=saved_searches,
    )


def validate_active_saved_search(
    *,
    product_store: ProductStore,
    current_user_id: int,
    current_user_is_guest: bool,
) -> None:
    """在登入狀態切換後，清除失效的已儲存搜尋參照。"""
    if current_user_is_guest:
        st.session_state.active_saved_search_id = None
        return
    if not st.session_state.active_saved_search_id:
        return
    active_candidate = product_store.get_saved_search(
        int(st.session_state.active_saved_search_id),
        user_id=current_user_id,
    )
    if active_candidate is None:
        st.session_state.active_saved_search_id = None
