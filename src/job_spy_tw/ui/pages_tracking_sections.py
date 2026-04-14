"""提供追蹤中心頁面的 section render helper。"""

from __future__ import annotations

import streamlit as st

from .common import build_chip_row
from .dev_annotations import render_dev_card_annotation
from .page_context import PageContext
from .pages_tracking_actions import (
    _delete_saved_search,
    _load_saved_search,
    _mark_all_notifications_read,
    _open_board,
    _overwrite_saved_search,
    _refresh_saved_search,
    _remove_favorite_shortcut,
)


def _render_tracking_summary(ctx: PageContext) -> None:
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


def _render_notification_stream(ctx: PageContext) -> None:
    with st.container(border=True):
        render_dev_card_annotation(
            "新職缺通知流卡",
            element_id="tracking-notification-stream",
            description="追蹤中心上半部的通知流卡片。",
            layers=[
                "notification header",
                "notification item cards",
                "mark-all-notifications-read",
            ],
            text_nodes=[
                ("新職缺通知", "通知流主標題。"),
                ("Email 推播 / LINE 推播", "通道狀態小字。"),
                ("ui-chip ui-chip--warm", "通知狀態 tag。"),
            ],
            show_popover=True,
            popover_key="tracking-notification-stream",
        )
        header_cols = st.columns([2.4, 1], gap="medium")
        header_cols[0].markdown("**新職缺通知**")
        header_cols[0].caption(
            f"Email 推播：{'已可用' if ctx.notification_service.email_configured else '未就緒'} ｜ "
            f"LINE 推播：{'已可用' if ctx.notification_service.line_configured else '未就緒'}"
        )
        if ctx.unread_notification_count and header_cols[1].button(
            "全部標為已讀",
            key="mark-all-notifications-read",
            use_container_width=True,
        ):
            _mark_all_notifications_read(ctx)

        if not ctx.notifications:
            st.info("目前還沒有新職缺通知。先儲存搜尋條件，再用同一組搜尋重新抓取，就會開始追蹤。")
            return

        for notification in ctx.notifications:
            _render_notification_item(notification)


def _render_notification_item(notification) -> None:
    with st.container(border=True):
        render_dev_card_annotation(
            "通知紀錄卡",
            element_id=f"tracking-notification-item-{notification.id}",
            description="單次新職缺通知的紀錄卡。",
            layers=[
                "saved_search_name",
                "status chips",
                "new job expander",
            ],
            text_nodes=[
                ("saved_search_name", "通知對應的搜尋名稱。"),
                ("created_at / new_jobs_count", "通知建立時間與筆數。"),
                ("ui-chip ui-chip--warm", "未讀 / Email / LINE 狀態 tag。"),
            ],
            compact=True,
            show_popover=True,
            popover_key=f"tracking-notification-item-{notification.id}",
        )
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
                st.caption(f"另有 {len(notification.new_jobs) - 8} 筆新職缺可到下載資料或職缺總覽查看。")


def _render_saved_searches_section(ctx: PageContext) -> None:
    st.markdown("**已儲存的搜尋條件**")
    st.caption("這裡保留每一組追蹤設定，也能直接重新抓取最新結果。")
    if not ctx.saved_searches:
        st.info("目前沒有已儲存的搜尋條件。")
        return

    for saved_search in ctx.saved_searches:
        _render_saved_search_card(ctx, saved_search)


def _render_saved_search_card(ctx: PageContext, saved_search) -> None:
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
        render_dev_card_annotation(
            "已儲存搜尋卡",
            element_id=f"tracking-saved-search-{saved_search.id}",
            description="單組已儲存搜尋卡，含名稱、tag、統計與操作按鈕。",
            layers=[
                "saved-search title",
                "role chips",
                "saved-search stats",
                "saved-search actions",
            ],
            text_nodes=[
                ("saved_search.name", "搜尋名稱。"),
                ("ui-chip ui-chip--warm", "目標職缺 role tag。"),
                ("ui-chip ui-chip--soft", "模式 / 上次抓取 / 職缺數等統計 tag。"),
                ("搜尋名稱", "可編輯的搜尋名稱欄位標籤。"),
            ],
            compact=True,
            show_popover=True,
            popover_key=f"tracking-saved-search-{saved_search.id}",
        )
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
            _load_saved_search(ctx, saved_search)
        if action_cols[1].button(
            "立即重新抓取",
            key=f"tracking-refresh-{saved_search.id}",
            type="primary",
            use_container_width=True,
        ):
            _refresh_saved_search(ctx, saved_search)
        if action_cols[2].button(
            "用目前搜尋設定覆蓋",
            key=f"tracking-update-{saved_search.id}",
            use_container_width=True,
        ):
            _overwrite_saved_search(ctx, saved_search, edited_name=edited_name)
        if action_cols[3].button(
            "刪除搜尋",
            key=f"tracking-delete-{saved_search.id}",
            use_container_width=True,
        ):
            _delete_saved_search(ctx, saved_search)
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


def _render_favorite_shortcuts_section(ctx: PageContext) -> None:
    header_cols = st.columns([1.6, 1], gap="medium")
    header_cols[0].markdown("**收藏捷徑**")
    header_cols[0].caption("這裡只保留快速瀏覽；要更新狀態與備註，建議到投遞看板。")
    if header_cols[1].button(
        "前往投遞看板",
        key="tracking-go-board",
        use_container_width=True,
    ):
        _open_board()

    if not ctx.favorite_jobs:
        st.info("你收藏的職缺會出現在這裡。")
        return

    for favorite in ctx.favorite_jobs[:8]:
        with st.container(border=True):
            render_dev_card_annotation(
                "收藏捷徑卡",
                element_id=f"tracking-favorite-shortcut-{favorite.id}",
                description="追蹤中心右側的收藏職缺快速卡。",
                layers=[
                    "favorite title",
                    "favorite chips",
                    "favorite note",
                    "favorite actions",
                ],
                text_nodes=[
                    ("favorite.title", "職缺標題。"),
                    ("favorite.company", "公司名稱。"),
                    ("ui-chip ui-chip--warm", "狀態 / 來源 / 搜尋名稱 / 地點 tag。"),
                ],
                compact=True,
                show_popover=True,
                popover_key=f"tracking-favorite-shortcut-{favorite.id}",
            )
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
                _remove_favorite_shortcut(ctx, favorite)

    if len(ctx.favorite_jobs) > 8:
        st.caption(f"還有另外 {len(ctx.favorite_jobs) - 8} 筆收藏，已收在投遞看板。")
