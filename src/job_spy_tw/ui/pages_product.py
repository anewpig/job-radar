"""提供追蹤中心、投遞看板與通知設定頁面的渲染函式。"""

from __future__ import annotations

import streamlit as st

from ..models import JobListing, NotificationPreference
from .common import build_chip_row, mask_identifier, render_section_header, _escape
from .page_context import PageContext
from .search import get_committed_search_rows
from .session import apply_notification_session_state, set_main_tab

APPLICATION_STATUS_OPTIONS = [
    "未投遞",
    "準備中",
    "已投遞",
    "已面試",
    "已婉拒",
    "已錄取",
]
KANBAN_STATUS_ROWS = [
    ["未投遞", "準備中", "已投遞"],
    ["已面試", "已錄取", "已婉拒"],
]


def render_tracking_page(ctx: PageContext) -> None:
    """渲染追蹤中心，包括已儲存搜尋、通知與收藏捷徑。"""
    render_section_header(
        "追蹤中心",
        "集中看已儲存的搜尋條件、收藏職缺與最新通知，讓你之後可以用同一套設定反覆追蹤市場變化。",
        "Tracking",
    )
    if ctx.current_user_is_guest:
        st.info("登入後，這裡會顯示你自己的已儲存搜尋、收藏職缺與新職缺通知。")
    metrics = st.columns(3)
    metrics[0].metric("已儲存搜尋", len(ctx.saved_searches))
    metrics[1].metric("收藏職缺", len(ctx.favorite_jobs))
    metrics[2].metric("未讀通知", ctx.unread_notification_count)
    tracking_chips = build_chip_row(
        [
            "先看新職缺，再決定要不要追蹤",
            "每組搜尋都能直接重新抓取",
            "收藏管理集中到投遞看板更清楚",
        ],
        tone="soft",
        limit=3,
    )
    st.markdown(
        f"<div class='chip-row' style='margin:0.2rem 0 0.75rem;'>{tracking_chips}</div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        pass
        notification_header_cols = st.columns([2.4, 1], gap="medium")
        notification_header_cols[0].markdown("**新職缺通知**")
        notification_header_cols[0].caption(
            f"Email 推播：{'已可用' if ctx.notification_service.email_configured else '未就緒'} ｜ "
            f"LINE 推播：{'已可用' if ctx.notification_service.line_configured else '未就緒'}"
        )
        if ctx.unread_notification_count:
            if notification_header_cols[1].button(
                "全部標為已讀",
                key="mark-all-notifications-read",
                use_container_width=True,
            ):
                ctx.product_store.mark_all_notifications_read(user_id=ctx.current_user_id)
                set_main_tab("tracking")
                st.rerun()
        if ctx.notifications:
            for notification in ctx.notifications:
                with st.container(border=True):
                    pass
                    count = len(notification.new_jobs)
                    status_labels: list[str] = []
                    status_labels.append("未讀" if not notification.is_read else "已讀")
                    if notification.email_sent:
                        status_labels.append("Email 已送出")
                    if notification.line_sent:
                        status_labels.append("LINE 已送出")
                    if not notification.email_sent and not notification.line_sent:
                        status_labels.append("站內通知")
                    st.markdown(f"**{notification.saved_search_name}**")
                    st.caption(f"{notification.created_at} ｜ {count} 筆新職缺")
                    st.markdown(
                        f"<div class='chip-row'>{build_chip_row(status_labels, tone='warm', limit=4)}</div>",
                        unsafe_allow_html=True,
                    )
                    if notification.delivery_notes:
                        for note in notification.delivery_notes:
                            st.caption(note)
                    with st.expander("查看本次新職缺", expanded=not notification.is_read):
                        for job in notification.new_jobs[:8]:
                            st.markdown(
                                f"- [{job['title']}]({job['url']}) ｜ {job['company']} ｜ "
                                f"{job['source']} ｜ {job.get('location') or '地點未提供'}"
                            )
                        if len(notification.new_jobs) > 8:
                            st.caption(
                                f"另有 {len(notification.new_jobs) - 8} 筆新職缺可到下載資料或職缺總覽查看。"
                            )
        else:
            st.info("目前還沒有新職缺通知。先儲存搜尋條件，再用同一組搜尋重新抓取，就會開始追蹤。")

    saved_search_col, favorites_col = st.columns([1.35, 0.95], gap="large")
    with saved_search_col:
        st.markdown("**已儲存的搜尋條件**")
        st.caption("這裡保留每一組追蹤設定，也能直接重新抓取最新結果。")
        if ctx.saved_searches:
            for saved_search in ctx.saved_searches:
                search_favorites = ctx.product_store.list_favorites_for_search(
                    saved_search.id,
                    user_id=ctx.current_user_id,
                )
                role_names = [
                    str(row.get("role", "")).strip()
                    for row in (saved_search.rows or [])
                    if row.get("enabled", True) and str(row.get("role", "")).strip()
                ]
                with st.container(border=True):
                    pass
                    st.markdown(f"**{saved_search.name}**")
                    st.markdown(
                        f"<div class='chip-row'>{build_chip_row(role_names, tone='warm', limit=4, empty_text='尚未設定目標職缺')}</div>",
                        unsafe_allow_html=True,
                    )
                    saved_search_stats = [
                        f"模式 {saved_search.crawl_preset_label}",
                        f"上次抓取 {saved_search.last_run_at or '尚未抓取'}",
                        f"職缺 {saved_search.last_job_count}",
                        f"新增 {saved_search.last_new_job_count}",
                        f"收藏 {len(search_favorites)}",
                    ]
                    st.markdown(
                        f"<div class='chip-row' style='margin-top:0.55rem;'>{build_chip_row(saved_search_stats, tone='soft', limit=5)}</div>",
                        unsafe_allow_html=True,
                    )
                    edited_name = st.text_input(
                        "搜尋名稱",
                        value=saved_search.name,
                        key=f"saved-search-edit-name-{saved_search.id}",
                    )
                    action_cols = st.columns(4)
                    if action_cols[0].button(
                        "套用設定",
                        key=f"tracking-load-{saved_search.id}",
                        use_container_width=True,
                    ):
                        st.session_state.search_role_rows = saved_search.rows or ctx.default_rows
                        st.session_state.search_role_widget_refresh = (
                            saved_search.rows or ctx.default_rows
                        )
                        st.session_state.custom_queries_text = saved_search.custom_queries_text
                        st.session_state.crawl_preset_label = saved_search.crawl_preset_label
                        st.session_state.active_saved_search_id = saved_search.id
                        st.session_state.saved_search_name_input = saved_search.name
                        set_main_tab("tracking")
                        st.session_state.favorite_feedback = f"已載入搜尋條件：{saved_search.name}"
                        st.rerun()
                    if action_cols[1].button(
                        "立即重新抓取",
                        key=f"tracking-refresh-{saved_search.id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state.search_role_rows = saved_search.rows or ctx.default_rows
                        st.session_state.search_role_widget_refresh = (
                            saved_search.rows or ctx.default_rows
                        )
                        st.session_state.custom_queries_text = saved_search.custom_queries_text
                        st.session_state.crawl_preset_label = saved_search.crawl_preset_label
                        st.session_state.active_saved_search_id = saved_search.id
                        st.session_state.saved_search_name_input = saved_search.name
                        st.session_state.pending_saved_search_refresh_id = saved_search.id
                        set_main_tab("tracking")
                        st.rerun()
                    if action_cols[2].button(
                        "用目前搜尋設定覆蓋",
                        key=f"tracking-update-{saved_search.id}",
                        use_container_width=True,
                    ):
                        snapshot_for_baseline = None
                        if (
                            st.session_state.snapshot is not None
                            and st.session_state.last_crawl_signature == ctx.current_signature
                        ):
                            snapshot_for_baseline = st.session_state.snapshot
                            ctx.product_store.save_search(
                                user_id=ctx.current_user_id,
                                name=edited_name,
                                rows=get_committed_search_rows(
                                    st.session_state.search_role_rows,
                                    draft_index=st.session_state.get("search_role_draft_index"),
                                ),
                                custom_queries_text=st.session_state.custom_queries_text,
                                crawl_preset_label=st.session_state.crawl_preset_label,
                                snapshot=snapshot_for_baseline,
                                search_id=saved_search.id,
                            )
                        st.session_state.active_saved_search_id = saved_search.id
                        set_main_tab("tracking")
                        st.session_state.favorite_feedback = f"已覆蓋搜尋條件：{edited_name}"
                        st.rerun()
                    if action_cols[3].button(
                        "刪除搜尋",
                        key=f"tracking-delete-{saved_search.id}",
                        use_container_width=True,
                    ):
                        ctx.product_store.delete_saved_search(
                            saved_search.id,
                            user_id=ctx.current_user_id,
                        )
                        if st.session_state.active_saved_search_id == saved_search.id:
                            st.session_state.active_saved_search_id = None
                        set_main_tab("tracking")
                        st.session_state.favorite_feedback = f"已刪除搜尋條件：{saved_search.name}"
                        st.rerun()
                    st.caption("「用目前搜尋設定覆蓋」會以頁面上方最新的搜尋設定取代這組追蹤條件。")
                    with st.expander("查看這組搜尋的收藏職缺", expanded=False):
                        if search_favorites:
                            for favorite in search_favorites:
                                st.markdown(
                                    f"- [{favorite.title}]({favorite.job_url}) ｜ "
                                    f"{favorite.company} ｜ {favorite.application_status}"
                                )
                                if favorite.notes:
                                    st.caption(favorite.notes)
                        else:
                            st.caption("目前這組搜尋還沒有收藏職缺。")
        else:
            st.info("目前沒有已儲存的搜尋條件。")

    with favorites_col:
        header_cols = st.columns([1.6, 1], gap="medium")
        header_cols[0].markdown("**收藏捷徑**")
        header_cols[0].caption("這裡只保留快速瀏覽；要更新狀態與備註，建議到投遞看板。")
        if header_cols[1].button(
            "前往投遞看板",
            key="tracking-go-board",
            use_container_width=True,
        ):
            set_main_tab("board")
            st.rerun()
        if not ctx.favorite_jobs:
            st.info("你收藏的職缺會出現在這裡。")
        else:
            for favorite in ctx.favorite_jobs[:8]:
                with st.container(border=True):
                    pass
                    st.markdown(f"**{favorite.title}**")
                    st.caption(f"{favorite.company}")
                    st.markdown(
                        f"<div class='chip-row'>{build_chip_row([favorite.application_status, favorite.source, favorite.saved_search_name or '未綁定搜尋', favorite.location or '地點未提供'], tone='warm', limit=4)}</div>",
                        unsafe_allow_html=True,
                    )
                    if favorite.notes.strip():
                        st.caption(favorite.notes.strip())
                    st.markdown(f"[查看職缺原文]({favorite.job_url})")
                    if st.button(
                        "取消收藏",
                        key=f"tracking-remove-favorite-{favorite.id}",
                        use_container_width=True,
                    ):
                        job = ctx.jobs_by_url.get(favorite.job_url)
                        if job is not None:
                            ctx.product_store.toggle_favorite(
                                job,
                                user_id=ctx.current_user_id,
                            )
                        else:
                            ctx.product_store.toggle_favorite(
                                JobListing(
                                    source=favorite.source,
                                    title=favorite.title,
                                    company=favorite.company,
                                    location=favorite.location,
                                    salary=favorite.salary,
                                    matched_role=favorite.matched_role,
                                    url=favorite.job_url,
                                ),
                                user_id=ctx.current_user_id,
                            )
                        set_main_tab("tracking")
                        st.session_state.favorite_feedback = f"已取消收藏：{favorite.title}"
                        st.rerun()
            if len(ctx.favorite_jobs) > 8:
                st.caption(f"還有另外 {len(ctx.favorite_jobs) - 8} 筆收藏，已收在投遞看板。")


def render_board_page(ctx: PageContext) -> None:
    """渲染看板式投遞流程管理頁。"""
    render_section_header(
        "投遞流程管理看板",
        "把收藏職缺依投遞狀態分欄管理。你可以在卡片裡直接移動狀態、補備註，追蹤目前的求職進度。",
        "Application Board",
    )
    if ctx.current_user_is_guest:
        st.info("登入後才能建立自己的投遞看板，收藏職缺後就能開始管理投遞與面試紀錄。")
    board_summary_cols = st.columns(4, gap="medium")
    pending_count = sum(
        1 for item in ctx.favorite_jobs if item.application_status in {"未投遞", "準備中"}
    )
    active_count = sum(
        1 for item in ctx.favorite_jobs if item.application_status in {"已投遞", "已面試"}
    )
    finished_count = sum(
        1 for item in ctx.favorite_jobs if item.application_status in {"已錄取", "已婉拒"}
    )
    board_summary_cols[0].metric("收藏職缺", len(ctx.favorite_jobs))
    board_summary_cols[1].metric("待處理", pending_count)
    board_summary_cols[2].metric("進行中", active_count)
    board_summary_cols[3].metric("已結束", finished_count)

    board_status_chips = build_chip_row(
        [
            "從收藏一路追蹤到面試結果",
            "可直接更新狀態與備註",
            "支援依搜尋條件與來源快速篩選",
        ],
        tone="soft",
        limit=3,
    )
    st.markdown(
        f"<div class='chip-row' style='margin:0.2rem 0 0.75rem;'>{board_status_chips}</div>",
        unsafe_allow_html=True,
    )

    if not ctx.favorite_jobs:
        st.info("先收藏幾筆職缺，這裡才會形成投遞流程看板。")
        return

    filtered_favorites = ctx.favorite_jobs

    for row_index, status_row in enumerate(KANBAN_STATUS_ROWS):
        columns = st.columns(len(status_row), gap="large")
        for column_index, (column, status) in enumerate(zip(columns, status_row)):
            status_items = [
                item for item in filtered_favorites if item.application_status == status
            ]
            with column:
                with st.container(
                    border=True,
                    key=f"board-status-shell-{row_index}-{column_index}",
                ):
                    pass
                    st.markdown(f"**{status}**")
                    st.caption(f"{len(status_items)} 筆職缺")
                if not status_items:
                    with st.container(
                        border=True,
                        key=f"board-empty-shell-{row_index}-{column_index}",
                    ):
                        pass
                        st.markdown(
                            f"""
<div class="board-empty-shell">
  <div class="board-empty-copy">目前這個階段還沒有職缺，之後更新投遞進度後會顯示在這裡。</div>
</div>
                            """,
                            unsafe_allow_html=True,
                        )
                for favorite in status_items:
                    with st.container(border=True, key=f"board-card-container-{favorite.id}"):
                        pass
                        meta_items = [
                            favorite.saved_search_name or "未綁定搜尋",
                            favorite.source,
                            favorite.location or "地點未提供",
                        ]
                        if favorite.salary:
                            meta_items.append(favorite.salary)
                        timeline_labels = []
                        if favorite.application_date:
                            timeline_labels.append(f"投遞 {favorite.application_date}")
                        if favorite.interview_date:
                            timeline_labels.append(f"面試 {favorite.interview_date}")
                        meta_markup = build_chip_row(meta_items, tone="soft", limit=4)
                        timeline_markup = build_chip_row(
                            timeline_labels,
                            tone="warm",
                            limit=2,
                            empty_text="尚未設定投遞 / 面試日期",
                        )
                        notes_preview = favorite.notes.strip() or "尚未留下備註。"
                        interview_preview = (
                            favorite.interview_notes.strip() or "尚未留下紀錄。"
                        )
                        updated_label = (
                            f"最後更新：{favorite.updated_at}"
                            if favorite.updated_at
                            else "最後更新：尚未提供"
                        )
                        st.markdown(
                            f"""
<div class="board-card-shell">
  <div class="board-card-icon">✦</div>
  <div class="board-card-head">
    <div class="board-card-title">{_escape(favorite.title)}</div>
    <div class="board-card-company">{_escape(favorite.company)}</div>
  </div>
  <div class="chip-row board-card-meta">{meta_markup}</div>
  <div class="chip-row board-card-timeline">{timeline_markup}</div>
  <div class="board-card-section">
    <div class="board-card-section-title">備註</div>
    <div class="board-card-copy">{_escape(notes_preview)}</div>
  </div>
  <div class="board-card-section">
    <div class="board-card-section-title">面試紀錄</div>
    <div class="board-card-copy">{_escape(interview_preview)}</div>
  </div>
  <div class="board-card-footer">
    <div class="section-desc" style="margin:0 0 0.45rem;font-size:0.8rem;">{_escape(updated_label)}</div>
    <a href="{_escape(favorite.job_url)}" target="_blank">查看職缺原文</a>
  </div>
</div>
                            """,
                            unsafe_allow_html=True,
                        )
                        with st.container(key=f"board-editor-shell-{favorite.id}"):
                            st.markdown("**更新狀態與備註**")
                            with st.form(f"kanban-favorite-form-{favorite.id}"):
                                next_status = st.selectbox(
                                    "狀態",
                                    APPLICATION_STATUS_OPTIONS,
                                    index=APPLICATION_STATUS_OPTIONS.index(
                                        favorite.application_status
                                    )
                                    if favorite.application_status in APPLICATION_STATUS_OPTIONS
                                    else 0,
                                    key=f"kanban-status-{favorite.id}",
                                )
                                next_notes = st.text_area(
                                    "備註",
                                    value=favorite.notes,
                                    height=90,
                                    placeholder="例如：已投遞、等回覆、面試時間、追蹤提醒...",
                                    key=f"kanban-notes-{favorite.id}",
                                )
                                date_cols = st.columns(2, gap="medium")
                                application_date = date_cols[0].text_input(
                                    "投遞日期",
                                    value=favorite.application_date,
                                    placeholder="例如：2026-04-02",
                                    key=f"kanban-application-date-{favorite.id}",
                                )
                                interview_date = date_cols[1].text_input(
                                    "面試日期",
                                    value=favorite.interview_date,
                                    placeholder="例如：2026-04-10",
                                    key=f"kanban-interview-date-{favorite.id}",
                                )
                                interview_notes = st.text_area(
                                    "面試紀錄",
                                    value=favorite.interview_notes,
                                    height=100,
                                    placeholder="例如：面試官提到的重點、後續補件、下一輪安排...",
                                    key=f"kanban-interview-notes-{favorite.id}",
                                )
                                action_cols = st.columns(2)
                                save_card = action_cols[0].form_submit_button(
                                    "更新卡片",
                                    use_container_width=True,
                                )
                                delete_card = action_cols[1].form_submit_button(
                                    "刪除卡片",
                                    use_container_width=True,
                                )
                            if save_card:
                                ctx.product_store.update_favorite(
                                    user_id=ctx.current_user_id,
                                    job_url=favorite.job_url,
                                    application_status=next_status,
                                    notes=next_notes,
                                    application_date=application_date,
                                    interview_date=interview_date,
                                    interview_notes=interview_notes,
                                )
                                set_main_tab("board")
                                st.session_state.favorite_feedback = f"已更新投遞狀態：{favorite.title}"
                                st.rerun()
                            if delete_card:
                                ctx.product_store.delete_favorite(
                                    favorite.job_url,
                                    user_id=ctx.current_user_id,
                                )
                                set_main_tab("board")
                                st.session_state.favorite_feedback = f"已刪除卡片：{favorite.title}"
                                st.rerun()


def render_notifications_page(ctx: PageContext) -> None:
    """渲染使用者通知偏好與推播控制頁。"""
    apply_notification_session_state(
        user_id=ctx.current_user_id,
        preferences=ctx.notification_preferences,
    )

    site_enabled = st.session_state.notify_site_enabled
    line_target = st.session_state.notify_line_target
    line_is_bound = ctx.notification_service.is_valid_line_target(line_target)
    auto_bind_available = bool(
        ctx.settings.line_channel_secret
        and ctx.settings.public_base_url
        and ctx.notification_service.line_service_configured
    )
    channel_status_items = [
        f"站內通知 {'開啟' if site_enabled else '關閉'}",
        f"Email {'可用' if ctx.notification_service.email_service_configured else '尚未就緒'}",
        f"LINE {'已綁定' if line_is_bound else '尚未綁定'}",
        "重新抓取已儲存搜尋時會檢查新職缺",
    ]

    with st.container(border=True, key="notifications-shell"):
        pass
        st.markdown(
            f"""
<div class="section-shell notifications-intro">
  <div class="section-kicker">{_escape("Notification Settings")}</div>
  <div class="section-title">{_escape("通知設定")}</div>
  <div class="section-desc">{_escape("設定哪些新職缺值得提醒你，並決定站內、Email、LINE 哪些通道要啟用。")}</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(key="notifications-body"):
            if ctx.current_user_is_guest:
                st.info("登入後才能保存自己的通知條件，並綁定 Email 或 LINE 推播。")
            st.markdown(
                f"<div class='chip-row'>{build_chip_row(channel_status_items, tone='warm', limit=4)}</div>",
                unsafe_allow_html=True,
            )
        step_cols = st.columns(3, gap="large")
        with step_cols[0]:
            with st.container():
                pass
                st.markdown("**1. 選擇通知方式**")
                st.caption("先決定哪些提醒方式要開啟。")
                st.checkbox(
                    "站內通知",
                    key="notify_site_enabled",
                    help="重新抓取同一組已儲存搜尋後，會在站內建立新職缺通知。",
                )
                st.checkbox(
                    "Email 推播",
                    key="notify_email_enabled",
                    help="有新職缺時寄到你的通知信箱。",
                )
                st.checkbox(
                    "LINE 推播",
                    key="notify_line_enabled",
                    help="有新職缺時直接推送到 LINE。",
                )

        with step_cols[1]:
            with st.container():
                pass
                st.markdown("**2. 收件設定**")
                st.caption("只會顯示你目前有開啟的通知方式。")
                if st.session_state.notify_email_enabled:
                    if not ctx.notification_service.email_service_configured:
                        st.info("Email 推播尚未完全就緒，先填通知 Email 也可以，之後可直接啟用。")
                    st.text_input(
                        "通知 Email",
                        key="notify_email_recipients",
                        placeholder="例如：me@example.com, hr@example.com",
                        help="可填一個或多個 Email，逗號分隔。",
                    )
                if st.session_state.notify_line_enabled:
                    st.text_input(
                        "LINE 收件者 ID / 綁定 ID",
                        key="notify_line_target",
                        placeholder="例如：Uxxxxxxxxxxxx",
                        help="如果你已經有 LINE 收件者 ID，可以直接貼上。",
                    )
                    current_line_target = st.session_state.notify_line_target
                    current_line_bound = ctx.notification_service.is_valid_line_target(
                        current_line_target
                    )
                    if current_line_bound:
                        st.success(
                            "目前 LINE 已可推播："
                            + mask_identifier(current_line_target, prefix=3, suffix=4)
                        )
                    elif auto_bind_available:
                        st.caption("也可以用自動綁定，系統會幫你寫回真正的 LINE userId。")
                        bind_action_cols = st.columns(3)
                        generate_bind_code = bind_action_cols[0].button(
                            "產生綁定碼",
                            key="generate-line-bind-code",
                            use_container_width=True,
                            disabled=ctx.current_user_is_guest,
                        )
                        clear_line_binding = bind_action_cols[1].button(
                            "解除綁定",
                            key="clear-line-binding",
                            use_container_width=True,
                            disabled=ctx.current_user_is_guest,
                        )
                        refresh_line_binding = bind_action_cols[2].button(
                            "重新整理",
                            key="refresh-line-binding",
                            use_container_width=True,
                        )
                        if generate_bind_code:
                            latest_preferences = ctx.product_store.issue_line_bind_code(
                                user_id=ctx.current_user_id,
                                ttl_minutes=15,
                            )
                            st.session_state.notify_line_target = latest_preferences.line_target
                            st.session_state.favorite_feedback = "已產生新的 LINE 綁定碼。"
                            st.rerun()
                        if clear_line_binding:
                            ctx.product_store.clear_line_target(user_id=ctx.current_user_id)
                            st.session_state.notify_line_target = ""
                            st.session_state.favorite_feedback = "已解除目前的 LINE 綁定。"
                            st.rerun()
                        if refresh_line_binding:
                            latest_preferences = ctx.product_store.get_notification_preferences(
                                user_id=ctx.current_user_id
                            )
                            st.session_state.notify_line_target = latest_preferences.line_target
                            st.rerun()

                        if ctx.notification_preferences.line_bind_code:
                            st.info("把下面這串訊息傳給 LINE Bot，就能完成綁定。")
                            st.code(f"綁定 {ctx.notification_preferences.line_bind_code}")
                            if ctx.notification_preferences.line_bind_expires_at:
                                st.caption(
                                    f"有效期限到：{ctx.notification_preferences.line_bind_expires_at}"
                                )
                        else:
                            st.caption("如果你還沒綁定，可以先按上方的「產生綁定碼」。")
                    else:
                        st.info("目前先填入 LINE 收件者 ID 即可，之後也可以再補自動綁定。")
                if not st.session_state.notify_email_enabled and not st.session_state.notify_line_enabled:
                    st.caption("開啟 Email 或 LINE 推播後，這裡就會出現對應的收件設定。")

        with step_cols[2]:
            with st.container():
                pass
                st.markdown("**3. 通知條件**")
                st.caption("控制要提醒多少筆，以及哪些分數以上才通知。")
                st.slider(
                    "最低相關分數",
                    min_value=0,
                    max_value=100,
                    step=1,
                    key="notify_min_score",
                    help="低於這個分數的新職缺不會進通知。",
                )
                st.slider(
                    "每次通知最多幾筆",
                    min_value=1,
                    max_value=20,
                    step=1,
                    key="notify_max_jobs",
                )
                st.info("目前通知會在你重新抓取同一組已儲存搜尋後立即檢查。")

        st.divider()
        st.markdown("**4. 測試通知**")
        st.caption("確認設定是否能送達，不需要等到真的出現新職缺。")
        test_cols = st.columns(2)
        send_test_email = test_cols[0].button(
            "發送 Email 測試",
            use_container_width=True,
            disabled=ctx.current_user_is_guest or not st.session_state.notify_email_enabled,
        )
        send_test_line = test_cols[1].button(
            "發送 LINE 測試",
            use_container_width=True,
            disabled=ctx.current_user_is_guest or not st.session_state.notify_line_enabled,
        )

        current_email_recipients = st.session_state.notify_email_recipients
        current_line_target = st.session_state.notify_line_target
        current_line_bound = ctx.notification_service.is_valid_line_target(current_line_target)

        validation_messages: list[str] = []
        if st.session_state.notify_email_enabled and not ctx.notification_service.email_service_configured:
            validation_messages.append("平台目前尚未完成 Email 寄件設定。")
        elif st.session_state.notify_email_enabled and not ctx.notification_service.resolve_recipient_emails(
            current_email_recipients
        ):
            validation_messages.append("請先填寫至少一個通知 Email。")
        if st.session_state.notify_line_enabled and not ctx.notification_service.line_service_configured:
            validation_messages.append("平台目前尚未完成 LINE 推播設定。")
        elif st.session_state.notify_line_enabled and not current_line_bound:
            validation_messages.append("請先填寫有效的 LINE 收件者 ID，或完成 LINE 綁定。")
        for message in validation_messages:
            st.warning(message)

        st.divider()
        action_cols = st.columns([1.4, 1.2, 1.4], gap="medium")
        save_preferences = action_cols[1].button(
            "儲存通知條件",
            type="primary",
            use_container_width=True,
            disabled=ctx.current_user_is_guest,
        )
        if save_preferences:
            ctx.product_store.save_notification_preferences(
                NotificationPreference(
                    site_enabled=st.session_state.notify_site_enabled,
                    email_enabled=st.session_state.notify_email_enabled,
                    line_enabled=st.session_state.notify_line_enabled,
                    email_recipients=st.session_state.notify_email_recipients,
                    line_target=st.session_state.notify_line_target,
                    min_relevance_score=float(st.session_state.notify_min_score),
                    max_jobs_per_alert=int(st.session_state.notify_max_jobs),
                    frequency="即時",
                ),
                user_id=ctx.current_user_id,
            )
            st.session_state.favorite_feedback = "已更新通知條件設定。"
            st.rerun()

    test_payload = [
        {
            "title": "測試通知｜職缺雷達",
            "company": "System Check",
            "source": "系統測試",
            "location": "台灣",
            "salary": "",
            "url": "https://example.com/job-radar-test",
        }
    ]
    if send_test_email:
        result = ctx.notification_service.send_new_job_alert(
            search_name="通知測試",
            new_jobs=test_payload,
            email_enabled=True,
            line_enabled=False,
            email_recipients_text=st.session_state.notify_email_recipients,
            max_jobs=1,
        )
        if result["email_sent"]:
            st.success("Email 測試通知已送出。")
        else:
            st.warning("Email 測試通知未送出：" + "；".join(result["notes"]))
    if send_test_line:
        result = ctx.notification_service.send_new_job_alert(
            search_name="通知測試",
            new_jobs=test_payload,
            email_enabled=False,
            line_enabled=True,
            line_target=st.session_state.notify_line_target,
            max_jobs=1,
        )
        if result["line_sent"]:
            st.success("LINE 測試通知已送出。")
        else:
            st.warning("LINE 測試通知未送出：" + "；".join(result["notes"]))
