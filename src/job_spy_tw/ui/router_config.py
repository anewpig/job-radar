"""提供主應用 router 相關常數設定。"""

from __future__ import annotations

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

DRAWER_ICON_TOKENS = {
    "overview": "◌",
    "assistant": "✦",
    "resume": "▣",
    "tasks": "≣",
    "tracking": "●",
    "board": "▤",
    "sources": "◎",
    "notifications": "◍",
    "database": "⌘",
    "export": "↧",
    "backend_console": "⋯",
}

DRAWER_SECTION_SPECS: list[tuple[str, str, tuple[str, ...]]] = [
    ("workspace", "工作台", ("overview", "assistant", "resume", "tasks", "tracking", "board")),
    ("analysis", "分析與管理", ("sources", "notifications", "database", "export")),
    ("system", "系統", ("backend_console",)),
]

PAGE_SURFACE_KEYS = {
    "overview": ("overview-shell", "overview-body"),
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
    "overview-shell": {
        "name": "職缺總覽頁主卡",
        "description": "職缺總覽的外層卡片，包含頁首、篩選器、列表與分頁。",
        "layers": [
            "overview-body",
            "overview-filter-shell",
            "overview-job-card-shell-*",
            "overview-pagination-shell",
        ],
        "text_nodes": [
            ("section-kicker", "總覽頁頁首小標。"),
            ("section-title", "總覽頁主標題。"),
            ("overview-intro-desc", "總覽頁的使用者導向副標。"),
            ("overview-intro-stat-value", "頁首右側摘要數字。"),
            ("overview-filter-meta", "篩選後摘要 chip 列。"),
        ],
    },
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
