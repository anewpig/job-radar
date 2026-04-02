from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import Settings  # noqa: E402
from job_spy_tw.crawl_tuning import apply_crawl_preset, get_crawl_preset  # noqa: E402
from job_spy_tw.models import JobListing, TargetRole  # noqa: E402
from job_spy_tw.pipeline import JobMarketPipeline  # noqa: E402


class FakeConnector:
    def __init__(self, source: str) -> None:
        self.source = source
        self.enriched_titles: list[str] = []

    def enrich_details(self, jobs):
        self.enriched_titles = [job.title for job in jobs]
        return jobs


class CrawlTuningTests(unittest.TestCase):
    def build_settings(self) -> Settings:
        return Settings(
            data_dir=Path(tempfile.mkdtemp()),
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
        )

    def test_quick_preset_overrides_speed_sensitive_settings(self) -> None:
        settings = self.build_settings()
        tuned = apply_crawl_preset(settings, get_crawl_preset("快速"))
        self.assertEqual(tuned.max_pages_per_source, 1)
        self.assertEqual(tuned.max_detail_jobs_per_source, 12)
        self.assertAlmostEqual(tuned.request_delay, 0.15)
        self.assertEqual(tuned.max_concurrent_requests, 6)
        self.assertEqual(tuned.min_relevance_score, settings.min_relevance_score)

    def test_full_preset_disables_low_relevance_filter(self) -> None:
        settings = self.build_settings()
        tuned = apply_crawl_preset(settings, get_crawl_preset("完整"))
        self.assertEqual(tuned.min_relevance_score, 0.0)

    def test_pipeline_enriches_top_jobs_by_relevance_per_source(self) -> None:
        role_targets = [TargetRole(name="AI工程師", priority=1, keywords=["AI Engineer"])]
        pipeline = JobMarketPipeline(settings=self.build_settings(), role_targets=role_targets)
        pipeline.settings.max_detail_jobs_per_source = 1
        connector_104 = FakeConnector("104")
        connector_1111 = FakeConnector("1111")
        pipeline.connectors = [connector_104, connector_1111]
        jobs = [
            JobListing(
                source="104",
                title="junior",
                company="A",
                location="台北市",
                url="https://example.com/1",
                relevance_score=30,
            ),
            JobListing(
                source="104",
                title="senior",
                company="A",
                location="台北市",
                url="https://example.com/2",
                relevance_score=90,
            ),
            JobListing(
                source="1111",
                title="pm-low",
                company="B",
                location="新北市",
                url="https://example.com/3",
                relevance_score=10,
            ),
            JobListing(
                source="1111",
                title="pm-high",
                company="B",
                location="新北市",
                url="https://example.com/4",
                relevance_score=70,
            ),
        ]
        errors: list[str] = []

        pipeline._enrich_details_by_relevance(jobs, errors)

        self.assertEqual(errors, [])
        self.assertEqual(connector_104.enriched_titles, ["senior"])
        self.assertEqual(connector_1111.enriched_titles, ["pm-high"])

    def test_full_preset_keeps_low_relevance_jobs_in_pipeline_filter(self) -> None:
        role_targets = [TargetRole(name="藥師", priority=1, keywords=["Pharmacist"])]
        settings = apply_crawl_preset(self.build_settings(), get_crawl_preset("完整"))
        pipeline = JobMarketPipeline(settings=settings, role_targets=role_targets)
        jobs = [
            JobListing(
                source="104",
                title="藥師",
                company="A",
                location="台北市",
                url="https://example.com/1",
                relevance_score=3,
            ),
            JobListing(
                source="1111",
                title="門市藥師",
                company="B",
                location="新北市",
                url="https://example.com/2",
                relevance_score=28,
            ),
        ]
        errors: list[str] = []

        filtered = pipeline._filter_low_relevance_jobs(jobs, errors)

        self.assertEqual(len(filtered), 2)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
