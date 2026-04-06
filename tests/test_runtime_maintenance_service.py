"""Tests for runtime cleanup orchestration."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import Settings  # noqa: E402
from job_spy_tw.models import JobListing, MarketSnapshot, TargetRole  # noqa: E402
from job_spy_tw.query_runtime import CrawlJobQueue, QuerySnapshotRegistry, RuntimeSignalStore  # noqa: E402
from job_spy_tw.runtime_maintenance_service import run_runtime_cleanup  # noqa: E402


class RuntimeMaintenanceServiceTests(unittest.TestCase):
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
            runtime_cleanup_interval_seconds=3600,
            runtime_job_retention_days=14,
            runtime_snapshot_retention_days=30,
            runtime_partial_snapshot_retention_hours=12,
            runtime_signal_retention_days=14,
        )

    def _snapshot(self, *, generated_at: str = "2026-04-06T10:00:00") -> MarketSnapshot:
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

    def test_run_runtime_cleanup_prunes_old_artifacts_and_respects_interval(self) -> None:
        settings = self.build_settings()
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

        old_partial = registry.put_snapshot(
            "sig-old-partial",
            self._snapshot(),
            status="pending",
            is_partial=True,
        )
        completed_job = queue.enqueue_crawl(
            "sig-old-job",
            priority=10,
            payload_json='{"q": 1}',
        )
        queue.complete_job(completed_job.id, "snapshots/sig-old-job.json")
        signal_store.put_signal(
            component_kind="worker",
            component_id="worker-old",
            status="completed",
            message="old worker",
        )
        with sqlite3.connect(settings.query_state_db_path) as connection:
            connection.execute(
                """
                UPDATE query_snapshots
                SET updated_at = '2026-03-01T10:00:00', last_accessed_at = '2026-03-01T10:00:00'
                WHERE query_signature = 'sig-old-partial'
                """
            )
            connection.execute(
                """
                UPDATE crawl_jobs
                SET updated_at = '2026-03-01T10:00:00'
                WHERE id = ?
                """,
                (completed_job.id,),
            )
            connection.execute(
                """
                UPDATE runtime_signals
                SET updated_at = '2026-03-01T10:00:00'
                WHERE component_kind = 'worker' AND component_id = 'worker-old'
                """
            )
            connection.commit()

        result = run_runtime_cleanup(
            settings=settings,
            trigger="test",
            force=True,
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.deleted_jobs, 1)
        self.assertEqual(result.deleted_snapshot_rows, 1)
        self.assertGreaterEqual(result.deleted_snapshot_files, 1)
        self.assertEqual(result.deleted_signals, 1)
        self.assertIsNone(queue.get_job(completed_job.id))
        self.assertIsNone(registry.get_snapshot("sig-old-partial"))
        self.assertFalse((settings.snapshot_store_dir / old_partial.storage_key).exists())

        skipped = run_runtime_cleanup(
            settings=settings,
            trigger="test",
            force=False,
        )
        self.assertEqual(skipped.status, "skipped")
        self.assertTrue(skipped.skipped_reason)


if __name__ == "__main__":
    unittest.main()
