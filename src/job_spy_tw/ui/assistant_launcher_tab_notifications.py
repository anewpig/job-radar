"""Notifications tab content for assistant launcher."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from ..models import JobNotification
from .assistant_launcher_data import (
    notification_status_labels,
    notification_timestamp_label,
)
from .common import _escape, build_chip_row


def render_notifications_tab(
    *,
    notifications: list[JobNotification],
    unread_notification_count: int,
    current_user_is_guest: bool,
    on_switch_page: Callable[[str], None],
) -> None:
    """Render the launcher notifications tab."""
    with st.container(key="assistant-launcher-notifications-body"):
        if current_user_is_guest:
            st.markdown(
                """
<div class="assistant-launcher-empty-state assistant-launcher-empty-state-centered">
  <div class="assistant-launcher-empty-icon">◎</div>
  <div class="assistant-launcher-empty-title">登入後可查看通知</div>
  <div class="assistant-launcher-empty-copy">
    這裡會顯示新職缺提醒、未讀狀態與站內更新。
    <a class="assistant-launcher-inline-link" href="?auth=start">前往登入</a>
  </div>
</div>
                """,
                unsafe_allow_html=True,
            )
            return

        preview_notifications = notifications[:3]
        last_timestamp = (
            notification_timestamp_label(preview_notifications[0].created_at)
            if preview_notifications
            else "目前沒有更新"
        )
        st.markdown(
            f"""
<div class="assistant-launcher-notification-summary">
  <div class="assistant-launcher-notification-summary-label">最近更新</div>
  <div class="assistant-launcher-notification-summary-title">未讀 {unread_notification_count} 筆提醒</div>
  <div class="assistant-launcher-notification-summary-copy">最後整理時間：{_escape(last_timestamp)}</div>
</div>
            """,
            unsafe_allow_html=True,
        )

        if preview_notifications:
            with st.container(key="assistant-launcher-notification-feed"):
                for index, notification in enumerate(preview_notifications, start=1):
                    count = len(notification.new_jobs)
                    chips = build_chip_row(
                        notification_status_labels(notification),
                        tone="soft",
                        limit=4,
                    )
                    note = (
                        notification.delivery_notes[0]
                        if notification.delivery_notes
                        else "可到通知設定或追蹤中心查看完整內容。"
                    )
                    st.markdown(
                        f"""
<div class="assistant-launcher-notification-card">
  <div class="assistant-launcher-notification-card-topline">通知 #{index}</div>
  <div class="assistant-launcher-notification-title">{_escape(notification.saved_search_name)}</div>
  <div class="assistant-launcher-notification-meta">{_escape(notification_timestamp_label(notification.created_at))}｜{count} 筆新職缺</div>
  <div class="chip-row">{chips}</div>
  <div class="assistant-launcher-notification-note">{_escape(note)}</div>
</div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown(
                """
<div class="assistant-launcher-empty-state assistant-launcher-empty-state-centered">
  <div class="assistant-launcher-empty-icon">✓</div>
  <div class="assistant-launcher-empty-title">目前沒有新的通知</div>
  <div class="assistant-launcher-empty-copy">等有新職缺或系統更新時，會先整理到這裡。</div>
</div>
                """,
                unsafe_allow_html=True,
            )

        if st.button(
            "打開通知中心",
            key="assistant-launcher-open-notifications",
            type="secondary",
            use_container_width=True,
        ):
            on_switch_page("notifications")
