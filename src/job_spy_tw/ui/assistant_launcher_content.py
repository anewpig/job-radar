"""AI launcher 內容層的相容入口。"""

from __future__ import annotations

from collections.abc import Callable

from ..models import JobNotification
from .assistant_launcher_data import LAUNCHER_TAB_ITEMS, valid_launcher_tab
from .assistant_launcher_header import render_panel_header
from .assistant_launcher_tab_assistant import render_assistant_tab
from .assistant_launcher_tab_guide import render_guide_tab
from .assistant_launcher_tab_notifications import render_notifications_tab


def render_tab_content(
    tab_id: str,
    *,
    notifications: list[JobNotification],
    unread_notification_count: int,
    current_user_is_guest: bool,
    on_submit_question: Callable[[str], None],
    on_switch_page: Callable[[str], None],
) -> None:
    """Dispatch launcher body rendering by active tab."""
    if tab_id == "assistant":
        render_assistant_tab(
            on_submit_question=on_submit_question,
            on_switch_page=on_switch_page,
        )
        return
    if tab_id == "guide":
        render_guide_tab(on_switch_page=on_switch_page)
        return
    render_notifications_tab(
        notifications=notifications,
        unread_notification_count=unread_notification_count,
        current_user_is_guest=current_user_is_guest,
        on_switch_page=on_switch_page,
    )


__all__ = [
    "LAUNCHER_TAB_ITEMS",
    "render_panel_header",
    "render_tab_content",
    "valid_launcher_tab",
]
