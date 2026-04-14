"""提供全域客服式 AI / 說明 / 通知入口。"""

from __future__ import annotations

import streamlit as st

from ..models import JobNotification
from .assistant_launcher_content import (
    LAUNCHER_TAB_ITEMS,
    render_panel_header,
    render_tab_content,
    valid_launcher_tab,
)
from .dev_annotations import render_dev_card_annotation
from .session import set_main_tab


def _inject_launcher_offset(*, open_panel: bool) -> None:
    active_offset = "var(--launcher-shell-stack-height)" if open_panel else "0px"
    st.markdown(
        f"<style>:root {{ --assistant-launcher-active-offset: {active_offset}; }}</style>",
        unsafe_allow_html=True,
    )


def _open_launcher_tab(tab_id: str) -> None:
    st.session_state.launcher_bottom_tab = valid_launcher_tab(tab_id)
    st.session_state.assistant_launcher_open = True
    st.rerun()


def _close_launcher() -> None:
    st.session_state.assistant_launcher_open = False
    st.rerun()


def _switch_page_from_launcher(tab_id: str) -> None:
    st.session_state.assistant_launcher_open = False
    set_main_tab(tab_id)
    st.rerun()


def _submit_assistant_question(question: str) -> None:
    cleaned_question = question.strip()
    if not cleaned_question:
        st.warning("請先輸入問題。")
        return
    st.session_state.assistant_question_draft = cleaned_question
    st.session_state.assistant_question_input = cleaned_question
    st.session_state.assistant_launcher_submit_pending = True
    st.session_state.assistant_launcher_open = False
    set_main_tab("assistant")
    st.rerun()


def render_assistant_launcher(
    *,
    notifications: list[JobNotification],
    unread_notification_count: int,
    current_user_is_guest: bool,
) -> None:
    """渲染手機客服式的 AI / 說明 / 通知浮動入口。"""
    current_tab = valid_launcher_tab(str(st.session_state.get("launcher_bottom_tab", "assistant")))
    st.session_state.launcher_bottom_tab = current_tab
    panel_open = bool(st.session_state.get("assistant_launcher_open"))
    _inject_launcher_offset(open_panel=panel_open)

    with st.container(key="assistant-launcher-trigger-shell"):
        render_dev_card_annotation(
            "AI 助手浮動入口",
            element_id="assistant-launcher-trigger-shell",
            description="登入頁與工作台右下角共用的 AI 浮動按鈕入口，可打開 AI / 說明 / 通知 launcher。",
            layers=[
                "assistant-launcher-trigger-button-shell",
            ],
            text_nodes=[
                ("assistant-launcher-trigger", "右下角 AI 浮動按鈕文字與點擊入口。"),
            ],
            notes=[
                "點擊後會打開 assistant-launcher-card-shell 浮動視窗。",
                "登入頁與一般工作台都共用這顆入口。",
            ],
            show_popover=True,
            popover_key="assistant-launcher-trigger-shell",
            compact=True,
        )
        with st.container(key="assistant-launcher-trigger-button-shell"):
            if st.button("AI", key="assistant-launcher-trigger", type="secondary", help="打開 AI 助手"):
                _open_launcher_tab("assistant")

    if not panel_open:
        return

    with st.container(key="assistant-launcher-card-shell"):
        render_dev_card_annotation(
            "浮動 Launcher 視窗",
            element_id="assistant-launcher-card-shell",
            description="右下角 AI 浮動按鈕打開後的手機客服高卡視窗。",
            layers=[
                "assistant-launcher-mobile-shell",
                "assistant-launcher-mobile-body",
                "assistant-launcher-mobile-tabbar",
                "assistant-launcher-guide-body",
                "assistant-launcher-notification-feed",
            ],
            text_nodes=[
                ("assistant-launcher-header-title", "Launcher 頂部的當前頁標題。"),
                ("assistant-launcher-guide-title", "說明列表的功能標題。"),
                ("assistant-launcher-notification-title", "通知卡片標題。"),
            ],
            show_popover=True,
            popover_key="assistant-launcher-card-shell",
        )

        with st.container(border=True, key="assistant-launcher-mobile-shell"):
            render_panel_header(current_tab, on_close=_close_launcher)

            with st.container(key="assistant-launcher-mobile-body"):
                render_tab_content(
                    current_tab,
                    notifications=notifications,
                    unread_notification_count=unread_notification_count,
                    current_user_is_guest=current_user_is_guest,
                    on_submit_question=_submit_assistant_question,
                    on_switch_page=_switch_page_from_launcher,
                )

            with st.container(key="assistant-launcher-mobile-tabbar"):
                tab_cols = st.columns(len(LAUNCHER_TAB_ITEMS), gap="small")
                for index, (tab_id, label) in enumerate(LAUNCHER_TAB_ITEMS):
                    if tab_cols[index].button(
                        label,
                        key=f"assistant-launcher-tab-{tab_id}",
                        type="primary" if current_tab == tab_id else "secondary",
                        use_container_width=True,
                    ):
                        _open_launcher_tab(tab_id)
