"""提供搜尋設定卡片與其控制元件的渲染入口。"""

from __future__ import annotations

import streamlit as st

from ..models import MarketSnapshot
from .common import render_metrics_cta
from .dev_annotations import render_dev_card_annotation
from .search_setup_sections import (
    render_active_role_row,
    render_committed_role_tags,
    render_filters,
    render_intro,
    render_row_headers,
)
from .search_setup_state import (
    SearchSetupState,
    commit_current_draft,
    edit_committed_role,
    prepare_search_rows_for_ui,
    remove_committed_role,
    sync_autofill,
    sync_search_row_widgets,
)


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
            description="搜尋設定外框，左側是主操作面板，右側是本次搜尋摘要。",
            layers=[
                "search-setup-intro",
                "search-setup-main-panel",
                "metrics-cta-card",
            ],
            text_nodes=[
                ("section-title", "搜尋設定主標題。"),
                ("section-desc", "搜尋設定說明文字。"),
            ],
            show_popover=True,
            popover_key="search-setup-shell",
        )
        render_intro()
        # 左欄放搜尋表單，右欄放摘要 CTA。
        setup_shell_cols = st.columns([1.72, 0.68], gap="medium")

        with setup_shell_cols[0].container(key="search-setup-main"):
            with st.container(key="search-setup-body"):
                prepared_role_rows = prepare_search_rows_for_ui(list(st.session_state.search_role_rows))
                if prepared_role_rows != list(st.session_state.search_role_rows):
                    sync_search_row_widgets(prepared_role_rows)
                previous_role_rows = list(st.session_state.search_role_rows)
                draft_index = len(previous_role_rows) - 1
                committed_rows = previous_role_rows[:-1]
                with st.container(border=True, key="search-setup-main-panel"):
                    render_dev_card_annotation(
                        "搜尋設定主面板",
                        element_id="search-setup-main-panel",
                        description="左側主要操作面板，包含職缺輸入與抓取方式兩個 section。",
                        layers=[
                            "search-fields-group-shell",
                            "search-controls-group-shell",
                        ],
                        show_popover=True,
                        popover_key="search-setup-main-panel",
                    )
                    with st.container(key="search-fields-group-shell"):
                        render_dev_card_annotation(
                            "搜尋欄位區",
                            element_id="search-fields-group-shell",
                            description="輸入職缺名稱與關鍵字，並把條件收進下方 chips。",
                            layers=[
                                "search-row-headers-shell",
                                "search-role-rows-shell",
                                "search-role-tags-shell",
                            ],
                            text_nodes=[
                                ("search-row-header-label", "欄位表頭文字。"),
                                ("search-row-inline-label", "每個輸入框上方的小標。"),
                                ("search-role-badge-cluster", "已加入職缺的 badge / tag 群組。"),
                            ],
                            show_popover=True,
                            popover_key="search-fields-group-shell",
                        )
                        render_row_headers()
                        with st.container(key="search-role-rows-shell"):
                            add_search_row = render_active_role_row(
                                draft_index=draft_index,
                                search_role_rows=st.session_state.search_role_rows,
                            )
                        edit_row_index, remove_row_index = render_committed_role_tags(committed_rows)
                        if add_search_row:
                            commit_current_draft(draft_index=draft_index, committed_rows=committed_rows)
                        if edit_row_index is not None:
                            edit_committed_role(
                                edit_row_index=edit_row_index,
                                committed_rows=committed_rows,
                                draft_index=draft_index,
                            )
                        if remove_row_index is not None:
                            remove_committed_role(
                                remove_row_index=remove_row_index,
                                committed_rows=committed_rows,
                                draft_index=draft_index,
                            )
                        sync_autofill(previous_role_rows, committed_rows, draft_index, keyword_recommender)
                    with st.container(key="search-controls-group-shell"):
                        render_dev_card_annotation(
                            "抓取方式區",
                            element_id="search-controls-group-shell",
                            description="設定抓取速度與更新模式，並開始分析。",
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
                        crawl_preset, custom_queries, force_refresh, run_crawl = render_filters()

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
