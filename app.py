from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import load_settings
from job_spy_tw.crawl_tuning import CRAWL_PRESETS, apply_crawl_preset, get_crawl_preset
from job_spy_tw.models import (
    MarketSnapshot,
    NotificationPreference,
)
from job_spy_tw.pipeline import JobMarketPipeline
from job_spy_tw.search_keyword_recommender import (
    autofill_role_keyword_rows,
    normalize_search_role_rows,
)
from job_spy_tw.storage import load_snapshot
from job_spy_tw.targets import build_default_queries
from job_spy_tw.ui import (
    _default_search_row,
    _escape,
    _next_search_priority,
    _prime_search_row_widget_state,
    _read_search_row_widgets,
    _search_widget_key,
    _suggest_saved_search_name,
    activate_user_session,
    apply_notification_session_state,
    cache_snapshot_views,
    build_role_targets,
    get_keyword_recommender,
    get_notification_service,
    get_product_store,
    get_user_data_store,
    inject_global_styles,
    initialize_session_state,
    PageContext,
    render_assistant_page,
    render_hero,
    render_auth_popover,
    render_board_page,
    render_export_page,
    render_notifications_page,
    render_overview_page,
    render_resume_page,
    render_skills_page,
    render_sources_page,
    render_tasks_page,
    render_tracking_page,
)


