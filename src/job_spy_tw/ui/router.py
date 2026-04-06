"""提供主應用外框的導覽選項與頁面分派輔助函式。"""

from __future__ import annotations

import streamlit as st

from .dev_annotations import render_dev_card_annotation
from .navigation import render_main_navigation

MAIN_TAB_ITEMS_BASE: list[tuple[str, str]] = [
    ("overview", "職缺總覽"),
    ("assistant", "AI 助理"),
    ("resume", "履歷匹配"),
    ("tasks", "工作內容 / 技能"),
    ("board", "投遞看板"),
]

LEGACY_TAB_MAP = {
    "職缺總覽": "overview",
    "AI 助理": "assistant",
    "履歷匹配": "resume",
    "工作內容統計": "tasks",
    "工作內容 / 技能": "tasks",
    "技能地圖": "tasks",
    "來源比較": "sources",
    "資料庫報告": "database",
    "投遞看板": "board",
    "通知設定": "notifications",
    "後端控制台": "backend_console",
    "後端營運": "backend_ops",
    "下載資料": "export",
}

PAGE_SURFACE_KEYS = {
    "resume": ("resume-shell", "resume-body"),
    "assistant": ("assistant-shell", "assistant-body"),
    "tasks": ("tasks-shell", "tasks-body"),
    "skills": ("skills-shell", "skills-body"),
    "sources": ("sources-shell", "sources-body"),
    "tracking": ("tracking-shell", "tracking-body"),
    "board": ("board-shell", "board-body"),
    "backend": ("backend-shell", "backend-body"),
    "backend_ops": ("backend-ops-shell", "backend-ops-body"),
    "backend_console": ("backend-console-shell", "backend-console-body"),
}

PAGE_SHELL_METADATA = {
    "resume-shell": {
        "name": "履歷匹配頁主卡",
        "description": "履歷上傳、履歷摘要、缺口分析與推薦職缺的共同外框。",
        "layers": [
            "resume-body",
            "resume_match_form",
            "resume-summary-card",
            "resume-gap-summary-card",
            "resume recommendation cards",
        ],
        "text_nodes": [
            ("section-kicker", "頁首小標。"),
            ("section-title", "頁面主標題。"),
            ("section-desc", "頁面說明文字。"),
        ],
    },
    "assistant-shell": {
        "name": "AI 助理頁主卡",
        "description": "個人化背景、快速提問、問答紀錄與報告輸出的共同外框。",
        "layers": [
            "assistant-body",
            "assistant-profile-card-shell",
            "assistant-quick-ask-card-shell",
            "assistant history cards",
        ],
        "text_nodes": [
            ("section-kicker", "頁首小標。"),
            ("section-title", "頁面主標題。"),
            ("chip-row / ui-chip", "AI 助理頁上方的個人化背景 tag。"),
        ],
    },
    "tasks-shell": {
        "name": "工作內容 / 技能頁主卡",
        "description": "工作內容統計與技能地圖兩大區塊的共用外框。",
        "layers": [
            "tasks-body",
            "task-summary-card",
            "skill-summary-card",
            "chart sections",
        ],
        "text_nodes": [
            ("section-kicker", "頁首小標。"),
            ("section-title", "頁面主標題。"),
            ("section-desc", "頁面說明文字。"),
        ],
    },
    "sources-shell": {
        "name": "來源比較頁主卡",
        "description": "來源比較圖表與表格的共用外框。",
        "layers": [
            "sources-body",
            "source summary chart",
            "source role distribution chart",
            "detail expander",
        ],
        "text_nodes": [
            ("section-kicker", "頁首小標。"),
            ("section-title", "頁面主標題。"),
            ("section-desc", "頁面說明文字。"),
        ],
    },
    "tracking-shell": {
        "name": "追蹤中心頁主卡",
        "description": "通知流、已儲存搜尋與收藏捷徑的共同外框。",
        "layers": [
            "tracking-body",
            "tracking notification stream",
            "saved search cards",
            "favorite shortcut cards",
        ],
        "text_nodes": [
            ("section-kicker", "頁首小標。"),
            ("section-title", "頁面主標題。"),
            ("section-desc", "頁面說明文字。"),
            ("chip-row / ui-chip", "追蹤中心上方的導覽提示 tag。"),
        ],
    },
    "board-shell": {
        "name": "投遞看板頁主卡",
        "description": "投遞流程看板整頁的共用外框。",
        "layers": [
            "board-body",
            "board-status-shell-*",
            "board-card-container-*",
            "board-editor-shell-*",
        ],
        "text_nodes": [
            ("section-kicker", "頁首小標。"),
            ("section-title", "頁面主標題。"),
            ("section-desc", "頁面說明文字。"),
            ("chip-row / ui-chip", "看板上方的導覽提示 tag。"),
        ],
    },
    "backend-ops-shell": {
        "name": "後端營運頁主卡",
        "description": "後端營運狀態、queue 與 scheduler / worker 資訊的共用外框。",
        "layers": [
            "backend-ops-body",
            "runtime signal cards",
            "saved search due table",
            "queue table",
            "snapshot table",
        ],
        "text_nodes": [
            ("section-kicker", "頁首小標。"),
            ("section-title", "頁面主標題。"),
            ("section-desc", "頁面說明文字。"),
        ],
    },
    "backend-shell": {
        "name": "後端架構頁主卡",
        "description": "後端架構說明頁的共用外框。",
        "layers": [
            "backend-body",
            "architecture sections",
        ],
        "text_nodes": [
            ("section-kicker", "頁首小標。"),
            ("section-title", "頁面主標題。"),
            ("section-desc", "頁面說明文字。"),
        ],
    },
    "backend-console-shell": {
        "name": "後端控制台頁主卡",
        "description": "整合 runtime、營運與架構說明的總入口外框。",
        "layers": [
            "backend-console-body",
            "current query runtime",
            "backend operations",
            "backend architecture",
        ],
        "text_nodes": [
            ("section-kicker", "頁首小標。"),
            ("section-title", "頁面主標題。"),
            ("section-desc", "頁面說明文字。"),
        ],
    },
}


