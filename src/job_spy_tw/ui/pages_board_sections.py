"""提供投遞看板頁面的 section render helper。"""

from __future__ import annotations

from datetime import date as date_value

import streamlit as st

from .common import _escape, build_chip_row
from .dev_annotations import render_dev_card_annotation
from .page_context import PageContext
from .pages_board_actions import _delete_board_card, _update_board_card

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
BOARD_STATUS_DESCRIPTIONS = {
    "未投遞": "尚未開始投遞，先整理目標與優先順序。",
    "準備中": "正在修改履歷、自傳或準備投遞材料。",
    "已投遞": "已送出申請，等待企業回覆。",
    "已面試": "已進入面試流程，持續追蹤下一步。",
    "已錄取": "收到錄取結果，進入決策與安排階段。",
    "已婉拒": "該職缺流程已結束，可保留紀錄備查。",
}
BOARD_STATUS_CLASS_NAMES = {
    "未投遞": "pending",
    "準備中": "preparing",
    "已投遞": "applied",
    "已面試": "interview",
    "已錄取": "offer",
    "已婉拒": "declined",
}


def _parse_optional_date(raw_value: str) -> date_value | None:
    cleaned = str(raw_value or "").strip()
    if not cleaned:
        return None
    try:
        return date_value.fromisoformat(cleaned)
    except ValueError:
        return None


def _resolve_recent_milestone(favorite) -> tuple[str, str]:
    dated_candidates: list[tuple[date_value, str, str]] = []
    raw_candidates: list[tuple[str, str]] = []

    for label, raw_value in (
        ("面試", favorite.interview_date),
        ("投遞", favorite.application_date),
    ):
        cleaned = str(raw_value or "").strip()
        if not cleaned:
            continue
        parsed = _parse_optional_date(cleaned)
        if parsed:
            dated_candidates.append((parsed, label, cleaned))
        else:
            raw_candidates.append((label, cleaned))

    if dated_candidates:
        _, label, value = max(dated_candidates, key=lambda item: item[0])
        return label, value
    if raw_candidates:
        return raw_candidates[0]
    return ("最近日期", "尚未安排")


def _status_class_name(status: str) -> str:
    return BOARD_STATUS_CLASS_NAMES.get(status, "default")


def _render_board_summary(ctx: PageContext) -> None:
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
    summary_cards = [
        ("收藏職缺", len(ctx.favorite_jobs), "全部流程卡", "all", "◎"),
        ("待處理", pending_count, "未投遞 / 準備中", "pending", "◌"),
        ("進行中", active_count, "已投遞 / 已面試", "active", "→"),
        ("已結束", finished_count, "已錄取 / 已婉拒", "finished", "✓"),
    ]
    for column, (label, value, hint, tone, icon) in zip(board_summary_cols, summary_cards):
        with column:
            st.markdown(
                f"""
<div class="board-summary-card board-summary-card--{tone}">
  <div class="board-summary-card-top">
    <span class="board-summary-card-icon board-summary-card-icon--{tone}">{_escape(icon)}</span>
    <span class="board-summary-card-label">{_escape(label)}</span>
  </div>
  <div class="board-summary-card-value">{_escape(str(value))}</div>
  <div class="board-summary-card-copy">{_escape(hint)}</div>
</div>
                """,
                unsafe_allow_html=True,
            )
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
        f"<div class='chip-row board-summary-chips' style='margin:0.2rem 0 0.75rem;'>{board_status_chips}</div>",
        unsafe_allow_html=True,
    )


def _render_board_kanban(ctx: PageContext) -> None:
    if not ctx.favorite_jobs:
        st.info("先收藏幾筆職缺，這裡才會形成投遞流程看板。")
        return

    filtered_favorites = ctx.favorite_jobs

    for row_index, status_row in enumerate(KANBAN_STATUS_ROWS):
        columns = st.columns(len(status_row), gap="medium")
        for column_index, (column, status) in enumerate(zip(columns, status_row)):
            status_items = [
                item for item in filtered_favorites if item.application_status == status
            ]
            with column:
                _render_status_header(
                    status=status,
                    status_items=status_items,
                    row_index=row_index,
                    column_index=column_index,
                )
                if not status_items:
                    _render_empty_status(row_index=row_index, column_index=column_index)
                for favorite in status_items:
                    _render_board_card(ctx, favorite)


