"""Tests for staged crawl flow and crawl-speed optimizations."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import Settings  # noqa: E402
from job_spy_tw.connectors.base import BaseConnector  # noqa: E402
from job_spy_tw.connectors.site_104 import Site104Connector  # noqa: E402
from job_spy_tw.models import JobListing, TargetRole  # noqa: E402
from job_spy_tw.pipeline import JobMarketPipeline  # noqa: E402
from job_spy_tw.utils import CachedFetcher  # noqa: E402


class TrackingSearchConnector(BaseConnector):
    """Connector used to verify `(query, page)` search fan-out."""

    source = "Tracking"
    search_url_template = "https://example.com/jobs?q={query}&page={page}"
    job_href_pattern = re.compile(r".*")

    def __init__(self, settings: Settings, fetcher: CachedFetcher) -> None:
        super().__init__(settings, fetcher)
        self._lock = threading.Lock()
        self.active_calls = 0
        self.max_active_calls = 0

    @property
    def base_url(self) -> str:
        return "https://example.com"

    def fetch_search_page(self, query: str, page: int) -> str:
        with self._lock:
            self.active_calls += 1
            self.max_active_calls = max(self.max_active_calls, self.active_calls)
        try:
            time.sleep(0.03)
            return f"{query}|{page}"
        finally:
            with self._lock:
                self.active_calls -= 1

    def parse_search_page(self, html: str, query: str) -> list[JobListing]:
        _, page = html.split("|", maxsplit=1)
        return [
            JobListing(
                source=self.source,
                title=f"{query}-p{page}",
                company="Example",
                location="台北市",
                url=f"https://example.com/{query}/{page}",
                summary="Python API",
            )
        ]


class TrackingDetailFetcher:
    """Fetcher that records concurrent 104 detail requests and delay overrides."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.active_calls = 0
        self.max_active_calls = 0
        self.delay_values: list[float | None] = []

    def fetch(
        self,
        url: str,
        force_refresh: bool = False,
        headers: dict[str, str] | None = None,
        delay_seconds: float | None = None,
        cache_ttl_seconds: float | None = None,
    ) -> str:
        del force_refresh, headers, cache_ttl_seconds
        with self._lock:
            self.active_calls += 1
            self.max_active_calls = max(self.max_active_calls, self.active_calls)
            self.delay_values.append(delay_seconds)
        try:
            time.sleep(0.03)
            return json.dumps(
                {
                    "data": {
                        "jobDetail": {
                            "jobDescription": "1. 規劃 AI 工作流\n2. 建置 Python API"
                        },
                        "condition": {
                            "workExp": "3年以上",
                            "edu": "大學",
                            "major": ["資訊工程相關"],
                            "specialty": [],
                            "skill": ["Python"],
                            "certificate": [],
                            "driverLicense": [],
                            "language": [],
                            "other": "具備 API 串接經驗",
                        },
                    }
                }
            )
        finally:
            with self._lock:
                self.active_calls -= 1


class StagedFakeConnector:
    """Connector used to verify staged pipeline contracts."""

    def __init__(self, source: str = "Fake") -> None:
        self.source = source
        self.last_errors: list[str] = []

    def search(
        self,
        queries: list[str],
        *,
        pages: list[int] | None = None,
    ) -> list[JobListing]:
        del pages
        return [
            JobListing(
                source=self.source,
                title="AI 工程師",
                company="Example",
                location="台北市",
                url="https://example.com/jobs/1",
                summary=f"{queries[0]} Python LLM",
            )
        ]

    def enrich_details(self, jobs: list[JobListing]) -> list[JobListing]:
        for job in jobs:
            job.description = "負責設計 AI 工作流、整合 LLM 與企業 API。"
            job.work_content_items = ["設計 AI 工作流", "整合 LLM 與企業 API"]
            job.required_skill_items = ["Python", "LLM"]
            job.requirement_items = ["Python", "LLM", "API 串接"]
            job.metadata["detail_enriched"] = True
        return jobs


