from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.analysis import JobAnalyzer
from job_spy_tw.models import JobListing, TargetRole
from job_spy_tw.targets import DEFAULT_TARGET_ROLES


class AnalysisTests(unittest.TestCase):
    def test_extract_skills_prefers_ai_stack(self) -> None:
        analyzer = JobAnalyzer(DEFAULT_TARGET_ROLES)
        skills = analyzer.extract_skills(
            """
            我們正在找 AI Engineer，需要 Python、PyTorch、LLM、RAG、Docker，
            並且有 API design 與 AWS 經驗。
            """
        )
        self.assertIn("Python", skills)
        self.assertIn("PyTorch", skills)
        self.assertIn("LLM", skills)
        self.assertIn("RAG", skills)
        self.assertIn("Docker", skills)

    def test_role_scoring_matches_ai_application_engineer(self) -> None:
        analyzer = JobAnalyzer(DEFAULT_TARGET_ROLES)
        jobs = [
            JobListing(
                source="LinkedIn",
                title="Applied AI Engineer",
                company="Example AI",
                location="台北市",
                url="https://example.com/jobs/1",
                summary="Build LLM products with RAG and AI agent workflows.",
            )
        ]
        scored = analyzer.score_jobs(jobs)
        self.assertEqual(scored[0].matched_role, "AI應用工程師")
        self.assertGreater(scored[0].relevance_score, 80)

    def test_skill_summary_orders_high_frequency_skills_first(self) -> None:
        analyzer = JobAnalyzer(DEFAULT_TARGET_ROLES)
        jobs = analyzer.score_jobs(
            [
                JobListing(
                    source="104",
                    title="AI工程師",
                    company="A",
                    location="台北市",
                    url="https://example.com/1",
                    summary="Python LLM RAG Docker AWS",
                ),
                JobListing(
                    source="1111",
                    title="機器學習工程師",
                    company="B",
                    location="新竹市",
                    url="https://example.com/2",
                    summary="Python PyTorch LLM Docker",
                ),
            ]
        )
        skills = analyzer.summarize_skills(jobs)
        self.assertIn(skills[0].skill, {"Python", "LLM", "Docker"})

    def test_role_scoring_keeps_unrelated_jobs_low_for_pharmacist_search(self) -> None:
        analyzer = JobAnalyzer(
            [
                TargetRole(
                    name="藥師",
                    priority=1,
                    keywords=["Pharmacist", "門市藥師", "臨床藥師", "藥品調劑"],
                )
            ]
        )
        jobs = analyzer.score_jobs(
            [
                JobListing(
                    source="104",
                    title="AI工程師",
                    company="Example AI",
                    location="台北市",
                    url="https://example.com/ai",
                    summary="LLM, RAG, Python",
                ),
                JobListing(
                    source="1111",
                    title="門市藥師",
                    company="Example Pharma",
                    location="台中市",
                    url="https://example.com/pharma",
                    summary="藥品調劑、用藥諮詢與衛教",
                ),
            ]
        )
        self.assertEqual(jobs[0].title, "門市藥師")
        self.assertGreater(jobs[0].relevance_score, 80)
        self.assertLess(jobs[1].relevance_score, 18)


if __name__ == "__main__":
    unittest.main()
