"""提供通知設定頁面的共用操作 helper。"""

from __future__ import annotations

import streamlit as st

from ..models import NotificationPreference
from .page_context import PageContext


def _issue_line_bind_code(ctx: PageContext) -> None:
    latest_preferences = ctx.product_store.issue_line_bind_code(
        user_id=ctx.current_user_id,
        ttl_minutes=15,
    )
    st.session_state.notify_line_target = latest_preferences.line_target
    st.session_state.favorite_feedback = "已產生新的 LINE 綁定碼。"
    st.rerun()


def _clear_line_binding(ctx: PageContext) -> None:
    ctx.product_store.clear_line_target(user_id=ctx.current_user_id)
    st.session_state.notify_line_target = ""
    st.session_state.favorite_feedback = "已解除目前的 LINE 綁定。"
    st.rerun()


def _refresh_line_binding(ctx: PageContext) -> None:
    latest_preferences = ctx.product_store.get_notification_preferences(
        user_id=ctx.current_user_id
    )
    st.session_state.notify_line_target = latest_preferences.line_target
    st.rerun()


def _save_notification_preferences(ctx: PageContext) -> None:
    ctx.product_store.save_notification_preferences(
        NotificationPreference(
            site_enabled=st.session_state.notify_site_enabled,
            email_enabled=st.session_state.notify_email_enabled,
            line_enabled=st.session_state.notify_line_enabled,
            email_recipients=st.session_state.notify_email_recipients,
            line_target=st.session_state.notify_line_target,
            min_relevance_score=float(st.session_state.notify_min_score),
            max_jobs_per_alert=int(st.session_state.notify_max_jobs),
            frequency="即時",
        ),
        user_id=ctx.current_user_id,
    )
    st.session_state.favorite_feedback = "已更新通知條件設定。"
    st.rerun()


def _send_test_email(ctx: PageContext) -> None:
    result = ctx.notification_service.send_new_job_alert(
        search_name="通知測試",
        new_jobs=_build_test_payload(),
        email_enabled=True,
        line_enabled=False,
        email_recipients_text=st.session_state.notify_email_recipients,
        max_jobs=1,
    )
    if result["email_sent"]:
        st.success("Email 測試通知已送出。")
    else:
        st.warning("Email 測試通知未送出：" + "；".join(result["notes"]))


def _send_test_line(ctx: PageContext) -> None:
    result = ctx.notification_service.send_new_job_alert(
        search_name="通知測試",
        new_jobs=_build_test_payload(),
        email_enabled=False,
        line_enabled=True,
        line_target=st.session_state.notify_line_target,
        max_jobs=1,
    )
    if result["line_sent"]:
        st.success("LINE 測試通知已送出。")
    else:
        st.warning("LINE 測試通知未送出：" + "；".join(result["notes"]))


def _build_test_payload() -> list[dict[str, str]]:
    return [
        {
            "title": "測試通知｜職缺雷達",
            "company": "System Check",
            "source": "系統測試",
            "location": "台灣",
            "salary": "",
            "url": "https://example.com/job-radar-test",
        }
    ]
