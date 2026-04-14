"""Tests for AI assistant profile merging behavior."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.models import ResumeProfile
from job_spy_tw.ui.search import merge_assistant_profiles


class AssistantProfileMergeTests(unittest.TestCase):
    def test_merge_assistant_profiles_returns_resume_when_manual_missing(self) -> None:
        resume_profile = ResumeProfile(
            source_name="resume.pdf",
            summary="履歷摘要",
            target_roles=["前端工程師"],
            core_skills=["JavaScript", "TypeScript"],
        )

        merged = merge_assistant_profiles(resume_profile, None)

        self.assertIs(merged, resume_profile)

    def test_merge_assistant_profiles_combines_resume_and_manual_context(self) -> None:
        resume_profile = ResumeProfile(
            source_name="resume.pdf",
            summary="履歷摘要",
            target_roles=["AI 工程師"],
            core_skills=["Python", "LLM"],
            domain_keywords=["台北市"],
            match_keywords=["Python", "LLM", "台北市"],
        )
        manual_profile = ResumeProfile(
            source_name="assistant_intake",
            summary="目標職缺：前端工程師；年資：1-3 年；希望地點：桃園市；目前技能：React",
            target_roles=["前端工程師"],
            core_skills=["React"],
            domain_keywords=["桃園市"],
            match_keywords=["前端工程師", "React", "桃園市"],
            notes=["AI 助理目前使用你填寫的求職基本資料進行個人化回答。"],
        )

        merged = merge_assistant_profiles(resume_profile, manual_profile)

        assert merged is not None
        self.assertEqual(merged.extraction_method, "merged_resume_manual_profile")
        self.assertEqual(merged.target_roles[:2], ["前端工程師", "AI 工程師"])
        self.assertIn("React", merged.core_skills)
        self.assertIn("Python", merged.core_skills)
        self.assertIn("桃園市", merged.domain_keywords)
        self.assertIn("台北市", merged.domain_keywords)
        self.assertIn("補充條件：目標職缺：前端工程師", merged.summary)
        self.assertIn("AI 助理會優先參考履歷內容", " ".join(merged.notes))


if __name__ == "__main__":
    unittest.main()
