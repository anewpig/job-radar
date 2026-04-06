"""提供應用層服務初始化與使用者執行期狀態整理的輔助函式。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from ..config import load_settings
from ..models import NotificationPreference, SavedSearch, UserAccount
from ..product_store import ProductStore
from ..runtime_maintenance_service import run_runtime_cleanup
from ..search_keyword_recommender import RoleKeywordRecommender
from ..settings import Settings
from ..storage import load_snapshot
from ..user_data_store import UserDataStore
from .resources import (
    get_keyword_recommender,
    get_notification_service,
    get_product_store,
    get_user_data_store,
)
from .session import activate_user_session, apply_notification_session_state


@dataclass(frozen=True, slots=True)
class AppRuntime:
    """封裝整個 UI 執行期間共用的長生命週期服務與設定。"""

    root: Path
    settings: Settings
    keyword_recommender: RoleKeywordRecommender
    user_data_store: UserDataStore
    product_store: ProductStore
    notification_service: object
    guest_user: UserAccount


@dataclass(frozen=True, slots=True)
class ActiveUserContext:
    """封裝目前 Streamlit session 對應的使用者狀態。"""

    user: UserAccount
    current_user_id: int
    current_user_is_guest: bool
    notification_preferences: NotificationPreference
    saved_searches: list[SavedSearch]


def bootstrap_runtime(root: Path) -> AppRuntime:
    """建立支撐整個 Streamlit 應用的共用服務。"""
    settings = load_settings(root)
    run_runtime_cleanup(
        settings=settings,
        trigger="ui",
    )
    product_store = get_product_store(str(settings.product_state_db_path))
    return AppRuntime(
        root=root,
        settings=settings,
        keyword_recommender=get_keyword_recommender(),
        user_data_store=get_user_data_store(str(settings.user_data_db_path)),
        product_store=product_store,
        notification_service=get_notification_service(
            root=str(root),
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password,
            smtp_from_email=settings.smtp_from_email,
            smtp_use_tls=settings.smtp_use_tls,
            smtp_use_ssl=settings.smtp_use_ssl,
            line_channel_access_token=settings.line_channel_access_token,
            line_channel_secret=settings.line_channel_secret,
            line_to=settings.line_to,
            public_base_url=settings.public_base_url,
            line_webhook_host=settings.line_webhook_host,
            line_webhook_port=settings.line_webhook_port,
        ),
        guest_user=product_store.get_guest_user(),
    )


def hydrate_initial_snapshot(settings: Settings) -> None:
    """當 session 內尚未有快照時，載入最近一次保存的市場快照。"""
    if st.session_state.snapshot is not None:
        return
    cached_snapshot = load_snapshot(settings.snapshot_path)
    if cached_snapshot is not None:
        st.session_state.snapshot = cached_snapshot


def ensure_visit_tracking(product_store: ProductStore) -> None:
    """在每個瀏覽器 session 中記錄或還原累計來訪次數。"""
    if not st.session_state.visit_count_recorded:
        st.session_state.total_visit_count = product_store.record_visit()
        st.session_state.visit_count_recorded = True
        return
    if not st.session_state.total_visit_count:
        st.session_state.total_visit_count = product_store.get_total_visits()


def ensure_guest_session(*, product_store: ProductStore, guest_user: UserAccount) -> None:
    """在訪客首次冷啟動時建立通知與 session 的預設狀態。"""
    if int(st.session_state.auth_user_id) != int(guest_user.id):
        return
    if st.session_state.get("notification_state_user_id") is not None:
        return
    activate_user_session(user=guest_user, product_store=product_store)


def resolve_current_user(
    *,
    product_store: ProductStore,
    guest_user: UserAccount,
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
        saved_searches: list[SavedSearch] = []
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
