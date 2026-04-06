"""職缺雷達的 Streamlit 入口檔。"""

from __future__ import annotations

import sys
import importlib
from pathlib import Path

import streamlit as st

# 允許直接從專案根目錄啟動，不需要先把套件安裝到目前的 Python 環境。
ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Streamlit 熱重載時偶爾會在子模組匯入前把母套件狀態弄亂，
# 先顯式載入 package 可避免 `KeyError: job_spy_tw.ui`。
importlib.import_module("job_spy_tw")
importlib.import_module("job_spy_tw.ui")

from job_spy_tw.models import (
    MarketSnapshot,
)
from job_spy_tw.ui.assistant_launcher import render_assistant_launcher
from job_spy_tw.ui.auth import render_auth_popover
from job_spy_tw.ui.bootstrap import (
    bootstrap_runtime,
    ensure_guest_session,
    ensure_visit_tracking,
    hydrate_initial_snapshot,
    resolve_current_user,
    validate_active_saved_search,
)
from job_spy_tw.ui.common import (
    _escape,
    render_hero,
    render_newsletter_footer,
    render_top_header,
)
from job_spy_tw.ui.context_builder import build_page_context
from job_spy_tw.ui.crawl_runtime import (
    maybe_start_crawl,
    render_finalize_worker_fragment,
)
from job_spy_tw.ui.router import (
    dispatch_main_tab,
    peek_selected_main_tab,
    resolve_selected_main_tab,
)
from job_spy_tw.ui.search import (
    _prime_search_row_widget_state,
    _suggest_saved_search_name,
    build_role_targets,
    get_committed_search_rows,
)
from job_spy_tw.ui.search_setup import render_search_setup
from job_spy_tw.ui.session import cache_snapshot_views, initialize_session_state
from job_spy_tw.ui.styles import inject_global_styles


