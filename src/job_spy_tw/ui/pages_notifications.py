"""提供通知設定頁面的渲染函式。"""

from __future__ import annotations

import streamlit as st

from .page_context import PageContext
from .pages_notifications_actions import (
    _clear_line_binding,
    _issue_line_bind_code,
    _refresh_line_binding,
    _save_notification_preferences,
    _send_test_email,
    _send_test_line,
)
from .pages_notifications_sections import (
    _build_notification_render_state,
    _render_notification_channel_step,
    _render_notification_destination_step,
    _render_notification_footer,
    _render_notification_rules_step,
    _render_notification_test_section,
    _render_notifications_intro,
)
from .session import apply_notification_session_state


def render_notifications_page(ctx: PageContext) -> None:
    """渲染使用者通知偏好與推播控制頁。"""
    apply_notification_session_state(
        user_id=ctx.current_user_id,
        preferences=ctx.notification_preferences,
    )
    state = _build_notification_render_state(ctx)

    with st.container(border=True, key="notifications-shell"):
        _render_notifications_intro(ctx, state)
        step_cols = st.columns(3, gap="large")
        with step_cols[0]:
            _render_notification_channel_step()

        with step_cols[1]:
            destination_actions = _render_notification_destination_step(ctx, state)

        with step_cols[2]:
            _render_notification_rules_step()

        test_actions = _render_notification_test_section(ctx, state)
        save_preferences = _render_notification_footer(
            current_user_is_guest=ctx.current_user_is_guest
        )

    if destination_actions["generate_bind_code"]:
        _issue_line_bind_code(ctx)
    if destination_actions["clear_line_binding"]:
        _clear_line_binding(ctx)
    if destination_actions["refresh_line_binding"]:
        _refresh_line_binding(ctx)
    if save_preferences:
        _save_notification_preferences(ctx)
    if test_actions["send_test_email"]:
        _send_test_email(ctx)
    if test_actions["send_test_line"]:
        _send_test_line(ctx)
