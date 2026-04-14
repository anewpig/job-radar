"""Tests for canonical job normalization and duplicate merging."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.job_cleaning import merge_duplicate_jobs, normalize_job_listing  # noqa: E402
from job_spy_tw.models import JobListing  # noqa: E402


class JobCleaningTests(unittest.TestCase):
    def test_normalize_job_listing_populates_canonical_metadata(self) -> None:
        job = normalize_job_listing(
            JobListing(
                source="104",
                title="AI自動化工程師（台北總公司）",
                company="富邦媒體科技股份有限公司(富邦momo)",
                location="Taipei City, Taiwan",
                url="HTTPS://Example.com/jobs/1?ref=abc",
            )
        )

        self.assertEqual(job.metadata["canonical_title"], "ai自動化工程師")
        self.assertEqual(job.metadata["canonical_company"], "富邦媒體科技")
        self.assertEqual(job.metadata["canonical_location"], "台北市")
        self.assertEqual(job.metadata["canonical_url"], "https://example.com/jobs/1")

    def test_merge_duplicate_jobs_combines_cross_source_matches(self) -> None:
        merged = merge_duplicate_jobs(
            [
                JobListing(
                    source="104",
                    title="AI自動化工程師（台北總公司）",
                    company="富邦媒體科技股份有限公司(富邦momo)",
                    location="Taipei City, Taiwan",
                    url="https://www.104.com.tw/job/abc123?jobsource=cs_sub_custlist_rc",
                    summary="協助導入 AI 流程。",
                    work_content_items=["協助導入 AI 流程"],
                ),
                JobListing(
                    source="cake",
                    title="AI自動化工程師",
                    company="富邦媒體科技股份有限公司",
                    location="台北市信義區",
                    url="https://www.cake.me/companies/example/jobs/xyz",
                    description="負責規劃與導入生成式 AI 應用，並串接內部工作流程。",
                    required_skill_items=["Python", "RAG"],
                    requirement_items=["熟悉 API 串接"],
                ),
            ]
        )

        self.assertEqual(len(merged), 1)
        job = merged[0]
        self.assertTrue(job.metadata["cross_source_merged"])
        self.assertEqual(job.metadata["canonical_company"], "富邦媒體科技")
        self.assertEqual(job.metadata["canonical_location"], "台北市")
        self.assertEqual(job.metadata["source_aliases"], ["104", "cake"])
        self.assertIn("Python", job.required_skill_items)
        self.assertIn("協助導入 AI 流程", job.work_content_items)
        self.assertIn("生成式 AI 應用", job.description)

    def test_merge_duplicate_jobs_keeps_same_source_different_urls_separate(self) -> None:
        merged = merge_duplicate_jobs(
            [
                JobListing(
                    source="104",
                    title="AI工程師",
                    company="Example AI",
                    location="台北市",
                    url="https://www.104.com.tw/job/aaa111",
                    salary="月薪 70,000",
                ),
                JobListing(
                    source="104",
                    title="AI工程師",
                    company="Example AI",
                    location="台北市",
                    url="https://www.104.com.tw/job/bbb222",
                    salary="月薪 90,000",
                ),
            ]
        )

        self.assertEqual(len(merged), 2)


if __name__ == "__main__":
    unittest.main()