def build_main_tab_items(unread_notification_count: int) -> list[tuple[str, str]]:
    """建立顯示在頁面頂部的主頁籤清單。"""
    tracking_label = (
        f"追蹤中心{' · ' + str(unread_notification_count) if unread_notification_count else ''}"
    )
    return [
        *MAIN_TAB_ITEMS_BASE[:4],
        ("tracking", tracking_label),
        *MAIN_TAB_ITEMS_BASE[4:],
    ]


def build_drawer_items(
    unread_notification_count: int,
    *,
    show_backend_console: bool,
) -> list[tuple[str, str]]:
    """建立顯示在 hamburger drawer 內的完整功能清單。"""
    items = [
        *build_main_tab_items(unread_notification_count),
        ("sources", "來源比較"),
        ("database", "資料庫報告"),
        ("notifications", "通知設定"),
        ("export", "下載資料"),
    ]
    if show_backend_console:
        items.insert(-1, ("backend_console", "後端控制台"))
    return items


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
        selected_tab=selected_main_tab,
    )
    st.session_state.main_tab_selection = selected_main_tab
    return selected_main_tab


def _render_page_in_surface(shell_key: str, body_key: str, render_fn, page_context) -> None:
    """用共用 surface shell 包住頁面內容，讓各功能頁有一致的大卡片底板。"""
    with st.container(border=True, key=shell_key):
        metadata = PAGE_SHELL_METADATA.get(shell_key)
        if metadata is not None:
            render_dev_card_annotation(
                metadata["name"],
                element_id=shell_key,
                description=metadata["description"],
                layers=metadata["layers"],
                text_nodes=metadata["text_nodes"],
                show_popover=True,
                popover_key=shell_key,
            )
        with st.container(key=body_key):
            render_fn(page_context)


def dispatch_main_tab(selected_main_tab: str, page_context) -> None:
    """依目前主頁籤把控制權分派到對應頁面渲染函式。"""
    if selected_main_tab == "overview":
        from .pages_market import render_overview_page

        render_overview_page(page_context)
    elif selected_main_tab == "resume":
        from .pages_resume_assistant import render_resume_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["resume"], render_resume_page, page_context)
    elif selected_main_tab == "assistant":
        from .pages_resume_assistant import render_assistant_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["assistant"], render_assistant_page, page_context)
    elif selected_main_tab == "tasks":
        from .pages_market import render_tasks_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["tasks"], render_tasks_page, page_context)
    elif selected_main_tab == "skills":
        from .pages_market import render_tasks_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["tasks"], render_tasks_page, page_context)
    elif selected_main_tab == "sources":
        from .pages_market import render_sources_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["sources"], render_sources_page, page_context)
    elif selected_main_tab == "tracking":
        from .pages_product import render_tracking_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["tracking"], render_tracking_page, page_context)
    elif selected_main_tab == "board":
        from .pages_product import render_board_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["board"], render_board_page, page_context)
    elif selected_main_tab == "notifications":
        from .pages_product import render_notifications_page

        render_notifications_page(page_context)
    elif selected_main_tab == "database":
        from .pages_database import render_database_page

        render_database_page(page_context)
    elif selected_main_tab == "backend_console":
        from .pages_backend_console import render_backend_console_page

        _render_page_in_surface(
            *PAGE_SURFACE_KEYS["backend_console"],
            render_backend_console_page,
            page_context,
        )
    elif selected_main_tab == "backend_ops":
        from .pages_backend_operations import render_backend_operations_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["backend_ops"], render_backend_operations_page, page_context)
    elif selected_main_tab == "backend":
        from .pages_backend_architecture import render_backend_architecture_page

        _render_page_in_surface(*PAGE_SURFACE_KEYS["backend"], render_backend_architecture_page, page_context)
    elif selected_main_tab == "export":
        from .pages_market import render_export_page

        render_export_page(page_context)
