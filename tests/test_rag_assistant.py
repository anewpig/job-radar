"""Tests for rag assistant behavior."""

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
from job_spy_tw.assistant.chunks import build_chunks
from job_spy_tw.assistant.models import KnowledgeChunk
from job_spy_tw.assistant.retrieval import EmbeddingRetriever
from job_spy_tw.rag_assistant import JobMarketRAGAssistant
from job_spy_tw.assistant.service import _build_citation_snippet, _select_citation_chunks


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
            return SimpleNamespace(
                output_text='{"summary":"優先補強 Python、LLM、RAG。","key_points":["Python 是核心技能","LLM 與 RAG 反覆出現"],"limitations":["薪資資料仍有限"],"next_step":"先把 RAG 專案經驗補進履歷。"}'
            )
        return SimpleNamespace(
            output_text='{"summary":"目前薪資多為月薪 5-8 萬。","key_points":["AI工程師職缺多集中在月薪區間","不同來源平台揭露程度不同"],"limitations":["部分職缺未揭露薪資"],"next_step":"可再依地點與年資細分比較。"}'
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsAPI()
        self.responses = FakeResponsesAPI()


class FlatEmbeddingsAPI:
    def create(self, *, model, input):  # noqa: A002
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=[1.0, 1.0, 1.0]) for _ in input]
        )


