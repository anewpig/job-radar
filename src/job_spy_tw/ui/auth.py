"""處理登入入口、帳號對話框與相關認證 UI 的渲染邏輯。"""

from __future__ import annotations

import streamlit as st

from ..notification_service import NotificationService
from ..product_store import ProductStore
from .session import activate_user_session


def _oidc_provider_available(provider: str) -> bool:
    """檢查指定 OIDC provider 是否已在 secrets 中完整設定。"""
    try:
        auth_config = st.secrets["auth"]
    except Exception:
        return False
    try:
        provider_config = auth_config[provider]
    except Exception:
        return False
    required_auth_keys = ("redirect_uri", "cookie_secret")
    required_provider_keys = ("client_id", "client_secret", "server_metadata_url")
    return all(str(auth_config.get(key, "")).strip() for key in required_auth_keys) and all(
        str(provider_config.get(key, "")).strip() for key in required_provider_keys
    )


def _current_oidc_identity() -> dict[str, str] | None:
    """從 Streamlit 內建 OIDC session 讀取目前登入者的關鍵識別資料。"""
    try:
        user_info = st.user.to_dict()
    except Exception:
        return None
    if not bool(user_info.get("is_logged_in")):
        return None

    issuer = str(user_info.get("iss") or "").strip()
    provider_key = issuer.lower() if issuer else "oidc"
    subject = str(user_info.get("sub") or user_info.get("oid") or "").strip()
    email = str(
        user_info.get("email") or user_info.get("preferred_username") or ""
    ).strip()
    display_name = str(
        user_info.get("name")
        or user_info.get("given_name")
        or user_info.get("preferred_username")
        or email
    ).strip()
    if not subject or not email:
        return None
    return {
        "provider": provider_key,
        "subject": subject,
        "email": email,
        "display_name": display_name,
    }


def _sync_oidc_user_session(*, guest_user, product_store: ProductStore) -> None:
    """把 Streamlit OIDC cookie 映射到目前的本地產品 session。"""
    oidc_identity = _current_oidc_identity()
    current_login_method = str(st.session_state.get("auth_login_method", "guest"))
    current_user_id = int(st.session_state.get("auth_user_id", int(guest_user.id)))
    if oidc_identity is None:
        if current_login_method == "oidc" and current_user_id != int(guest_user.id):
            st.session_state.show_auth_dialog = False
            activate_user_session(
                user=guest_user,
                product_store=product_store,
                success_message="已登出，目前切回訪客模式。",
            )
            st.rerun()
        return

    same_subject = (
        current_login_method == "oidc"
        and st.session_state.get("auth_oidc_provider", "") == oidc_identity["provider"]
        and st.session_state.get("auth_oidc_subject", "") == oidc_identity["subject"]
    )
    same_email = str(st.session_state.get("auth_user_email", "")).strip().lower() == str(
        oidc_identity["email"]
    ).strip().lower()
    if same_subject and same_email:
        return

    user = product_store.authenticate_oidc_user(
        provider=oidc_identity["provider"],
        subject=oidc_identity["subject"],
        email=oidc_identity["email"],
        display_name=oidc_identity["display_name"],
    )
    st.session_state.show_auth_dialog = False
    activate_user_session(
        user=user,
        product_store=product_store,
        success_message="",
        login_method="oidc",
        oidc_provider=oidc_identity["provider"],
        oidc_subject=oidc_identity["subject"],
    )
    st.rerun()


def _close_auth_dialog() -> None:
    """關閉目前開啟中的登入或帳號對話框。"""
    st.session_state.show_auth_dialog = False


