"""頂部主頁籤列的渲染邏輯。"""

from __future__ import annotations

import streamlit as st

from .dev_annotations import render_dev_card_annotation


def render_primary_tab_bar(
    *,
    tab_items: list[tuple[str, str]],
    selected_tab: str,
) -> tuple[str, str, dict[str, str]]:
    """渲染頂部主頁籤列並回傳選中 tab 與 labels。"""
    tab_labels = {tab_id: label for tab_id, label in tab_items}
    tab_ids = [tab_id for tab_id, _label in tab_items]
    primary_fallback = st.session_state.get("last_primary_tab", "overview")
    default_tab = selected_tab if selected_tab in tab_labels else primary_fallback
    if default_tab not in tab_labels:
        default_tab = "overview"

    with st.container(key="nav-sticky-row-shell"):
        with st.container(border=True, key="nav-tab-bar-shell"):
            render_dev_card_annotation(
                "主導覽 Sticky Bar",
                element_id="nav-tab-bar-shell",
                description="頂部主頁籤列，包含主要功能頁 tab 與狀態同步。",
                layers=[
                    "nav-tab-list-shell",
                    "main_tab_control",
                ],
                text_nodes=[
                    ("main_tab_control", "頂部 tab 文字本體。"),
                ],
                notes=[
                    "更多功能入口改由右下角浮動漢堡按鈕開啟。",
                    "追蹤中心已改放到更多功能選單。",
                ],
                show_popover=True,
                popover_key="nav-tab-bar-shell",
            )
            with st.container(key="nav-tab-list-shell"):
                chosen_tab = st.pills(
                    "頁面切換",
                    options=tab_ids,
                    selection_mode="single",
                    default=default_tab,
                    format_func=lambda tab_id: tab_labels.get(tab_id, tab_id),
                    key="main_tab_control",
                    label_visibility="collapsed",
                    width="stretch",
                ) or default_tab

    return chosen_tab, default_tab, tab_labels