def _render_status_header(
    *,
    status: str,
    status_items: list[object],
    row_index: int,
    column_index: int,
) -> None:
    status_class = _status_class_name(status)
    with st.container(border=True, key=f"board-status-shell-{row_index}-{column_index}"):
        render_dev_card_annotation(
            "看板欄位標頭卡",
            element_id=f"board-status-shell-{row_index}-{column_index}",
            description="單一投遞狀態欄位的標頭卡。",
            layers=["status heading", "status description", "status count"],
            text_nodes=[
                ("status label", "欄位狀態名稱。"),
                ("status desc", "欄位用途說明。"),
                ("status count", "欄位內職缺數量。"),
            ],
            compact=True,
            show_popover=True,
            popover_key=f"board-status-shell-{row_index}-{column_index}",
        )
        st.markdown(
            f"""
<div class="board-status-heading board-status-heading--{status_class}">
  <div class="board-status-copy">
    <div class="board-status-label board-status-label--{status_class}">{_escape(status)}</div>
    <div class="board-status-desc">{_escape(BOARD_STATUS_DESCRIPTIONS.get(status, ""))}</div>
  </div>
  <div class="board-status-count board-status-count--{status_class}">{len(status_items)} 筆</div>
</div>
            """,
            unsafe_allow_html=True,
        )


def _render_empty_status(*, row_index: int, column_index: int) -> None:
    with st.container(border=True, key=f"board-empty-shell-{row_index}-{column_index}"):
        render_dev_card_annotation(
            "看板空狀態卡",
            element_id=f"board-empty-shell-{row_index}-{column_index}",
            description="某個投遞欄位目前沒有卡片時的空狀態提示。",
            text_nodes=[
                ("board-empty-copy", "空狀態提示文字。"),
            ],
            compact=True,
            show_popover=True,
            popover_key=f"board-empty-shell-{row_index}-{column_index}",
        )
        st.markdown(
            """
<div class="board-empty-shell">
  <div class="board-empty-copy">目前這個階段還沒有職缺，之後更新投遞進度後會顯示在這裡。</div>
</div>
            """,
            unsafe_allow_html=True,
        )


