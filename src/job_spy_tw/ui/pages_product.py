"""提供產品工作台相關頁面的相容匯出入口。"""

from __future__ import annotations

from .pages_board import render_board_page
from .pages_notifications import render_notifications_page
from .pages_tracking import render_tracking_page

__all__ = [
    "render_board_page",
    "render_notifications_page",
    "render_tracking_page",
]
