"""Tests for cache-first query runtime helpers."""

from __future__ import annotations

import sys
import sqlite3
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.models import JobListing, MarketSnapshot, TargetRole  # noqa: E402
from job_spy_tw.query_runtime import (  # noqa: E402
    CrawlJobQueue,
    QuerySnapshotRegistry,
    RuntimeSignalStore,
)


class QueryRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_dir = Path(tempfile.mkdtemp())
        self.registry = QuerySnapshotRegistry(
            db_path=self.runtime_dir / "query_runtime.sqlite3",
            snapshot_dir=self.runtime_dir / "snapshots",
            snapshot_ttl_seconds=1800,
        )
        self.queue = CrawlJobQueue(
            db_path=self.runtime_dir / "query_runtime.sqlite3",
            lease_seconds=180,
        )
        self.signal_store = RuntimeSignalStore(
            db_path=self.runtime_dir / "query_runtime.sqlite3",
        )
        self.snapshot = MarketSnapshot(
            generated_at="2026-04-06T01:00:00",
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

    def test_snapshot_registry_round_trip_and_stale_transition(self) -> None:
        record = self.registry.put_snapshot(
            "sig-1",
            self.snapshot,
            status="ready",
            is_partial=False,
        )

        loaded = self.registry.get_snapshot("sig-1")

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertTrue(loaded.is_fresh())
        self.assertEqual(loaded.storage_key, record.storage_key)
        self.assertIsNotNone(loaded.snapshot)
        assert loaded.snapshot is not None
        self.assertEqual(loaded.snapshot.jobs[0].title, "AI工程師")

        self.registry.mark_snapshot_stale("sig-1")
        stale_loaded = self.registry.get_snapshot("sig-1")
        self.assertIsNotNone(stale_loaded)
        assert stale_loaded is not None
        self.assertEqual(stale_loaded.status, "stale")
        self.assertFalse(stale_loaded.is_fresh())

    def test_final_snapshot_replaces_partial_file(self) -> None:
        partial = self.registry.put_snapshot(
            "sig-2",
            self.snapshot,
            status="pending",
            is_partial=True,
        )
        self.assertTrue((self.runtime_dir / "snapshots" / partial.storage_key).exists())

        final_record = self.registry.put_snapshot(
            "sig-2",
            self.snapshot,
            status="ready",
            is_partial=False,
        )

        self.assertFalse((self.runtime_dir / "snapshots" / partial.storage_key).exists())
        self.assertTrue((self.runtime_dir / "snapshots" / final_record.storage_key).exists())

    def test_queue_dedupes_and_single_worker_leases_same_query(self) -> None:
        first_job = self.queue.enqueue_crawl("sig-3", priority=10, payload_json='{"q": 1}')
        second_job = self.queue.enqueue_crawl("sig-3", priority=10, payload_json='{"q": 1}')

        self.assertEqual(first_job.id, second_job.id)

        leased = self.queue.lease_job_for_signature("sig-3", worker_id="worker-a")
        self.assertIsNotNone(leased)
        assert leased is not None
        self.assertEqual(leased.lease_owner, "worker-a")

        blocked = self.queue.lease_job_for_signature("sig-3", worker_id="worker-b")
        self.assertIsNone(blocked)

        self.queue.complete_job(leased.id, "snapshots/sig-3.json")
        completed = self.queue.get_job(leased.id)
        self.assertIsNotNone(completed)
        assert completed is not None
        self.assertEqual(completed.status, "completed")
        self.assertEqual(completed.snapshot_ref, "snapshots/sig-3.json")

    def test_retryable_failure_requeues_job_until_max_attempts(self) -> None:
        job = self.queue.enqueue_crawl(
            "sig-retry",
            priority=10,
            max_attempts=2,
            payload_json='{"q": 1}',
        )

        leased = self.queue.lease_job("worker-a")
        self.assertIsNotNone(leased)
        assert leased is not None
        self.assertEqual(leased.id, job.id)
        self.assertEqual(leased.attempt_count, 1)

        retried = self.queue.record_attempt_failure(
            leased.id,
            "temporary failure",
            allow_retry=True,
            retry_backoff_seconds=60,
        )
        self.assertEqual(retried.status, "pending")
        self.assertEqual(retried.attempt_count, 1)
        self.assertTrue(retried.next_retry_at)
        self.assertIsNone(self.queue.lease_job("worker-b"))

        with sqlite3.connect(self.runtime_dir / "query_runtime.sqlite3") as connection:
            connection.execute(
                """
                UPDATE crawl_jobs
                SET next_retry_at = '2026-04-05T10:00:00'
                WHERE id = ?
                """,
                (leased.id,),
            )
            connection.commit()

        second_lease = self.queue.lease_job("worker-b")
        self.assertIsNotNone(second_lease)
        assert second_lease is not None
        self.assertEqual(second_lease.attempt_count, 2)

        failed = self.queue.record_attempt_failure(
            second_lease.id,
            "still broken",
            allow_retry=True,
            retry_backoff_seconds=60,
        )
        self.assertEqual(failed.status, "failed")
        self.assertEqual(failed.attempt_count, 2)
        self.assertEqual(failed.max_attempts, 2)

    def test_runtime_signal_store_and_list_helpers(self) -> None:
        self.registry.put_snapshot(
            "sig-4",
            self.snapshot,
            status="pending",
            is_partial=True,
        )
        self.registry.put_snapshot(
            "sig-5",
            self.snapshot,
            status="ready",
            is_partial=False,
        )
        first_job = self.queue.enqueue_crawl("sig-4", priority=10, payload_json='{"q": 1}')
        leased_job = self.queue.lease_job_for_signature("sig-4", worker_id="worker-a")
        self.assertIsNotNone(leased_job)
        self.queue.enqueue_crawl("sig-5", priority=20, payload_json='{"q": 2}')
        self.signal_store.put_signal(
            component_kind="worker",
            component_id="worker-a",
            status="processing",
            message="processing sig-4",
            payload={"job_id": first_job.id},
        )

        recent_snapshots = self.registry.list_snapshots(limit=2)
        recent_jobs = self.queue.list_jobs(limit=5)
        signals = self.signal_store.list_signals(limit=5)

        self.assertEqual(len(recent_snapshots), 2)
        self.assertEqual(self.registry.count_snapshots(is_partial=True), 1)
        self.assertEqual(self.registry.count_snapshots(status="ready", is_partial=False), 1)
        self.assertEqual(len(recent_jobs), 2)
        self.assertEqual(self.queue.count_jobs(status="leased"), 1)
        self.assertEqual(self.queue.count_jobs(status="pending"), 1)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].component_kind, "worker")
        self.assertEqual(signals[0].payload()["job_id"], first_job.id)

    def test_prune_helpers_remove_old_runtime_rows_and_files(self) -> None:
        old_ready = self.registry.put_snapshot(
            "sig-old-ready",
            self.snapshot,
            status="ready",
            is_partial=False,
        )
        old_partial = self.registry.put_snapshot(
            "sig-old-partial",
            self.snapshot,
            status="pending",
            is_partial=True,
        )
        recent_ready = self.registry.put_snapshot(
            "sig-recent-ready",
            self.snapshot,
            status="ready",
            is_partial=False,
        )
        completed_job = self.queue.enqueue_crawl(
            "sig-completed",
            priority=10,
            payload_json='{"q": 1}',
        )
        self.queue.complete_job(completed_job.id, "snapshots/sig-completed.json")
        failed_job = self.queue.enqueue_crawl(
            "sig-failed",
            priority=10,
            payload_json='{"q": 2}',
        )
        self.queue.fail_job(failed_job.id, "boom")
        recent_job = self.queue.enqueue_crawl(
            "sig-recent-job",
            priority=10,
            payload_json='{"q": 3}',
        )
        self.signal_store.put_signal(
            component_kind="worker",
            component_id="worker-old",
            status="completed",
            message="old",
        )
        self.signal_store.put_signal(
            component_kind="worker",
            component_id="worker-recent",
            status="idle",
            message="recent",
        )
        orphan_path = self.runtime_dir / "snapshots" / "orphan.json"
        orphan_path.write_text("{}", encoding="utf-8")

        with sqlite3.connect(self.runtime_dir / "query_runtime.sqlite3") as connection:
            connection.execute(
                """
                UPDATE query_snapshots
                SET updated_at = '2026-03-01T10:00:00', last_accessed_at = '2026-03-01T10:00:00'
                WHERE query_signature IN ('sig-old-ready', 'sig-old-partial')
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
                UPDATE runtime_signals
                SET updated_at = '2026-03-01T10:00:00'
                WHERE component_id = 'worker-old'
                """
            )
            connection.commit()

        snapshot_result = self.registry.prune_snapshots(
            ready_retention_days=14,
            partial_retention_hours=12,
        )
        deleted_jobs = self.queue.prune_jobs(retention_days=14)
        deleted_signals = self.signal_store.prune_signals(retention_days=14)

        self.assertEqual(snapshot_result["deleted_rows"], 2)
        self.assertGreaterEqual(snapshot_result["deleted_files"], 2)
        self.assertEqual(snapshot_result["deleted_orphan_files"], 1)
        self.assertEqual(deleted_jobs, 2)
        self.assertEqual(deleted_signals, 1)
        self.assertIsNone(self.queue.get_job(completed_job.id))
        self.assertIsNone(self.queue.get_job(failed_job.id))
        self.assertIsNotNone(self.queue.get_job(recent_job.id))
        self.assertIsNone(self.registry.get_snapshot("sig-old-ready"))
        self.assertIsNone(self.registry.get_snapshot("sig-old-partial"))
        self.assertIsNotNone(self.registry.get_snapshot("sig-recent-ready"))
