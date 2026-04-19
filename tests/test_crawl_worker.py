"""Tests for crawl worker loop orchestration."""

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
from job_spy_tw import crawl_worker  # noqa: E402


class _SignalStoreStub:
    def __init__(self) -> None:
        self.signals: list[dict[str, object]] = []

    def put_signal(self, **kwargs) -> None:
        self.signals.append(kwargs)


class _QueueStub:
    def __init__(self, job) -> None:
        self.job = job

    def lease_job(self, worker_id: str):
        del worker_id
        job = self.job
        self.job = None
        return job


class CrawlWorkerTests(unittest.TestCase):
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
        )

    def test_run_worker_loop_once_idle_returns_zero_and_emits_idle_signal(self) -> None:
        settings = self._settings()
        signal_store = _SignalStoreStub()
        logger = mock.Mock()

        with mock.patch.object(crawl_worker, "load_settings", return_value=settings):
            with mock.patch.object(crawl_worker, "configure_logging", return_value=logger):
                with mock.patch.object(
                    crawl_worker,
                    "build_query_runtime",
                    return_value=(object(), _QueueStub(None)),
                ):
                    with mock.patch.object(
                        crawl_worker,
                        "RuntimeSignalStore",
                        return_value=signal_store,
                    ):
                        with mock.patch.object(crawl_worker, "run_runtime_cleanup") as cleanup:
                            result = crawl_worker.run_worker_loop(
                                base_dir=".",
                                worker_id="worker-1",
                                poll_interval=2.5,
                                once=True,
                            )

        self.assertEqual(result, 0)
        cleanup.assert_called_once()
        self.assertEqual(len(signal_store.signals), 1)
        self.assertEqual(signal_store.signals[0]["status"], "idle")
        self.assertEqual(signal_store.signals[0]["payload"]["poll_interval"], 2.5)
        logger.info.assert_called_once_with("No pending crawl job found.")

    def test_run_worker_loop_once_processes_completed_job(self) -> None:
        settings = self._settings()
        signal_store = _SignalStoreStub()
        logger = mock.Mock()
        job = SimpleNamespace(id=12, query_signature="sig-worker")

        with mock.patch.object(crawl_worker, "load_settings", return_value=settings):
            with mock.patch.object(crawl_worker, "configure_logging", return_value=logger):
                with mock.patch.object(
                    crawl_worker,
                    "build_query_runtime",
                    return_value=(object(), _QueueStub(job)),
                ):
                    with mock.patch.object(
                        crawl_worker,
                        "RuntimeSignalStore",
                        return_value=signal_store,
                    ):
                        with mock.patch.object(crawl_worker, "run_runtime_cleanup"):
                            with mock.patch.object(
                                crawl_worker,
                                "process_queued_crawl_job",
                                return_value=SimpleNamespace(
                                    status="completed",
                                    snapshot=SimpleNamespace(jobs=[1, 2, 3]),
                                ),
                            ):
                                result = crawl_worker.run_worker_loop(
                                    base_dir=".",
                                    worker_id="worker-2",
                                    poll_interval=1.0,
                                    once=True,
                                )

        self.assertEqual(result, 0)
        self.assertEqual([signal["status"] for signal in signal_store.signals], ["processing", "completed"])
        self.assertEqual(signal_store.signals[1]["payload"]["job_count"], 3)
        logger.info.assert_any_call(
            "Processing crawl job #%s for signature %s",
            12,
            "sig-worker",
        )
        logger.info.assert_any_call("Completed crawl job #%s with %s jobs.", 12, 3)


if __name__ == "__main__":
    unittest.main()
