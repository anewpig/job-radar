from __future__ import annotations

import base64
import hashlib
import hmac
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import Settings  # noqa: E402
from job_spy_tw.line_webhook import (  # noqa: E402
    extract_line_bind_code,
    handle_line_event,
    verify_line_signature,
)
from job_spy_tw.notification_service import NotificationService  # noqa: E402
from job_spy_tw.product_store import ProductStore  # noqa: E402


class LineWebhookTests(unittest.TestCase):
    def _settings(self) -> Settings:
        return Settings(
            data_dir=Path(tempfile.mkdtemp()),
            request_timeout=20.0,
            request_delay=1.0,
            max_concurrent_requests=4,
            max_pages_per_source=1,
            max_detail_jobs_per_source=0,
            min_relevance_score=18.0,
            location="台灣",
            enable_linkedin=True,
            allow_insecure_ssl_fallback=True,
            user_agent="test-agent",
            openai_api_key="",
            openai_base_url="",
            resume_llm_model="gpt-4.1-mini",
            title_similarity_model="gpt-4.1-mini",
            embedding_model="text-embedding-3-large",
            assistant_model="gpt-4.1-mini",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="user",
            smtp_password="pass",
            smtp_from_email="noreply@example.com",
            notification_email_to="user@example.com",
            smtp_use_tls=True,
            smtp_use_ssl=False,
            line_channel_access_token="line-token",
            line_channel_secret="line-secret",
            line_to="",
            public_base_url="https://example.ngrok.app",
            line_webhook_host="0.0.0.0",
            line_webhook_port=8787,
        )

    def test_verify_line_signature(self) -> None:
        body = b'{"events":[]}'
        signature = base64.b64encode(
            hmac.new(b"line-secret", body, hashlib.sha256).digest()
        ).decode("utf-8")
        self.assertTrue(verify_line_signature("line-secret", body, signature))
        self.assertFalse(verify_line_signature("line-secret", body, "bad-signature"))

    def test_extract_line_bind_code(self) -> None:
        self.assertEqual(extract_line_bind_code("綁定 LINE-ABC123"), "LINE-ABC123")
        self.assertEqual(extract_line_bind_code("line-xyz789"), "LINE-XYZ789")
        self.assertEqual(extract_line_bind_code("你好"), "")

    def test_handle_line_event_binds_user_id(self) -> None:
        settings = self._settings()
        store = ProductStore(settings.product_state_db_path)
        user = store.register_user(
            email="line@example.com",
            password="password123",
            display_name="line",
        )
        preferences = store.issue_line_bind_code(user_id=user.id, ttl_minutes=15)
        replies: list[tuple[str, str]] = []
        service = NotificationService(
            settings,
            line_sender=lambda body, target: None,
        )
        service.reply_line_text = lambda reply_token, body: replies.append((reply_token, body))  # type: ignore[method-assign]

        result = handle_line_event(
            {
                "type": "message",
                "replyToken": "reply-token",
                "source": {"type": "user", "userId": "U1234567890"},
                "message": {"type": "text", "text": f"綁定 {preferences.line_bind_code}"},
            },
            store=store,
            notification_service=service,
        )

        self.assertEqual(result["status"], "bound")
        self.assertEqual(
            store.get_notification_preferences(user_id=user.id).line_target,
            "U1234567890",
        )
        self.assertEqual(store.get_notification_preferences().line_target, "")
        self.assertEqual(len(replies), 1)
        self.assertIn("綁定成功", replies[0][1])


if __name__ == "__main__":
    unittest.main()
