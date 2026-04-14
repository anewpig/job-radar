"""認證 UI 的狀態、驗證與 OIDC session helper。"""

from __future__ import annotations

import streamlit as st

from ..product_store import ProductStore
from .common import _escape
from .dev_annotations import render_dev_card_annotation
from .session import activate_user_session

AUTH_VIEW_LOGIN = "login"
AUTH_VIEW_REGISTER = "register"
AUTH_VIEW_FORGOT_REQUEST = "forgot_request"
AUTH_VIEW_FORGOT_CONFIRM = "forgot_confirm"


def ensure_auth_ui_state() -> None:
    st.session_state.setdefault("show_auth_dialog", False)
    st.session_state.setdefault("auth_view_mode", AUTH_VIEW_LOGIN)
    st.session_state.setdefault("auth_form_error", "")
    st.session_state.setdefault("auth_form_success", "")
    st.session_state.setdefault("auth_form_field_errors", {})
    st.session_state.setdefault("auth_reset_email_prefill", "")
    st.session_state.setdefault("auth_pending_oidc_link_user_id", 0)
    st.session_state.setdefault("auth_pending_oidc_provider", "")


def set_auth_feedback(
    *,
    error: str = "",
    success: str = "",
    field_errors: dict[str, str] | None = None,
) -> None:
    st.session_state.auth_form_error = error
    st.session_state.auth_form_success = success
    st.session_state.auth_form_field_errors = field_errors or {}


def set_auth_view(
    view_mode: str,
    *,
    error: str = "",
    success: str = "",
    field_errors: dict[str, str] | None = None,
) -> None:
    st.session_state.auth_view_mode = view_mode
    set_auth_feedback(error=error, success=success, field_errors=field_errors)


def close_auth_dialog() -> None:
    """關閉目前開啟中的登入或帳號對話框。"""
    st.session_state.show_auth_dialog = False
    set_auth_view(AUTH_VIEW_LOGIN)


def oidc_provider_available(provider: str) -> bool:
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


def clear_pending_oidc_link() -> None:
    st.session_state.auth_pending_oidc_link_user_id = 0
    st.session_state.auth_pending_oidc_provider = ""


def begin_oidc_link_flow(*, user_id: int, provider: str) -> None:
    st.session_state.auth_pending_oidc_link_user_id = int(user_id)
    st.session_state.auth_pending_oidc_provider = str(provider).strip().lower()
    set_auth_feedback(error="", success="")


def _claim_is_truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    cleaned = str(value or "").strip().lower()
    return cleaned in {"1", "true", "yes", "y"}


def current_oidc_identity() -> dict[str, str | bool] | None:
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
    email_verified = _claim_is_truthy(
        user_info["email_verified"]
        if "email_verified" in user_info
        else user_info.get("verified_email")
    )
    if not subject or not email:
        return None
    return {
        "provider": provider_key,
        "subject": subject,
        "email": email,
        "display_name": display_name,
        "email_verified": email_verified,
    }


def sync_oidc_user_session(*, guest_user, product_store: ProductStore) -> None:
    """把 Streamlit OIDC cookie 映射到目前的本地產品 session。"""
    oidc_identity = current_oidc_identity()
    current_login_method = str(st.session_state.get("auth_login_method", "guest"))
    current_user_id = int(st.session_state.get("auth_user_id", int(guest_user.id)))
    pending_link_user_id = int(st.session_state.get("auth_pending_oidc_link_user_id", 0) or 0)
    if oidc_identity is None:
        if current_login_method == "oidc" and current_user_id != int(guest_user.id):
            st.session_state.show_auth_dialog = False
            clear_pending_oidc_link()
            activate_user_session(
                user=guest_user,
                product_store=product_store,
                success_message="已登出，目前切回訪客模式。",
            )
            st.rerun()
        return

    if (
        current_login_method == "password"
        and current_user_id != int(guest_user.id)
        and not pending_link_user_id
    ):
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

    link_user_id = (
        current_user_id
        if pending_link_user_id and pending_link_user_id == current_user_id
        else None
    )
    try:
        user = product_store.authenticate_oidc_user(
            provider=str(oidc_identity["provider"]),
            subject=str(oidc_identity["subject"]),
            email=str(oidc_identity["email"]),
            display_name=str(oidc_identity["display_name"]),
            email_verified=bool(oidc_identity["email_verified"]),
            link_user_id=link_user_id,
        )
    except ValueError as exc:
        clear_pending_oidc_link()
        set_auth_feedback(error=str(exc))
        st.session_state.show_auth_dialog = True
        if current_login_method != "password" or current_user_id == int(guest_user.id):
            activate_user_session(
                user=guest_user,
                product_store=product_store,
                success_message="",
            )
        st.logout()
        return

    clear_pending_oidc_link()
    st.session_state.show_auth_dialog = False
    activate_user_session(
        user=user,
        product_store=product_store,
        success_message="",
        login_method="oidc",
        oidc_provider=str(oidc_identity["provider"]),
        oidc_subject=str(oidc_identity["subject"]),
    )
    st.rerun()


def is_valid_email(value: str) -> bool:
    cleaned = str(value or "").strip()
    return bool(cleaned) and "@" in cleaned and "." in cleaned.split("@")[-1]


def render_auth_feedback() -> None:
    error = str(st.session_state.get("auth_form_error", "")).strip()
    success = str(st.session_state.get("auth_form_success", "")).strip()
    if error:
        st.markdown(
            f"<div class='auth-feedback auth-feedback--error'>{_escape(error)}</div>",
            unsafe_allow_html=True,
        )
    elif success:
        st.markdown(
            f"<div class='auth-feedback auth-feedback--success'>{_escape(success)}</div>",
            unsafe_allow_html=True,
        )


def render_field_error(field_key: str) -> None:
    field_errors = st.session_state.get("auth_form_field_errors", {}) or {}
    message = str(field_errors.get(field_key, "")).strip()
    if not message:
        return
    st.markdown(
        f"<div class='auth-field-error'>{_escape(message)}</div>",
        unsafe_allow_html=True,
    )


def render_auth_dev_marker(
    *,
    name: str,
    element_id: str,
    description: str,
    popover_key: str | None = None,
) -> None:
    render_dev_card_annotation(
        name,
        element_id=element_id,
        description=description,
        show_popover=True,
        popover_key=popover_key or element_id,
        compact=True,
    )
