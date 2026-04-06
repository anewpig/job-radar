"""Tests for the extracted crawl application service."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import Settings  # noqa: E402
from job_spy_tw.crawl_application_service import (  # noqa: E402
    PendingCrawlState,
    advance_finalize_batch,
    build_query_runtime,
    collect_due_saved_searches,
    collect_saved_search_sync_targets,
    inspect_query_runtime_status,
    is_saved_search_due,
    parse_role_targets,
    process_queued_crawl_job,
    schedule_due_saved_searches,
    start_crawl,
    sync_saved_search_results,
)
from job_spy_tw.models import (  # noqa: E402
    JobListing,
    MarketSnapshot,
    NotificationPreference,
    TargetRole,
)
from job_spy_tw.product_store import ProductStore  # noqa: E402


class _NotificationServiceStub:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def send_new_job_alert(self, **kwargs):
        self.calls.append(kwargs)
        return {"email_sent": False, "line_sent": False, "notes": ["stubbed"]}


class CrawlApplicationServiceTests(unittest.TestCase):
    def build_settings(self, *, max_pages_per_source: int = 2) -> Settings:
        return Settings(
            data_dir=Path(tempfile.mkdtemp()),
            request_timeout=5.0,
            request_delay=0.2,
            max_concurrent_requests=4,
            max_pages_per_source=max_pages_per_source,
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

    def _job(self, *, source: str = "104", url: str = "https://example.com/jobs/1") -> JobListing:
        return JobListing(
            source=source,
            title="AI工程師",
            company="Example",
            location="台北市",
            url=url,
            matched_role="AI工程師",
            relevance_score=35.0,
        )

    def _snapshot(self, *jobs: JobListing, generated_at: str = "2026-04-06T10:00:00") -> MarketSnapshot:
        return MarketSnapshot(
            generated_at=generated_at,
            queries=["AI工程師"],
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM"])],
            jobs=list(jobs),
            skills=[],
            task_insights=[],
            errors=[],
        )

    def test_sync_saved_search_results_returns_feedback_and_resolved_search_id(self) -> None:
        store = ProductStore(Path(tempfile.mkdtemp()) / "product_state.sqlite3")
        user = store.register_user(
            email="member@example.com",
            password="password123",
            display_name="member",
        )
        search_id = store.save_search(
            user_id=user.id,
            name="AI 追蹤",
            rows=[{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": "LLM"}],
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=self._snapshot(self._job()),
        )

        result = sync_saved_search_results(
            product_store=store,
            notification_service=_NotificationServiceStub(),
            snapshot=self._snapshot(
                self._job(),
                self._job(source="1111", url="https://example.com/jobs/2"),
                generated_at="2026-04-06T11:00:00",
            ),
            current_user_id=user.id,
            current_user_is_guest=False,
            notification_preferences=NotificationPreference(site_enabled=True),
            rows=[{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": "LLM"}],
            custom_queries_text="",
            crawl_preset_label="快速",
            active_saved_search_id=search_id,
        )

        self.assertEqual(result.active_saved_search_id, search_id)
        self.assertIn("1 筆新職缺", result.feedback)
        self.assertEqual(store.unread_notification_count(user_id=user.id), 1)

    def test_is_saved_search_due_uses_frequency_window(self) -> None:
        self.assertTrue(is_saved_search_due(last_run_at="", frequency="即時"))
        self.assertFalse(
            is_saved_search_due(
                last_run_at="2026-04-06T11:30:00",
                frequency="每日",
                now=self._snapshot().generated_at and __import__("datetime").datetime.fromisoformat("2026-04-06T12:00:00"),
            )
        )
        self.assertTrue(
            is_saved_search_due(
                last_run_at="2026-04-05T10:00:00",
                frequency="每日",
                now=__import__("datetime").datetime.fromisoformat("2026-04-06T12:00:00"),
            )
        )

    def test_collect_due_saved_searches_and_scheduler_enqueue_due_items(self) -> None:
        settings = self.build_settings(max_pages_per_source=2)
        store = ProductStore(settings.product_state_db_path)
        user = store.register_user(
            email="scheduler@example.com",
            password="password123",
            display_name="scheduler",
        )
        store.save_notification_preferences(
            NotificationPreference(
                site_enabled=True,
                frequency="每日",
            ),
            user_id=user.id,
        )
        old_snapshot = self._snapshot(self._job(), generated_at="2026-04-04T08:00:00")
        store.save_search(
            user_id=user.id,
            name="每天追蹤",
            rows=[{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": "LLM"}],
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=old_snapshot,
        )

        due_items = collect_due_saved_searches(product_store=store)
        self.assertEqual(len(due_items), 1)

        result = schedule_due_saved_searches(
            settings=settings,
            product_store=store,
            worker_id="scheduler-worker",
        )
        self.assertEqual(result.checked_count, 1)
        self.assertEqual(result.enqueued_count, 1)
        _registry, queue = build_query_runtime(settings)
        signature = store.build_signature(
            [{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": "LLM"}],
            "",
            "快速",
        )
        self.assertIsNotNone(queue.get_active_job_for_signature(signature))

    def test_collect_saved_search_sync_targets_returns_all_subscribers_for_signature(self) -> None:
        settings = self.build_settings(max_pages_per_source=2)
        store = ProductStore(settings.product_state_db_path)
        first_user = store.register_user(
            email="first@example.com",
            password="password123",
            display_name="first",
        )
        second_user = store.register_user(
            email="second@example.com",
            password="password123",
            display_name="second",
        )
        rows = [{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": "LLM"}]
        first_search_id = store.save_search(
            user_id=first_user.id,
            name="共同追蹤 A",
            rows=rows,
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=self._snapshot(self._job(url="https://example.com/jobs/old-a")),
        )
        second_search_id = store.save_search(
            user_id=second_user.id,
            name="共同追蹤 B",
            rows=rows,
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=self._snapshot(self._job(url="https://example.com/jobs/old-b")),
        )

        targets = collect_saved_search_sync_targets(
            product_store=store,
            query_signature=store.build_signature(rows, "", "快速"),
        )

        self.assertCountEqual(
            targets,
            [
                (first_user.id, first_search_id),
                (second_user.id, second_search_id),
            ],
        )

    def test_start_crawl_returns_partial_state_and_persists_partial_snapshot(self) -> None:
        settings = self.build_settings(max_pages_per_source=2)
        partial_snapshot = self._snapshot(self._job(), generated_at="2026-04-06T12:00:00")

        class FakePipeline:
            def __init__(self, *, settings, role_targets, force_refresh, perform_cache_maintenance):
                del settings, role_targets, force_refresh, perform_cache_maintenance
                self.connectors = ["104", "1111"]

            def collect_initial_wave(self, *, queries):
                del queries
                return [self_job], ["partial warning"], ["104", "1111"]

            def enrich_job_batch(self, jobs, errors, *, start_index, batch_size):
                del jobs, errors, start_index, batch_size
                return 1, 1

            def build_partial_snapshot(self, *, queries, jobs, errors):
                del queries, jobs, errors
                return partial_snapshot

        self_job = self._job()
        with mock.patch("job_spy_tw.crawl_application_service.JobMarketPipeline", FakePipeline):
            result = start_crawl(
                settings=settings,
                role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM"])],
                queries=["AI工程師"],
                query_signature="sig-partial",
                force_refresh=False,
                crawl_preset_label="快速",
                worker_id="worker-a",
            )

        self.assertEqual(result.status, "partial_ready")
        self.assertIsNotNone(result.snapshot)
        self.assertIsNotNone(result.pending_state)
        assert result.pending_state is not None
        self.assertEqual(result.pending_state.remaining_page_cursor, 2)
        self.assertGreater(result.pending_state.active_job_id, 0)

        registry, _queue = build_query_runtime(settings)
        cached_entry = registry.get_snapshot("sig-partial")
        self.assertIsNotNone(cached_entry)
        assert cached_entry is not None
        self.assertTrue(cached_entry.is_partial)

    def test_start_crawl_worker_mode_only_enqueues_job_with_role_targets_payload(self) -> None:
        settings = self.build_settings(max_pages_per_source=2)

        result = start_crawl(
            settings=settings,
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM", "RAG"])],
            queries=["AI工程師", "RAG"],
            query_signature="sig-worker",
            force_refresh=False,
            crawl_preset_label="快速",
            worker_id="worker-a",
            execution_mode="worker",
        )

        self.assertEqual(result.status, "awaiting_snapshot")
        self.assertIsNotNone(result.pending_state)
        assert result.pending_state is not None
        registry, queue = build_query_runtime(settings)
        del registry
        job = queue.get_job(result.pending_state.active_job_id)
        self.assertIsNotNone(job)
        assert job is not None
        payload_roles = parse_role_targets(job.payload())
        self.assertEqual([role.name for role in payload_roles], ["AI工程師"])
        self.assertEqual(payload_roles[0].keywords, ["LLM", "RAG"])

    def test_inspect_query_runtime_status_reads_snapshot_and_job_state(self) -> None:
        settings = self.build_settings(max_pages_per_source=2)
        registry, queue = build_query_runtime(settings)
        partial_snapshot = self._snapshot(self._job(), generated_at="2026-04-06T12:34:56")
        registry.put_snapshot(
            "sig-status",
            partial_snapshot,
            status="pending",
            is_partial=True,
        )
        enqueued = queue.enqueue_crawl(
            "sig-status",
            priority=50,
            payload_json='{"queries":["AI工程師"]}',
        )
        self.assertGreater(enqueued.id, 0)

        runtime_status = inspect_query_runtime_status(
            settings=settings,
            query_signature="sig-status",
        )

        self.assertEqual(runtime_status.snapshot_status, "pending")
        self.assertTrue(runtime_status.snapshot_is_partial)
        self.assertEqual(runtime_status.job_status, "pending")
        self.assertEqual(runtime_status.job_id, enqueued.id)

    def test_advance_finalize_batch_completes_job_and_ready_snapshot(self) -> None:
        settings = self.build_settings(max_pages_per_source=2)
        registry, queue = build_query_runtime(settings)
        queue.enqueue_crawl("sig-final", priority=50, payload_json='{"q":1}')
        leased = queue.lease_job_for_signature("sig-final", worker_id="worker-a")
        self.assertIsNotNone(leased)
        assert leased is not None
        final_snapshot = self._snapshot(self._job(url="https://example.com/jobs/final"))

        class FakePipeline:
            def __init__(self, *, settings, role_targets, force_refresh):
                del settings, role_targets, force_refresh

            def enrich_job_batch(self, jobs, errors, *, start_index, batch_size):
                del jobs, errors, start_index, batch_size
                return 1, 1

            def complete_snapshot(self, *, queries, jobs, errors):
                del queries, jobs, errors
                return final_snapshot

        with mock.patch("job_spy_tw.crawl_application_service.JobMarketPipeline", FakePipeline):
            result = advance_finalize_batch(
                settings=settings,
                snapshot=self._snapshot(self._job()),
                pending_state=PendingCrawlState(
                    query_signature="sig-final",
                    active_job_id=leased.id,
                    pending_queries=["AI工程師"],
                    pending_jobs=[self._job()],
                    pending_errors=[],
                    partial_ready_at="2026-04-06T12:00:00",
                    detail_cursor=0,
                    detail_total=0,
                    remaining_page_cursor=3,
                    initial_wave_sources=["104", "1111"],
                ),
                crawl_preset_label="快速",
                force_refresh=False,
            )

        self.assertEqual(result.status, "completed")
        self.assertIsNotNone(result.snapshot)
        completed_job = queue.get_job(leased.id)
        self.assertIsNotNone(completed_job)
        assert completed_job is not None
        self.assertEqual(completed_job.status, "completed")
        ready_entry = registry.get_snapshot("sig-final")
        self.assertIsNotNone(ready_entry)
        assert ready_entry is not None
        self.assertEqual(ready_entry.status, "ready")

    def test_process_queued_crawl_job_completes_background_job(self) -> None:
        settings = self.build_settings(max_pages_per_source=2)
        store = ProductStore(settings.product_state_db_path)
        user = store.register_user(
            email="worker@example.com",
            password="password123",
            display_name="worker",
        )
        search_id = store.save_search(
            user_id=user.id,
            name="背景追蹤",
            rows=[{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": "LLM"}],
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=self._snapshot(self._job(url="https://example.com/jobs/old"), generated_at="2026-04-06T09:00:00"),
        )
        registry, queue = build_query_runtime(settings)
        del registry
        worker_start = start_crawl(
            settings=settings,
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM"])],
            queries=["AI工程師"],
            query_signature="sig-bg-worker",
            force_refresh=False,
            crawl_preset_label="快速",
            worker_id="ui-worker",
            execution_mode="worker",
            rows=[{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": "LLM"}],
            custom_queries_text="",
            user_id=user.id,
            active_saved_search_id=search_id,
        )
        assert worker_start.pending_state is not None
        job = queue.lease_job("bg-worker")
        self.assertIsNotNone(job)
        assert job is not None
        final_snapshot = self._snapshot(
            self._job(url="https://example.com/jobs/old"),
            self._job(url="https://example.com/jobs/bg-final"),
        )

        class FakePipeline:
            def __init__(self, *, settings, role_targets, force_refresh, perform_cache_maintenance):
                del settings, role_targets, force_refresh, perform_cache_maintenance
                self.connectors = ["104", "1111"]

            def collect_initial_wave(self, *, queries):
                del queries
                return [self_job], [], ["104", "1111"]

            def build_partial_snapshot(self, *, queries, jobs, errors, generated_at=None):
                del queries, jobs, errors, generated_at
                return self._partial_snapshot

            def collect_remaining_waves(
                self,
                queries,
                existing_jobs,
                *,
                page_cursor,
                completed_initial_sources=None,
            ):
                del queries, page_cursor, completed_initial_sources
                return existing_jobs, [], 3

            def finalize_snapshot(self, *, queries, jobs, errors):
                del queries, jobs, errors
                return final_snapshot

        self_job = self._job(url="https://example.com/jobs/bg-partial")
        fake_pipeline = FakePipeline
        fake_pipeline._partial_snapshot = self._snapshot(self_job, generated_at="2026-04-06T12:10:00")

        with mock.patch("job_spy_tw.crawl_application_service.JobMarketPipeline", fake_pipeline):
            result = process_queued_crawl_job(settings=settings, job=job)

        self.assertEqual(result.status, "completed")
        completed = queue.get_job(job.id)
        self.assertIsNotNone(completed)
        assert completed is not None
        self.assertEqual(completed.status, "completed")
        self.assertEqual(store.unread_notification_count(user_id=user.id), 1)

    def test_process_queued_crawl_job_schedules_retry_for_transient_failure(self) -> None:
        settings = self.build_settings(max_pages_per_source=2)
        registry, queue = build_query_runtime(settings)
        del registry
        start_result = start_crawl(
            settings=settings,
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM"])],
            queries=["AI工程師"],
            query_signature="sig-retry-worker",
            force_refresh=False,
            crawl_preset_label="快速",
            worker_id="ui-worker",
            execution_mode="worker",
        )
        self.assertIsNotNone(start_result.pending_state)
        job = queue.lease_job("bg-worker")
        self.assertIsNotNone(job)
        assert job is not None

        class FailingPipeline:
            def __init__(self, *, settings, role_targets, force_refresh, perform_cache_maintenance):
                del settings, role_targets, force_refresh, perform_cache_maintenance
                self.connectors = ["104", "1111"]

            def collect_initial_wave(self, *, queries):
                del queries
                raise TimeoutError("connector timed out")

        with mock.patch("job_spy_tw.crawl_application_service.JobMarketPipeline", FailingPipeline):
            result = process_queued_crawl_job(settings=settings, job=job)

        self.assertEqual(result.status, "retry_scheduled")
        self.assertEqual(result.attempt_count, 1)
        self.assertEqual(result.max_attempts, 2)
        self.assertTrue(result.next_retry_at)
        refreshed_job = queue.get_job(job.id)
        self.assertIsNotNone(refreshed_job)
        assert refreshed_job is not None
        self.assertEqual(refreshed_job.status, "pending")
        self.assertTrue(refreshed_job.next_retry_at)

    def test_process_queued_crawl_job_syncs_all_saved_search_subscribers(self) -> None:
        settings = self.build_settings(max_pages_per_source=2)
        store = ProductStore(settings.product_state_db_path)
        first_user = store.register_user(
            email="subscriber-a@example.com",
            password="password123",
            display_name="subscriber-a",
        )
        second_user = store.register_user(
            email="subscriber-b@example.com",
            password="password123",
            display_name="subscriber-b",
        )
        rows = [{"enabled": True, "priority": 1, "role": "AI工程師", "keywords": "LLM"}]
        baseline_snapshot = self._snapshot(
            self._job(url="https://example.com/jobs/shared-old"),
            generated_at="2026-04-06T09:00:00",
        )
        first_search_id = store.save_search(
            user_id=first_user.id,
            name="共同搜尋 A",
            rows=rows,
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=baseline_snapshot,
        )
        second_search_id = store.save_search(
            user_id=second_user.id,
            name="共同搜尋 B",
            rows=rows,
            custom_queries_text="",
            crawl_preset_label="快速",
            snapshot=baseline_snapshot,
        )
        query_signature = store.build_signature(rows, "", "快速")
        first_start = start_crawl(
            settings=settings,
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM"])],
            queries=["AI工程師"],
            query_signature=query_signature,
            force_refresh=False,
            crawl_preset_label="快速",
            worker_id="ui-worker-a",
            execution_mode="worker",
            rows=rows,
            custom_queries_text="",
            user_id=first_user.id,
            active_saved_search_id=first_search_id,
        )
        second_start = start_crawl(
            settings=settings,
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM"])],
            queries=["AI工程師"],
            query_signature=query_signature,
            force_refresh=False,
            crawl_preset_label="快速",
            worker_id="ui-worker-b",
            execution_mode="worker",
            rows=rows,
            custom_queries_text="",
            user_id=second_user.id,
            active_saved_search_id=second_search_id,
        )
        self.assertIsNotNone(first_start.pending_state)
        self.assertIsNotNone(second_start.pending_state)
        assert first_start.pending_state is not None
        assert second_start.pending_state is not None
        self.assertEqual(
            first_start.pending_state.active_job_id,
            second_start.pending_state.active_job_id,
        )

        _registry, queue = build_query_runtime(settings)
        job = queue.lease_job("bg-worker-shared")
        self.assertIsNotNone(job)
        assert job is not None
        final_snapshot = self._snapshot(
            self._job(url="https://example.com/jobs/shared-old"),
            self._job(url="https://example.com/jobs/shared-new"),
        )

        class FakePipeline:
            def __init__(self, *, settings, role_targets, force_refresh, perform_cache_maintenance):
                del settings, role_targets, force_refresh, perform_cache_maintenance
                self.connectors = ["104", "1111"]

            def collect_initial_wave(self, *, queries):
                del queries
                return [self_job], [], ["104", "1111"]

            def build_partial_snapshot(self, *, queries, jobs, errors, generated_at=None):
                del queries, jobs, errors, generated_at
                return self._partial_snapshot

            def collect_remaining_waves(
                self,
                queries,
                existing_jobs,
                *,
                page_cursor,
                completed_initial_sources=None,
            ):
                del queries, page_cursor, completed_initial_sources
                return existing_jobs, [], 3

            def finalize_snapshot(self, *, queries, jobs, errors):
                del queries, jobs, errors
                return final_snapshot

        self_job = self._job(url="https://example.com/jobs/shared-partial")
        fake_pipeline = FakePipeline
        fake_pipeline._partial_snapshot = self._snapshot(
            self_job,
            generated_at="2026-04-06T12:10:00",
        )
        notification_stub = _NotificationServiceStub()

        with mock.patch("job_spy_tw.crawl_application_service.JobMarketPipeline", fake_pipeline):
            with mock.patch(
                "job_spy_tw.crawl_application_service.NotificationService",
                return_value=notification_stub,
            ):
                result = process_queued_crawl_job(settings=settings, job=job)

        self.assertEqual(result.status, "completed")
        self.assertEqual(store.unread_notification_count(user_id=first_user.id), 1)
        self.assertEqual(store.unread_notification_count(user_id=second_user.id), 1)
        first_saved_search = store.get_saved_search(first_search_id, user_id=first_user.id)
        second_saved_search = store.get_saved_search(second_search_id, user_id=second_user.id)
        self.assertIsNotNone(first_saved_search)
        self.assertIsNotNone(second_saved_search)
        assert first_saved_search is not None
        assert second_saved_search is not None
        self.assertEqual(first_saved_search.last_new_job_count, 1)
        self.assertEqual(second_saved_search.last_new_job_count, 1)


if __name__ == "__main__":
    unittest.main()
