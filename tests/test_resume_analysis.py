from __future__ import annotations

import sys
from types import SimpleNamespace
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.models import JobListing
from job_spy_tw.resume_analysis import (
    ResumeAnalysisService,
    RuleBasedResumeExtractor,
    describe_resume_source,
    extract_resume_text,
    mask_personal_text,
    summarize_match_gaps,
)
from job_spy_tw.targets import DEFAULT_TARGET_ROLES


class ResumeAnalysisTests(unittest.TestCase):
    class FakeEmbeddingsAPI:
        def create(self, *, model, input):  # noqa: A002
            data = []
            for text in input:
                lowered = text.lower()
                if any(token in lowered for token in ("ai應用工程師", "llm", "python", "rag", "api")):
                    vector = [1.0, 0.0, 0.0]
                elif any(token in lowered for token in ("product manager", "figma", "jira", "產品")):
                    vector = [0.0, 1.0, 0.0]
                else:
                    vector = [0.0, 0.0, 1.0]
                data.append(SimpleNamespace(embedding=vector))
            return SimpleNamespace(data=data)

    class FakeResponsesAPI:
        def parse(self, **kwargs):
            input_text = kwargs["input"]
            scores = []
            for line in input_text.splitlines():
                if "job_index=" not in line:
                    continue
                index = int(line.split("job_index=")[1].split(";")[0].strip())
                if "AI應用工程師" in line:
                    scores.append(
                        SimpleNamespace(
                            job_index=index,
                            similarity=0.95,
                            reason="幾乎同職稱",
                        )
                    )
                else:
                    scores.append(
                        SimpleNamespace(
                            job_index=index,
                            similarity=0.12,
                            reason="職稱差距大",
                        )
                    )
            return SimpleNamespace(output_parsed=SimpleNamespace(scores=scores))

    class FakeOpenAIClient:
        def __init__(self) -> None:
            self.embeddings = ResumeAnalysisTests.FakeEmbeddingsAPI()
            self.responses = ResumeAnalysisTests.FakeResponsesAPI()

    def test_extract_resume_text_reads_utf8_bytes(self) -> None:
        text, notes = extract_resume_text("resume.txt", "AI工程師\n熟悉 Python 與 LLM".encode("utf-8"))
        self.assertEqual(notes, [])
        self.assertIn("Python", text)

    def test_rule_based_resume_extractor_detects_roles_skills_and_tasks(self) -> None:
        extractor = RuleBasedResumeExtractor(DEFAULT_TARGET_ROLES)
        profile = extractor.extract(
            """
            Applied AI Engineer / AI工程師
            熟悉 Python、LLM、RAG、Docker，曾開發企業知識搜尋與 AI agent workflow。
            負責需求分析、API 串接、流程自動化與跨部門協作。
            """
        )
        self.assertIn("AI應用工程師", profile.target_roles)
        self.assertIn("LLM", profile.core_skills)
        self.assertIn("Python", profile.tool_skills)
        self.assertIn("系統整合 / API 串接", profile.preferred_tasks)
        self.assertTrue(profile.generated_prompts)

    def test_summary_skips_personal_info_and_garbled_lines(self) -> None:
        extractor = RuleBasedResumeExtractor(DEFAULT_TARGET_ROLES)
        profile = extractor.extract(
            """
            王小明 男 27 歲 (2023/6)
            主�⼿�0907-509-233
            abc123@gmail.com
            AI應用工程師，熟悉 Python、LLM、RAG 與 Docker。
            曾負責需求分析、API 串接與流程自動化。
            """
        )
        self.assertNotIn("0907", profile.summary)
        self.assertNotIn("gmail", profile.summary.lower())
        self.assertNotIn("�", profile.summary)
        self.assertIn("AI應用工程師", profile.summary)

    def test_domain_keywords_exclude_contact_address_and_license(self) -> None:
        extractor = RuleBasedResumeExtractor(DEFAULT_TARGET_ROLES)
        profile = extractor.extract(
            """
            Email: abc123@gmail.com
            地址：桃園市觀光路 99 號
            Vic
            具普通重型機車駕照、普通小型車駕照
            參與企業 AI 導入、資料分析與流程自動化專案
            """
        )
        joined = " ".join(profile.domain_keywords).lower()
        self.assertIn("企業 AI 導入", profile.domain_keywords)
        self.assertIn("資料分析", profile.domain_keywords)
        self.assertNotIn("gmail", joined)
        self.assertNotIn("桃園市", joined)
        self.assertNotIn("觀光路", joined)
        self.assertNotIn("vic", joined)
        self.assertNotIn("重型", joined)
        self.assertNotIn("小型車", joined)
        self.assertNotIn("駕照", joined)

    def test_mask_personal_text_redacts_name_phone_and_email(self) -> None:
        masked = mask_personal_text("姓名：王小明 / 0907-509-233 / abc123@gmail.com")
        self.assertNotIn("王小明", masked)
        self.assertNotIn("0907-509-233", masked)
        self.assertNotIn("abc123@gmail.com", masked)
        self.assertIn("***", masked)

    def test_describe_resume_source_hides_filename(self) -> None:
        self.assertEqual(describe_resume_source("王小明_履歷.pdf"), "已上傳 PDF 履歷")
        self.assertEqual(describe_resume_source("手動貼上的履歷文字"), "手動貼上的履歷文字")

    def test_resume_matcher_ranks_skill_overlap_higher(self) -> None:
        service = ResumeAnalysisService(DEFAULT_TARGET_ROLES)
        profile = service.build_profile(
            """
            AI應用工程師
            技能：Python、LLM、RAG、Docker、AWS
            工作內容：需求分析、API 串接、流程自動化
            """,
            use_llm=False,
        )

        strong_match = JobListing(
            source="104",
            title="AI應用工程師",
            company="Example AI",
            location="台北市",
            url="https://example.com/jobs/1",
            matched_role="AI應用工程師",
            extracted_skills=["Python", "LLM", "RAG", "Docker"],
            work_content_items=["需求分析與系統規格訪談", "負責 API 串接與流程自動化"],
            required_skill_items=["Python", "LLM", "Docker"],
            requirement_items=["熟悉 RAG 與 AWS"],
            summary="打造企業 AI 應用",
        )
        weak_match = JobListing(
            source="1111",
            title="Product Manager",
            company="Example PM",
            location="台北市",
            url="https://example.com/jobs/2",
            matched_role="PM",
            extracted_skills=["Figma", "Jira"],
            work_content_items=["產品路線圖規劃", "跨部門會議安排"],
            required_skill_items=["產品管理"],
            requirement_items=["熟悉 PRD 撰寫"],
            summary="產品規劃與溝通",
        )

        matches = service.match_jobs(profile, [weak_match, strong_match])
        self.assertEqual(matches[0].job_url, strong_match.url)
        self.assertGreater(matches[0].overall_score, matches[1].overall_score)
        self.assertGreater(matches[0].market_fit_score, matches[1].market_fit_score)
        self.assertGreater(matches[0].exact_match_score, matches[1].exact_match_score)
        self.assertIn("Python", matches[0].matched_skills)
        self.assertTrue(matches[0].fit_summary)

    def test_ai_matcher_uses_llm_title_and_embedding_scores(self) -> None:
        service = ResumeAnalysisService(
            DEFAULT_TARGET_ROLES,
            title_model="fake-title",
            embedding_model="fake-embedding",
            openai_client=self.FakeOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        profile = service.build_profile(
            """
            AI應用工程師
            技能：Python、LLM、RAG、Docker、AWS
            工作內容：需求分析、API 串接、流程自動化
            """,
            use_llm=False,
        )
        strong_match = JobListing(
            source="104",
            title="AI應用工程師",
            company="Example AI",
            location="台北市",
            url="https://example.com/jobs/1",
            matched_role="AI應用工程師",
            extracted_skills=["Python", "LLM", "RAG", "Docker"],
            work_content_items=["需求分析與系統規格訪談", "負責 API 串接與流程自動化"],
            required_skill_items=["Python", "LLM", "Docker"],
            requirement_items=["熟悉 RAG 與 AWS"],
            summary="打造企業 AI 應用",
        )
        weak_match = JobListing(
            source="1111",
            title="Product Manager",
            company="Example PM",
            location="台北市",
            url="https://example.com/jobs/2",
            matched_role="PM",
            extracted_skills=["Figma", "Jira"],
            work_content_items=["產品路線圖規劃", "跨部門會議安排"],
            required_skill_items=["產品管理"],
            requirement_items=["熟悉 PRD 撰寫"],
            summary="產品規劃與溝通",
        )

        matches = service.match_jobs(profile, [weak_match, strong_match])
        self.assertEqual(matches[0].job_url, strong_match.url)
        self.assertEqual(matches[0].scoring_method, "llm_embedding")
        self.assertGreater(matches[0].title_similarity, matches[1].title_similarity)
        self.assertGreater(matches[0].semantic_similarity, matches[1].semantic_similarity)
        self.assertGreater(matches[0].market_fit_score, matches[1].market_fit_score)
        self.assertGreater(matches[0].exact_match_score, matches[1].exact_match_score)
        self.assertGreater(matches[0].overall_score, matches[0].market_fit_score)

    def test_summarize_match_gaps_returns_strengths_and_gaps(self) -> None:
        service = ResumeAnalysisService(DEFAULT_TARGET_ROLES)
        profile = service.build_profile(
            """
            AI應用工程師
            技能：Python、LLM、RAG
            工作內容：需求分析、流程自動化
            """,
            use_llm=False,
        )
        job = JobListing(
            source="104",
            title="AI應用工程師",
            company="Example AI",
            location="台北市",
            url="https://example.com/jobs/1",
            matched_role="AI應用工程師",
            extracted_skills=["Python", "LLM", "RAG", "Docker"],
            work_content_items=["需求分析與系統規格訪談", "負責 API 串接與流程自動化"],
            required_skill_items=["Python", "LLM", "Docker"],
            requirement_items=["熟悉 AWS"],
            summary="打造企業 AI 應用",
        )

        matches = service.match_jobs(profile, [job])
        summary = summarize_match_gaps(matches, top_n=5, limit=3)

        self.assertEqual(summary["strength_skills"][0][0], "LLM")
        gap_skill_labels = {label for label, _ in summary["gap_skills"]}
        self.assertIn("Docker", gap_skill_labels)
        self.assertIn("AWS", gap_skill_labels)
        self.assertTrue(summary["gap_tasks"])


if __name__ == "__main__":
    unittest.main()
