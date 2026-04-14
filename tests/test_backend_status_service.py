"""Tests for backend status report helpers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.backend_status_service import collect_backend_status_report  # noqa: E402
from job_spy_tw.config import Settings  # noqa: E402
from job_spy_tw.models import JobListing, MarketSnapshot, NotificationPreference, TargetRole  # noqa: E402
from job_spy_tw.product_store import ProductStore  # noqa: E402
from job_spy_tw.query_runtime import CrawlJobQueue, QuerySnapshotRegistry, RuntimeSignalStore  # noqa: E402
from job_spy_tw.sqlite_backup_service import run_sqlite_backup  # noqa: E402


class BackendStatusServiceTests(unittest.TestCase):
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

    def _snapshot(self, *, generated_at: str) -> MarketSnapshot:
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
                    url="https://example.com/jobs/1",
                )
            ],
            skills=[],
            task_insights=[],
            errors=[],
        )

    def test_collect_backend_status_report_includes_backup_and_runtime_summary(self) -> None:
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
        queue.enqueue_crawl(
            "sig-pending",
            priority=50,
            payload_json='{"queries":["AI工程師","RAG engineer"]}',
        )
        signal_store.put_signal(
            component_kind="scheduler",
            component_id="scheduler-a",
            status="completed",
            message="checked=1 enqueued=1",
            payload={"poll_interval": 60.0},
        )
        signal_store.put_signal(
            component_kind="worker",
            component_id="worker-a",
            status="completed",
            message="processed=1",
            payload={"poll_interval": 2.0},
        )
        run_sqlite_backup(settings=settings)

        report = collect_backend_status_report(
            settings=settings,
            product_store=product_store,
        )

        self.assertEqual(report.build.package_name, "job-spy-tw")
        self.assertIn("product_state", report.schema_versions)
        self.assertEqual(report.execution_mode, "worker")
        self.assertEqual(report.operations.pending_job_count, 1)
        self.assertEqual(report.backups.backup_count, 1)
        self.assertTrue(report.backups.latest_manifest_path.endswith("manifest.json"))
        self.assertIn("latency_budgets", report.ai_health)
        self.assertIn("cache_efficiency", report.ai_health)
        self.assertEqual(report.issues, [])

    def test_collect_backend_status_report_surfaces_missing_worker_and_backup_issues(self) -> None:
        settings = self.build_settings()
        product_store = ProductStore(settings.product_state_db_path)

        report = collect_backend_status_report(
            settings=settings,
            product_store=product_store,
        )

        self.assertIn("scheduler heartbeat missing", report.issues)
        self.assertIn("worker heartbeat missing", report.issues)
        self.assertIn("sqlite backup missing", report.issues)
