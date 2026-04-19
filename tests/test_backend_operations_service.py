"""Tests for backend operations monitoring helpers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.backend_operations_service import collect_backend_operations_snapshot  # noqa: E402
from job_spy_tw.config import Settings  # noqa: E402
from job_spy_tw.models import (  # noqa: E402
    JobListing,
    MarketSnapshot,
    NotificationPreference,
    TargetRole,
)
from job_spy_tw.product_store import ProductStore  # noqa: E402
from job_spy_tw.query_runtime import (  # noqa: E402
    CrawlJobQueue,
    QuerySnapshotRegistry,
    RuntimeSignalStore,
)


class BackendOperationsServiceTests(unittest.TestCase):
    def build_settings(self) -> Settings:
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

    def _snapshot(
        self,
        *,
        generated_at: str,
        url: str = "https://example.com/jobs/1",
    ) -> MarketSnapshot:
        return MarketSnapshot(
            generated_at=generated_at,
            queries=["AI工程師"],
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM"])],
            jobs=[
                JobListing(
                    source="104",
                    title="AI工程師",
                    company="Example",
                    location="台北市",
                    url=url,
                )
            ],
            skills=[],
            task_insights=[],
            errors=[],
        )

    def test_collect_backend_operations_snapshot_summarizes_runtime_state(self) -> None:
        settings = self.build_settings()
        product_store = ProductStore(settings.product_state_db_path)
        user = product_store.register_user(
            email="ops@example.com",
            password="password123",
            display_name="ops-user",
        )
        product_store.save_notification_preferences(
            NotificationPreference(site_enabled=True, frequency="每日"),
            user_id=user.id,
        )
        product_store.save_search(
            user_id=user.id,
            name="每日 AI 追蹤",
            rows=[{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": "LLM"}],
            custom_queries_text="RAG engineer",
            crawl_preset_label="快速",
            snapshot=self._snapshot(generated_at="2026-04-04T08:00:00"),
        )

        registry = QuerySnapshotRegistry(
            db_path=settings.query_state_db_path,
            snapshot_dir=settings.snapshot_store_dir,
            snapshot_ttl_seconds=settings.snapshot_ttl_seconds,
        )
        queue = CrawlJobQueue(
            db_path=settings.query_state_db_path,
            lease_seconds=settings.crawl_job_lease_seconds,
        )
        signal_store = RuntimeSignalStore(db_path=settings.query_state_db_path)

        registry.put_snapshot(
            "sig-ready",
            self._snapshot(generated_at="2026-04-06T12:00:00"),
            status="ready",
            is_partial=False,
        )
        registry.put_snapshot(
            "sig-partial",
            self._snapshot(generated_at="2026-04-06T12:05:00", url="https://example.com/jobs/2"),
            status="pending",
            is_partial=True,
        )
        queue.enqueue_crawl(
            "sig-pending",
            priority=50,
            payload_json='{"queries":["AI工程師","RAG engineer"]}',
        )
        queue.enqueue_crawl(
            "sig-leased",
            priority=60,
            payload_json='{"queries":["AI工程師"]}',
        )
        leased = queue.lease_job_for_signature("sig-leased", worker_id="worker-a")
        self.assertIsNotNone(leased)
        failed_job = queue.enqueue_crawl(
            "sig-failed",
            priority=40,
            payload_json='{"queries":["AI工程師","LLM 平台工程師"]}',
        )
        queue.fail_job(failed_job.id, "database is locked")
        signal_store.put_signal(
            component_kind="scheduler",
            component_id="scheduler-a",
            status="completed",
            message="checked=1 enqueued=1",
            payload={"poll_interval": 60.0, "checked_count": 1, "enqueued_count": 1},
        )
        signal_store.put_signal(
            component_kind="worker",
            component_id="worker-a",
            status="failed",
            message="RUNTIME_DATABASE_LOCKED: 系統資料庫忙碌中，稍後可再試一次。",
            payload={
                "poll_interval": 2.0,
                "job_id": leased.id if leased is not None else 0,
                "error": {
                    "error_code": "RUNTIME_DATABASE_LOCKED",
                    "error_kind": "runtime_error",
                    "error_retryable": True,
                    "error_user_message": "系統資料庫忙碌中，稍後可再試一次。",
                },
            },
        )

        operations = collect_backend_operations_snapshot(
            settings=settings,
            product_store=product_store,
        )

        self.assertEqual(operations.execution_mode, "worker")
        self.assertEqual(operations.due_saved_search_count, 1)
        self.assertEqual(operations.pending_job_count, 1)
        self.assertEqual(operations.leased_job_count, 1)
        self.assertEqual(operations.failed_job_count, 1)
        self.assertEqual(operations.dead_letter_count, 1)
        self.assertEqual(operations.ready_snapshot_count, 1)
        self.assertEqual(operations.partial_snapshot_count, 1)
        self.assertEqual(len(operations.due_saved_searches), 1)
        self.assertEqual(operations.due_saved_searches[0].search_name, "每日 AI 追蹤")
        self.assertEqual(len(operations.recent_jobs), 3)
        self.assertEqual(len(operations.recent_dead_letters), 1)
        self.assertEqual(operations.recent_dead_letters[0].error_code, "RUNTIME_DATABASE_LOCKED")
        self.assertEqual(len(operations.recent_snapshots), 2)
        self.assertEqual(len(operations.runtime_components), 2)
        worker_component = next(
            item for item in operations.runtime_components if item.component_kind == "worker"
        )
        self.assertEqual(worker_component.error_code, "RUNTIME_DATABASE_LOCKED")
        self.assertTrue(operations.last_scheduler_pass_at)
        self.assertTrue(operations.last_worker_activity_at)


if __name__ == "__main__":
    unittest.main()
