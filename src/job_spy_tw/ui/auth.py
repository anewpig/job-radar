"""處理登入入口、帳號對話框與認證 dialog 入口。"""

from __future__ import annotations

import streamlit as st

from ..notification_service import NotificationService
from ..product_store import ProductStore
from .auth_persistence import clear_persistent_login
from .auth_state import (
    AUTH_VIEW_LOGIN,
    begin_oidc_link_flow,
    close_auth_dialog,
    ensure_auth_ui_state,
    oidc_provider_available,
    set_auth_view,
    sync_oidc_user_session,
)
from .auth_views import render_credentials_panel, render_social_login_panel
from .common import _escape
from .dev_annotations import render_dev_card_annotation
from .session import activate_user_session


@st.dialog("登入", width="large", on_dismiss=close_auth_dialog)
def _render_guest_auth_dialog(
    *,
    guest_user,
    product_store: ProductStore,
    notification_service: NotificationService,
) -> None:
    """渲染訪客可見的登入、註冊與忘記密碼對話框。"""
    del guest_user
    with st.container(key="auth-page-shell"):
        render_dev_card_annotation(
            "登入 / 註冊對話框",
            element_id="auth-page-shell",
            description="從右上角登入入口打開的主認證對話框，左側是品牌與第三方登入，右側是網站帳號登入 / 註冊 / 忘記密碼流程。",
            layers=[
                "auth-page-form-shell",
                "dialog-google-login-shell",
                "dialog-facebook-login-shell",
                "dialog-login-form",
                "dialog-forgot-password-request-form",
                "dialog-forgot-password-confirm-form",
            ],
            text_nodes=[
                ("auth-social-title", "第三方登入卡片標題。"),
            ],
            notes=[
                "右側內容會依 auth_view_mode 在登入、註冊、忘記密碼流程之間切換。",
                "第三方登入按鈕是否可用取決於 secrets 裡的 OIDC 設定。",
            ],
            show_popover=True,
            popover_key="auth-page-shell",
        )
        auth_cols = st.columns([0.95, 1.05], gap="large")
        with auth_cols[0]:
            with st.container(key="auth-page-brand-shell"):
                render_social_login_panel()
        with auth_cols[1]:
            with st.container(key="auth-page-form-shell"):
                render_dev_card_annotation(
                    "網站帳號流程區",
                    element_id="auth-page-form-shell",
                    description="登入、註冊與忘記密碼流程所在的右側表單區。",
                    layers=[
                        "dialog-login-form",
                        "dialog-forgot-password-request-form",
                        "dialog-forgot-password-confirm-form",
                    ],
                    notes=[
                        "會依 auth_view_mode 在四種流程間切換。",
                    ],
                    show_popover=True,
                    popover_key="auth-page-form-shell",
                    compact=True,
                )
                render_credentials_panel(
                    product_store=product_store,
                    notification_service=notification_service,
                )


@st.dialog("帳號", width="medium", on_dismiss=close_auth_dialog)
def _render_account_dialog(
    *,
    guest_user,
    product_store: ProductStore,
) -> None:
    """渲染已登入使用者的帳號資訊與登出操作。"""
    display_name = str(st.session_state.get("auth_user_display_name", "") or "已登入帳號")
    email = str(st.session_state.get("auth_user_email", "") or "")
    login_method = str(st.session_state.get("auth_login_method", "password"))
    current_user_id = int(st.session_state.get("auth_user_id", 0) or 0)
    method_label = {
        "password": "網站帳號",
        "oidc": "第三方登入",
        "guest": "訪客模式",
    }.get(login_method, "已登入")
    with st.container(key="auth-account-shell"):
        render_dev_card_annotation(
            "帳號資訊對話框",
            element_id="auth-account-shell",
            description="已登入後由右上角帳號入口打開的帳號資訊面板，包含登入方式、目前帳號與登出動作。",
            layers=[
                "auth-dialog-brand",
                "auth-account-pill-row",
                "dialog-logout-button",
            ],
            text_nodes=[
                ("auth-dialog-title", "目前登入者名稱。"),
                ("auth-dialog-subtitle", "目前登入者 Email。"),
                ("auth-account-pill", "登入方式與連線狀態 tag。"),
            ],
            show_popover=True,
            popover_key="auth-account-shell",
        )
        st.markdown(
            f"""
<div class="auth-dialog-shell auth-dialog-shell--account">
  <div class="auth-dialog-brand">
    <div class="auth-dialog-logo">JR</div>
    <div>
      <div class="auth-dialog-title">{_escape(display_name)}</div>
      <div class="auth-dialog-subtitle">{_escape(email)}</div>
    </div>
  </div>
  <div class="auth-account-pill-row">
    <span class="auth-account-pill">{_escape(method_label)}</span>
    <span class="auth-account-pill">已連線工作台</span>
  </div>
  <div class="auth-account-copy">你目前可以繼續保存搜尋、收藏職缺與管理投遞流程。</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        if login_method == "password":
            provider_rows = [
                ("google", "連結 Google 帳號"),
                ("facebook", "連結 Facebook 帳號"),
            ]
            enabled_providers = [
                (provider, label)
                for provider, label in provider_rows
                if oidc_provider_available(provider)
            ]
            if enabled_providers:
                st.markdown(
                    "<div class='auth-account-copy'>若第三方帳號 Email 與目前網站帳號一致，可以安全連結後直接用它登入。</div>",
                    unsafe_allow_html=True,
                )
                for provider, label in enabled_providers:
                    if st.button(
                        label,
                        key=f"dialog-link-{provider}-button",
                        use_container_width=True,
                        type="secondary",
                    ):
                        begin_oidc_link_flow(user_id=current_user_id, provider=provider)
                        st.session_state.show_auth_dialog = False
                        st.login(provider)
        if st.button(
            "登出並切回訪客模式",
            key="dialog-logout-button",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.show_auth_dialog = False
            if str(st.session_state.get("auth_login_method", "")) == "oidc":
                activate_user_session(
                    user=guest_user,
                    product_store=product_store,
                    success_message="已登出，目前切回訪客模式。",
                )
                clear_persistent_login()
                st.logout()
                return
            clear_persistent_login()
            activate_user_session(
                user=guest_user,
                product_store=product_store,
                success_message="已登出，目前切回訪客模式。",
            )
            st.rerun()


def render_auth_popover(
    *,
    current_user_is_guest: bool,
    guest_user,
    product_store: ProductStore,
    notification_service: NotificationService,
) -> None:
    """渲染 Header 的登入入口，並依目前狀態切換對應對話框。"""
    ensure_auth_ui_state()
    sync_oidc_user_session(guest_user=guest_user, product_store=product_store)
    button_label = "登入" if current_user_is_guest else "帳號"
    if st.button(
        button_label,
        key="header-auth-trigger-button",
        type="tertiary",
        use_container_width=False,
    ):
        if current_user_is_guest:
            set_auth_view(AUTH_VIEW_LOGIN)
        st.session_state.show_auth_dialog = True

    if st.session_state.get("show_auth_dialog"):
        if current_user_is_guest:
            _render_guest_auth_dialog(
                guest_user=guest_user,
                product_store=product_store,
                notification_service=notification_service,
            )
        else:
            _render_account_dialog(
                guest_user=guest_user,
                product_store=product_store,
            )