class WaveTimingConnector:
    """Connector used to verify initial-wave readiness and remaining-wave page routing."""

    def __init__(self, source: str, delay_seconds: float, jobs_per_page: dict[int, int]) -> None:
        self.source = source
        self.delay_seconds = delay_seconds
        self.jobs_per_page = jobs_per_page
        self.last_errors: list[str] = []

    def search(
        self,
        queries: list[str],
        *,
        pages: list[int] | None = None,
    ) -> list[JobListing]:
        time.sleep(self.delay_seconds)
        target_pages = list(pages or [1])
        jobs: list[JobListing] = []
        for page in target_pages:
            job_count = self.jobs_per_page.get(int(page), 0)
            for index in range(job_count):
                jobs.append(
                    JobListing(
                        source=self.source,
                        title=f"{self.source}-{queries[0]}-p{page}-{index}",
                        company=f"{self.source} Corp",
                        location="台北市",
                        url=f"https://example.com/{self.source}/{page}/{index}",
                        summary=f"{self.source} {queries[0]} page {page}",
                    )
                )
        return jobs

    def enrich_details(self, jobs: list[JobListing]) -> list[JobListing]:
        return jobs


class QueryScaledWaveConnector:
    """Connector whose completion time scales with query count to simulate force-refresh full mode."""

    def __init__(self, source: str, per_query_delay: float, jobs_per_query: int = 1) -> None:
        self.source = source
        self.per_query_delay = per_query_delay
        self.jobs_per_query = jobs_per_query
        self.last_errors: list[str] = []

    def search(
        self,
        queries: list[str],
        *,
        pages: list[int] | None = None,
    ) -> list[JobListing]:
        del pages
        time.sleep(self.per_query_delay * len(queries))
        jobs: list[JobListing] = []
        for query_index, query in enumerate(queries):
            for item_index in range(self.jobs_per_query):
                jobs.append(
                    JobListing(
                        source=self.source,
                        title=f"{self.source}-{query}-{item_index}",
                        company=f"{self.source} Corp",
                        location="台北市",
                        url=f"https://example.com/{self.source}/{query_index}/{item_index}",
                        summary=f"{query} summary",
                    )
                )
        return jobs

    def enrich_details(self, jobs: list[JobListing]) -> list[JobListing]:
        return jobs


