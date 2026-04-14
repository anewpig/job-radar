"""提供主應用導覽資料與頁籤解析 helper。"""

from __future__ import annotations

import streamlit as st

from .navigation import render_main_navigation
from .router_config import (
    DRAWER_ICON_TOKENS,
    DRAWER_SECTION_SPECS,
    LEGACY_TAB_MAP,
    MAIN_TAB_ITEMS_BASE,
)


def build_main_tab_items(unread_notification_count: int) -> list[tuple[str, str]]:
    """建立顯示在頁面頂部的主頁籤清單。"""
    _ = unread_notification_count
    return list(MAIN_TAB_ITEMS_BASE)


def build_drawer_items(
    unread_notification_count: int,
    *,
    show_backend_console: bool,
) -> list[tuple[str, str]]:
    """建立顯示在 hamburger drawer 內的完整功能清單。"""
    items = [
        *build_main_tab_items(unread_notification_count),
        (
            "tracking",
            f"追蹤中心{' · ' + str(unread_notification_count) if unread_notification_count else ''}",
        ),
        ("sources", "來源比較"),
        ("database", "資料庫報告"),
        ("notifications", "通知設定"),
        ("export", "下載資料"),
    ]
    if show_backend_console:
        items.insert(-1, ("backend_console", "後端控制台"))
    return items


def build_drawer_sections(
    unread_notification_count: int,
    *,
    show_backend_console: bool,
) -> list[dict[str, object]]:
    """把 drawer items 整理成帶分組與 icon 的浮動面板結構。"""
    drawer_labels = {
        tab_id: label
        for tab_id, label in build_drawer_items(
            unread_notification_count,
            show_backend_console=show_backend_console,
        )
    }
    sections: list[dict[str, object]] = []
    for section_key, section_label, tab_ids in DRAWER_SECTION_SPECS:
        items: list[dict[str, str]] = []
        for tab_id in tab_ids:
            label = drawer_labels.get(tab_id)
            if label is None:
                continue
            items.append(
                {
                    "tab_id": tab_id,
                    "label": label,
                    "icon": DRAWER_ICON_TOKENS.get(tab_id, "•"),
                }
            )
        if items:
            sections.append(
                {
                    "key": section_key,
                    "label": section_label,
                    "items": items,
                }
            )
    return sections


def peek_selected_main_tab(
    *,
    unread_notification_count: int,
    show_backend_console: bool,
) -> str:
    """在不渲染導覽元件的前提下，解析目前應顯示的頁面。"""
    drawer_labels = {
        tab_id: label
        for tab_id, label in build_drawer_items(
            unread_notification_count,
            show_backend_console=show_backend_console,
        )
    }
    pending_main_tab = st.session_state.get("pending_main_tab_selection", "")
    selected_main_tab = pending_main_tab or st.session_state.get(
        "main_tab_selection",
        st.session_state.get("main_tab_control", "overview"),
    )
    if str(selected_main_tab).startswith("追蹤中心"):
        selected_main_tab = "tracking"
    else:
        selected_main_tab = LEGACY_TAB_MAP.get(str(selected_main_tab), str(selected_main_tab))
    if selected_main_tab not in drawer_labels:
        fallback_tab = st.session_state.get("main_tab_selection", "overview")
        selected_main_tab = LEGACY_TAB_MAP.get(str(fallback_tab), str(fallback_tab))
    if selected_main_tab not in drawer_labels:
        selected_main_tab = "overview"
    return selected_main_tab


def resolve_selected_main_tab(
    *,
    unread_notification_count: int,
    show_backend_console: bool,
) -> str:
    """解析目前主頁籤，並渲染對應的導覽控制元件。"""
    main_tab_items = build_main_tab_items(unread_notification_count)
    drawer_items = build_drawer_items(
        unread_notification_count,
        show_backend_console=show_backend_console,
    )
    drawer_sections = build_drawer_sections(
        unread_notification_count,
        show_backend_console=show_backend_console,
    )
    pending_main_tab = st.session_state.pop("pending_main_tab_selection", "")
    selected_main_tab = pending_main_tab or peek_selected_main_tab(
        unread_notification_count=unread_notification_count,
        show_backend_console=show_backend_console,
    )
    if pending_main_tab and pending_main_tab in {tab_id for tab_id, _label in main_tab_items}:
        st.session_state.main_tab_control = pending_main_tab
    selected_main_tab = render_main_navigation(
        tab_items=main_tab_items,
        drawer_items=drawer_items,
        drawer_sections=drawer_sections,
        selected_tab=selected_main_tab,
    )
    st.session_state.main_tab_selection = selected_main_tab
    return selected_main_tab
