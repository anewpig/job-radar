"""Tests for pipeline snapshot lineage and data-quality metadata."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import load_settings  # noqa: E402
from job_spy_tw.models import JobListing, MARKET_SNAPSHOT_SCHEMA_VERSION, TargetRole  # noqa: E402
from job_spy_tw.pipeline import JobMarketPipeline  # noqa: E402
from job_spy_tw.storage import load_snapshot  # noqa: E402


class PipelineSnapshotQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        settings = load_settings(ROOT)
        settings.data_dir = Path(self._temp_dir.name)
        settings.enable_cake = False
        settings.enable_linkedin = False
        self.pipeline = JobMarketPipeline(
            settings=settings,
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM", "RAG"])],
        )

    def tearDown(self) -> None:
        self._temp_dir.cleanup()

    def _raw_jobs(self) -> list[JobListing]:
        return [
            JobListing(
                source="104",
                title="AI工程師（台北）",
                company="Example AI 股份有限公司",
                location="台北市信義區",
                url="https://example.com/jobs/1?ref=abc",
                summary="負責 LLM 應用與 RAG 系統",
                matched_role="AI工程師",
                extracted_skills=["Python", "LLM"],
                work_content_items=["建置 RAG 流程"],
                required_skill_items=["Python", "LLM"],
            ),
            JobListing(
                source="Cake",
                title="AI工程師",
                company="Example AI",
                location="Taipei City",
                url="https://jobs.example.com/ai-engineer",
                summary="負責 RAG 與 API 串接",
                matched_role="AI工程師",
                extracted_skills=["Python", "RAG"],
                work_content_items=["串接 API"],
                required_skill_items=["Python", "RAG"],
            ),
        ]

    def test_build_partial_snapshot_includes_data_quality_and_lineage(self) -> None:
        raw_jobs = self._raw_jobs()
        deduped_jobs = self.pipeline._dedupe_jobs(raw_jobs)
        self.pipeline._record_collection_quality(
            new_raw_jobs=raw_jobs,
            deduped_jobs=deduped_jobs,
        )

        snapshot = self.pipeline.build_partial_snapshot(
            queries=["AI工程師"],
            jobs=deduped_jobs,
            errors=["104: timeout"],
        )

        self.assertEqual(snapshot.snapshot_kind, "partial")
        self.assertEqual(snapshot.schema_version, MARKET_SNAPSHOT_SCHEMA_VERSION)
        self.assertEqual(snapshot.data_quality["snapshot_version"], MARKET_SNAPSHOT_SCHEMA_VERSION)
        self.assertEqual(snapshot.data_quality["job_counts"]["raw_collected"], 2)
        self.assertEqual(snapshot.data_quality["job_counts"]["deduped"], 1)
        self.assertGreaterEqual(snapshot.data_quality["lineage"]["lineage_record_count"], 2)
        self.assertTrue(snapshot.data_quality["snapshot_query_signature"])

    def test_complete_snapshot_persists_snapshot_version_and_quality(self) -> None:
        raw_jobs = self._raw_jobs()
        deduped_jobs = self.pipeline._dedupe_jobs(raw_jobs)
        self.pipeline._record_collection_quality(
            new_raw_jobs=raw_jobs,
            deduped_jobs=deduped_jobs,
        )

        snapshot = self.pipeline.complete_snapshot(
            queries=["AI工程師"],
            jobs=deduped_jobs,
            errors=[],
        )
        reloaded = load_snapshot(self.pipeline.settings.snapshot_path)

        self.assertIsNotNone(reloaded)
        assert reloaded is not None
        self.assertEqual(snapshot.snapshot_kind, "complete")
        self.assertEqual(reloaded.snapshot_kind, "complete")
        self.assertEqual(reloaded.schema_version, MARKET_SNAPSHOT_SCHEMA_VERSION)
        self.assertEqual(
            reloaded.data_quality["lineage"]["final_count"],
            len(snapshot.jobs),
        )
        self.assertEqual(
            reloaded.data_quality["job_counts"]["merged_duplicates"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
