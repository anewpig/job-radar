"""提供通知設定頁面的 section render helper。"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from .common import _escape, build_chip_row, mask_identifier
from .dev_annotations import render_dev_card_annotation
from .page_context import PageContext


@dataclass(slots=True)
class NotificationRenderState:
    site_enabled: bool
    line_is_bound: bool
    auto_bind_available: bool
    current_email_recipients: str
    current_line_target: str
    current_line_bound: bool
    channel_status_items: list[str]
    validation_messages: list[str]


def _build_notification_render_state(ctx: PageContext) -> NotificationRenderState:
    site_enabled = st.session_state.notify_site_enabled
    current_email_recipients = st.session_state.notify_email_recipients
    current_line_target = st.session_state.notify_line_target
    current_line_bound = ctx.notification_service.is_valid_line_target(current_line_target)
    auto_bind_available = bool(
        ctx.settings.line_channel_secret
        and ctx.settings.public_base_url
        and ctx.notification_service.line_service_configured
    )
    channel_status_items = [
        f"站內通知 {'開啟' if site_enabled else '關閉'}",
        f"Email {'可用' if ctx.notification_service.email_service_configured else '尚未就緒'}",
        f"LINE {'已綁定' if current_line_bound else '尚未綁定'}",
        "重新抓取已儲存搜尋時會檢查新職缺",
    ]
    validation_messages: list[str] = []
    if st.session_state.notify_email_enabled and not ctx.notification_service.email_service_configured:
        validation_messages.append("平台目前尚未完成 Email 寄件設定。")
    elif st.session_state.notify_email_enabled and not ctx.notification_service.resolve_recipient_emails(
        current_email_recipients
    ):
        validation_messages.append("請先填寫至少一個通知 Email。")
    if st.session_state.notify_line_enabled and not ctx.notification_service.line_service_configured:
        validation_messages.append("平台目前尚未完成 LINE 推播設定。")
    elif st.session_state.notify_line_enabled and not current_line_bound:
        validation_messages.append("請先填寫有效的 LINE 收件者 ID，或完成 LINE 綁定。")
    return NotificationRenderState(
        site_enabled=site_enabled,
        line_is_bound=current_line_bound,
        auto_bind_available=auto_bind_available,
        current_email_recipients=current_email_recipients,
        current_line_target=current_line_target,
        current_line_bound=current_line_bound,
        channel_status_items=channel_status_items,
        validation_messages=validation_messages,
    )


def _render_notifications_intro(ctx: PageContext, state: NotificationRenderState) -> None:
    render_dev_card_annotation(
        "通知設定頁主卡",
        element_id="notifications-shell",
        description="通知設定頁的外層卡片，包含頁首、狀態 tag、三步驟設定與測試送出。",
        layers=[
            "notifications-body",
            "notification setup steps",
            "test notification actions",
        ],
        text_nodes=[
            ("section-kicker", "頁首小標。"),
            ("section-title", "頁面主標題。"),
            ("section-desc", "頁面說明文字。"),
            ("ui-chip ui-chip--warm", "目前通知狀態 tag。"),
        ],
        show_popover=True,
        popover_key="notifications-shell",
    )
    st.markdown(
        f"""
<div class="section-shell notifications-intro">
  <div class="section-kicker">{_escape("Notification Settings")}</div>
  <div class="section-title">{_escape("通知設定")}</div>
  <div class="section-desc">{_escape("設定哪些新職缺值得提醒你，並決定站內、Email、LINE 哪些通道要啟用。")}</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="notifications-body"):
        if ctx.current_user_is_guest:
            st.info("登入後才能保存自己的通知條件，並綁定 Email 或 LINE 推播。")
        st.markdown(
            f"<div class='chip-row'>{build_chip_row(state.channel_status_items, tone='warm', limit=4)}</div>",
            unsafe_allow_html=True,
        )


def _render_notification_channel_step() -> None:
    with st.container():
        render_dev_card_annotation(
            "通知方式設定卡",
            element_id="notifications-step-channel",
            description="第一步，控制站內 / Email / LINE 哪些通道要開啟。",
            layers=["notify_site_enabled", "notify_email_enabled", "notify_line_enabled"],
            text_nodes=[
                ("1. 選擇通知方式", "步驟標題。"),
                ("checkbox label", "各通知通道的開關文字。"),
            ],
            compact=True,
            show_popover=True,
            popover_key="notifications-step-channel",
        )
        st.markdown("**1. 選擇通知方式**")
        st.caption("先決定哪些提醒方式要開啟。")
        st.checkbox(
            "站內通知",
            key="notify_site_enabled",
            help="重新抓取同一組已儲存搜尋後，會在站內建立新職缺通知。",
        )
        st.checkbox(
            "Email 推播",
            key="notify_email_enabled",
            help="有新職缺時寄到你的通知信箱。",
        )
        st.checkbox(
            "LINE 推播",
            key="notify_line_enabled",
            help="有新職缺時直接推送到 LINE。",
        )


