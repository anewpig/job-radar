"""Third-party/social auth views."""

from __future__ import annotations

import streamlit as st

from .auth_state import oidc_provider_available, render_auth_dev_marker
from .common import _escape
from .dev_annotations import render_dev_card_annotation


def _provider_status_copy(provider: str) -> str:
    if provider == "google":
        return "可直接用 Google 帳號登入工作台。"
    return "可用 Facebook 帳號登入；若尚未開通會顯示為不可用。"


def _provider_unavailable_copy(provider: str) -> str:
    if provider == "google":
        return "Google 登入尚未開通。"
    return "Facebook 登入尚未開通，通常需要先接上 OIDC broker。"


def render_social_login_panel() -> None:
    """Render social login / OIDC cards."""
    st.markdown(
        """
<div class="auth-page-pane auth-page-pane--brand">
  <div class="auth-page-kicker">Job Search Workspace</div>
  <div class="auth-page-brand-row">
    <div class="auth-dialog-logo">JR</div>
    <div>
      <div class="auth-page-title">職缺雷達</div>
      <div class="auth-page-subtitle">登入你的求職工作台</div>
    </div>
  </div>
  <div class="auth-page-copy">
    整合職缺搜尋、履歷匹配、AI 助理與投遞追蹤，讓你用同一個入口管理整個求職流程。
  </div>
  <div class="auth-page-trust-row">
    <span class="auth-page-trust-pill">整合 104 / 1111 / Cake / LinkedIn</span>
    <span class="auth-page-trust-pill">保存搜尋、收藏與通知設定</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    provider_rows = [
        ("google", "使用 Google 登入", oidc_provider_available("google")),
        ("facebook", "使用 Facebook 登入", oidc_provider_available("facebook")),
    ]
    for provider, label, enabled in provider_rows:
        shell_key = f"dialog-{provider}-login-shell"
        with st.container(key=shell_key):
            render_auth_dev_marker(
                name="第三方登入標題",
                element_id="auth-social-title",
                description="第三方登入卡片標題。",
                popover_key=f"auth-social-title-{provider}",
            )
            render_dev_card_annotation(
                f"{label} 卡片",
                element_id=shell_key,
                description=f"{label} 的第三方登入卡片與按鈕。",
                text_nodes=[
                    ("auth-social-title", "第三方登入卡片標題。"),
                    ("auth-social-desc", "第三方登入卡片描述。"),
                ],
                notes=[
                    "按鈕是否可用取決於目前的 OIDC 設定。",
                ],
                show_popover=True,
                popover_key=shell_key,
                compact=True,
            )
            st.markdown(
                f"""
<div class="auth-social-card">
  <div class="auth-social-copy">
    <div class="auth-social-title">{_escape(label)}</div>
    <div class="auth-social-desc">{_escape(_provider_status_copy(provider) if enabled else _provider_unavailable_copy(provider))}</div>
  </div>
</div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                label,
                key=f"dialog-{provider}-login-button",
                use_container_width=True,
                disabled=not enabled,
                type="secondary",
            ):
                st.login(provider)
