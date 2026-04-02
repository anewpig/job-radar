from __future__ import annotations

import streamlit as st

from ..notification_service import NotificationService
from ..product_store import ProductStore
from .session import activate_user_session


def render_auth_popover(
    *,
    current_user_is_guest: bool,
    guest_user,
    product_store: ProductStore,
    notification_service: NotificationService,
) -> None:
    button_label = "登入" if current_user_is_guest else "帳號"
    with st.popover(
        button_label,
        icon=":material/account_circle:",
        use_container_width=True,
        width="stretch",
    ):
        if current_user_is_guest:
            st.caption("登入後會保存自己的搜尋、收藏、履歷摘要與通知設定。")
            auth_tabs = st.tabs(["登入", "註冊"])
            with auth_tabs[0]:
                with st.form("topbar-login-form"):
                    login_email = st.text_input("Email", key="topbar_login_email_input")
                    login_password = st.text_input(
                        "密碼",
                        type="password",
                        key="topbar_login_password_input",
                    )
                    login_submit = st.form_submit_button(
                        "登入",
                        use_container_width=True,
                    )
                if login_submit:
                    user = product_store.authenticate_user(login_email, login_password)
                    if user is None:
                        st.warning("帳號或密碼不正確。")
                    else:
                        activate_user_session(
                            user=user,
                            product_store=product_store,
                            success_message="",
                        )
                        st.rerun()
                with st.expander("忘記密碼", expanded=False):
                    st.caption("輸入註冊 Email，我們會寄一組重設碼給你。")
                    if not notification_service.email_service_configured:
                        st.info("目前管理員尚未設定 Email 寄件服務，暫時不能使用忘記密碼。")
                    with st.form("topbar-forgot-password-request-form"):
                        reset_email = st.text_input("註冊 Email", key="topbar_reset_email_input")
                        request_reset = st.form_submit_button(
                            "寄送重設碼",
                            use_container_width=True,
                            disabled=not notification_service.email_service_configured,
                        )
                    if request_reset:
                        try:
                            user, reset_code = product_store.issue_password_reset(reset_email)
                            notification_service.send_password_reset_code(
                                email=user.email,
                                reset_code=reset_code,
                            )
                        except Exception as exc:  # noqa: BLE001
                            st.warning(str(exc))
                        else:
                            st.success("重設碼已寄出，請到 Email 收信。")

                    with st.form("topbar-forgot-password-confirm-form"):
                        reset_email_confirm = st.text_input(
                            "註冊 Email",
                            key="topbar_reset_email_confirm_input",
                        )
                        reset_code = st.text_input(
                            "重設碼",
                            key="topbar_reset_code_input",
                            placeholder="請輸入收到的 6 碼重設碼",
                        )
                        new_password = st.text_input(
                            "新密碼",
                            type="password",
                            key="topbar_reset_new_password_input",
                        )
                        new_password_confirm = st.text_input(
                            "確認新密碼",
                            type="password",
                            key="topbar_reset_new_password_confirm_input",
                        )
                        confirm_reset = st.form_submit_button(
                            "重設密碼",
                            use_container_width=True,
                        )
                    if confirm_reset:
                        if new_password != new_password_confirm:
                            st.warning("兩次輸入的新密碼不一致。")
                        else:
                            try:
                                product_store.reset_password_with_code(
                                    email=reset_email_confirm,
                                    reset_code=reset_code,
                                    new_password=new_password,
                                )
                            except Exception as exc:  # noqa: BLE001
                                st.warning(str(exc))
                            else:
                                st.success("密碼已重設，現在可以直接登入。")
            with auth_tabs[1]:
                with st.form("topbar-register-form"):
                    register_name = st.text_input("暱稱（選填）", key="topbar_register_name_input")
                    register_email = st.text_input("Email", key="topbar_register_email_input")
                    register_password = st.text_input(
                        "密碼",
                        type="password",
                        key="topbar_register_password_input",
                    )
                    register_password_confirm = st.text_input(
                        "確認密碼",
                        type="password",
                        key="topbar_register_password_confirm_input",
                    )
                    register_submit = st.form_submit_button(
                        "建立帳號",
                        use_container_width=True,
                    )
                if register_submit:
                    if register_password != register_password_confirm:
                        st.warning("兩次輸入的密碼不一致。")
                    else:
                        try:
                            user = product_store.register_user(
                                email=register_email,
                                password=register_password,
                                display_name=register_name,
                            )
                        except ValueError as exc:
                            st.warning(str(exc))
                        else:
                            activate_user_session(
                                user=user,
                                product_store=product_store,
                                success_message="",
                            )
                            st.rerun()
        else:
            if st.button(
                "登出並切回訪客模式",
                key="topbar-logout-button",
                use_container_width=True,
            ):
                activate_user_session(
                    user=guest_user,
                    product_store=product_store,
                    success_message="已登出，目前切回訪客模式。",
                )
                st.rerun()
