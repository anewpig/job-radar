"""Shared data and helpers for assistant launcher tabs."""

from __future__ import annotations

from ..models import JobNotification

LAUNCHER_TAB_ITEMS: list[tuple[str, str]] = [
    ("assistant", "AI 助手"),
    ("guide", "說明"),
    ("notifications", "通知"),
]

GUIDE_ITEMS: list[tuple[str, str, str, str]] = [
    ("搜尋設定", "設定目標職缺、關鍵字與抓取方式。", "overview", "回到主頁"),
    ("職缺總覽", "先縮小範圍，再比較值得深入看的職缺。", "overview", "查看總覽"),
    ("履歷匹配", "整理履歷重點，對照目前市場職缺。", "resume", "查看匹配"),
    ("AI 助理", "直接詢問技能缺口、薪資與投遞方向。", "assistant", "打開問答"),
    ("工作內容 / 技能", "看市場最常出現的技能與工作內容。", "tasks", "查看技能"),
    ("追蹤中心", "集中看通知、已儲存搜尋與收藏職缺。", "tracking", "查看追蹤"),
    ("投遞看板", "把投遞進度和收藏整理成流程。", "board", "打開看板"),
]

QUICK_PROMPTS = [
    "我該先補哪些技能？",
    "哪類職缺最適合先投？",
    "履歷還缺什麼重點？",
    "目前市場最重視什麼？",
]

GUIDE_GROUPS: list[tuple[str, tuple[str, ...]]] = [
    ("快速上手", ("搜尋設定", "職缺總覽", "AI 助理")),
    ("分析與管理", ("履歷匹配", "工作內容 / 技能", "追蹤中心", "投遞看板")),
]

PANEL_COPY = {
    "assistant": ("AI 助手", "職涯提問、技能盤點與下一步建議。"),
    "guide": ("說明", "快速找到頁面用途與常用功能入口。"),
    "notifications": ("通知", "查看最近提醒、未讀狀態與更新摘要。"),
}


def valid_launcher_tab(tab_id: str) -> str:
    """Normalize launcher tab id to supported tabs."""
    valid_tabs = {tab_key for tab_key, _ in LAUNCHER_TAB_ITEMS}
    return tab_id if tab_id in valid_tabs else "assistant"


def notification_timestamp_label(value: str) -> str:
    """Format notification timestamp for compact launcher cards."""
    cleaned = str(value or "").strip()
    if not cleaned:
        return "剛剛"
    return cleaned.replace("T", " ")[:16]


def notification_status_labels(notification: JobNotification) -> list[str]:
    """Build delivery/read status chips for one notification."""
    labels = ["未讀" if not notification.is_read else "已讀"]
    if notification.email_sent:
        labels.append("Email")
    if notification.line_sent:
        labels.append("LINE")
    if not notification.email_sent and not notification.line_sent:
        labels.append("站內通知")
    return labels


def filter_guide_groups(search_term: str) -> list[tuple[str, list[tuple[str, str, str, str]]]]:
    """Filter guide groups by a user-entered search term."""
    normalized = search_term.strip().lower()
    grouped_items: list[tuple[str, list[tuple[str, str, str, str]]]] = []
    guide_lookup = {title: item for item in GUIDE_ITEMS for title in [item[0]]}

    for group_title, group_item_titles in GUIDE_GROUPS:
        matched_items: list[tuple[str, str, str, str]] = []
        for item_title in group_item_titles:
            item = guide_lookup.get(item_title)
            if item is None:
                continue
            haystack = f"{item[0]} {item[1]} {item[2]}".lower()
            if normalized and normalized not in haystack:
                continue
            matched_items.append(item)
        if matched_items:
            grouped_items.append((group_title, matched_items))

    if normalized:
        grouped_titles = {item[0] for _, items in grouped_items for item in items}
        residual_items = [
            item
            for item in GUIDE_ITEMS
            if item[0] not in grouped_titles
            and normalized in f"{item[0]} {item[1]} {item[2]}".lower()
        ]
        if residual_items:
            grouped_items.append(("更多結果", residual_items))

    return grouped_items
