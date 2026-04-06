"""集中管理 Streamlit session state 的輔助函式。

這個模組負責三類事情：
1. 把資料庫中的偏好設定轉成 session 預設值。
2. 初始化整個 UI 需要的 session key，避免頁面在首次載入時缺欄位。
3. 管理頁面導覽、快照快取與 AI 助理快捷問題等跨頁共用狀態。
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from uuid import uuid4

from ..models import MarketSnapshot, NotificationPreference
from ..product_store import ProductStore
from .frames import jobs_to_frame, skills_to_frame, task_insights_to_frame
from .search import _default_search_row


def notification_state_defaults(
    preferences: NotificationPreference,
) -> dict[str, str | bool | int]:
    """把通知偏好物件轉成可直接寫入 session state 的基本型別。

    Streamlit 的 session state 適合存放 bool、str、int 這類扁平資料。
    這個函式把 `NotificationPreference` 物件拆成頁面表單會直接使用的欄位，
    讓後續的初始化與使用者切換都能共用同一套資料結構。
    """
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
    """把指定使用者的通知設定同步到目前 session。

    這裡會做兩件事：
    1. 依資料庫中的通知偏好，把相關欄位寫入 `st.session_state`。
    2. 記住這些通知欄位目前屬於哪個使用者，避免同一個使用者重複覆寫。

    如果目前 session 已經是同一個使用者，且通知欄位都存在，就直接略過，
    以免每次 rerun 都重置使用者在畫面上的暫時修改。
    """
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
    """切換目前 session 到指定使用者，並重建使用者相關狀態。

    這個函式是登入、切換帳號或恢復使用者狀態時的核心入口。
    它會：
    1. 更新目前登入者的基本識別資料。
    2. 清掉只屬於上一位使用者的暫存結果，例如履歷匹配、AI 助理紀錄。
    3. 從資料庫還原這位使用者自己的履歷摘要與通知偏好。

    這樣可以避免不同使用者之間共用同一份前端暫存資料。
    """
    st.session_state.auth_user_id = int(user.id)
    st.session_state.auth_user_email = user.email
    st.session_state.auth_user_display_name = user.display_name
    st.session_state.auth_user_is_guest = bool(user.is_guest)
    st.session_state.auth_login_method = (
        "guest" if bool(user.is_guest) else (login_method or "password")
    )
    st.session_state.auth_oidc_provider = "" if bool(user.is_guest) else oidc_provider
    st.session_state.auth_oidc_subject = "" if bool(user.is_guest) else oidc_subject
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
    """把 AI 助理的快捷問題切成固定大小的批次。

    UI 一次只會顯示一小批快捷問題，避免按鈕太多把版面撐亂。
    這裡先清理空字串，再依 `batch_size` 切成多批，
    供前端輪播顯示「換一批問題」使用。
    """
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
    """渲染圖表前 N 筆控制器，並在資料太少時自動降級成文字提示。

    某些圖表只有資料量夠大時才需要 slider。
    如果總數量低於最小 slider 門檻，就直接顯示「目前共 X 項」，
    避免出現 `min_value == max_value` 造成的 Streamlit slider 例外。
    """
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
    """排程切換主頁籤，讓導覽元件在下次 rerun 時更新。

    這裡同時寫入：
    - `main_tab_selection`
    - `pending_main_tab_selection`

    原因是有些導覽元件建立後不能立刻回寫自己的 key；
    透過 pending 欄位可以在下一輪渲染前安全套用新的頁籤。
    """
    st.session_state.main_tab_selection = tab_id
    st.session_state.pending_main_tab_selection = tab_id


def cache_snapshot_views(snapshot: MarketSnapshot) -> None:
    """快取目前快照轉出的 DataFrame 視圖，避免每次 rerun 都重算。

    `MarketSnapshot` 會被多個頁面重複消費，例如：
    - 職缺總覽
    - 技能地圖
    - 工作內容統計
    - 職缺 URL 對照表

    這些投影結果在同一份快照下是穩定的，所以用一個簡單的 key
    判斷是否需要重算，可以明顯減少頁面切換時的額外成本。
    """
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
    """建立應用程式預期會存在的所有 session key。

    這個函式的目標是讓整個 UI 在第一次載入時就有完整的狀態欄位，
    避免後續程式直接讀取 `st.session_state.xxx` 時發生缺值錯誤。

    目前初始化的內容大致分為：
    - 搜尋設定與抓取模式
    - 快照、履歷匹配、AI 助理相關暫存
    - 分階段爬蟲的執行狀態
    - 導覽與分頁控制
    - 認證與來訪統計

    回傳值是預設搜尋列，讓入口層需要時可直接重用。
    """
    default_rows = [_default_search_row()]
    defaults: dict[str, object] = {
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
        "assistant_profile": None,
        "assistant_suggestion_page": 0,
        "assistant_launcher_open": False,
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

        # 來訪次數統計
        "visit_count_recorded": False,
        "total_visit_count": 0,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    return default_rows
