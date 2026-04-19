"""Tests for runtime cleanup orchestration."""

from __future__ import annotations

import json
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
        settings.cache_max_files = 1
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
        failed_job = queue.enqueue_crawl(
            "sig-old-failed-job",
            priority=10,
            payload_json='{"q": 2}',
        )
        queue.fail_job(failed_job.id, "connector timed out")
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
                WHERE id IN (?, ?)
                """,
                (completed_job.id, failed_job.id),
            )
            connection.execute(
                """
                UPDATE crawl_dead_letters
                SET updated_at = '2026-03-01T10:00:00'
                WHERE original_job_id = ?
                """,
                (failed_job.id,),
            )
            connection.execute(
                """
                UPDATE runtime_signals
                SET updated_at = '2026-03-01T10:00:00'
                WHERE component_kind = 'worker' AND component_id = 'worker-old'
                """
            )
            connection.commit()

        settings.cache_dir.mkdir(parents=True, exist_ok=True)
        for key in ("cache-a", "cache-b"):
            (settings.cache_dir / f"{key}.html").write_text(
                f"<html>{key}</html>",
                encoding="utf-8",
            )
            (settings.cache_dir / f"{key}.meta.json").write_text(
                json.dumps(
                    {
                        "url": f"https://example.com/{key}",
                        "created_at_ts": 1_700_000_000.0,
                        "last_accessed_at_ts": 1_700_000_000.0,
                        "ttl_seconds": 0.0,
                    }
                ),
                encoding="utf-8",
            )

        result = run_runtime_cleanup(
            settings=settings,
            trigger="test",
            force=True,
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.deleted_jobs, 2)
        self.assertEqual(result.deleted_dead_letters, 1)
        self.assertEqual(result.deleted_snapshot_rows, 1)
        self.assertGreaterEqual(result.deleted_snapshot_files, 1)
        self.assertEqual(result.deleted_signals, 1)
        self.assertGreaterEqual(result.deleted_cache_files, 2)
        self.assertLessEqual(result.retained_cache_files, 2)
        self.assertIsNone(queue.get_job(completed_job.id))
        self.assertIsNone(queue.get_job(failed_job.id))
        self.assertEqual(queue.count_dead_letters(), 0)
        self.assertIsNone(registry.get_snapshot("sig-old-partial"))
        self.assertFalse((settings.snapshot_store_dir / old_partial.storage_key).exists())

        skipped = run_runtime_cleanup(
            settings=settings,
            trigger="test",
            force=False,
        )
        self.assertEqual(skipped.status, "skipped")
        self.assertTrue(skipped.skipped_reason)

    def test_run_runtime_cleanup_recovers_from_corrupted_cache_metadata(self) -> None:
        settings = self.build_settings()
        settings.cache_max_files = 2
        settings.cache_dir.mkdir(parents=True, exist_ok=True)
        (settings.cache_dir / "broken.html").write_text("<html>broken</html>", encoding="utf-8")
        (settings.cache_dir / "broken.meta.json").write_text(
            '{\n  "url": "https://example.com/broken"\n}\nnot-json',
            encoding="utf-8",
        )

        result = run_runtime_cleanup(
            settings=settings,
            trigger="test",
            force=True,
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.deleted_cache_files, 0)
        repaired_meta = settings.cache_dir / "broken.meta.json"
        self.assertTrue(repaired_meta.exists())
        self.assertEqual(json.loads(repaired_meta.read_text(encoding="utf-8"))["url"], "https://example.com/broken")

    def test_run_runtime_cleanup_prunes_nested_cache_tree_to_remaining_budget(self) -> None:
        settings = self.build_settings()
        settings.cache_max_files = 2
        settings.cache_max_bytes = 1_000
        settings.cache_dir.mkdir(parents=True, exist_ok=True)
        (settings.cache_dir / "root-a.html").write_text("<html>a</html>", encoding="utf-8")
        (settings.cache_dir / "root-a.meta.json").write_text(
            json.dumps(
                {
                    "url": "https://example.com/root-a",
                    "created_at_ts": 1_700_000_000.0,
                    "last_accessed_at_ts": 1_700_000_000.0,
                    "ttl_seconds": 0.0,
                }
            ),
            encoding="utf-8",
        )
        nested_dir = settings.cache_dir / "rag_embeddings"
        nested_dir.mkdir(parents=True, exist_ok=True)
        (nested_dir / "old.json").write_text('{"embedding":[1,2,3]}', encoding="utf-8")
        (nested_dir / "new.json").write_text('{"embedding":[4,5,6]}', encoding="utf-8")

        result = run_runtime_cleanup(
            settings=settings,
            trigger="test",
            force=True,
        )

        self.assertEqual(result.status, "completed")
        self.assertGreaterEqual(result.deleted_cache_files, 1)
        self.assertLessEqual(result.retained_cache_files, settings.cache_max_files)
        self.assertFalse((nested_dir / "old.json").exists() and (nested_dir / "new.json").exists())


if __name__ == "__main__":
    unittest.main()