@st.dialog("登入", width="large", on_dismiss=_close_auth_dialog)
def _render_guest_auth_dialog(
    *,
    guest_user,
    product_store: ProductStore,
    notification_service: NotificationService,
) -> None:
    """渲染訪客可見的登入、註冊與忘記密碼對話框。"""
    st.markdown(
        """
<div class="auth-dialog-shell">
  <div class="auth-dialog-brand">
    <div class="auth-dialog-logo">JR</div>
    <div>
      <div class="auth-dialog-title">職缺雷達</div>
      <div class="auth-dialog-subtitle">登入你的工作台</div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("登入後會保存自己的搜尋、收藏、履歷摘要與通知設定。")
    social_login_cols = st.columns(2, gap="medium")
    google_enabled = _oidc_provider_available("google")
    facebook_enabled = _oidc_provider_available("facebook")
    if social_login_cols[0].button(
        "使用 Google 登入",
        key="dialog-google-login-button",
        use_container_width=True,
        disabled=not google_enabled,
    ):
        st.login("google")
    if social_login_cols[1].button(
        "使用 Facebook 登入",
        key="dialog-facebook-login-button",
        use_container_width=True,
        disabled=not facebook_enabled,
    ):
        st.login("facebook")
    if not google_enabled or not facebook_enabled:
        st.caption("Google / Facebook 需先在 `.streamlit/secrets.toml` 完成 OIDC 設定。")
    st.divider()
    auth_tabs = st.tabs(["登入", "註冊"])
    with auth_tabs[0]:
        with st.form("dialog-login-form"):
            login_email = st.text_input("Email", key="dialog_login_email_input")
            login_password = st.text_input(
                "密碼",
                type="password",
                key="dialog_login_password_input",
            )
            login_submit = st.form_submit_button(
                "登入",
                use_container_width=True,
                type="primary",
            )
        if login_submit:
            user = product_store.authenticate_user(login_email, login_password)
            if user is None:
                st.warning("帳號或密碼不正確。")
            else:
                st.session_state.show_auth_dialog = False
                activate_user_session(
                    user=user,
                    product_store=product_store,
                    success_message="",
                    login_method="password",
                )
                st.rerun()
        with st.expander("忘記密碼", expanded=False):
            st.caption("輸入註冊 Email，我們會寄一組重設碼給你。")
            if not notification_service.email_service_configured:
                st.info("目前管理員尚未設定 Email 寄件服務，暫時不能使用忘記密碼。")
            with st.form("dialog-forgot-password-request-form"):
                reset_email = st.text_input("註冊 Email", key="dialog_reset_email_input")
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

            with st.form("dialog-forgot-password-confirm-form"):
                reset_email_confirm = st.text_input(
                    "註冊 Email",
                    key="dialog_reset_email_confirm_input",
                )
                reset_code = st.text_input(
                    "重設碼",
                    key="dialog_reset_code_input",
                    placeholder="請輸入收到的 6 碼重設碼",
                )
                new_password = st.text_input(
                    "新密碼",
                    type="password",
                    key="dialog_reset_new_password_input",
                )
                new_password_confirm = st.text_input(
                    "確認新密碼",
                    type="password",
                    key="dialog_reset_new_password_confirm_input",
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
        with st.form("dialog-register-form"):
            register_name = st.text_input("暱稱（選填）", key="dialog_register_name_input")
            register_email = st.text_input("Email", key="dialog_register_email_input")
            register_password = st.text_input(
                "密碼",
                type="password",
                key="dialog_register_password_input",
            )
            register_password_confirm = st.text_input(
                "確認密碼",
                type="password",
                key="dialog_register_password_confirm_input",
            )
            register_submit = st.form_submit_button(
                "建立帳號",
                use_container_width=True,
                type="primary",
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
                    st.session_state.show_auth_dialog = False
                    activate_user_session(
                        user=user,
                        product_store=product_store,
                        success_message="",
                        login_method="password",
                    )
                    st.rerun()


@st.dialog("帳號", width="medium", on_dismiss=_close_auth_dialog)
def _render_account_dialog(
    *,
    guest_user,
    product_store: ProductStore,
) -> None:
    """渲染已登入使用者的帳號資訊與登出操作。"""
    current_user = st.session_state.get("current_user")
    display_name = getattr(current_user, "display_name", "") or "已登入帳號"
    email = getattr(current_user, "email", "")
    st.markdown(
        f"""
<div class="auth-dialog-shell auth-dialog-shell--account">
  <div class="auth-dialog-brand">
    <div class="auth-dialog-logo">JR</div>
    <div>
      <div class="auth-dialog-title">{display_name}</div>
      <div class="auth-dialog-subtitle">{email}</div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("你目前可以繼續保存搜尋、收藏職缺與管理投遞流程。")
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
            st.logout()
            return
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
    _sync_oidc_user_session(guest_user=guest_user, product_store=product_store)
    button_label = "登入" if current_user_is_guest else "帳號"
    if st.button(
        button_label,
        key="header-auth-trigger-button",
        type="tertiary",
        use_container_width=False,
    ):
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
