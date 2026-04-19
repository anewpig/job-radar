"""Forgot-password request/confirm views."""

from __future__ import annotations

import streamlit as st

from ..error_taxonomy import build_error_info
from ..notification_service import NotificationService
from ..observability import new_trace_id
from ..product_store import ProductStore
from .auth_state import (
    AUTH_VIEW_FORGOT_CONFIRM,
    AUTH_VIEW_LOGIN,
    is_valid_email,
    render_field_error,
    set_auth_feedback,
    set_auth_view,
)
from .dev_annotations import render_dev_card_annotation


def _handle_forgot_request_submit(
    *,
    product_store: ProductStore,
    notification_service: NotificationService,
) -> None:
    trace_id = new_trace_id("auth")
    reset_email = str(st.session_state.get("dialog_reset_email_input", "")).strip()
    if not is_valid_email(reset_email):
        product_store.record_audit_event(
            event_type="auth.password_reset.request_validation_failed",
            status="blocked",
            target_type="user_email",
            target_id=reset_email.lower(),
            details={"reason": "invalid_email"},
            trace_id=trace_id,
        )
        set_auth_feedback(
            error="請先輸入有效的 Email。",
            field_errors={"reset_email": "請輸入有效的 Email。"},
        )
        st.rerun()

    generic_success_message = "如果這個 Email 有註冊，我們已寄出重設碼。"
    try:
        user, reset_code = product_store.issue_password_reset(reset_email)
        notification_service.send_password_reset_code(
            email=user.email,
            reset_code=reset_code,
        )
        product_store.record_audit_event(
            event_type="auth.password_reset.request_succeeded",
            status="success",
            target_type="user",
            target_id=str(user.id),
            details={"email": user.email},
            user_id=int(user.id),
            actor_role=user.role,
            trace_id=trace_id,
        )
    except ValueError:
        user = None
    except Exception as exc:  # noqa: BLE001
        error_info = build_error_info(
            exc,
            metadata={
                "operation": "password_reset_request",
                "email": reset_email.lower(),
            },
        )
        product_store.record_audit_event(
            event_type="auth.password_reset.request_failed",
            status="error",
            target_type="user_email",
            target_id=reset_email.lower(),
            details=error_info.to_dict(),
            trace_id=trace_id,
        )
        set_auth_feedback(error=error_info.user_message)
        st.rerun()

    del user
    st.session_state.auth_reset_email_prefill = reset_email
    st.session_state.dialog_reset_email_confirm_input = reset_email
    set_auth_view(
        AUTH_VIEW_FORGOT_CONFIRM,
        success=generic_success_message,
    )
    st.rerun()