def _render_notification_destination_step(
    ctx: PageContext,
    state: NotificationRenderState,
) -> dict[str, bool]:
    actions = {
        "generate_bind_code": False,
        "clear_line_binding": False,
        "refresh_line_binding": False,
    }
    with st.container():
        render_dev_card_annotation(
            "通知收件設定卡",
            element_id="notifications-step-destination",
            description="第二步，設定 Email 收件者或 LINE 綁定資訊。",
            layers=[
                "notify_email_recipients",
                "notify_line_target",
                "line binding actions",
            ],
            text_nodes=[
                ("2. 收件設定", "步驟標題。"),
                ("通知 Email", "Email 輸入欄位標籤。"),
                ("LINE 收件者 ID / 綁定 ID", "LINE 欄位標籤。"),
            ],
            compact=True,
            show_popover=True,
            popover_key="notifications-step-destination",
        )
        st.markdown("**2. 收件設定**")
        st.caption("只會顯示你目前有開啟的通知方式。")
        if st.session_state.notify_email_enabled:
            if not ctx.notification_service.email_service_configured:
                st.info("Email 推播尚未完全就緒，先填通知 Email 也可以，之後可直接啟用。")
            st.text_input(
                "通知 Email",
                key="notify_email_recipients",
                placeholder="例如：me@example.com, hr@example.com",
                help="可填一個或多個 Email，逗號分隔。",
            )
        if st.session_state.notify_line_enabled:
            st.text_input(
                "LINE 收件者 ID / 綁定 ID",
                key="notify_line_target",
                placeholder="例如：Uxxxxxxxxxxxx",
                help="如果你已經有 LINE 收件者 ID，可以直接貼上。",
            )
            if state.current_line_bound:
                st.success(
                    "目前 LINE 已可推播："
                    + mask_identifier(state.current_line_target, prefix=3, suffix=4)
                )
            elif state.auto_bind_available:
                st.caption("也可以用自動綁定，系統會幫你寫回真正的 LINE userId。")
                bind_action_cols = st.columns(3)
                actions["generate_bind_code"] = bind_action_cols[0].button(
                    "產生綁定碼",
                    key="generate-line-bind-code",
                    use_container_width=True,
                    disabled=ctx.current_user_is_guest,
                )
                actions["clear_line_binding"] = bind_action_cols[1].button(
                    "解除綁定",
                    key="clear-line-binding",
                    use_container_width=True,
                    disabled=ctx.current_user_is_guest,
                )
                actions["refresh_line_binding"] = bind_action_cols[2].button(
                    "重新整理",
                    key="refresh-line-binding",
                    use_container_width=True,
                )
                if ctx.notification_preferences.line_bind_code:
                    st.info("把下面這串訊息傳給 LINE Bot，就能完成綁定。")
                    st.code(f"綁定 {ctx.notification_preferences.line_bind_code}")
                    if ctx.notification_preferences.line_bind_expires_at:
                        st.caption(
                            f"有效期限到：{ctx.notification_preferences.line_bind_expires_at}"
                        )
                else:
                    st.caption("如果你還沒綁定，可以先按上方的「產生綁定碼」。")
            else:
                st.info("目前先填入 LINE 收件者 ID 即可，之後也可以再補自動綁定。")
        if not st.session_state.notify_email_enabled and not st.session_state.notify_line_enabled:
            st.caption("開啟 Email 或 LINE 推播後，這裡就會出現對應的收件設定。")
    return actions


def _render_notification_rules_step() -> None:
    with st.container():
        render_dev_card_annotation(
            "通知條件卡",
            element_id="notifications-step-rules",
            description="第三步，設定最低分數與每次最多通知筆數。",
            layers=[
                "notify_min_score",
                "notify_max_jobs",
            ],
            text_nodes=[
                ("3. 通知條件", "步驟標題。"),
                ("最低相關分數", "分數 slider 標籤。"),
                ("每次通知最多幾筆", "筆數 slider 標籤。"),
            ],
            compact=True,
            show_popover=True,
            popover_key="notifications-step-rules",
        )
        st.markdown("**3. 通知條件**")
        st.caption("控制要提醒多少筆，以及哪些分數以上才通知。")
        st.slider(
            "最低相關分數",
            min_value=0,
            max_value=100,
            step=1,
            key="notify_min_score",
            help="低於這個分數的新職缺不會進通知。",
        )
        st.slider(
            "每次通知最多幾筆",
            min_value=1,
            max_value=20,
            step=1,
            key="notify_max_jobs",
        )
        st.info("目前通知會在你重新抓取同一組已儲存搜尋後立即檢查。")


def _render_notification_test_section(
    ctx: PageContext,
    state: NotificationRenderState,
) -> dict[str, bool]:
    st.divider()
    st.markdown("**4. 測試通知**")
    st.caption("確認設定是否能送達，不需要等到真的出現新職缺。")
    test_cols = st.columns(2)
    send_test_email = test_cols[0].button(
        "發送 Email 測試",
        use_container_width=True,
        disabled=ctx.current_user_is_guest or not st.session_state.notify_email_enabled,
    )
    send_test_line = test_cols[1].button(
        "發送 LINE 測試",
        use_container_width=True,
        disabled=ctx.current_user_is_guest or not st.session_state.notify_line_enabled,
    )
    for message in state.validation_messages:
        st.warning(message)
    return {
        "send_test_email": send_test_email,
        "send_test_line": send_test_line,
    }


def _render_notification_footer(*, current_user_is_guest: bool) -> bool:
    st.divider()
    action_cols = st.columns([1.4, 1.2, 1.4], gap="medium")
    return action_cols[1].button(
        "儲存通知條件",
        type="primary",
        use_container_width=True,
        disabled=current_user_is_guest,
    )
