"""處理頂部導覽列與導覽抽屜的渲染邏輯。"""

from __future__ import annotations

import streamlit as st

from .common import _escape
from .dev_annotations import render_dev_card_annotation
from .session import set_main_tab


def render_main_navigation(
    *,
    tab_items: list[tuple[str, str]],
    drawer_items: list[tuple[str, str]],
    selected_tab: str,
) -> str:
    """渲染頂部頁籤列與可展開的左側導覽抽屜。"""
    tab_labels = {tab_id: label for tab_id, label in tab_items}
    tab_ids = [tab_id for tab_id, _label in tab_items]
    drawer_open = bool(st.session_state.get("nav_drawer_open"))
    primary_fallback = st.session_state.get("last_primary_tab", "overview")
    default_tab = selected_tab if selected_tab in tab_labels else primary_fallback
    if default_tab not in tab_labels:
        default_tab = "overview"

    with st.container(key="nav-sticky-row-shell"):
        nav_cols = st.columns([1.0, 0.085], gap="small")
        with nav_cols[0].container(border=True, key="nav-tab-bar-shell"):
            render_dev_card_annotation(
                "主導覽 Sticky Bar",
                element_id="nav-tab-bar-shell",
                description="頂部主頁籤列，包含主要功能頁 tab 與狀態同步。",
                layers=[
                    "nav-tab-list-shell",
                    "main_tab_control",
                    "nav-drawer-toggle-shell",
                ],
                text_nodes=[
                    ("main_tab_control", "頂部 tab 文字本體。"),
                    ("tracking label", "追蹤中心 tab 可能附帶未讀數。"),
                    ("nav-drawer-toggle-button", "右側漢堡 / 關閉按鈕。"),
                ],
                notes=[
                    "drawer 展開後的項目會出現在 nav-drawer-panel-shell。",
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
        with nav_cols[1].container(key="nav-drawer-toggle-shell"):
            if st.button(
                "✕" if drawer_open else "☰",
                key="nav-drawer-toggle-button",
                use_container_width=True,
                type="secondary",
            ):
                st.session_state.nav_drawer_open = not drawer_open
                st.rerun()

    if chosen_tab in tab_labels:
        st.session_state.last_primary_tab = chosen_tab

    if drawer_open:
        with st.container(border=True, key="nav-drawer-panel-shell"):
            for tab_id, label in drawer_items:
                is_active = tab_id == selected_tab
                if st.button(
                    _escape(label),
                    key=f"nav-drawer-item-{tab_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    st.session_state.nav_drawer_open = False
                    set_main_tab(tab_id)
                    st.rerun()

    if selected_tab not in tab_labels and chosen_tab == default_tab:
        return selected_tab
    return chosen_tab
