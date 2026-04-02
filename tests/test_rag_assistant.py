from __future__ import annotations

import sys
from types import SimpleNamespace
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.models import JobListing, MarketSnapshot, ResumeProfile, TargetRole
from job_spy_tw.rag_assistant import JobMarketRAGAssistant


class FakeEmbeddingsAPI:
    def create(self, *, model, input):  # noqa: A002
        data = []
        for text in input:
            lowered = text.lower()
            if any(token in lowered for token in ("薪資", "月薪", "salary")):
                vector = [1.0, 0.0, 0.0]
            elif any(token in lowered for token in ("技能", "python", "llm", "rag")):
                vector = [0.0, 1.0, 0.0]
            else:
                vector = [0.0, 0.0, 1.0]
            data.append(SimpleNamespace(embedding=vector))
        return SimpleNamespace(data=data)


class FakeResponsesAPI:
    def create(self, **kwargs):
        prompt = kwargs["input"]
        if "優先學習" in prompt:
            return SimpleNamespace(output_text="結論：優先補強 Python、LLM、RAG。\n參考來源：[1][2]")
        return SimpleNamespace(output_text="結論：目前薪資多為月薪 5-8 萬。\n參考來源：[1]")


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsAPI()
        self.responses = FakeResponsesAPI()


class RAGAssistantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = MarketSnapshot(
            generated_at="2026-04-01T10:00:00",
            queries=["AI工程師"],
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM"])],
            jobs=[
                JobListing(
                    source="104",
                    title="AI工程師",
                    company="Example AI",
                    location="台北市",
                    url="https://example.com/jobs/1",
                    summary="月薪 60,000 - 80,000，負責 LLM 應用開發",
                    salary="月薪 60,000 - 80,000",
                    matched_role="AI工程師",
                    extracted_skills=["Python", "LLM", "RAG"],
                    work_content_items=["開發 LLM 應用", "建置 RAG 流程"],
                    required_skill_items=["Python", "LLM", "RAG"],
                ),
                JobListing(
                    source="1111",
                    title="Product Manager",
                    company="Example PM",
                    location="台北市",
                    url="https://example.com/jobs/2",
                    summary="產品規劃與跨部門溝通",
                    matched_role="PM",
                    extracted_skills=["Jira"],
                    work_content_items=["產品路線圖規劃"],
                    required_skill_items=["產品管理"],
                ),
            ],
            skills=[],
            task_insights=[],
        )
        self.resume_profile = ResumeProfile(
            summary="具備 Python 與 AI 專案經驗",
            target_roles=["AI工程師"],
            core_skills=["LLM", "RAG"],
            tool_skills=["Python"],
        )

    def test_answer_question_returns_answer_and_citations(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=FakeOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        response = assistant.answer_question(
            question="可以優先學習的技能有哪些？",
            snapshot=self.snapshot,
            resume_profile=self.resume_profile,
        )
        self.assertIn("Python", response.answer)
        self.assertGreaterEqual(len(response.citations), 1)
        self.assertEqual(response.model, "fake-answer")

    def test_generate_report_uses_same_rag_pipeline(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=FakeOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        response = assistant.generate_report(
            snapshot=self.snapshot,
            resume_profile=self.resume_profile,
        )
        self.assertIn("結論", response.answer)
        self.assertGreater(response.used_chunks, 0)

    def test_prompt_without_resume_requests_basic_info_before_personalized_advice(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=FakeOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        prompt = assistant._build_answer_prompt(
            question="我還需補足哪些技能？",
            snapshot=self.snapshot,
            resume_profile=None,
            chunks=[],
        )
        self.assertIn("不要假設使用者要應徵哪一種職缺", prompt)
        self.assertIn("目標職缺、年資、地點偏好、目前技能、想補強方向", prompt)


if __name__ == "__main__":
    unittest.main()