def _render_board_card(ctx: PageContext, favorite) -> None:
    with st.container(key=f"board-card-container-{favorite.id}"):
        card_open_key = f"board_card_open_{favorite.id}"
        if card_open_key not in st.session_state:
            st.session_state[card_open_key] = False
        status_class = _status_class_name(favorite.application_status)

        render_dev_card_annotation(
            "投遞看板卡片",
            element_id=f"board-card-container-{favorite.id}",
            description="單張投遞流程卡片，固定顯示看板摘要，展開後才會看到可編輯欄位。",
            layers=[
                "board-card-summary",
                "board-card-head",
                "board-card-signal-panel",
                "board-card-meta",
                "board-card-timeline",
                "board-card-editor",
            ],
            text_nodes=[
                ("board-card-title", "看板卡的職缺標題。"),
                ("board-card-company", "公司名稱。"),
                ("ui-chip ui-chip--soft", "狀態 / 來源 / 搜尋條件 / 地點 tag。"),
                ("ui-chip ui-chip--warm", "投遞 / 面試日期 tag。"),
                ("board-card-signal-value", "目前狀態與最近重要日期摘要。"),
                ("board-card-flag", "是否有備註 / 面試紀錄的指示文字。"),
            ],
            compact=True,
            show_popover=True,
            popover_key=f"board-card-container-{favorite.id}",
        )
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
        milestone_label, milestone_value = _resolve_recent_milestone(favorite)
        notes_filled = bool(str(favorite.notes or "").strip())
        interview_notes_filled = bool(str(favorite.interview_notes or "").strip())
        with st.container(key=f"board-card-shell-{status_class}-{favorite.id}"):
            with st.container(key=f"board-card-summary-row-{favorite.id}"):
                summary_cols = st.columns([1.02, 0.98], gap="medium")
                with summary_cols[0]:
                    st.markdown(
                        f"""
<div class="board-card-main">
  <div class="board-card-icon">✦</div>
  <div class="board-card-head">
    <div class="board-card-title">{_escape(favorite.title)}</div>
    <div class="board-card-company">{_escape(favorite.company)}</div>
  </div>
</div>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.container(key=f"board-card-toggle-inline-shell-{favorite.id}"):
                        toggle_editor = st.button(
                            "收起編輯" if st.session_state[card_open_key] else "更新資料",
                            key=f"board-card-toggle-{favorite.id}",
                            use_container_width=False,
                        )
                with summary_cols[1]:
                    st.markdown(
                        f"""
<div class="board-card-signal-panel board-card-signal-panel--{status_class}">
  <div class="board-card-signal-label">目前狀態</div>
  <div class="board-status-pill board-status-pill--{status_class}">{_escape(favorite.application_status)}</div>
  <div class="board-card-signal-meta">{_escape(milestone_label)} · {_escape(milestone_value)}</div>
  <div class="board-card-signal-flags">
    <span class="board-card-flag {'is-filled' if notes_filled else 'is-empty'}">備註：{'已填' if notes_filled else '未填'}</span>
    <span class="board-card-flag {'is-filled' if interview_notes_filled else 'is-empty'}">面試紀錄：{'已填' if interview_notes_filled else '未填'}</span>
  </div>
</div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown(
                f"<div class='chip-row board-card-meta'>{meta_markup}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='chip-row board-card-timeline'>{timeline_markup}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
<div class="board-card-footer">
  <a href="{_escape(favorite.job_url)}" target="_blank">查看職缺原文</a>
</div>
                """,
                unsafe_allow_html=True,
            )
        if toggle_editor:
            st.session_state[card_open_key] = not st.session_state[card_open_key]

        if st.session_state[card_open_key]:
            with st.container(key=f"board-editor-shell-{favorite.id}"):
                with st.form(f"kanban-favorite-form-{favorite.id}"):
                    status_cols = st.columns([1.15, 0.85, 0.85], gap="small")
                    next_status = status_cols[0].selectbox(
                        "狀態",
                        APPLICATION_STATUS_OPTIONS,
                        index=APPLICATION_STATUS_OPTIONS.index(favorite.application_status)
                        if favorite.application_status in APPLICATION_STATUS_OPTIONS
                        else 0,
                        key=f"kanban-status-{favorite.id}",
                    )
                    application_date_value = status_cols[1].date_input(
                        "投遞日期",
                        value=_parse_optional_date(favorite.application_date),
                        format="YYYY-MM-DD",
                        key=f"kanban-application-date-{favorite.id}",
                    )
                    interview_date_value = status_cols[2].date_input(
                        "面試日期",
                        value=_parse_optional_date(favorite.interview_date),
                        format="YYYY-MM-DD",
                        key=f"kanban-interview-date-{favorite.id}",
                    )
                    next_notes = st.text_area(
                        "備註",
                        value=favorite.notes,
                        height=92,
                        placeholder="例如：已投遞、等回覆、追蹤提醒...",
                        key=f"kanban-notes-{favorite.id}",
                    )
                    interview_notes = st.text_area(
                        "面試紀錄",
                        value=favorite.interview_notes,
                        height=100,
                        placeholder="例如：面試官提到的重點、後續安排...",
                        key=f"kanban-interview-notes-{favorite.id}",
                    )
                    action_cols = st.columns(2, gap="small")
                    save_card = action_cols[0].form_submit_button(
                        "儲存卡片",
                        use_container_width=True,
                    )
                    delete_card = action_cols[1].form_submit_button(
                        "刪除卡片",
                        use_container_width=True,
                    )
                if save_card:
                    st.session_state[card_open_key] = False
                    _update_board_card(
                        ctx,
                        favorite,
                        next_status=next_status,
                        next_notes=next_notes,
                        application_date=application_date_value.isoformat()
                        if application_date_value
                        else "",
                        interview_date=interview_date_value.isoformat()
                        if interview_date_value
                        else "",
                        interview_notes=interview_notes,
                    )
                if delete_card:
                    _delete_board_card(ctx, favorite)
