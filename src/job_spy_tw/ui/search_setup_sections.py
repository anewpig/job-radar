"""搜尋設定卡片的 UI sections。"""

from __future__ import annotations

import streamlit as st

from ..crawl_tuning import CRAWL_PRESETS, CrawlPreset, get_crawl_preset
from .common import _escape, build_chip_row
from .search import _search_widget_key


def render_intro() -> None:
    """渲染搜尋設定卡片上方的標題與說明文字。"""
    st.markdown(
        f"""
<div class="section-shell search-setup-intro">
  <div class="section-kicker">{_escape("Job Search Setup")}</div>
  <div class="section-title">{_escape("搜尋設定")}</div>
  <div class="section-desc">{_escape("設定想追蹤的職缺與分析條件")}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_row_headers() -> None:
    """渲染動態搜尋列上方共用的欄位標題。"""
    with st.container(key="search-row-headers-shell"):
        field_header_cols = st.columns([1.1, 0.9, 0.5], gap="medium")
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


def render_active_role_row(*, draft_index: int, search_role_rows: list[dict]) -> bool:
    """渲染目前可編輯的一列搜尋輸入，並回傳是否按下加入按鈕。"""
    current_role_value = str(st.session_state.get(_search_widget_key(draft_index, "role"), "")).strip()
    with st.container(key=f"search-row-shell-{draft_index}"):
        row_field_cols = st.columns([1.1, 0.9, 0.5], gap="medium")
        with row_field_cols[0].container(key=f"search-row-role-shell-{draft_index}"):
            st.markdown(
                '<div class="search-row-inline-label">職缺名稱</div>',
                unsafe_allow_html=True,
            )
            st.text_input(
                "職缺名稱",
                value=str(search_role_rows[draft_index].get("role", "")),
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
                value=str(search_role_rows[draft_index].get("keywords", "")),
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


def render_committed_role_tags(committed_rows: list[dict]) -> tuple[int | None, int | None]:
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
                            f"<div class=\"search-role-badge-row search-role-badge-row--role\">{role_markup}</div>"
                            f"<div class=\"search-role-badge-row search-role-badge-row--keywords\">{keyword_markup}</div>"
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


def render_filters() -> tuple[CrawlPreset, str, bool, bool]:
    """渲染抓取模式、更新模式與主動作按鈕，並回傳目前設定。"""
    with st.container(key="search-controls-options-shell"):
        filter_cols = st.columns([1.16, 1.0], gap="medium")
        with filter_cols[0].container(key="crawl-preset-control-shell"):
            crawl_preset_label = st.segmented_control(
                "抓取速度",
                options=[preset.label for preset in CRAWL_PRESETS],
                selection_mode="single",
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
