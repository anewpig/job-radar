"""認證 UI 的相容入口。"""

from __future__ import annotations

import streamlit as st

from ..notification_service import NotificationService
from ..product_store import ProductStore
from .auth_credentials_views import (
    render_credentials_panel_tabs,
    render_login_view,
    render_register_view,
)
from .auth_reset_views import (
    render_forgot_confirm_view,
    render_forgot_request_view,
)
from .auth_social_views import render_social_login_panel
from .auth_state import (
    AUTH_VIEW_FORGOT_REQUEST,
    AUTH_VIEW_LOGIN,
    AUTH_VIEW_REGISTER,
    render_auth_feedback,
)


def render_credentials_panel(
    *,
    product_store: ProductStore,
    notification_service: NotificationService,
) -> None:
    """Render password-based auth panel by current auth view."""
    current_view = str(st.session_state.get("auth_view_mode", AUTH_VIEW_LOGIN))
    render_auth_feedback()

    if current_view in {AUTH_VIEW_LOGIN, AUTH_VIEW_REGISTER}:
        render_credentials_panel_tabs(current_view=current_view)
        if current_view == AUTH_VIEW_LOGIN:
            render_login_view(product_store=product_store)
        else:
            render_register_view(product_store=product_store)
        return

    if current_view == AUTH_VIEW_FORGOT_REQUEST:
        render_forgot_request_view(
            product_store=product_store,
            notification_service=notification_service,
        )
        return

    render_forgot_confirm_view(product_store=product_store)
