"""Password-based login/register views."""

from __future__ import annotations

import streamlit as st

from ..product_store import ProductStore
from ..observability import new_trace_id
from .auth_state import (
    AUTH_VIEW_FORGOT_REQUEST,
    AUTH_VIEW_LOGIN,
    AUTH_VIEW_REGISTER,
    is_valid_email,
    render_field_error,
    set_auth_feedback,
    set_auth_view,
)
from .dev_annotations import render_dev_card_annotation
from .auth_persistence import persist_login
from .session import activate_user_session


def _handle_login_submit(*, product_store: ProductStore) -> None:
    trace_id = new_trace_id("auth")
    login_email = str(st.session_state.get("dialog_login_email_input", "")).strip()
    login_password = str(st.session_state.get("dialog_login_password_input", ""))
    field_errors: dict[str, str] = {}
    if not is_valid_email(login_email):
        field_errors["login_email"] = "請輸入有效的 Email。"
    if not login_password:
        field_errors["login_password"] = "請輸入密碼。"
    if field_errors:
        product_store.record_audit_event(
            event_type="auth.login.validation_failed",
            status="blocked",
            target_type="user_email",
            target_id=login_email.lower(),
            details={"field_errors": field_errors},
            trace_id=trace_id,
        )
        set_auth_feedback(
            error="請先修正登入欄位。",
            field_errors=field_errors,
        )
        st.rerun()

    user = product_store.authenticate_user(login_email, login_password)
    if user is None:
        product_store.record_audit_event(
            event_type="auth.login.failed",
            status="error",
            target_type="user_email",
            target_id=login_email.lower(),
            details={"reason": "invalid_credentials"},
            trace_id=trace_id,
        )
        set_auth_feedback(
            error="帳號或密碼不正確。",
            field_errors={"login_password": "請重新確認密碼。"},
        )
        st.rerun()

    st.session_state.show_auth_dialog = False
    product_store.record_audit_event(
        event_type="auth.login.succeeded",
        status="success",
        target_type="user",
        target_id=str(user.id),
        details={"email": user.email},
        user_id=int(user.id),
        actor_role=user.role,
        trace_id=trace_id,
    )
    activate_user_session(
        user=user,
        product_store=product_store,
        success_message="",
        login_method="password",
    )
    persist_login(user_id=int(user.id))
    st.rerun()


def render_login_view(*, product_store: ProductStore) -> None:
    """Render login form."""
    render_dev_card_annotation(
        "登入表單",
        element_id="dialog-login-form",
        description="網站帳號登入表單，包含 Email、密碼與送出動作。",
        text_nodes=[
            ("auth-form-label", "登入表單欄位標題。"),
        ],
        show_popover=True,
        popover_key="dialog-login-form",
        compact=True,
    )
    with st.form("dialog-login-form"):
        st.markdown("<div class='auth-form-label'>Email</div>", unsafe_allow_html=True)
        st.text_input(
            "Email",
            key="dialog_login_email_input",
            placeholder="you@example.com",
            label_visibility="collapsed",
        )
        render_field_error("login_email")
        st.markdown("<div class='auth-form-label'>密碼</div>", unsafe_allow_html=True)
        st.text_input(
            "密碼",
            type="password",
            key="dialog_login_password_input",
            placeholder="請輸入密碼",
            label_visibility="collapsed",
        )
        render_field_error("login_password")
        login_submit = st.form_submit_button(
            "登入",
            use_container_width=True,
            type="primary",
        )
    if login_submit:
        _handle_login_submit(product_store=product_store)

    action_cols = st.columns([1, 1], gap="small")
    if action_cols[0].button(
        "忘記密碼",
        key="dialog-open-forgot-password",
        type="secondary",
        use_container_width=True,
    ):
        set_auth_view(AUTH_VIEW_FORGOT_REQUEST)
        st.rerun()
    if action_cols[1].button(
        "切換到註冊",
        key="dialog-switch-register-link",
        type="secondary",
        use_container_width=True,
    ):
        set_auth_view(AUTH_VIEW_REGISTER)
        st.rerun()


