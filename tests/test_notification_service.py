from __future__ import annotations

import ssl
import sys
import unittest
from pathlib import Path
from urllib import error

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import Settings  # noqa: E402
from job_spy_tw.notification_service import NotificationService  # noqa: E402


class NotificationServiceTests(unittest.TestCase):
    def _settings(self) -> Settings:
        return Settings(
            data_dir=ROOT / "data",
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
            line_to="U1234567890",
        )

    def test_send_new_job_alert_uses_email_and_line_channels(self) -> None:
        email_calls: list[tuple[str, str, list[str]]] = []
        line_calls: list[tuple[str, str]] = []
        service = NotificationService(
            self._settings(),
            email_sender=lambda subject, body, recipients: email_calls.append(
                (subject, body, recipients)
            ),
            line_sender=lambda body, target: line_calls.append((body, target)),
        )

        result = service.send_new_job_alert(
            search_name="AI追蹤",
            new_jobs=[
                {
                    "title": "AI工程師",
                    "company": "Example AI",
                    "source": "104",
                    "location": "台北市",
                    "url": "https://example.com/jobs/1",
                }
            ],
        )

        self.assertTrue(result["email_sent"])
        self.assertTrue(result["line_sent"])
        self.assertEqual(len(email_calls), 1)
        self.assertEqual(len(line_calls), 1)
        self.assertIn("AI追蹤", email_calls[0][0])
        self.assertIn("AI工程師", line_calls[0][0])
        self.assertEqual(line_calls[0][1], "U1234567890")

    def test_send_new_job_alert_respects_channel_flags(self) -> None:
        email_calls: list[tuple[str, str, list[str]]] = []
        line_calls: list[tuple[str, str]] = []
        service = NotificationService(
            self._settings(),
            email_sender=lambda subject, body, recipients: email_calls.append(
                (subject, body, recipients)
            ),
            line_sender=lambda body, target: line_calls.append((body, target)),
        )

        result = service.send_new_job_alert(
            search_name="AI追蹤",
            new_jobs=[{"title": "AI工程師", "company": "A", "source": "104", "url": "u"}],
            email_enabled=False,
            line_enabled=True,
            max_jobs=1,
        )

        self.assertFalse(result["email_sent"])
        self.assertTrue(result["line_sent"])
        self.assertEqual(len(email_calls), 0)
        self.assertEqual(len(line_calls), 1)

    def test_send_new_job_alert_uses_user_provided_destinations(self) -> None:
        email_calls: list[tuple[str, str, list[str]]] = []
        line_calls: list[tuple[str, str]] = []
        service = NotificationService(
            self._settings(),
            email_sender=lambda subject, body, recipients: email_calls.append(
                (subject, body, recipients)
            ),
            line_sender=lambda body, target: line_calls.append((body, target)),
        )

        result = service.send_new_job_alert(
            search_name="藥師追蹤",
            new_jobs=[{"title": "藥師", "company": "A", "source": "104", "url": "u"}],
            email_recipients_text="first@example.com; second@example.com",
            line_target="U9999999999",
        )

        self.assertTrue(result["email_sent"])
        self.assertTrue(result["line_sent"])
        self.assertEqual(email_calls[0][2], ["first@example.com", "second@example.com"])
        self.assertEqual(line_calls[0][1], "U9999999999")

    def test_send_line_retries_with_insecure_ssl_context(self) -> None:
        service = NotificationService(self._settings())
        seen_contexts: list[ssl.SSLContext] = []

        def fake_open(_req, ssl_context):
            seen_contexts.append(ssl_context)
            if len(seen_contexts) == 1:
                raise error.URLError("CERTIFICATE_VERIFY_FAILED")

        service._open_line_request = fake_open  # type: ignore[method-assign]

        service._send_line_to("hello", "U1234567890")

        self.assertEqual(len(seen_contexts), 2)
        self.assertTrue(seen_contexts[0].check_hostname)
        self.assertFalse(seen_contexts[1].check_hostname)


if __name__ == "__main__":
    unittest.main()
