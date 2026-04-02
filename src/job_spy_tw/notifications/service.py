from __future__ import annotations

import json
import ssl
from typing import Callable
from urllib import error, request

from ..settings import Settings
from .email_channel import send_email_message
from .line_channel import (
    build_secure_ssl_context,
    open_line_request,
    should_retry_without_ssl_verification,
)
from .message_builder import (
    build_alert_message,
    is_valid_line_target,
    resolve_line_target,
    resolve_recipient_emails,
)


class NotificationService:
    def __init__(
        self,
        settings: Settings,
        *,
        email_sender: Callable[[str, str, list[str]], None] | None = None,
        line_sender: Callable[[str, str], None] | None = None,
    ) -> None:
        self.settings = settings
        self._email_sender = email_sender or self._send_email
        self._line_sender = line_sender or self._send_line_to

    @property
    def email_configured(self) -> bool:
        return self.can_send_email()

    @property
    def line_configured(self) -> bool:
        return self.can_send_line()

    @property
    def email_service_configured(self) -> bool:
        return bool(self.settings.smtp_host and self.settings.smtp_from_email)

    @property
    def line_service_configured(self) -> bool:
        return bool(self.settings.line_channel_access_token)

    @property
    def recipient_emails(self) -> list[str]:
        return self.resolve_recipient_emails()

    def resolve_recipient_emails(self, recipients_text: str = "") -> list[str]:
        return resolve_recipient_emails(self.settings, recipients_text)

    def resolve_line_target(self, line_target: str = "") -> str:
        return resolve_line_target(self.settings, line_target)

    def is_valid_line_target(self, line_target: str = "") -> bool:
        return is_valid_line_target(self.settings, line_target)

    def can_send_email(self, recipients_text: str = "") -> bool:
        return bool(self.email_service_configured and self.resolve_recipient_emails(recipients_text))

    def can_send_line(self, line_target: str = "") -> bool:
        return bool(self.line_service_configured and self.is_valid_line_target(line_target))

    def send_new_job_alert(
        self,
        *,
        search_name: str,
        new_jobs: list[dict],
        email_enabled: bool = True,
        line_enabled: bool = True,
        email_recipients_text: str = "",
        line_target: str = "",
        max_jobs: int = 8,
    ) -> dict[str, object]:
        notes: list[str] = []
        email_sent = False
        line_sent = False
        if not new_jobs:
            return {"email_sent": False, "line_sent": False, "notes": ["沒有新職缺可通知。"]}

        selected_jobs = new_jobs[:max_jobs] if max_jobs > 0 else new_jobs
        message = self._build_message(search_name, selected_jobs)
        recipients = self.resolve_recipient_emails(email_recipients_text)
        resolved_line_target = self.resolve_line_target(line_target)
        if email_enabled and self.can_send_email(email_recipients_text):
            try:
                self._email_sender(
                    f"職缺雷達通知｜{search_name} 有 {len(selected_jobs)} 筆新職缺",
                    message,
                    recipients,
                )
                email_sent = True
            except Exception as exc:  # noqa: BLE001
                notes.append(f"Email 推播失敗：{exc}")
        elif email_enabled:
            if not self.email_service_configured:
                notes.append("Email 服務尚未設定。")
            else:
                notes.append("尚未填寫 Email 收件地址。")
        else:
            notes.append("Email 推播已停用。")

        if line_enabled and self.can_send_line(line_target):
            try:
                self._line_sender(message, resolved_line_target)
                line_sent = True
            except Exception as exc:  # noqa: BLE001
                notes.append(f"LINE 推播失敗：{exc}")
        elif line_enabled:
            if not self.line_service_configured:
                notes.append("LINE 服務尚未設定。")
            else:
                notes.append("尚未綁定 LINE 收件者。")
        else:
            notes.append("LINE 推播已停用。")

        if email_sent:
            notes.append("Email 推播成功。")
        if line_sent:
            notes.append("LINE 推播成功。")
        return {
            "email_sent": email_sent,
            "line_sent": line_sent,
            "notes": notes,
        }

    def send_password_reset_code(self, *, email: str, reset_code: str) -> None:
        if not self.email_service_configured:
            raise RuntimeError("Email 服務尚未設定，暫時無法寄送重設碼。")
        body = (
            "你剛剛在職缺雷達申請重設密碼。\n\n"
            f"重設碼：{reset_code}\n"
            "有效時間為 15 分鐘。\n"
            "如果這不是你本人操作，可以忽略這封信。"
        )
        self._email_sender(
            "職缺雷達｜密碼重設碼",
            body,
            [email.strip()],
        )

    def _build_message(self, search_name: str, new_jobs: list[dict]) -> str:
        return build_alert_message(search_name, new_jobs)

    def _send_email(self, subject: str, body: str, recipients: list[str]) -> None:
        send_email_message(self.settings, subject, body, recipients)

    def _send_line_to(self, body: str, line_target: str) -> None:
        self._post_line_json(
            "https://api.line.me/v2/bot/message/push",
            {
                "to": line_target,
                "messages": [{"type": "text", "text": body[:4500]}],
            },
        )

    def reply_line_text(self, reply_token: str, body: str) -> None:
        self._post_line_json(
            "https://api.line.me/v2/bot/message/reply",
            {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": body[:4500]}],
            },
        )

    def _post_line_json(self, url: str, payload_obj: dict[str, object]) -> None:
        payload = json.dumps(payload_obj).encode("utf-8")
        req = request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.line_channel_access_token}",
            },
            method="POST",
        )
        secure_context = self._build_secure_ssl_context()
        try:
            self._open_line_request(req, secure_context)
        except error.URLError as exc:
            if not self._should_retry_without_ssl_verification(exc):
                raise
            insecure_context = ssl._create_unverified_context()
            self._open_line_request(req, insecure_context)

    def _build_secure_ssl_context(self) -> ssl.SSLContext:
        return build_secure_ssl_context()

    def _should_retry_without_ssl_verification(self, exc: Exception) -> bool:
        return should_retry_without_ssl_verification(self.settings, exc)

    def _open_line_request(
        self,
        req: request.Request,
        ssl_context: ssl.SSLContext,
    ) -> None:
        open_line_request(req, ssl_context)