def render_forgot_request_view(
    *,
    product_store: ProductStore,
    notification_service: NotificationService,
) -> None:
    """Render forgot-password request step."""
    st.markdown(
        """
<div class="auth-step-shell">
  <div class="auth-step-kicker">忘記密碼</div>
  <div class="auth-step-title">先寄送重設碼到你的 Email</div>
  <div class="auth-step-copy">輸入註冊 Email，我們會寄一組 6 碼重設碼給你。</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    render_dev_card_annotation(
        "重設碼寄送表單",
        element_id="dialog-forgot-password-request-form",
        description="忘記密碼流程的第一步，輸入 Email 並寄送重設碼。",
        text_nodes=[
            ("auth-form-label", "寄送重設碼表單欄位標題。"),
        ],
        show_popover=True,
        popover_key="dialog-forgot-password-request-form",
        compact=True,
    )
    if not notification_service.email_service_configured:
        st.markdown(
            "<div class='auth-inline-note auth-inline-note--muted'>目前寄信服務尚未啟用，暫時無法使用忘記密碼。</div>",
            unsafe_allow_html=True,
        )
    with st.form("dialog-forgot-password-request-form"):
        st.markdown("<div class='auth-form-label'>註冊 Email</div>", unsafe_allow_html=True)
        st.text_input(
            "註冊 Email",
            key="dialog_reset_email_input",
            placeholder="you@example.com",
            label_visibility="collapsed",
        )
        render_field_error("reset_email")
        request_reset = st.form_submit_button(
            "寄送重設碼",
            use_container_width=True,
            disabled=not notification_service.email_service_configured,
            type="primary",
        )
    if request_reset:
        _handle_forgot_request_submit(
            product_store=product_store,
            notification_service=notification_service,
        )

    if st.button(
        "返回登入",
        key="dialog-back-to-login-from-forgot-request",
        type="secondary",
        use_container_width=True,
    ):
        set_auth_view(AUTH_VIEW_LOGIN)
        st.rerun()


def _handle_forgot_confirm_submit(*, product_store: ProductStore) -> None:
    trace_id = new_trace_id("auth")
    reset_email_confirm = str(
        st.session_state.get("dialog_reset_email_confirm_input", "")
    ).strip()
    reset_code = str(st.session_state.get("dialog_reset_code_input", "")).strip()
    new_password = str(st.session_state.get("dialog_reset_new_password_input", ""))
    new_password_confirm = str(
        st.session_state.get("dialog_reset_new_password_confirm_input", "")
    )
    field_errors: dict[str, str] = {}
    if not is_valid_email(reset_email_confirm):
        field_errors["reset_email_confirm"] = "請輸入有效的 Email。"
    if not reset_code:
        field_errors["reset_code"] = "請輸入 6 碼重設碼。"
    if len(new_password) < 8:
        field_errors["reset_new_password"] = "新密碼至少需要 8 個字元。"
    if new_password != new_password_confirm:
        field_errors["reset_new_password_confirm"] = "兩次輸入的新密碼不一致。"
    if field_errors:
        product_store.record_audit_event(
            event_type="auth.password_reset.confirm_validation_failed",
            status="blocked",
            target_type="user_email",
            target_id=reset_email_confirm.lower(),
            details={"field_errors": field_errors},
            trace_id=trace_id,
        )
        set_auth_feedback(error="請先修正重設欄位。", field_errors=field_errors)
        st.rerun()

    try:
        user = product_store.reset_password_with_code(
            email=reset_email_confirm,
            reset_code=reset_code,
            new_password=new_password,
        )
    except ValueError as exc:
        error_info = build_error_info(
            exc,
            metadata={
                "operation": "password_reset_confirm",
                "email": reset_email_confirm.lower(),
            },
        )
        product_store.record_audit_event(
            event_type="auth.password_reset.confirm_failed",
            status="error",
            target_type="user_email",
            target_id=reset_email_confirm.lower(),
            details=error_info.to_dict(),
            trace_id=trace_id,
        )
        message = error_info.user_message
        field_key = "reset_code"
        if "密碼至少需要" in message:
            field_key = "reset_new_password"
        set_auth_feedback(error=message, field_errors={field_key: message})
        st.rerun()

    product_store.record_audit_event(
        event_type="auth.password_reset.confirm_succeeded",
        status="success",
        target_type="user",
        target_id=str(user.id),
        details={"email": user.email},
        user_id=int(user.id),
        actor_role=user.role,
        trace_id=trace_id,
    )
    set_auth_view(
        AUTH_VIEW_LOGIN,
        success="密碼已重設，現在可以直接登入。",
    )
    st.rerun()


def render_forgot_confirm_view(*, product_store: ProductStore) -> None:
    """Render forgot-password confirmation step."""
    st.markdown(
        """
<div class="auth-step-shell">
  <div class="auth-step-kicker">重設密碼</div>
  <div class="auth-step-title">輸入重設碼並設定新密碼</div>
  <div class="auth-step-copy">重設碼有效時間為 15 分鐘，輸入完成後會直接回到登入。</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    render_dev_card_annotation(
        "重設密碼確認表單",
        element_id="dialog-forgot-password-confirm-form",
        description="忘記密碼流程第二步，輸入重設碼並設定新密碼。",
        text_nodes=[
            ("auth-form-label", "重設密碼表單欄位標題。"),
        ],
        show_popover=True,
        popover_key="dialog-forgot-password-confirm-form",
        compact=True,
    )
    with st.form("dialog-forgot-password-confirm-form"):
        st.markdown("<div class='auth-form-label'>註冊 Email</div>", unsafe_allow_html=True)
        st.text_input(
            "註冊 Email",
            key="dialog_reset_email_confirm_input",
            value=str(st.session_state.get("auth_reset_email_prefill", "")).strip(),
            label_visibility="collapsed",
        )
        render_field_error("reset_email_confirm")
        st.markdown("<div class='auth-form-label'>重設碼</div>", unsafe_allow_html=True)
        st.text_input(
            "重設碼",
            key="dialog_reset_code_input",
            placeholder="請輸入收到的 6 碼重設碼",
            label_visibility="collapsed",
        )
        render_field_error("reset_code")
        st.markdown("<div class='auth-form-label'>新密碼</div>", unsafe_allow_html=True)
        st.text_input(
            "新密碼",
            type="password",
            key="dialog_reset_new_password_input",
            placeholder="至少 8 個字元",
            label_visibility="collapsed",
        )
        render_field_error("reset_new_password")
        st.markdown("<div class='auth-form-label'>確認新密碼</div>", unsafe_allow_html=True)
        st.text_input(
            "確認新密碼",
            type="password",
            key="dialog_reset_new_password_confirm_input",
            placeholder="再輸入一次新密碼",
            label_visibility="collapsed",
        )
        render_field_error("reset_new_password_confirm")
        confirm_reset = st.form_submit_button(
            "重設密碼",
            use_container_width=True,
            type="primary",
        )
    if confirm_reset:
        _handle_forgot_confirm_submit(product_store=product_store)

    if st.button(
        "返回登入",
        key="dialog-back-to-login-from-forgot-confirm",
        type="secondary",
        use_container_width=True,
    ):
        set_auth_view(AUTH_VIEW_LOGIN)
        st.rerun()
