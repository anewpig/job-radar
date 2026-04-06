"""提供搜尋設定卡片與其控制元件的渲染邏輯。"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from ..crawl_tuning import CRAWL_PRESETS, CrawlPreset, get_crawl_preset
from ..models import MarketSnapshot
from ..search_keyword_recommender import (
    autofill_role_keyword_rows,
    normalize_search_role_rows,
)
from .common import _escape, build_chip_row, render_metrics_cta
from .dev_annotations import render_dev_card_annotation
from .search import (
    _default_search_row,
    _next_search_priority,
    _search_widget_key,
    split_search_rows_for_ui,
)


@dataclass(frozen=True, slots=True)
class SearchSetupState:
    """封裝本輪搜尋設定渲染後回傳的控制狀態。"""

    run_crawl: bool
    crawl_preset: CrawlPreset
    custom_queries: str
    force_refresh: bool


def _render_intro() -> None:
    """渲染搜尋設定卡片上方的標題與說明文字。"""
    st.markdown(
        f"""
<div class="section-shell search-setup-intro">
  <div class="section-title">{_escape("搜尋設定")}</div>
  <div class="section-desc">{_escape("設定想追蹤的職缺與抓取方式")}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _render_group_head(*, title: str, copy: str = "") -> None:
    """渲染搜尋欄位 / 抓取控制共用的卡片標頭。"""
    copy_markup = (
        f'<div class="search-card-copy">{_escape(copy)}</div>'
        if str(copy).strip()
        else ""
    )
    st.markdown(
        f"""
<div class="search-card-head">
  <div class="search-card-head-copy">
    <div class="search-card-title">{_escape(title)}</div>
    {copy_markup}
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _render_row_headers() -> None:
    """渲染動態搜尋列上方共用的欄位標題。"""
    with st.container(key="search-row-headers-shell"):
        field_header_cols = st.columns([1.18, 1.18, 0.72], gap="medium")
        field_header_cols[0].markdown(
            '<div class="search-row-header-label">職缺名稱</div>',
            unsafe_allow_html=True,
        )
        field_header_cols[1].markdown(
            '<div class="search-row-header-label">關鍵字</div>',
            unsafe_allow_html=True,
        )
        field_header_cols[2].markdown(
            '<div class="search-row-header-label search-row-header-label--action">加入清單</div>',
            unsafe_allow_html=True,
        )


def _row_has_content(row: dict) -> bool:
    """判斷某列是否已經有可視為一組搜尋條件的內容。"""
    return bool(str(row.get("role", "")).strip() or str(row.get("keywords", "")).strip())


def _read_single_row_widget(index: int) -> dict[str, object]:
    """讀取單一搜尋列的 widget 狀態。"""
    return {
        "enabled": True,
        "priority": int(st.session_state.get(_search_widget_key(index, "priority"), index + 1) or (index + 1)),
        "role": str(st.session_state.get(_search_widget_key(index, "role"), "")).strip(),
        "keywords": str(st.session_state.get(_search_widget_key(index, "keywords"), "")).strip(),
    }


def _prepare_search_rows_for_ui(rows: list[dict]) -> list[dict]:
    """把搜尋列整理成「已加入 rows + 最後一列可編輯 draft」的型態。"""
    committed_rows, draft_row = split_search_rows_for_ui(
        rows,
        draft_index=st.session_state.get("search_role_draft_index"),
    )
    return committed_rows + [draft_row]


def _sync_search_row_widgets(rows: list[dict]) -> None:
    """把整理後的搜尋列同步回 session widget 狀態。"""
    st.session_state.search_role_rows = rows
    st.session_state.search_role_draft_index = max(0, len(rows) - 1)
    for index, row in enumerate(rows):
        for field, fallback in _default_search_row().items():
            st.session_state[_search_widget_key(index, field)] = row.get(field, fallback)


def _replace_search_rows(rows: list[dict]) -> None:
    """把搜尋列寫回 session 並在下一輪重新同步 widget。"""
    updated_rows = normalize_search_role_rows(rows) or [_default_search_row()]
    st.session_state.search_role_rows = updated_rows
    st.session_state.search_role_draft_index = max(0, len(updated_rows) - 1)
    st.session_state.search_role_widget_refresh = updated_rows
    st.rerun()


def _commit_current_draft(*, draft_index: int, committed_rows: list[dict]) -> None:
    """把目前編輯中的搜尋列收進已加入清單，並補一列新的 draft。"""
    draft_row = normalize_search_role_rows([_read_single_row_widget(draft_index)])[0]
    if not str(draft_row.get("role", "")).strip():
        return
    committed = normalize_search_role_rows(committed_rows)
    draft_row["priority"] = _next_search_priority(committed)
    updated_rows = committed + [draft_row]
    next_draft = _default_search_row()
    next_draft["priority"] = _next_search_priority(updated_rows)
    updated_rows.append(next_draft)
    st.session_state.search_role_rows = updated_rows
    st.session_state.search_role_draft_index = len(updated_rows) - 1
    st.session_state.search_role_widget_refresh = updated_rows
    st.rerun()


def _remove_committed_role(*, remove_row_index: int, committed_rows: list[dict], draft_index: int) -> None:
    """移除指定 tag，並保留目前正在編輯的 draft。"""
    current_draft = normalize_search_role_rows([_read_single_row_widget(draft_index)])[0]
    remaining_rows = [row for index, row in enumerate(committed_rows) if index != remove_row_index]
    _replace_search_rows(remaining_rows + [current_draft])


def _edit_committed_role(*, edit_row_index: int, committed_rows: list[dict], draft_index: int) -> None:
    """把已加入 tag 載回編輯列，原本 draft 若有內容則先收回 tag 區。"""
    current_draft = normalize_search_role_rows([_read_single_row_widget(draft_index)])[0]
    remaining_rows = [row for index, row in enumerate(committed_rows) if index != edit_row_index]
    if _row_has_content(current_draft):
        current_draft["priority"] = _next_search_priority(remaining_rows)
        remaining_rows.append(current_draft)
    row_to_edit = normalize_search_role_rows([committed_rows[edit_row_index]])[0]
    row_to_edit["priority"] = _next_search_priority(remaining_rows)
    _replace_search_rows(remaining_rows + [row_to_edit])


def _render_active_role_row(draft_index: int) -> bool:
    """渲染目前可編輯的一列搜尋輸入，並回傳是否按下加入按鈕。"""
    current_role_value = str(st.session_state.get(_search_widget_key(draft_index, "role"), "")).strip()
    with st.container(key=f"search-row-shell-{draft_index}"):
        row_field_cols = st.columns([1.18, 1.18, 0.72], gap="medium")
        with row_field_cols[0].container(key=f"search-row-role-shell-{draft_index}"):
            st.markdown(
                '<div class="search-row-inline-label">職缺名稱</div>',
                unsafe_allow_html=True,
            )
            st.text_input(
                "職缺名稱",
                value=str(st.session_state.search_role_rows[draft_index].get("role", "")),
                key=_search_widget_key(draft_index, "role"),
                placeholder="藥師、韌體工程師、老師...",
                label_visibility="collapsed",
            )
        with row_field_cols[1].container(key=f"search-row-keywords-shell-{draft_index}"):
            st.markdown(
                '<div class="search-row-inline-label">關鍵字</div>',
                unsafe_allow_html=True,
            )
            st.text_input(
                "關鍵字",
                value=str(st.session_state.search_role_rows[draft_index].get("keywords", "")),
                key=_search_widget_key(draft_index, "keywords"),
                placeholder="證照、IOT應用、親和力...",
                label_visibility="collapsed",
            )
        with row_field_cols[2].container(key=f"search-row-add-action-shell-{draft_index}"):
            st.markdown(
                '<div class="search-row-inline-label search-row-inline-label--action">加入清單</div>',
                unsafe_allow_html=True,
            )
            add_search_row = st.button(
                "加入職缺",
                key="add-search-row",
                type="secondary",
                use_container_width=True,
                disabled=not current_role_value,
            )
    return add_search_row


def _render_committed_role_tags(committed_rows: list[dict]) -> tuple[int | None, int | None]:
    """把已加入的搜尋列渲染成 tag 清單，並收集編輯 / 移除操作。"""
    edit_row_index: int | None = None
    remove_row_index: int | None = None
    if not committed_rows:
        return None, None

    with st.container(key="search-role-tags-shell"):
        for index, row in enumerate(committed_rows):
            role_markup = build_chip_row(
                [str(row.get("role", "")).strip()],
                tone="accent",
                empty_text="未命名職缺",
            )
            keywords = str(row.get("keywords", "")).strip()
            keyword_markup = build_chip_row(
                [item.strip() for item in keywords.split(",") if item.strip()],
                tone="soft",
                empty_text="尚未設定關鍵字",
            )
            with st.container(key=f"search-role-tag-shell-{index}"):
                tag_cols = st.columns([1.0, 0.16, 0.16], gap="small")
                with tag_cols[0]:
                    st.markdown(
                        (
                            "<div class=\"search-role-badge-cluster\">"
                            f"{role_markup}"
                            f"{keyword_markup}"
                            "</div>"
                        ),
                        unsafe_allow_html=True,
                    )
                with tag_cols[1].container(key=f"search-role-tag-edit-shell-{index}"):
                    if st.button("編輯", key=f"edit-search-row-{index}", use_container_width=True):
                        edit_row_index = index
                with tag_cols[2].container(key=f"search-role-tag-remove-shell-{index}"):
                    if st.button("移除", key=f"remove-search-tag-{index}", use_container_width=True):
                        remove_row_index = index

    return edit_row_index, remove_row_index


def _sync_autofill(
    previous_role_rows: list[dict],
    committed_rows: list[dict],
    draft_index: int,
    keyword_recommender: object,
) -> None:
    """讀取目前輸入值、補齊推薦關鍵字，並顯示自動補齊提示。"""
    edited_roles = normalize_search_role_rows(committed_rows + [_read_single_row_widget(draft_index)])
    normalized_roles, autofilled = autofill_role_keyword_rows(
        edited_roles,
        previous_role_rows,
        keyword_recommender,
    )
    st.session_state.search_role_rows = normalized_roles
    st.session_state.search_role_draft_index = max(0, len(normalized_roles) - 1)
    if autofilled:
        st.session_state.search_role_autofilled_notice = True
        st.session_state.search_role_widget_refresh = normalized_roles
        st.rerun()
    if st.session_state.search_role_autofilled_notice:
        st.session_state.search_role_autofilled_notice = False


def _render_filters() -> tuple[CrawlPreset, str, bool, bool]:
    """渲染抓取模式、更新模式與主動作按鈕，並回傳目前設定。"""
    with st.container(key="search-controls-options-shell"):
        filter_cols = st.columns([1.16, 1.0], gap="medium")
        with filter_cols[0].container(key="crawl-preset-control-shell"):
            crawl_preset_label = st.segmented_control(
                "抓取速度",
                options=[preset.label for preset in CRAWL_PRESETS],
                selection_mode="single",
                default=st.session_state.crawl_preset_label,
                required=True,
                key="crawl_preset_label",
                label_visibility="visible",
                width="stretch",
            )

        with filter_cols[1].container(key="crawl-refresh-control-shell"):
            st.segmented_control(
                "更新模式",
                options=["使用快取", "強制更新"],
                selection_mode="single",
                default=st.session_state.crawl_refresh_mode,
                required=True,
                key="crawl_refresh_mode",
                label_visibility="visible",
                help="使用快取會直接讀取本地資料；強制更新會重新抓取來源頁面與職缺原文。",
                width="stretch",
            )

    with st.container(key="search-setup-run-shell"):
        run_crawl = st.button(
            "開始抓取並分析",
            type="primary",
            use_container_width=True,
        )

    crawl_preset = get_crawl_preset(crawl_preset_label)
    st.session_state.custom_queries_text = ""
    custom_queries = ""
    force_refresh = st.session_state.crawl_refresh_mode == "強制更新"
    return crawl_preset, custom_queries, force_refresh, run_crawl


def render_search_setup(
    *,
    snapshot: MarketSnapshot | None,
    keyword_recommender: object,
) -> SearchSetupState:
    """渲染完整的搜尋設定卡片，並回傳目前選定的抓取參數。"""
    with st.container(border=True, key="search-setup-shell"):
        render_dev_card_annotation(
            "搜尋設定主卡",
            element_id="search-setup-shell",
            description="首頁主輸入區，左側是搜尋條件與抓取方式，右側是摘要 CTA。",
            layers=[
                "search-setup-main",
                "search-fields-group-shell",
                "search-controls-group-shell",
                "metrics-cta-card",
            ],
            text_nodes=[
                ("section-title", "搜尋設定主標題。"),
                ("section-desc", "搜尋設定說明文字。"),
                ("search-card-title", "群組卡片的小標題。"),
                ("search-card-copy", "群組卡片補充說明。"),
            ],
            show_popover=True,
            popover_key="search-setup-shell",
        )
        # 左欄放搜尋表單，右欄放摘要 CTA。
        setup_shell_cols = st.columns([1.68, 0.8], gap="large")

        with setup_shell_cols[0].container(key="search-setup-main"):
            _render_intro()
            with st.container(key="search-setup-body"):
                prepared_role_rows = _prepare_search_rows_for_ui(list(st.session_state.search_role_rows))
                if prepared_role_rows != list(st.session_state.search_role_rows):
                    _sync_search_row_widgets(prepared_role_rows)
                previous_role_rows = list(st.session_state.search_role_rows)
                draft_index = len(previous_role_rows) - 1
                committed_rows = previous_role_rows[:-1]
                with st.container(border=True, key="search-fields-group-shell"):
                    render_dev_card_annotation(
                        "搜尋欄位群組卡",
                        element_id="search-fields-group-shell",
                        description="上方是一列可編輯輸入，下方是已加入的職缺與關鍵字 tag。",
                        layers=[
                            "search-row-headers-shell",
                            "search-role-rows-shell",
                            "search-role-tags-shell",
                        ],
                        text_nodes=[
                            ("search-row-header-label", "欄位表頭文字。"),
                            ("search-row-inline-label", "每個輸入框上方的小標。"),
                            ("search-role-badge-cluster", "已加入職缺的 badge / tag 群組。"),
                            ("ui-chip ui-chip--accent", "職缺名稱 tag。"),
                            ("ui-chip ui-chip--soft", "關鍵字 tag。"),
                        ],
                        show_popover=True,
                        popover_key="search-fields-group-shell",
                    )
                    _render_group_head(
                        title="想追蹤的職缺",
                    )
                    _render_row_headers()
                    with st.container(key="search-role-rows-shell"):
                        add_search_row = _render_active_role_row(draft_index)
                    edit_row_index, remove_row_index = _render_committed_role_tags(committed_rows)
                    if add_search_row:
                        _commit_current_draft(draft_index=draft_index, committed_rows=committed_rows)
                    if edit_row_index is not None:
                        _edit_committed_role(
                            edit_row_index=edit_row_index,
                            committed_rows=committed_rows,
                            draft_index=draft_index,
                        )
                    if remove_row_index is not None:
                        _remove_committed_role(
                            remove_row_index=remove_row_index,
                            committed_rows=committed_rows,
                            draft_index=draft_index,
                        )
                    _sync_autofill(previous_role_rows, committed_rows, draft_index, keyword_recommender)
                st.markdown('<div class="search-controls-group-offset"></div>', unsafe_allow_html=True)
                with st.container(border=True, key="search-controls-group-shell"):
                    render_dev_card_annotation(
                        "抓取控制群組卡",
                        element_id="search-controls-group-shell",
                        description="切換抓取速度、更新模式並送出分析。",
                        layers=[
                            "search-controls-options-shell",
                            "crawl-preset-control-shell",
                            "crawl-refresh-control-shell",
                            "search-setup-run-shell",
                        ],
                        text_nodes=[
                            ("segmented_control", "抓取速度與更新模式的切換文字。"),
                            ("開始抓取並分析", "主要送出按鈕文字。"),
                        ],
                        show_popover=True,
                        popover_key="search-controls-group-shell",
                    )
                    _render_group_head(
                        title="抓取方式",
                    )
                    crawl_preset, custom_queries, force_refresh, run_crawl = _render_filters()

        with setup_shell_cols[1].container(key="search-setup-cta"):
            render_metrics_cta(
                row_count=len(committed_rows),
                crawl_preset_label=crawl_preset.label,
                refresh_mode=st.session_state.crawl_refresh_mode,
                snapshot=snapshot,
            )

    return SearchSetupState(
        run_crawl=run_crawl,
        crawl_preset=crawl_preset,
        custom_queries=custom_queries,
        force_refresh=force_refresh,
    )