def _handle_register_submit(*, product_store: ProductStore) -> None:
    trace_id = new_trace_id("auth")
    register_name = str(st.session_state.get("dialog_register_name_input", "")).strip()
    register_email = str(st.session_state.get("dialog_register_email_input", "")).strip()
    register_password = str(st.session_state.get("dialog_register_password_input", ""))
    register_password_confirm = str(
        st.session_state.get("dialog_register_password_confirm_input", "")
    )
    field_errors: dict[str, str] = {}
    if not is_valid_email(register_email):
        field_errors["register_email"] = "請輸入有效的 Email。"
    if len(register_password) < 8:
        field_errors["register_password"] = "密碼至少需要 8 個字元。"
    if register_password != register_password_confirm:
        field_errors["register_password_confirm"] = "兩次輸入的密碼不一致。"
    if field_errors:
        product_store.record_audit_event(
            event_type="auth.register.validation_failed",
            status="blocked",
            target_type="user_email",
            target_id=register_email.lower(),
            details={"field_errors": field_errors},
            trace_id=trace_id,
        )
        set_auth_feedback(
            error="請先修正註冊欄位。",
            field_errors=field_errors,
        )
        st.rerun()

    try:
        user = product_store.register_user(
            email=register_email,
            password=register_password,
            display_name=register_name,
        )
    except ValueError as exc:
        product_store.record_audit_event(
            event_type="auth.register.failed",
            status="error",
            target_type="user_email",
            target_id=register_email.lower(),
            details={"reason": str(exc)},
            trace_id=trace_id,
        )
        set_auth_feedback(error=str(exc), field_errors={"register_email": str(exc)})
        st.rerun()

    st.session_state.show_auth_dialog = False
    product_store.record_audit_event(
        event_type="auth.register.succeeded",
        status="success",
        target_type="user",
        target_id=str(user.id),
        details={"email": user.email},
        user_id=int(user.id),
        actor_role=user.role,
        trace_id=trace_id,
    )
    activate_user_session(
        user=user,
        product_store=product_store,
        success_message="",
        login_method="password",
    )
    persist_login(user_id=int(user.id))
    st.rerun()


def render_register_view(*, product_store: ProductStore) -> None:
    """Render registration form."""
    with st.form("dialog-register-form"):
        st.markdown("<div class='auth-form-label'>暱稱（選填）</div>", unsafe_allow_html=True)
        st.text_input(
            "暱稱（選填）",
            key="dialog_register_name_input",
            placeholder="例如：Alex",
            label_visibility="collapsed",
        )
        st.markdown("<div class='auth-form-label'>Email</div>", unsafe_allow_html=True)
        st.text_input(
            "Email",
            key="dialog_register_email_input",
            placeholder="you@example.com",
            label_visibility="collapsed",
        )
        render_field_error("register_email")
        st.markdown("<div class='auth-form-label'>密碼</div>", unsafe_allow_html=True)
        st.text_input(
            "密碼",
            type="password",
            key="dialog_register_password_input",
            placeholder="至少 8 個字元",
            label_visibility="collapsed",
        )
        render_field_error("register_password")
        st.markdown("<div class='auth-form-label'>確認密碼</div>", unsafe_allow_html=True)
        st.text_input(
            "確認密碼",
            type="password",
            key="dialog_register_password_confirm_input",
            placeholder="再輸入一次密碼",
            label_visibility="collapsed",
        )
        render_field_error("register_password_confirm")
        register_submit = st.form_submit_button(
            "建立帳號",
            use_container_width=True,
            type="primary",
        )
    if register_submit:
        _handle_register_submit(product_store=product_store)


def render_credentials_panel_tabs(*, current_view: str) -> None:
    """Render login/register tab switcher."""
    tab_cols = st.columns(2, gap="small")
    if tab_cols[0].button(
        "登入",
        key="dialog-auth-tab-login",
        type="primary" if current_view == AUTH_VIEW_LOGIN else "secondary",
        use_container_width=True,
    ):
        set_auth_view(AUTH_VIEW_LOGIN)
        st.rerun()
    if tab_cols[1].button(
        "註冊",
        key="dialog-auth-tab-register",
        type="primary" if current_view == AUTH_VIEW_REGISTER else "secondary",
        use_container_width=True,
    ):
        set_auth_view(AUTH_VIEW_REGISTER)
        st.rerun()