class FlatEmbeddingClient:
    def __init__(self) -> None:
        self.embeddings = FlatEmbeddingsAPI()


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
        self.assertEqual(response.summary, "優先補強 Python、LLM、RAG。")
        self.assertIn("Python 是核心技能", response.key_points)
        self.assertGreaterEqual(len(response.citations), 1)
        self.assertEqual(response.model, "fake-answer")
        self.assertTrue(
            any(keyword in response.citations[0].snippet for keyword in ("Python", "LLM", "RAG"))
        )

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

    def test_retrieval_prefers_rag_work_chunk_for_work_content_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="ai-skills",
                source_type="job-skill",
                label="AI 技能需求",
                text="Python；LLM；RAG；Docker",
                metadata={"role": "AI應用工程師"},
            ),
            KnowledgeChunk(
                chunk_id="rag-work",
                source_type="job-work",
                label="RAG 工作內容",
                text="Knowledge Base 維護；向量資料庫檢索優化；RAG workflow；API 整合",
                metadata={"role": "AI應用工程師"},
            ),
            KnowledgeChunk(
                chunk_id="pm-work",
                source_type="job-work",
                label="PM 工作內容",
                text="roadmap；PRD；跨部門協作",
                metadata={"role": "PM"},
            ),
        ]
        results = retriever.retrieve(
            question="RAG AI Engineer 的工作內容通常包含哪些模組？",
            chunks=chunks,
            top_k=2,
        )
        self.assertEqual(results[0].chunk_id, "rag-work")

    def test_retrieval_prefers_firmware_skill_chunk_for_firmware_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="firmware-summary",
                source_type="job",
                label="韌體工程師摘要",
                text="Bluetooth SoC 韌體開發，重視 C/C++、RTOS 與 ARM/MIPS。",
                metadata={"role": "韌體工程師"},
            ),
            KnowledgeChunk(
                chunk_id="firmware-skills",
                source_type="job-skill",
                label="韌體技能需求",
                text="C/C++；RTOS；ARM；Linux",
                metadata={"role": "韌體工程師"},
            ),
            KnowledgeChunk(
                chunk_id="ai-summary",
                source_type="job",
                label="AI應用工程師摘要",
                text="Python；LLM；RAG；Docker",
                metadata={"role": "AI應用工程師"},
            ),
        ]
        results = retriever.retrieve(
            question="韌體工程師最核心的能力通常有哪些？",
            chunks=chunks,
            top_k=2,
        )
        self.assertEqual(results[0].chunk_id, "firmware-skills")

    def test_retrieval_prefers_market_task_insight_for_aggregate_work_content_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="job-work-1",
                source_type="job-work-content",
                label="職缺工作內容",
                text="負責設計自動化流程並維護 Python 腳本。",
            ),
            KnowledgeChunk(
                chunk_id="market-task-1",
                source_type="market-task-insight",
                label="市場工作內容：流程自動化 / 效率優化",
                text="流程自動化 / 效率優化\n重要度：高\n出現次數：21",
                metadata={"occurrences": "21", "importance": "高"},
            ),
        ]
        results = retriever.retrieve(
            question="目前職缺常見的工作內容重點是什麼？",
            chunks=chunks,
            top_k=2,
        )
        self.assertEqual(results[0].chunk_id, "market-task-1")

    def test_retrieval_prefers_market_location_summary_for_location_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="market-skill-collab",
                source_type="market-skill-insight",
                label="市場技能：Collaboration",
                text="Collaboration\n重要度：高\n出現次數：8",
                metadata={"occurrences": "8", "importance": "高"},
            ),
            KnowledgeChunk(
                chunk_id="market-location",
                source_type="market-location-summary",
                label="地點分布摘要",
                text="總職缺數：34\n地點分布：\n- 台北市內湖區：2 筆\n最多的是：台北市內湖區（2 筆）",
            ),
        ]
        results = retriever.retrieve(
            question="目前職缺主要集中在哪些地點？",
            chunks=chunks,
            top_k=2,
        )
        self.assertEqual(results[0].chunk_id, "market-location")

    def test_build_chunks_emits_schema_types_and_metadata(self) -> None:
        chunks = build_chunks(snapshot=self.snapshot, resume_profile=self.resume_profile)
        chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}

        self.assertIn("job-summary-0", chunk_by_id)
        self.assertIn("job-salary-0", chunk_by_id)
        self.assertIn("job-skills-0", chunk_by_id)
        self.assertIn("job-work-0", chunk_by_id)
        self.assertIn("resume-summary", chunk_by_id)
        self.assertIn("market-source-summary", chunk_by_id)
        self.assertIn("market-role-summary", chunk_by_id)
        self.assertIn("market-location-summary", chunk_by_id)

        summary_chunk = chunk_by_id["job-summary-0"]
        self.assertEqual(summary_chunk.source_type, "job-summary")
        self.assertEqual(summary_chunk.metadata["source"], "104")
        self.assertEqual(summary_chunk.metadata["matched_role"], "AI工程師")
        self.assertEqual(summary_chunk.metadata["location"], "台北市")
        self.assertEqual(summary_chunk.metadata["salary"], "月薪 60,000 - 80,000")
        self.assertEqual(summary_chunk.metadata["updated_at"], "")
        self.assertTrue(summary_chunk.metadata["query_signature"])

        salary_chunk = chunk_by_id["job-salary-0"]
        self.assertEqual(salary_chunk.source_type, "job-salary")
        self.assertIn("薪資：月薪 60,000 - 80,000", salary_chunk.text)

        resume_chunk = chunk_by_id["resume-summary"]
        self.assertEqual(resume_chunk.source_type, "resume-summary")
        self.assertEqual(resume_chunk.metadata["roles"], ["AI工程師"])
        self.assertIn("query_signature", resume_chunk.metadata)

    def test_market_insight_snippet_prefers_top_lines_over_question_terms(self) -> None:
        chunk = KnowledgeChunk(
            chunk_id="market-skill",
            source_type="market-skill-insight",
            label="市場技能：Collaboration",
            text="Collaboration\n重要度：高\n出現次數：8\n範例職缺：自動化工程師",
        )

        snippet = _build_citation_snippet(
            question="目前市場最值得優先看的技能重點是什麼？",
            chunk=chunk,
            answer_summary="目前最值得先看的是 Collaboration。",
            answer_key_points=["Collaboration 出現次數最高"],
        )

        self.assertIn("Collaboration", snippet)
        self.assertIn("重要度：高", snippet)

    def test_citation_selection_prefers_top_market_skill_insight_for_aggregate_skill_question(self) -> None:
        chunks = [
            KnowledgeChunk(
                chunk_id="market-skill-python",
                source_type="market-skill-insight",
                label="市場技能：Python",
                text="Python\n重要度：中高\n出現次數：3",
                metadata={"occurrences": "3", "importance": "中高"},
            ),
            KnowledgeChunk(
                chunk_id="job-skill-rag",
                source_type="job-skills",
                label="RAG 技能需求",
                text="Python；LLM；RAG",
            ),
            KnowledgeChunk(
                chunk_id="market-skill-collab",
                source_type="market-skill-insight",
                label="市場技能：Collaboration",
                text="Collaboration\n重要度：高\n出現次數：8",
                metadata={"occurrences": "8", "importance": "高"},
            ),
        ]

        selected = _select_citation_chunks(
            question="目前市場最值得優先看的技能重點是什麼？",
            retrieved=chunks,
        )

        self.assertEqual(selected[0].chunk_id, "market-skill-collab")

    def test_citation_selection_prefers_market_task_insight_for_aggregate_work_content_question(self) -> None:
        chunks = [
            KnowledgeChunk(
                chunk_id="job-work-1",
                source_type="job-work-content",
                label="職缺工作內容",
                text="負責設計自動化流程並維護 Python 腳本。",
            ),
            KnowledgeChunk(
                chunk_id="market-task-1",
                source_type="market-task-insight",
                label="市場工作內容：流程自動化 / 效率優化",
                text="流程自動化 / 效率優化\n重要度：高\n出現次數：21",
                metadata={"occurrences": "21", "importance": "高"},
            ),
        ]

        selected = _select_citation_chunks(
            question="目前職缺常見的工作內容重點是什麼？",
            retrieved=chunks,
        )

        self.assertEqual(selected[0].chunk_id, "market-task-1")

    def test_retrieval_prefers_source_summary_for_source_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="market-source-summary",
                source_type="market-source-summary",
                label="來源分布摘要",
                text="總職缺數：30\n來源分布：\n- 104：20 筆\n- 1111：8 筆\n- Cake：2 筆\n最多的是：104（20 筆）",
            ),
            KnowledgeChunk(
                chunk_id="job-skills",
                source_type="job-skills",
                label="自動化工程師 技能需求",
                text="Python；PLC；自動控制",
            ),
        ]
        results = retriever.retrieve(
            question="目前哪個來源的職缺量最多？",
            chunks=chunks,
            top_k=1,
        )
        self.assertEqual(results[0].chunk_id, "market-source-summary")

    def test_retrieval_prefers_role_summary_for_role_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="market-role-summary",
                source_type="market-role-summary",
                label="角色分布摘要",
                text="總職缺數：30\n匹配角色分布：\n- 自動化工程師：24 筆\n- 韌體工程師：6 筆\n最多的是：自動化工程師（24 筆）",
            ),
            KnowledgeChunk(
                chunk_id="market-skill",
                source_type="market-skill-insight",
                label="市場技能：Python",
                text="重要度：高\n出現次數：10",
            ),
        ]
        results = retriever.retrieve(
            question="目前職缺主要集中在哪些匹配角色？",
            chunks=chunks,
            top_k=1,
        )
        self.assertEqual(results[0].chunk_id, "market-role-summary")

    def test_retrieval_prefers_location_summary_for_location_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="market-location-summary",
                source_type="market-location-summary",
                label="地點分布摘要",
                text="總職缺數：30\n地點分布：\n- 台北市內湖區：5 筆\n- 新竹市：4 筆\n最多的是：台北市內湖區（5 筆）",
            ),
            KnowledgeChunk(
                chunk_id="market-skill",
                source_type="market-skill-insight",
                label="市場技能：Collaboration",
                text="重要度：中\n出現次數：7",
            ),
        ]
        results = retriever.retrieve(
            question="目前職缺主要集中在哪些地點？",
            chunks=chunks,
            top_k=1,
        )
        self.assertEqual(results[0].chunk_id, "market-location-summary")

    def test_retrieval_prefers_salary_chunk_for_salary_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="ai-summary",
                source_type="job-summary",
                label="AI工程師摘要",
                text="負責 LLM 與 RAG 應用開發。",
                metadata={"matched_role": "AI工程師", "salary": "月薪 70,000 - 90,000"},
            ),
            KnowledgeChunk(
                chunk_id="ai-salary",
                source_type="job-salary",
                label="AI工程師薪資資訊",
                text="月薪 70,000 - 90,000；台北市；AI工程師",
                metadata={"matched_role": "AI工程師", "salary": "月薪 70,000 - 90,000"},
            ),
        ]
        results = retriever.retrieve(
            question="AI工程師目前常見的薪資區間是什麼？",
            chunks=chunks,
            top_k=1,
        )
        self.assertEqual(results[0].chunk_id, "ai-salary")


if __name__ == "__main__":
    unittest.main()
