"""Tests for crawl scheduler loop orchestration."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import Settings  # noqa: E402
from job_spy_tw import crawl_scheduler  # noqa: E402


class _SignalStoreStub:
    def __init__(self) -> None:
        self.signals: list[dict[str, object]] = []

    def put_signal(self, **kwargs) -> None:
        self.signals.append(kwargs)


class CrawlSchedulerTests(unittest.TestCase):
    def _settings(self) -> Settings:
        return Settings(
            data_dir=Path(tempfile.mkdtemp()),
            request_timeout=5.0,
            request_delay=0.2,
            max_concurrent_requests=4,
            max_pages_per_source=2,
            max_detail_jobs_per_source=8,
            min_relevance_score=0.0,
            location="台灣",
            enable_cake=True,
            enable_linkedin=True,
            allow_insecure_ssl_fallback=True,
            user_agent="test-agent",
            openai_api_key="",
            openai_base_url="",
            resume_llm_model="gpt-4.1-mini",
            title_similarity_model="gpt-4.1-mini",
            embedding_model="text-embedding-3-large",
            assistant_model="gpt-4.1-mini",
            crawl_execution_mode="worker",
        )

    def test_run_scheduler_loop_once_emits_completed_signal_and_logs_details(self) -> None:
        settings = self._settings()
        signal_store = _SignalStoreStub()
        logger = mock.Mock()
        scheduled_result = SimpleNamespace(
            checked_count=2,
            enqueued_count=1,
            skipped_count=1,
            invalid_count=0,
            details=["Enqueued 每日 AI 追蹤", "Skipped 共同搜尋"],
        )

        with mock.patch.object(crawl_scheduler, "load_settings", return_value=settings):
            with mock.patch.object(
                crawl_scheduler,
                "configure_logging",
                return_value=logger,
            ):
                with mock.patch.object(
                    crawl_scheduler,
                    "ProductStore",
                    return_value=SimpleNamespace(),
                ):
                    with mock.patch.object(
                        crawl_scheduler,
                        "RuntimeSignalStore",
                        return_value=signal_store,
                    ):
                        with mock.patch.object(crawl_scheduler, "run_runtime_cleanup") as cleanup:
                            with mock.patch.object(
                                crawl_scheduler,
                                "schedule_due_saved_searches",
                                return_value=scheduled_result,
                            ):
                                result = crawl_scheduler.run_scheduler_loop(
                                    base_dir=".",
                                    worker_id="scheduler-1",
                                    poll_interval=60.0,
                                    once=True,
                                )

        self.assertEqual(result, 0)
        cleanup.assert_called_once()
        self.assertEqual(len(signal_store.signals), 1)
        self.assertEqual(signal_store.signals[0]["status"], "completed")
        self.assertEqual(signal_store.signals[0]["payload"]["enqueued_count"], 1)
        logger.info.assert_any_call(
            "Scheduler pass: checked=%s enqueued=%s skipped=%s invalid=%s",
            2,
            1,
            1,
            0,
        )
        logger.info.assert_any_call("Enqueued 每日 AI 追蹤")
        logger.info.assert_any_call("Skipped 共同搜尋")

    def test_run_scheduler_loop_once_marks_idle_when_no_due_searches(self) -> None:
        settings = self._settings()
        signal_store = _SignalStoreStub()
        logger = mock.Mock()
        scheduled_result = SimpleNamespace(
            checked_count=0,
            enqueued_count=0,
            skipped_count=0,
            invalid_count=0,
            details=[],
        )

        with mock.patch.object(crawl_scheduler, "load_settings", return_value=settings):
            with mock.patch.object(
                crawl_scheduler,
                "configure_logging",
                return_value=logger,
            ):
                with mock.patch.object(
                    crawl_scheduler,
                    "ProductStore",
                    return_value=SimpleNamespace(),
                ):
                    with mock.patch.object(
                        crawl_scheduler,
                        "RuntimeSignalStore",
                        return_value=signal_store,
                    ):
                        with mock.patch.object(crawl_scheduler, "run_runtime_cleanup"):
                            with mock.patch.object(
                                crawl_scheduler,
                                "schedule_due_saved_searches",
                                return_value=scheduled_result,
                            ):
                                result = crawl_scheduler.run_scheduler_loop(
                                    base_dir=".",
                                    worker_id="scheduler-2",
                                    poll_interval=60.0,
                                    once=True,
                                )

        self.assertEqual(result, 0)
        self.assertEqual(signal_store.signals[0]["status"], "idle")


if __name__ == "__main__":
    unittest.main()