st.set_page_config(
    page_title="職缺雷達",
    page_icon=":mag:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def main() -> None:
    """組裝 app runtime、渲染外框，並分派目前選中的頁面。"""
    # 先建立本輪執行需要的 service/store/runtime 物件，再開始畫畫面。
    runtime = bootstrap_runtime(ROOT)
    settings = runtime.settings
    show_backend_console = settings.show_backend_console
    product_store = runtime.product_store
    user_data_store = runtime.user_data_store
    notification_service = runtime.notification_service
    guest_user = runtime.guest_user
    inject_global_styles()

    # 先把所有會用到的 session key 補齊，後面的頁面函式就能直接依賴這些狀態。
    default_rows = initialize_session_state(guest_user=guest_user)

    # 只有在記憶體裡還沒有 snapshot 時，才從磁碟載入最近一次快照。
    # 這樣 refresh 不會每次都重讀檔案，但 app 重啟後還是能恢復上一輪結果。
    hydrate_initial_snapshot(settings)

    # 來訪次數只在同一個瀏覽器 session 第一次進站時計一次，
    # 避免 Streamlit rerun 把數字灌水。
    ensure_visit_tracking(product_store)

    # 若目前是訪客且還沒建立好訪客 session，就補上預設訪客狀態。
    ensure_guest_session(product_store=product_store, guest_user=guest_user)

    # 從持久化資料還原目前使用者。
    # 如果 session 指向的帳號不存在，會明確退回訪客模式。
    user_state = resolve_current_user(
        product_store=product_store,
        guest_user=guest_user,
    )
    current_user_id = user_state.current_user_id
    current_user_is_guest = user_state.current_user_is_guest
    saved_searches = user_state.saved_searches
    notification_preferences = user_state.notification_preferences
    unread_notification_count = (
        product_store.unread_notification_count(user_id=current_user_id)
        if not current_user_is_guest
        else 0
    )
    validate_active_saved_search(
        product_store=product_store,
        current_user_id=current_user_id,
        current_user_is_guest=current_user_is_guest,
    )

    # 動態搜尋列在上一輪如果有增刪，這裡要把 widget state 重新對齊，
    # 否則 Streamlit 會沿用舊欄位結構。
    pending_search_rows = st.session_state.pop("search_role_widget_refresh", None)
    if pending_search_rows is not None:
        st.session_state.search_role_rows = pending_search_rows
        st.session_state.search_role_draft_index = None
        _prime_search_row_widget_state(pending_search_rows, force=True)
    else:
        _prime_search_row_widget_state(st.session_state.search_role_rows, force=False)

    # Header 與登入入口先畫，後面的 hero 和頁面內容都以這個外框為基準。
    if str(st.query_params.get("auth", "")).strip().lower() == "start":
        st.session_state.show_auth_dialog = True
        try:
            st.query_params.pop("auth")
        except KeyError:
            pass
    render_top_header(int(st.session_state.total_visit_count))
    render_auth_popover(
        current_user_is_guest=current_user_is_guest,
        guest_user=guest_user,
        product_store=product_store,
        notification_service=notification_service,
    )
    selected_main_tab_preview = peek_selected_main_tab(
        unread_notification_count=unread_notification_count,
        show_backend_console=show_backend_console,
    )

    hero_placeholder = st.empty()
    search_setup_state = None
    if selected_main_tab_preview not in {"export", "notifications", "backend", "backend_ops", "backend_console", "database"}:
        setup_snapshot = st.session_state.snapshot
        # 搜尋設定只回傳整理過的狀態物件，避免 `main()` 直接持有大量 widget 細節。
        search_setup_state = render_search_setup(
            snapshot=setup_snapshot,
            keyword_recommender=runtime.keyword_recommender,
        )

    effective_search_rows = get_committed_search_rows(
        st.session_state.search_role_rows,
        draft_index=st.session_state.get("search_role_draft_index"),
    )

    # 依目前搜尋設定建立穩定簽章，用來比對是否已經存在相同的已儲存搜尋。
    current_signature = product_store.build_signature(
        effective_search_rows,
        st.session_state.custom_queries_text,
        st.session_state.crawl_preset_label,
    )
    if (not current_user_is_guest) and (not st.session_state.active_saved_search_id):
        matched_saved_search = product_store.find_saved_search_by_signature(
            effective_search_rows,
            st.session_state.custom_queries_text,
            st.session_state.crawl_preset_label,
            user_id=current_user_id,
        )
        if matched_saved_search is not None:
            st.session_state.active_saved_search_id = matched_saved_search.id

    # 這裡只負責觸發 staged crawl，真正的抓取與 finalize 狀態機已搬到 runtime 模組。
    if search_setup_state is not None:
        maybe_start_crawl(
            settings=settings,
            search_setup_state=search_setup_state,
            product_store=product_store,
            notification_service=notification_service,
            current_user_id=current_user_id,
            current_user_is_guest=current_user_is_guest,
            notification_preferences=notification_preferences,
            current_signature=current_signature,
        )

    snapshot: MarketSnapshot | None = st.session_state.snapshot
    current_role_targets = build_role_targets(effective_search_rows)
    # hero 一律反映目前 session 內最新的 snapshot，可能是 partial，也可能是 final。
    if selected_main_tab_preview not in {"export", "notifications", "backend", "backend_ops", "backend_console", "database"}:
        with hero_placeholder.container():
            render_hero(snapshot, current_role_targets)
    if st.session_state.favorite_feedback:
        st.success(st.session_state.favorite_feedback)
        st.session_state.favorite_feedback = ""

    if snapshot is None and selected_main_tab_preview not in {"backend", "backend_ops", "backend_console", "database"}:
        st.info("按下左側的「開始抓取並分析」，系統會建立最新的職缺快照。")
        return

    if snapshot is not None:
        # 先把 snapshot 轉成各頁可直接使用的 DataFrame / dict 快取，避免每頁重算。
        cache_snapshot_views(snapshot)
        job_frame = st.session_state.snapshot_job_frame
        skill_frame = st.session_state.snapshot_skill_frame
        task_frame = st.session_state.snapshot_task_frame
        jobs_by_url = st.session_state.snapshot_jobs_by_url
    else:
        snapshot = MarketSnapshot(
            generated_at="",
            queries=[],
            role_targets=[],
            jobs=[],
            skills=[],
            task_insights=[],
            errors=[],
        )
        job_frame = st.session_state.snapshot_job_frame
        skill_frame = st.session_state.snapshot_skill_frame
        task_frame = st.session_state.snapshot_task_frame
        jobs_by_url = st.session_state.snapshot_jobs_by_url
    favorite_jobs = (
        product_store.list_favorites(user_id=current_user_id)
        if not current_user_is_guest
        else []
    )
    favorite_urls = {item.job_url for item in favorite_jobs}
    notifications = (
        product_store.list_notifications(limit=12, user_id=current_user_id)
        if not current_user_is_guest
        else []
    )
    active_saved_search = None
    if st.session_state.active_saved_search_id and not current_user_is_guest:
        active_saved_search = product_store.get_saved_search(
            int(st.session_state.active_saved_search_id),
            user_id=current_user_id,
        )
    current_search_name = (
        active_saved_search.name
        if active_saved_search is not None
        else _suggest_saved_search_name(
            st.session_state.search_role_rows,
            st.session_state.custom_queries_text,
        )
    )
    # 低相關過濾訊息只算資訊提示，其他錯誤仍保留 warning 顯示。
    low_relevance_notes = [
        error for error in snapshot.errors if "低相關職缺" in str(error)
    ]
    other_snapshot_errors = [
        error for error in snapshot.errors if "低相關職缺" not in str(error)
    ]

    if selected_main_tab_preview not in {"export", "notifications", "backend", "backend_ops", "backend_console", "database"} and low_relevance_notes:
        st.markdown(
            (
                "<div style='font-size:0.78rem;color:rgba(73,80,87,0.82);"
                "text-align:right;padding-top:0.2rem;'>"
                f"{_escape(' '.join(low_relevance_notes))}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    if other_snapshot_errors and selected_main_tab_preview not in {"export", "notifications", "backend", "backend_ops", "backend_console", "database"}:
        for error in other_snapshot_errors:
            st.warning(error)

    # 先決定目前頁籤，再把 runtime 狀態組成 page context 丟給各頁面。
    selected_main_tab = resolve_selected_main_tab(
        unread_notification_count=unread_notification_count,
        show_backend_console=show_backend_console,
    )

    page_context = build_page_context(
        settings=settings,
        snapshot=snapshot,
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

    dispatch_main_tab(selected_main_tab, page_context)

    # staged crawl 如果還在 finalize，這個 fragment 會持續推進下一批 enrich。
    # 這個 worker shell 只負責觸發背景補分析，不應在畫面上留下任何可見占位。
    with st.container(key="finalize-worker-shell"):
        render_finalize_worker_fragment(
            settings=settings,
            snapshot=st.session_state.snapshot,
            product_store=product_store,
            notification_service=notification_service,
            current_user_id=current_user_id,
            current_user_is_guest=current_user_is_guest,
            notification_preferences=notification_preferences,
        )

    # 浮動入口與 footer 最後再畫，避免影響主頁內容的版面計算。
    render_assistant_launcher()
    render_newsletter_footer(int(st.session_state.total_visit_count))


if __name__ == "__main__":
    main()