class PipelineStagingTests(unittest.TestCase):
    """Regression tests for staged crawl collection and finalization."""

    def build_settings(self) -> Settings:
        return Settings(
            data_dir=Path(tempfile.mkdtemp()),
            request_timeout=5.0,
            request_delay=0.4,
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

    def test_fetcher_respects_delay_override_and_skips_cache_hit_sleep(self) -> None:
        fetcher = CachedFetcher(
            cache_dir=Path(tempfile.mkdtemp()),
            timeout=5.0,
            delay_seconds=0.9,
            user_agent="test-agent",
        )
        with (
            mock.patch.object(fetcher, "_open_with_fallback", return_value=b"<html>ok</html>"),
            mock.patch("job_spy_tw.utils.time.sleep") as sleep_mock,
        ):
            fetcher.fetch("https://example.com/jobs", delay_seconds=0.12)
            sleep_mock.assert_called_once_with(0.12)
            sleep_mock.reset_mock()

            fetcher.fetch("https://example.com/jobs")
            sleep_mock.assert_not_called()

    def test_fetcher_purge_cache_removes_expired_and_oldest_entries(self) -> None:
        fetcher = CachedFetcher(
            cache_dir=Path(tempfile.mkdtemp()),
            timeout=5.0,
            delay_seconds=0.0,
            user_agent="test-agent",
        )
        now_ts = time.time()
        entries = [
            ("https://example.com/old", "<html>old</html>", now_ts - 100, now_ts - 100, 600),
            ("https://example.com/new", "<html>new</html>", now_ts - 10, now_ts - 10, 600),
            ("https://example.com/expired", "<html>expired</html>", now_ts - 1000, now_ts - 1000, 1),
        ]
        for url, html, created_at_ts, last_accessed_at_ts, ttl_seconds in entries:
            cache_key = hashlib.sha256(url.encode()).hexdigest()
            fetcher.backend.write(
                cache_key,
                html=html,
                meta={
                    "url": url,
                    "created_at_ts": created_at_ts,
                    "last_accessed_at_ts": last_accessed_at_ts,
                    "ttl_seconds": ttl_seconds,
                },
            )

        fetcher.purge_cache(max_bytes=10_000, max_files=1)

        remaining_keys = fetcher.backend.iter_entry_keys()
        self.assertEqual(len(remaining_keys), 1)
        self.assertEqual(
            remaining_keys[0],
            hashlib.sha256("https://example.com/new".encode()).hexdigest(),
        )

    def test_base_connector_search_parallelizes_query_page_fetches(self) -> None:
        settings = self.build_settings()
        connector = TrackingSearchConnector(
            settings=settings,
            fetcher=CachedFetcher(
                cache_dir=Path(tempfile.mkdtemp()),
                timeout=5.0,
                delay_seconds=0.0,
                user_agent="test-agent",
            ),
        )

        jobs = connector.search(["AI", "Data"])

        self.assertEqual(len(jobs), 4)
        self.assertGreater(connector.max_active_calls, 1)
        self.assertEqual(connector.last_errors, [])

    def test_base_connector_search_pages_filter_limits_to_requested_pages(self) -> None:
        settings = self.build_settings()
        connector = TrackingSearchConnector(
            settings=settings,
            fetcher=CachedFetcher(
                cache_dir=Path(tempfile.mkdtemp()),
                timeout=5.0,
                delay_seconds=0.0,
                user_agent="test-agent",
            ),
        )

        jobs = connector.search(["AI", "Data"], pages=[1])

        self.assertEqual(len(jobs), 2)
        self.assertEqual(sorted(job.title for job in jobs), ["AI-p1", "Data-p1"])

    def test_104_detail_enrichment_parallelizes_requests_and_uses_detail_delay(self) -> None:
        settings = self.build_settings()
        fetcher = TrackingDetailFetcher()
        connector = Site104Connector(settings=settings, fetcher=fetcher)  # type: ignore[arg-type]
        jobs = [
            JobListing(
                source="104",
                title=f"AI工程師-{index}",
                company="Example",
                location="台北市",
                url=f"https://www.104.com.tw/job/abc12{index}",
                metadata={"job_code": f"abc12{index}"},
            )
            for index in range(4)
        ]

        connector.enrich_details(jobs)

        self.assertGreater(fetcher.max_active_calls, 1)
        expected_delay = max(0.05, settings.request_delay * 0.12)
        self.assertTrue(all(value == expected_delay for value in fetcher.delay_values))
        self.assertTrue(all(job.work_content_items for job in jobs))

    def test_pipeline_collect_and_finalize_follow_staged_contract(self) -> None:
        settings = self.build_settings()
        role_targets = [TargetRole(name="AI工程師", priority=1, keywords=["AI Engineer"])]
        pipeline = JobMarketPipeline(settings=settings, role_targets=role_targets)
        pipeline.connectors = [StagedFakeConnector()]

        jobs, errors = pipeline.collect_jobs(["AI工程師"])
        partial_snapshot = pipeline.build_partial_snapshot(
            queries=["AI工程師"],
            jobs=jobs,
            errors=errors,
        )
        final_snapshot = pipeline.finalize_snapshot(
            queries=["AI工程師"],
            jobs=jobs,
            errors=errors,
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(jobs), 1)
        self.assertGreater(jobs[0].relevance_score, 0)
        self.assertEqual(partial_snapshot.skills, [])
        self.assertEqual(partial_snapshot.task_insights, [])
        self.assertTrue(final_snapshot.skills)
        self.assertTrue(final_snapshot.task_insights)
        self.assertTrue(final_snapshot.jobs[0].work_content_items)
        with sqlite3.connect(settings.market_history_db_path) as connection:
            run_row = connection.execute(
                "SELECT job_count, persisted_job_count FROM crawl_runs ORDER BY id DESC LIMIT 1"
            ).fetchone()
            run_job_count = connection.execute(
                "SELECT COUNT(*) FROM crawl_run_jobs"
            ).fetchone()

        self.assertEqual(int(run_row[0]), 1)
        self.assertEqual(int(run_row[1]), 1)
        self.assertEqual(int(run_job_count[0]), 1)

    def test_collect_initial_wave_returns_before_slow_source_finishes(self) -> None:
        settings = self.build_settings()
        role_targets = [TargetRole(name="AI工程師", priority=1, keywords=["AI Engineer"])]
        pipeline = JobMarketPipeline(settings=settings, role_targets=role_targets)
        pipeline.connectors = [
            WaveTimingConnector("FastA", delay_seconds=0.02, jobs_per_page={1: 11}),
            WaveTimingConnector("FastB", delay_seconds=0.02, jobs_per_page={1: 11}),
            WaveTimingConnector("Slow", delay_seconds=0.35, jobs_per_page={1: 8}),
        ]

        started_at = time.monotonic()
        jobs, errors, completed_sources = pipeline.collect_initial_wave(["AI工程師"])
        elapsed = time.monotonic() - started_at

        self.assertEqual(errors, [])
        self.assertLess(elapsed, 0.20)
        self.assertGreaterEqual(len(jobs), 20)
        self.assertEqual(sorted(completed_sources), ["FastA", "FastB"])

    def test_collect_remaining_waves_backfills_missing_page_one_then_advances(self) -> None:
        settings = self.build_settings()
        role_targets = [TargetRole(name="AI工程師", priority=1, keywords=["AI Engineer"])]
        pipeline = JobMarketPipeline(settings=settings, role_targets=role_targets)
        fast = WaveTimingConnector("Fast", delay_seconds=0.0, jobs_per_page={1: 2, 2: 1})
        slow = WaveTimingConnector("Slow", delay_seconds=0.0, jobs_per_page={1: 1, 2: 1})
        pipeline.connectors = [fast, slow]

        existing_jobs = fast.search(["AI工程師"], pages=[1])
        existing_jobs = pipeline._score_and_sort_jobs(existing_jobs)

        merged_jobs, errors, next_page = pipeline.collect_remaining_waves(
            ["AI工程師"],
            existing_jobs,
            page_cursor=1,
            completed_initial_sources=["Fast"],
        )

        self.assertEqual(errors, [])
        self.assertEqual(next_page, 2)
        self.assertEqual(sorted(job.source for job in merged_jobs), ["Fast", "Fast", "Slow"])

    def test_collect_initial_wave_waits_for_first_source_if_timeout_hits_before_any_completion(self) -> None:
        settings = self.build_settings()
        role_targets = [
            TargetRole(name="AI工程師", priority=1, keywords=["AI Engineer"]),
            TargetRole(name="全端工程師", priority=2, keywords=["Full Stack"]),
        ]
        pipeline = JobMarketPipeline(settings=settings, role_targets=role_targets)
        pipeline.connectors = [
            QueryScaledWaveConnector("ScaledA", per_query_delay=1.15, jobs_per_query=2),
            QueryScaledWaveConnector("ScaledB", per_query_delay=1.25, jobs_per_query=2),
        ]

        started_at = time.monotonic()
        jobs, errors, completed_sources = pipeline.collect_initial_wave(["AI工程師", "全端工程師"])
        elapsed = time.monotonic() - started_at

        self.assertEqual(errors, [])
        self.assertTrue(jobs)
        self.assertEqual(completed_sources, ["ScaledA"])
        self.assertGreater(elapsed, pipeline.INITIAL_WAVE_TIMEOUT_SECONDS)
        self.assertLess(elapsed, 3.5)


if __name__ == "__main__":
    unittest.main()