st.set_page_config(
    page_title="職缺雷達",
    page_icon=":mag:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def main() -> None:
    settings = load_settings(ROOT)
    keyword_recommender = get_keyword_recommender()
    user_data_store = get_user_data_store(str(settings.user_data_db_path))
    product_store = get_product_store(str(settings.product_state_db_path))
    notification_service = get_notification_service(
        root=str(ROOT),
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
    )
    guest_user = product_store.get_guest_user()
    inject_global_styles()

    default_rows = initialize_session_state(guest_user=guest_user)

    if st.session_state.snapshot is None:
        cached_snapshot = load_snapshot(settings.snapshot_path)
        if cached_snapshot is not None:
            st.session_state.snapshot = cached_snapshot

    if not st.session_state.visit_count_recorded:
        st.session_state.total_visit_count = product_store.record_visit()
        st.session_state.visit_count_recorded = True
    elif not st.session_state.total_visit_count:
        st.session_state.total_visit_count = product_store.get_total_visits()

    if int(st.session_state.auth_user_id) == int(guest_user.id) and (
        st.session_state.get("notification_state_user_id") is None
    ):
        activate_user_session(user=guest_user, product_store=product_store)

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

    if st.session_state.active_saved_search_id and not current_user_is_guest:
        active_candidate = product_store.get_saved_search(
            int(st.session_state.active_saved_search_id),
            user_id=current_user_id,
        )
        if active_candidate is None:
            st.session_state.active_saved_search_id = None
    elif current_user_is_guest:
        st.session_state.active_saved_search_id = None

    pending_search_rows = st.session_state.pop("search_role_widget_refresh", None)
    if pending_search_rows is not None:
        st.session_state.search_role_rows = pending_search_rows
        _prime_search_row_widget_state(pending_search_rows, force=True)
    else:
        _prime_search_row_widget_state(st.session_state.search_role_rows, force=False)

    topbar_cols = st.columns([4.8, 3.0, 1.35], gap="small")
    with topbar_cols[0]:
        st.caption(f"累計來訪 {int(st.session_state.total_visit_count):,} 人次")
    with topbar_cols[1]:
        st.empty()
    with topbar_cols[2]:
        render_auth_popover(
            current_user_is_guest=current_user_is_guest,
            guest_user=guest_user,
            product_store=product_store,
            notification_service=notification_service,
        )

    hero_placeholder = st.empty()

    with st.container(border=True):
        setup_intro_cols = st.columns([4.3, 1.1], gap="large")
        setup_intro_cols[0].markdown(
            f"""
<div class="section-shell" style="margin:0 0 0.35rem;">
  <div class="section-kicker">{_escape("Search Setup")}</div>
  <div class="section-title">{_escape("搜尋設定")}</div>
  <div class="section-desc">{_escape("依照你想追蹤的方向填寫優先序、目標職缺與關鍵字。系統會自動補推薦關鍵字。")}</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        add_search_row = setup_intro_cols[1].button(
            "新增追蹤方向",
            key="add-search-row",
            use_container_width=True,
        )

        previous_role_rows = list(st.session_state.search_role_rows)
        remove_row_index: int | None = None
        row_count = len(st.session_state.search_role_rows)
        for index in range(row_count):
            row = st.session_state.search_role_rows[index]
            with st.container():
                row_header_cols = st.columns([1.8, 1.1, 1.1], gap="small")
                row_header_cols[0].markdown(f"**追蹤方向 {index + 1}**")
                row_header_cols[0].caption("系統會依優先序排序，先抓你最想追蹤的方向。")
                row_header_cols[1].checkbox(
                    "啟用這列",
                    value=bool(row.get("enabled", True)),
                    key=_search_widget_key(index, "enabled"),
                    help="取消後會保留這列內容，但本次不會拿去搜尋。",
                )
                if row_header_cols[2].button(
                    "刪除這列",
                    key=f"remove-search-row-{index}",
                    use_container_width=True,
                    disabled=row_count == 1,
                ):
                    remove_row_index = index

                row_field_cols = st.columns([1.05, 2.1, 4.2], gap="medium")
                row_field_cols[0].number_input(
                    "優先序",
                    min_value=1,
                    step=1,
                    value=int(row.get("priority", index + 1) or (index + 1)),
                    key=_search_widget_key(index, "priority"),
                )
                row_field_cols[1].text_input(
                    "目標職缺",
                    value=str(row.get("role", "")),
                    key=_search_widget_key(index, "role"),
                    placeholder="例如：藥師、鋼琴老師、AI工程師",
                )
                row_field_cols[2].text_input(
                    "關鍵字",
                    value=str(row.get("keywords", "")),
                    key=_search_widget_key(index, "keywords"),
                    placeholder="留空可自動推薦；可用逗號分隔多個關鍵字",
                    help="可填技能、職稱別名、地點或產業詞，系統也會依目標職缺自動補上推薦關鍵字。",
                )
                if index < row_count - 1:
                    st.divider()

        if remove_row_index is not None:
            updated_rows = [
                row
                for index, row in enumerate(st.session_state.search_role_rows)
                if index != remove_row_index
            ]
            st.session_state.search_role_rows = updated_rows or [_default_search_row()]
            st.session_state.search_role_widget_refresh = st.session_state.search_role_rows
            st.rerun()

        if add_search_row:
            updated_rows = normalize_search_role_rows(_read_search_row_widgets(row_count))
            new_row = _default_search_row()
            new_row["priority"] = _next_search_priority(updated_rows)
            updated_rows.append(new_row)
            st.session_state.search_role_rows = updated_rows
            st.session_state.search_role_widget_refresh = updated_rows
            st.rerun()

        edited_roles = _read_search_row_widgets(row_count)
        normalized_roles, autofilled = autofill_role_keyword_rows(
            edited_roles,
            previous_role_rows,
            keyword_recommender,
        )
        st.session_state.search_role_rows = normalized_roles
        if autofilled:
            st.session_state.search_role_autofilled_notice = True
            st.session_state.search_role_widget_refresh = normalized_roles
            st.rerun()
        if st.session_state.search_role_autofilled_notice:
            st.info("已依目標職缺自動補上推薦關鍵字，你也可以直接改寫。")
            st.session_state.search_role_autofilled_notice = False

        st.divider()
        search_control_left, search_control_right = st.columns([1.15, 1], gap="large")
        search_panel_height = 265
        with search_control_left:
            with st.container(height=search_panel_height):
                st.markdown("**抓取模式**")
                st.caption("快速適合先看趨勢，平衡兼顧速度與完整度，完整則保留更多結果。")
                crawl_preset_label = st.radio(
                    "抓取模式",
                    options=[preset.label for preset in CRAWL_PRESETS],
                    index=[preset.label for preset in CRAWL_PRESETS].index(
                        st.session_state.crawl_preset_label
                    ),
                    captions=[preset.description for preset in CRAWL_PRESETS],
                    key="crawl_preset_label",
                    horizontal=True,
                    label_visibility="collapsed",
                )
                crawl_refresh_mode = st.segmented_control(
                    "資料更新模式",
                    options=["使用快取", "強制更新"],
                    default=st.session_state.crawl_refresh_mode,
                    key="crawl_refresh_mode",
                    help="使用快取會比較快；強制更新會重新向 104、1111、LinkedIn 抓取相同查詢的最新頁面。",
                )
                crawl_preset = get_crawl_preset(crawl_preset_label)
                force_refresh = crawl_refresh_mode == "強制更新"
                if force_refresh:
                    st.caption("這次會跳過本地快取，重新抓取最新職缺與原文。")
        with search_control_right:
            with st.container(height=search_panel_height):
                st.markdown("**搜尋資訊**")
                st.caption("這組名稱會用在追蹤、通知和收藏綁定，建議取一個你看得懂的名字。")
                current_search_name = st.text_input(
                    "搜尋名稱",
                    value=_suggest_saved_search_name(
                        st.session_state.search_role_rows,
                        st.session_state.custom_queries_text,
                    ),
                    key="saved_search_name_input",
                    help="儲存後可重複載入，也能用來追蹤新職缺。",
                )
                custom_queries = st.text_area(
                    "額外查詢字詞",
                    value=st.session_state.custom_queries_text,
                    help="每行一個關鍵字。這些字詞會和上方目標職缺一起搜尋。",
                    key="custom_queries_text",
                    height=100,
                    placeholder="例如：遠端、新竹、醫院藥局",
                )

        st.divider()
        search_action_cols = st.columns([1.6, 1.2, 1.2, 1.6], gap="medium")
        run_crawl = search_action_cols[1].button(
            "開始抓取並分析",
            type="primary",
            use_container_width=True,
        )
        save_search = search_action_cols[2].button(
            "儲存目前搜尋",
            use_container_width=True,
        )

    current_signature = product_store.build_signature(
        st.session_state.search_role_rows,
        st.session_state.custom_queries_text,
        st.session_state.crawl_preset_label,
    )
    if (not current_user_is_guest) and (not st.session_state.active_saved_search_id):
        matched_saved_search = product_store.find_saved_search_by_signature(
            normalize_search_role_rows(st.session_state.search_role_rows),
            st.session_state.custom_queries_text,
            st.session_state.crawl_preset_label,
            user_id=current_user_id,
        )
        if matched_saved_search is not None:
            st.session_state.active_saved_search_id = matched_saved_search.id

    if save_search:
        if current_user_is_guest:
            st.warning("登入後才能儲存搜尋條件、追蹤新職缺與綁定收藏。")
        else:
            snapshot_for_baseline = None
            if (
                st.session_state.snapshot is not None
                and st.session_state.last_crawl_signature == current_signature
            ):
                snapshot_for_baseline = st.session_state.snapshot
            saved_search_id = product_store.save_search(
                user_id=current_user_id,
                name=current_search_name,
                rows=normalize_search_role_rows(st.session_state.search_role_rows),
                custom_queries_text=st.session_state.custom_queries_text,
                crawl_preset_label=st.session_state.crawl_preset_label,
                snapshot=snapshot_for_baseline,
                search_id=st.session_state.active_saved_search_id,
            )
            st.session_state.active_saved_search_id = saved_search_id
            st.session_state.favorite_feedback = (
                f"已儲存搜尋條件：{current_search_name}"
                if snapshot_for_baseline is not None
                else f"已儲存搜尋條件：{current_search_name}。下次抓取後會開始追蹤新職缺。"
            )
            st.rerun()

    pending_saved_search_refresh_id = st.session_state.pop(
        "pending_saved_search_refresh_id",
        None,
    )
    if run_crawl or pending_saved_search_refresh_id:
        role_targets = build_role_targets(normalize_search_role_rows(st.session_state.search_role_rows))
        runtime_settings = apply_crawl_preset(settings, crawl_preset)
        queries = build_default_queries(
            role_targets,
            keywords_per_role=crawl_preset.keywords_per_role,
        )
        queries.extend(
            [line.strip() for line in custom_queries.splitlines() if line.strip()]
        )
        queries = list(dict.fromkeys(queries))

        if not role_targets and not queries:
            st.warning("請先勾選並填寫至少一筆目標職缺，或輸入額外查詢字詞。")
            return

            crawl_status = st.status("正在抓取並分析職缺...", expanded=True)
        try:
            crawl_status.write("1. 整理搜尋條件與查詢字詞")
            pipeline = JobMarketPipeline(
                settings=runtime_settings,
                role_targets=role_targets,
                force_refresh=force_refresh,
            )
            crawl_status.write("2. 抓取來源職缺並解析原文")
            st.session_state.snapshot = pipeline.run(queries=queries)
            st.session_state.last_crawl_signature = current_signature
            crawl_status.write("3. 彙整技能地圖與工作內容統計")

            saved_search = None
            if (not current_user_is_guest) and st.session_state.active_saved_search_id:
                saved_search = product_store.get_saved_search(
                    int(st.session_state.active_saved_search_id),
                    user_id=current_user_id,
                )
            if (not current_user_is_guest) and saved_search is None:
                saved_search = product_store.find_saved_search_by_signature(
                    normalize_search_role_rows(st.session_state.search_role_rows),
                    st.session_state.custom_queries_text,
                    st.session_state.crawl_preset_label,
                    user_id=current_user_id,
                )
                if saved_search is not None:
                    st.session_state.active_saved_search_id = saved_search.id

            if (
                (not current_user_is_guest)
                and saved_search is not None
                and st.session_state.snapshot is not None
            ):
                crawl_status.write("4. 同步追蹤搜尋與新職缺通知")
                sync_result = product_store.sync_saved_search_results(
                    user_id=current_user_id,
                    search_id=saved_search.id,
                    rows=normalize_search_role_rows(st.session_state.search_role_rows),
                    custom_queries_text=st.session_state.custom_queries_text,
                    crawl_preset_label=st.session_state.crawl_preset_label,
                    snapshot=st.session_state.snapshot,
                    min_relevance_score=notification_preferences.min_relevance_score,
                    max_jobs=notification_preferences.max_jobs_per_alert,
                    create_notification=notification_preferences.site_enabled,
                )
                if sync_result["baseline_created"]:
                    st.session_state.favorite_feedback = (
                        f"已更新追蹤搜尋「{sync_result['search_name']}」，目前先建立基準，下一次會開始通知新職缺。"
                    )
                elif sync_result["new_jobs"]:
                    notification_notes: list[str] = []
                    if notification_preferences.email_enabled or notification_preferences.line_enabled:
                        delivery_result = notification_service.send_new_job_alert(
                            search_name=sync_result["search_name"],
                            new_jobs=sync_result["new_jobs"],
                            email_enabled=notification_preferences.email_enabled,
                            line_enabled=notification_preferences.line_enabled,
                            email_recipients_text=notification_preferences.email_recipients,
                            line_target=notification_preferences.line_target,
                            max_jobs=notification_preferences.max_jobs_per_alert,
                        )
                        notification_notes = list(delivery_result["notes"])
                        if sync_result["notification_id"]:
                            product_store.update_notification_delivery(
                                int(sync_result["notification_id"]),
                                user_id=current_user_id,
                                email_sent=bool(delivery_result["email_sent"]),
                                line_sent=bool(delivery_result["line_sent"]),
                                delivery_notes=list(delivery_result["notes"]),
                            )
                    st.session_state.favorite_feedback = (
                        f"追蹤搜尋「{sync_result['search_name']}」有 {len(sync_result['new_jobs'])} 筆新職缺。"
                    )
                    if notification_notes:
                        st.session_state.favorite_feedback += " " + " ".join(notification_notes)
                else:
                    st.session_state.favorite_feedback = (
                        f"追蹤搜尋「{sync_result['search_name']}」本次沒有新職缺。"
                    )
            crawl_status.update(label="抓取與分析完成", state="complete", expanded=False)
        except Exception:
            crawl_status.update(label="抓取與分析失敗", state="error", expanded=True)
            raise

    snapshot: MarketSnapshot | None = st.session_state.snapshot
    current_role_targets = build_role_targets(
        normalize_search_role_rows(st.session_state.search_role_rows)
    )
    with hero_placeholder.container():
        render_hero(snapshot, current_role_targets)
    if st.session_state.favorite_feedback:
        st.success(st.session_state.favorite_feedback)
        st.session_state.favorite_feedback = ""

    if snapshot is None:
        st.info("按下左側的「開始抓取並分析」，系統會建立最新的職缺快照。")
        return

    cache_snapshot_views(snapshot)
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
    unread_notification_count = (
        product_store.unread_notification_count(user_id=current_user_id)
        if not current_user_is_guest
        else 0
    )
    active_saved_search = None
    if st.session_state.active_saved_search_id and not current_user_is_guest:
        active_saved_search = product_store.get_saved_search(
            int(st.session_state.active_saved_search_id),
            user_id=current_user_id,
        )
    parsed_job_count = int(
        (
            (job_frame["work_content_count"] > 0)
            | (job_frame["required_skill_count"] > 0)
        ).sum()
    ) if not job_frame.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("總職缺數", len(job_frame))
    col2.metric("技能數", len(skill_frame))
    col3.metric("資料來源", job_frame["source"].nunique() if not job_frame.empty else 0)
    col4.metric("已解析原文", parsed_job_count)

    low_relevance_notes = [
        error for error in snapshot.errors if "低相關職缺" in str(error)
    ]
    other_snapshot_errors = [
        error for error in snapshot.errors if "低相關職缺" not in str(error)
    ]

    status_cols = st.columns([1.15, 1.85], gap="small")
    with status_cols[0]:
        st.caption(f"最後更新：{snapshot.generated_at}")
    with status_cols[1]:
        if low_relevance_notes:
            st.markdown(
                (
                    "<div style='font-size:0.78rem;color:rgba(73,80,87,0.82);"
                    "text-align:right;padding-top:0.2rem;'>"
                    f"{_escape(' '.join(low_relevance_notes))}"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

    if other_snapshot_errors:
        for error in other_snapshot_errors:
            st.warning(error)

    tracking_tab_label = (
        f"追蹤中心{' · ' + str(unread_notification_count) if unread_notification_count else ''}"
    )
    main_tab_items = [
        ("overview", "職缺總覽"),
        ("assistant", "AI 助理"),
        ("resume", "履歷匹配"),
        ("tasks", "工作內容統計"),
        ("skills", "技能地圖"),
        ("sources", "來源比較"),
        ("tracking", tracking_tab_label),
        ("board", "投遞看板"),
        ("notifications", "通知設定"),
        ("export", "下載資料"),
    ]
    main_tab_labels = {tab_id: label for tab_id, label in main_tab_items}
    legacy_tab_map = {
        "職缺總覽": "overview",
        "AI 助理": "assistant",
        "履歷匹配": "resume",
        "工作內容統計": "tasks",
        "技能地圖": "skills",
        "來源比較": "sources",
        "投遞看板": "board",
        "通知設定": "notifications",
        "下載資料": "export",
    }
    pending_main_tab = st.session_state.pop("pending_main_tab_selection", "")
    if pending_main_tab:
        st.session_state.main_tab_control = pending_main_tab
    selected_main_tab = st.session_state.get(
        "main_tab_control",
        st.session_state.get("main_tab_selection", "overview"),
    )
    if str(selected_main_tab).startswith("追蹤中心"):
        selected_main_tab = "tracking"
    else:
        selected_main_tab = legacy_tab_map.get(str(selected_main_tab), str(selected_main_tab))
    if selected_main_tab not in main_tab_labels:
        fallback_tab = st.session_state.get("main_tab_selection", "overview")
        selected_main_tab = legacy_tab_map.get(str(fallback_tab), str(fallback_tab))
    if selected_main_tab not in main_tab_labels:
        selected_main_tab = "overview"
    selected_main_tab = st.pills(
        "頁面切換",
        options=[tab_id for tab_id, _label in main_tab_items],
        selection_mode="single",
        default=selected_main_tab,
        format_func=lambda tab_id: main_tab_labels.get(tab_id, tab_id),
        key="main_tab_control",
        label_visibility="collapsed",
        width="stretch",
    ) or "overview"
    st.session_state.main_tab_selection = selected_main_tab

    page_context = PageContext(
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

    if selected_main_tab == "overview":
        render_overview_page(page_context)
    elif selected_main_tab == "resume":
        render_resume_page(page_context)
    elif selected_main_tab == "assistant":
        render_assistant_page(page_context)
    elif selected_main_tab == "tasks":
        render_tasks_page(page_context)
    elif selected_main_tab == "skills":
        render_skills_page(page_context)
    elif selected_main_tab == "sources":
        render_sources_page(page_context)
    elif selected_main_tab == "tracking":
        render_tracking_page(page_context)
    elif selected_main_tab == "board":
        render_board_page(page_context)
    elif selected_main_tab == "notifications":
        render_notifications_page(page_context)
    elif selected_main_tab == "export":
        render_export_page(page_context)


if __name__ == "__main__":
    main()
