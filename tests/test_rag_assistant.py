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

from job_spy_tw.models import (
    AssistantResponse,
    JobListing,
    MarketSnapshot,
    ResumeProfile,
    SalaryEstimate,
    TargetRole,
)
from job_spy_tw.assistant.chunks import build_chunks
from job_spy_tw.assistant.external_search import ExternalSearchResult
from job_spy_tw.assistant.models import KnowledgeChunk
from job_spy_tw.assistant.retrieval import EmbeddingRetriever
from job_spy_tw.rag_assistant import JobMarketRAGAssistant
from job_spy_tw.assistant.service import (
    _build_guidance_sections,
    _build_market_sections,
    _build_comparison_sections,
    _build_citation_snippet,
    _build_retrieval_query,
    _classify_answer_mode,
    _ensure_comparison_coverage,
    _parse_structured_answer,
    _select_answer_max_output_tokens,
    _select_citation_chunks,
    _select_top_k,
)


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


class CaptureResponsesAPI:
    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.requests: list[dict] = []

    def create(self, **kwargs):
        prompt = kwargs["input"]
        self.prompts.append(prompt)
        self.requests.append(kwargs)
        return SimpleNamespace(
            output_text='{"summary":"已整理完成。","key_points":["有引用上下文"],"limitations":[],"next_step":"繼續追問。"}'
        )


class CaptureOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = FlatEmbeddingsAPI()
        self.responses = CaptureResponsesAPI()


class CaptureRetriever:
    def __init__(self) -> None:
        self.questions: list[str] = []
        self.last_usage = {}

    def retrieve(self, *, question: str, chunks: list[KnowledgeChunk], top_k: int):
        self.questions.append(question)
        return chunks[:top_k]


class FakeExternalSearchClient:
    def __init__(self, results: list[ExternalSearchResult] | None = None) -> None:
        self.results = results or [
            ExternalSearchResult(
                title="Python 3.14 release notes",
                url="https://docs.python.org/3.14/whatsnew/3.14.html",
                snippet="整理 Python 3.14 的語法與標準函式庫更新。",
            )
        ]
        self.queries: list[str] = []

    def search(self, *, query: str) -> list[ExternalSearchResult]:
        self.queries.append(query)
        return self.results


class CountingPersistentIndex:
    def __init__(self) -> None:
        self.runtime_sync_calls = 0
        self.search_calls = 0

    def sync_runtime_snapshot(self, *, snapshot, embed_texts) -> int:  # noqa: ANN001
        self.runtime_sync_calls += 1
        return 0

    def sync_snapshot_file(self, *, snapshot_path, embed_texts) -> int:  # noqa: ANN001
        return 0

    def sync_snapshot_store(self, *, snapshot_store_dir, embed_texts) -> int:  # noqa: ANN001
        return 0

    def sync_market_history(self, *, history_db_path, embed_texts) -> int:  # noqa: ANN001
        return 0

    def search(self, *, question, embed_texts, top_k, exclude_source_refs):  # noqa: ANN001
        self.search_calls += 1
        return []


class StubSalaryEstimator:
    def __init__(self, estimate: SalaryEstimate | None = None) -> None:
        self._estimate = estimate or SalaryEstimate(
            predicted_low=70_000,
            predicted_mid=80_000,
            predicted_high=90_000,
            confidence=0.74,
            evidence_job_urls=[
                "https://example.com/jobs/evidence-1",
                "https://example.com/jobs/evidence-2",
            ],
            model_version="salary_estimator.v1",
        )
        self.model_version = self._estimate.model_version

    def estimate_job(self, job: JobListing) -> SalaryEstimate:  # noqa: ARG002
        return self._estimate

    def evidence_rows(self, urls: list[str]) -> list[dict[str, object]]:
        rows = {
            "https://example.com/jobs/evidence-1": {
                "url": "https://example.com/jobs/evidence-1",
                "title": "資深 AI 工程師",
                "company": "Evidence AI",
                "source": "104",
                "location": "台北市",
                "salary": "月薪 78,000 - 92,000",
            },
            "https://example.com/jobs/evidence-2": {
                "url": "https://example.com/jobs/evidence-2",
                "title": "LLM 應用工程師",
                "company": "Evidence Labs",
                "source": "1111",
                "location": "新北市",
                "salary": "月薪 72,000 - 88,000",
            },
        }
        return [rows[url] for url in urls if url in rows]


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
            raw_text="AI 工程師\n負責建置 RAG 流程\n熟悉 Python 與 API 串接",
            summary="具備 Python 與 AI 專案經驗",
            target_roles=["AI工程師"],
            core_skills=["LLM", "RAG"],
            tool_skills=["Python"],
            preferred_tasks=["建置 RAG 流程"],
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
        self.assertTrue(response.answer.strip())
        self.assertNotIn("重點\n", response.answer)
        self.assertGreater(response.used_chunks, 0)

    def test_specific_job_salary_question_uses_prediction_for_missing_salary(self) -> None:
        snapshot = MarketSnapshot(
            generated_at="2026-04-01T10:00:00",
            queries=["AI工程師"],
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM"])],
            jobs=[
                JobListing(
                    source="104",
                    title="AI工程師",
                    company="Example AI",
                    location="台北市",
                    url="https://example.com/jobs/3",
                    summary="負責 LLM 與 RAG 系統開發",
                    salary="",
                    matched_role="AI工程師",
                    extracted_skills=["Python", "LLM", "RAG"],
                    work_content_items=["開發 LLM 應用", "建置 RAG 流程"],
                    required_skill_items=["Python", "LLM", "RAG"],
                )
            ],
            skills=[],
            task_insights=[],
        )
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=FakeOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
            persistent_index_enabled=False,
            salary_estimator=StubSalaryEstimator(),
        )

        response = assistant.answer_question(
            question="這個 AI工程師職缺大概薪資多少？",
            snapshot=snapshot,
            resume_profile=None,
        )

        self.assertIn("AI 預估月薪 70,000-90,000", response.answer)
        self.assertTrue(
            any(citation.source_type == "salary-estimate-evidence" for citation in response.citations)
        )
        self.assertTrue(assistant.last_request_metrics["salary_prediction_used"])
        self.assertEqual(
            assistant.last_request_metrics["salary_prediction_model_version"],
            "salary_estimator.v1",
        )

    def test_aggregate_salary_question_keeps_rag_only(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=FakeOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
            persistent_index_enabled=False,
            salary_estimator=StubSalaryEstimator(),
        )

        response = assistant.answer_question(
            question="AI 工程師市場薪資大概多少？",
            snapshot=self.snapshot,
            resume_profile=None,
        )

        self.assertNotIn("AI 預估月薪", response.answer)
        self.assertFalse(assistant.last_request_metrics["salary_prediction_used"])
        self.assertEqual(
            assistant.last_request_metrics["salary_prediction_fallback_reason"],
            "aggregate_salary_question",
        )

    def test_specific_job_salary_question_skips_prediction_when_actual_salary_exists(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=FakeOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
            persistent_index_enabled=False,
            salary_estimator=StubSalaryEstimator(),
        )

        response = assistant.answer_question(
            question="AI工程師這個職缺薪資大概多少？",
            snapshot=self.snapshot,
            resume_profile=None,
        )

        self.assertNotIn("AI 預估月薪", response.answer)
        self.assertFalse(assistant.last_request_metrics["salary_prediction_used"])
        self.assertEqual(
            assistant.last_request_metrics["salary_prediction_fallback_reason"],
            "has_actual_salary",
        )

    def test_generate_report_keeps_balanced_latency_profile(self) -> None:
        client = CaptureOpenAIClient()
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=client,
            cache_dir=ROOT / "data" / "cache",
            persistent_index_enabled=False,
        )

        assistant.generate_report(
            snapshot=self.snapshot,
            resume_profile=self.resume_profile,
        )

        self.assertEqual(client.responses.requests[0]["max_output_tokens"], 440)
        self.assertIn("Prompt 變體：control", client.responses.prompts[0])

    def test_parse_structured_answer_renders_natural_paragraphs_without_section_titles(self) -> None:
        payload = _parse_structured_answer(
            '{"summary":"優先補強 Python、LLM、RAG。","key_points":["Python 是核心技能","LLM 與 RAG 反覆出現"],"limitations":["薪資資料仍有限"],"next_step":"先把 RAG 專案經驗補進履歷。"}'
        )
        self.assertIn("優先補強 Python、LLM、RAG。", payload["answer"])
        self.assertIn("另外，Python 是核心技能；LLM 與 RAG 反覆出現。", payload["answer"])
        self.assertIn("需要留意的是，薪資資料仍有限。", payload["answer"])
        self.assertNotIn("重點\n", payload["answer"])
        self.assertNotIn("限制\n", payload["answer"])
        self.assertNotIn("下一步\n", payload["answer"])

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
            conversation_context=None,
            answer_mode="market_summary",
            chunks=[],
        )
        self.assertIn("不要假設使用者要應徵哪一種職缺", prompt)
        self.assertIn("目標職缺、年資、地點偏好、目前技能、想補強方向", prompt)

    def test_prompt_with_conversation_context_includes_recent_turns(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=CaptureOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        history = [
            AssistantResponse(
                question="如果我想往韌體工程師走呢？",
                answer="先補 C/C++、RTOS。",
                summary="先補 C/C++、RTOS。",
                key_points=["RTOS 很常見", "ARM 與 Linux 也重要"],
            )
        ]
        prompt = assistant._build_answer_prompt(
            question="那還需要哪些能力？",
            snapshot=self.snapshot,
            resume_profile=self.resume_profile,
            conversation_context=history,
            answer_mode="personalized_guidance",
            chunks=[],
        )
        self.assertIn("最近問答上下文", prompt)
        self.assertIn("如果我想往韌體工程師走呢", prompt)
        self.assertIn("RTOS 很常見", prompt)

    def test_prompt_with_conversation_context_limits_to_two_turns_and_one_key_point(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=CaptureOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        history = [
            AssistantResponse(
                question="第一題",
                answer="第一答",
                summary="第一摘要",
                key_points=["第一重點", "第一額外重點"],
            ),
            AssistantResponse(
                question="第二題",
                answer="第二答",
                summary="第二摘要",
                key_points=["第二重點", "第二額外重點"],
            ),
            AssistantResponse(
                question="第三題",
                answer="第三答",
                summary="第三摘要",
                key_points=["第三重點"],
            ),
        ]

        prompt = assistant._build_answer_prompt(
            question="延伸問題",
            snapshot=self.snapshot,
            resume_profile=self.resume_profile,
            conversation_context=history,
            answer_mode="personalized_guidance",
            chunks=[],
        )

        self.assertIn("第一題", prompt)
        self.assertIn("第二題", prompt)
        self.assertNotIn("第三題", prompt)
        self.assertIn("第一重點", prompt)
        self.assertNotIn("第一額外重點", prompt)

    def test_retrieval_query_uses_recent_context_for_follow_up(self) -> None:
        history = [
            AssistantResponse(
                question="如果我想往韌體工程師走呢？",
                answer="先補 C/C++、RTOS。",
                summary="先補 C/C++、RTOS。",
                key_points=["ARM 與 Linux 也重要"],
            )
        ]
        query = _build_retrieval_query(
            question="那還需要哪些能力？",
            conversation_context=history,
            answer_mode="personalized_guidance",
        )
        self.assertIn("那還需要哪些能力", query)
        self.assertIn("韌體工程師", query)
        self.assertIn("C/C++", query)
        self.assertIn("回答模式 個人化建議", query)

    def test_retrieval_query_limits_history_to_two_turns(self) -> None:
        history = [
            AssistantResponse(
                question="第一題",
                answer="第一答",
                summary="第一摘要",
                key_points=["第一重點", "第一額外重點"],
            ),
            AssistantResponse(
                question="第二題",
                answer="第二答",
                summary="第二摘要",
                key_points=["第二重點"],
            ),
            AssistantResponse(
                question="第三題",
                answer="第三答",
                summary="第三摘要",
                key_points=["第三重點"],
            ),
        ]

        query = _build_retrieval_query(
            question="延伸問題",
            conversation_context=history,
            answer_mode="personalized_guidance",
        )

        self.assertIn("第一題", query)
        self.assertIn("第二題", query)
        self.assertNotIn("第三題", query)
        self.assertIn("第一摘要", query)
        self.assertNotIn("第一額外重點", query)

    def test_answer_question_passes_conversation_context_to_retrieval(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=CaptureOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        capture_retriever = CaptureRetriever()
        assistant.retriever = capture_retriever
        history = [
            AssistantResponse(
                question="如果我想往韌體工程師走呢？",
                answer="先補 C/C++、RTOS。",
                summary="先補 C/C++、RTOS。",
                key_points=["ARM 與 Linux 也重要"],
            )
        ]

        assistant.answer_question(
            question="那還需要哪些能力？",
            snapshot=self.snapshot,
            resume_profile=self.resume_profile,
            conversation_context=history,
        )
        self.assertEqual(len(capture_retriever.questions), 1)
        self.assertIn("韌體工程師", capture_retriever.questions[0])
        self.assertIn("C/C++", capture_retriever.questions[0])

    def test_general_chat_uses_market_retrieval_and_higher_temperature(self) -> None:
        client = CaptureOpenAIClient()
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=client,
            cache_dir=ROOT / "data" / "cache",
            persistent_index_enabled=False,
        )
        capture_retriever = CaptureRetriever()
        assistant.retriever = capture_retriever

        response = assistant.answer_question(
            question="幫我寫一句今天也要加油的話",
            snapshot=self.snapshot,
            resume_profile=None,
        )

        self.assertEqual(response.answer_mode, "general_chat")
        self.assertEqual(len(capture_retriever.questions), 1)
        self.assertGreaterEqual(response.used_chunks, 1)
        self.assertEqual(client.responses.requests[0]["temperature"], 0.55)
        self.assertIn("回答模式：general_chat", response.retrieval_notes)
        self.assertIn("已檢索", response.retrieval_notes[1])
        self.assertIn("general_chat 目前會一律補充市場檢索內容", response.retrieval_notes[-1])
        self.assertEqual(client.responses.requests[0]["max_output_tokens"], 220)

    def test_general_chat_with_temporal_hint_still_uses_market_retrieval(self) -> None:
        client = CaptureOpenAIClient()
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=client,
            cache_dir=ROOT / "data" / "cache",
            persistent_index_enabled=False,
        )
        capture_retriever = CaptureRetriever()
        assistant.retriever = capture_retriever

        response = assistant.answer_question(
            question="最近 Python 和 Java 哪個比較值得學？",
            snapshot=self.snapshot,
            resume_profile=None,
        )

        self.assertEqual(response.answer_mode, "general_chat")
        self.assertEqual(len(capture_retriever.questions), 1)
        self.assertGreaterEqual(response.used_chunks, 1)
        self.assertIn("已檢索", response.retrieval_notes[1])
        self.assertIn("general_chat 目前會一律補充市場檢索內容", response.retrieval_notes[-1])
        self.assertEqual(client.responses.requests[0]["max_output_tokens"], 220)

    def test_general_chat_after_market_history_does_not_get_forced_back_to_market_summary(self) -> None:
        client = CaptureOpenAIClient()
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=client,
            cache_dir=ROOT / "data" / "cache",
            persistent_index_enabled=False,
        )
        capture_retriever = CaptureRetriever()
        assistant.retriever = capture_retriever
        history = [
            AssistantResponse(
                question="目前市場最常見的技能是什麼？",
                answer="Python、LLM、RAG 很常見。",
                summary="Python、LLM、RAG 很常見。",
                key_points=["AI工程師職缺集中在台北", "部分職缺有薪資揭露"],
            )
        ]

        response = assistant.answer_question(
            question="你喜歡吃什麼？",
            snapshot=self.snapshot,
            resume_profile=None,
            conversation_context=history,
        )

        self.assertEqual(response.answer_mode, "general_chat")
        self.assertEqual(len(capture_retriever.questions), 1)
        self.assertGreaterEqual(response.used_chunks, 1)
        self.assertIn("已檢索", response.retrieval_notes[1])
        self.assertIn("general_chat 目前會一律補充市場檢索內容", response.retrieval_notes[-1])

    def test_general_chat_can_include_external_search_context(self) -> None:
        client = CaptureOpenAIClient()
        external_client = FakeExternalSearchClient()
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=client,
            cache_dir=ROOT / "data" / "cache",
            persistent_index_enabled=False,
            external_search_enabled=True,
            external_search_client=external_client,
        )
        capture_retriever = CaptureRetriever()
        assistant.retriever = capture_retriever

        response = assistant.answer_question(
            question="Python 3.14 有什麼新功能？",
            snapshot=self.snapshot,
            resume_profile=None,
        )

        self.assertEqual(external_client.queries, ["Python 3.14 有什麼新功能？"])
        self.assertEqual(assistant.last_request_metrics["external_search_result_count"], 1)
        self.assertIn("外部查詢：duckduckgo 1 筆", response.retrieval_notes)
        self.assertIn("來源類型：external-web", client.responses.prompts[0])
        self.assertIn("Python 3.14 release notes", client.responses.prompts[0])

    def test_market_summary_uses_compact_output_budget(self) -> None:
        client = CaptureOpenAIClient()
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=client,
            cache_dir=ROOT / "data" / "cache",
            persistent_index_enabled=False,
        )

        assistant.answer_question(
            question="目前市場最常見的技能是什麼？",
            snapshot=self.snapshot,
            resume_profile=None,
        )
        self.assertEqual(client.responses.requests[0]["max_output_tokens"], 300)
        self.assertEqual(assistant.last_request_metrics["prompt_variant"], "compact_qa")

    def test_runtime_snapshot_sync_is_skipped_for_unchanged_snapshot(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=CaptureOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        counting_index = CountingPersistentIndex()
        assistant.persistent_index = counting_index

        assistant.answer_question(
            question="目前市場最常見的技能是什麼？",
            snapshot=self.snapshot,
            resume_profile=None,
        )
        assistant.answer_question(
            question="目前市場最常見的技能是什麼？",
            snapshot=self.snapshot,
            resume_profile=None,
        )

        self.assertEqual(counting_index.runtime_sync_calls, 1)
        self.assertEqual(counting_index.search_calls, 2)

    def test_classify_answer_mode_routes_market_personalized_and_comparison(self) -> None:
        self.assertEqual(
            _classify_answer_mode(
                question="目前市場最常見的技能是什麼？",
                resume_profile=None,
            ),
            "market_summary",
        )
        self.assertEqual(
            _classify_answer_mode(
                question="我還需要補足哪些技能？",
                resume_profile=self.resume_profile,
            ),
            "personalized_guidance",
        )
        self.assertEqual(
            _classify_answer_mode(
                question="AI工程師和 PM 的差異是什麼？",
                resume_profile=self.resume_profile,
            ),
            "job_comparison",
        )
        self.assertEqual(
            _classify_answer_mode(
                question="Python 和 Java 的差異是什麼？",
                resume_profile=None,
            ),
            "general_chat",
        )

    def test_classify_answer_mode_only_uses_job_history_for_context_dependent_follow_up(self) -> None:
        history = [
            AssistantResponse(
                question="目前市場最常見的技能是什麼？",
                answer="Python、LLM、RAG 很常見。",
                summary="Python、LLM、RAG 很常見。",
                key_points=["AI工程師職缺集中在台北"],
            )
        ]
        self.assertEqual(
            _classify_answer_mode(
                question="那薪資呢？",
                resume_profile=None,
                conversation_context=history,
            ),
            "market_summary",
        )
        self.assertEqual(
            _classify_answer_mode(
                question="你喜歡吃什麼？",
                resume_profile=None,
                conversation_context=history,
            ),
            "general_chat",
        )

    def test_select_top_k_uses_fast_mode_defaults(self) -> None:
        self.assertEqual(
            _select_top_k(
                answer_mode="market_summary",
                question="目前市場最常見的技能是什麼？",
                requested_top_k=8,
            ),
            4,
        )
        self.assertEqual(
            _select_top_k(
                answer_mode="personalized_guidance",
                question="我還需要補足哪些技能？",
                requested_top_k=8,
            ),
            4,
        )
        self.assertEqual(
            _select_top_k(
                answer_mode="job_comparison",
                question="AI工程師和 PM 的差異是什麼？",
                requested_top_k=8,
            ),
            6,
        )
        self.assertEqual(
            _select_top_k(
                answer_mode="general_chat",
                question="最近 Python 和 Java 哪個比較值得學？",
                requested_top_k=8,
            ),
            2,
        )
        self.assertEqual(
            _select_top_k(
                answer_mode="market_summary",
                question="自動化工程師（台灣北部區域） 這個職缺需要哪些技能？",
                requested_top_k=8,
            ),
            5,
        )

    def test_select_top_k_balanced_profile_preserves_previous_budget(self) -> None:
        self.assertEqual(
            _select_top_k(
                answer_mode="market_summary",
                question="目前市場最常見的技能是什麼？",
                requested_top_k=8,
                latency_profile="balanced",
            ),
            6,
        )
        self.assertEqual(
            _select_top_k(
                answer_mode="job_comparison",
                question="AI工程師和 PM 的差異是什麼？",
                requested_top_k=8,
                latency_profile="balanced",
            ),
            10,
        )
        self.assertEqual(
            _select_top_k(
                answer_mode="general_chat",
                question="最近 Python 和 Java 哪個比較值得學？",
                requested_top_k=8,
                latency_profile="balanced",
            ),
            4,
        )

    def test_select_answer_max_output_tokens_follows_latency_profile(self) -> None:
        self.assertEqual(
            _select_answer_max_output_tokens(answer_mode="market_summary"),
            300,
        )
        self.assertEqual(
            _select_answer_max_output_tokens(
                answer_mode="market_summary",
                latency_profile="balanced",
            ),
            420,
        )
        self.assertEqual(
            _select_answer_max_output_tokens(answer_mode="general_chat"),
            220,
        )

    def test_prompt_includes_answer_mode_instruction(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=CaptureOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        prompt = assistant._build_answer_prompt(
            question="AI工程師和 PM 的差異是什麼？",
            snapshot=self.snapshot,
            resume_profile=self.resume_profile,
            conversation_context=None,
            answer_mode="job_comparison",
            chunks=[],
        )
        self.assertIn("回答模式：職缺比較", prompt)
        self.assertIn("比較角色差異", prompt)
        self.assertIn("`summary` 必須先點出最主要差異或選擇方向", prompt)
        self.assertIn("`key_points` 請優先用 3-4 個比較維度", prompt)
        self.assertIn("`next_step` 必須給出使用者下一步", prompt)
        self.assertIn("Prompt 變體：compact_qa", prompt)

    def test_build_comparison_sections_parses_labeled_points(self) -> None:
        sections = _build_comparison_sections(
            key_points=[
                "技能：AI工程師偏 Python / LLM，PM 偏 PRD / 溝通。",
                "工作內容：AI工程師偏開發，PM 偏協作與規劃。",
            ],
            limitations=["目前薪資揭露不完整。"],
        )
        self.assertEqual(
            sections,
            [
                {"label": "技能差異", "value": "AI工程師偏 Python / LLM，PM 偏 PRD / 溝通。"},
                {"label": "工作內容", "value": "AI工程師偏開發，PM 偏協作與規劃。"},
                {"label": "風險", "value": "目前薪資揭露不完整。"},
            ],
        )

    def test_build_guidance_sections_parses_labeled_points(self) -> None:
        sections = _build_guidance_sections(
            key_points=[
                "市場需求：目前最常見的是 Python、LLM、RAG。",
                "目前缺口：履歷裡還缺部署與產品化案例。",
                "優先補強：先補一個可展示的 RAG 專案。",
            ],
            limitations=["還缺明確年資資訊。"],
        )
        self.assertEqual(
            sections,
            [
                {"label": "市場需求", "value": "目前最常見的是 Python、LLM、RAG。"},
                {"label": "目前缺口", "value": "履歷裡還缺部署與產品化案例。"},
                {"label": "優先補強", "value": "先補一個可展示的 RAG 專案。"},
                {"label": "提醒", "value": "還缺明確年資資訊。"},
            ],
        )

    def test_build_market_sections_parses_labeled_points(self) -> None:
        sections = _build_market_sections(
            key_points=[
                "市場分布：目前 AI工程師職缺仍以台北最多。",
                "核心技能：Python、LLM、RAG 最常出現。",
                "薪資樣態：揭露薪資多落在月薪 6-9 萬。",
            ],
            limitations=["部分來源薪資揭露仍不足。"],
        )
        self.assertEqual(
            sections,
            [
                {"label": "市場分布", "value": "目前 AI工程師職缺仍以台北最多。"},
                {"label": "核心技能", "value": "Python、LLM、RAG 最常出現。"},
                {"label": "薪資樣態", "value": "揭露薪資多落在月薪 6-9 萬。"},
                {"label": "趨勢提醒", "value": "部分來源薪資揭露仍不足。"},
            ],
        )

    def test_prompt_includes_market_summary_instruction(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=CaptureOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        prompt = assistant._build_answer_prompt(
            question="目前市場最常見的技能是什麼？",
            snapshot=self.snapshot,
            resume_profile=None,
            conversation_context=None,
            answer_mode="market_summary",
            chunks=[],
        )
        self.assertIn("回答模式：市場摘要", prompt)
        self.assertIn("`summary` 必須先講目前最值得注意的市場結論", prompt)
        self.assertIn("`key_points` 請優先用 3-4 個標記段落", prompt)
        self.assertIn("回答風格：正式 QA", prompt)
        self.assertIn("不要寫成教學文章、百科整理或過長的知識科普", prompt)

    def test_prompt_default_quick_question_now_uses_formal_qa_style(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=CaptureOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        prompt = assistant._build_answer_prompt(
            question="可以優先學習的技能有哪些？",
            snapshot=self.snapshot,
            resume_profile=None,
            conversation_context=None,
            answer_mode="market_summary",
            chunks=[],
        )
        self.assertIn("回答風格：正式 QA", prompt)
        self.assertNotIn("回答風格：標準化職涯 QA", prompt)

    def test_prompt_includes_personalized_guidance_instruction(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=CaptureOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        prompt = assistant._build_answer_prompt(
            question="我還需要補足哪些技能？",
            snapshot=self.snapshot,
            resume_profile=self.resume_profile,
            conversation_context=None,
            answer_mode="personalized_guidance",
            chunks=[],
        )
        self.assertIn("回答模式：個人化建議", prompt)
        self.assertIn("`summary` 必須先講最值得先做的方向", prompt)
        self.assertIn("`key_points` 請優先用 3-4 個標記段落", prompt)

    def test_prompt_includes_general_chat_instruction(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=CaptureOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        prompt = assistant._build_answer_prompt(
            question="Python 和 Java 的差異是什麼？",
            snapshot=self.snapshot,
            resume_profile=None,
            conversation_context=None,
            answer_mode="general_chat",
            chunks=[],
        )
        self.assertIn("回答模式：一般對話", prompt)
        self.assertIn("這題與求職市場不直接相關", prompt)
        self.assertIn("不要為了迎合系統背景，硬把話題拉回求職", prompt)
        self.assertIn("回答風格：自然 QA", prompt)
        self.assertIn("不要寫成知識科普、教科書或長篇背景整理", prompt)
        self.assertIn("目前沒有可用檢索內容，請直接回答使用者問題，並避免假裝引用市場資料。", prompt)

    def test_prompt_adds_skill_focus_guardrails_for_market_summary(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=CaptureOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        prompt = assistant._build_answer_prompt(
            question="目前市場最值得優先看的技能重點是什麼？",
            snapshot=self.snapshot,
            resume_profile=None,
            conversation_context=None,
            answer_mode="market_summary",
            chunks=[],
        )
        self.assertIn("這題聚焦：市場技能重點", prompt)
        self.assertIn("不要把技能題答成薪資題或地點題", prompt)
        self.assertIn("不要在 next_step 暗示可直接補出快照外資料", prompt)

    def test_prompt_adds_task_focus_guardrails_for_market_summary(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=CaptureOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        prompt = assistant._build_answer_prompt(
            question="目前職缺常見的工作內容重點是什麼？",
            snapshot=self.snapshot,
            resume_profile=None,
            conversation_context=None,
            answer_mode="market_summary",
            chunks=[],
        )
        self.assertIn("這題聚焦：工作內容重點", prompt)
        self.assertIn("優先使用動作型描述", prompt)
        self.assertIn("不要把技能名稱清單、地點或薪資描述當成主要工作內容", prompt)

    def test_prompt_adds_gap_guardrails_for_personalized_guidance(self) -> None:
        assistant = JobMarketRAGAssistant(
            api_key="test",
            answer_model="fake-answer",
            embedding_model="fake-embedding",
            client=CaptureOpenAIClient(),
            cache_dir=ROOT / "data" / "cache",
        )
        prompt = assistant._build_answer_prompt(
            question="以我目前履歷來看，現在最優先要補哪些技能？",
            snapshot=self.snapshot,
            resume_profile=self.resume_profile,
            conversation_context=None,
            answer_mode="personalized_guidance",
            chunks=[],
        )
        self.assertIn("這題聚焦：市場需求與個人缺口對照", prompt)
        self.assertIn("不要把市場常見技能直接等同於使用者缺口", prompt)
        self.assertIn("若履歷資訊不足，應在 limitations 明確說明", prompt)

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

    def test_retrieval_keeps_job_skill_chunk_in_top_k_for_aggregate_skill_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="job-skill-1",
                source_type="job-skills",
                label="AI工程師技能需求",
                text="Python；LLM；RAG",
            ),
        ]
        chunks.extend(
            KnowledgeChunk(
                chunk_id=f"market-skill-{index}",
                source_type="market-skill-insight",
                label=f"市場技能：技能{index}",
                text=f"技能{index}\n重要度：高\n出現次數：{20 - index}",
            )
            for index in range(1, 9)
        )
        results = retriever.retrieve(
            question="目前市場最值得優先看的技能重點是什麼？",
            chunks=chunks,
            top_k=8,
        )
        self.assertEqual(results[0].source_type, "market-skill-insight")
        self.assertTrue(any(chunk.chunk_id == "job-skill-1" for chunk in results))

    def test_retrieval_prefers_highest_occurrence_market_skill_for_aggregate_skill_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="market-skill-low",
                source_type="market-skill-insight",
                label="市場技能：Python",
                text="Python\n重要度：中高\n出現次數：3",
                metadata={"occurrences": "3", "importance": "中高"},
            ),
            KnowledgeChunk(
                chunk_id="market-skill-high",
                source_type="market-skill-insight",
                label="市場技能：Collaboration",
                text="Collaboration\n重要度：高\n出現次數：8",
                metadata={"occurrences": "8", "importance": "高"},
            ),
            KnowledgeChunk(
                chunk_id="market-skill-mid",
                source_type="market-skill-insight",
                label="市場技能：SQL",
                text="SQL\n重要度：中高\n出現次數：2",
                metadata={"occurrences": "2", "importance": "中高"},
            ),
        ]
        results = retriever.retrieve(
            question="目前市場最值得優先看的技能重點是什麼？",
            chunks=chunks,
            top_k=3,
        )
        self.assertEqual(results[0].chunk_id, "market-skill-high")

    def test_retrieval_keeps_job_work_chunk_in_top_k_for_aggregate_work_content_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="job-work-1",
                source_type="job-work-content",
                label="自動化工程師工作內容",
                text="負責設計自動化流程並維護 Python 腳本。",
            ),
        ]
        chunks.extend(
            KnowledgeChunk(
                chunk_id=f"market-task-{index}",
                source_type="market-task-insight",
                label=f"市場工作內容：重點{index}",
                text=f"重點{index}\n重要度：高\n出現次數：{20 - index}",
            )
            for index in range(1, 9)
        )
        results = retriever.retrieve(
            question="目前職缺常見的工作內容重點是什麼？",
            chunks=chunks,
            top_k=8,
        )
        self.assertEqual(results[0].source_type, "market-task-insight")
        self.assertTrue(any(chunk.chunk_id == "job-work-1" for chunk in results))

    def test_retrieval_keeps_job_summary_chunk_in_top_k_for_salary_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="summary-1",
                source_type="job-summary",
                label="AI工程師摘要",
                text="AI工程師，台北市，月薪 70,000 - 90,000，負責 LLM 與 RAG 平台開發。",
            ),
        ]
        chunks.extend(
            KnowledgeChunk(
                chunk_id=f"salary-{index}",
                source_type="job-salary",
                label=f"AI工程師薪資資訊 {index}",
                text=f"月薪 {70 + index},000 - {90 + index},000；台北市；AI工程師",
            )
            for index in range(1, 9)
        )
        results = retriever.retrieve(
            question="目前這批職缺的薪資帶大概怎麼看？",
            chunks=chunks,
            top_k=8,
        )
        self.assertEqual(results[0].source_type, "job-salary")
        self.assertTrue(any(chunk.chunk_id == "summary-1" for chunk in results))

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
        self.assertTrue(any(chunk.chunk_id.startswith("job-skill-item-0-") for chunk in chunks))
        self.assertTrue(any(chunk.chunk_id.startswith("job-task-item-0-") for chunk in chunks))
        self.assertIn("resume-summary", chunk_by_id)
        self.assertIn("resume-target-roles", chunk_by_id)
        self.assertIn("resume-core-skills", chunk_by_id)
        self.assertIn("resume-preferred-tasks", chunk_by_id)
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

        skills_chunk = chunk_by_id["job-skills-0"]
        self.assertIn("職缺：AI工程師", skills_chunk.text)
        self.assertIn("技能：Python；LLM；RAG", skills_chunk.text)

        work_chunk = chunk_by_id["job-work-0"]
        self.assertIn("職缺：AI工程師", work_chunk.text)
        self.assertIn("內容：開發 LLM 應用；建置 RAG 流程", work_chunk.text)

        resume_chunk = chunk_by_id["resume-summary"]
        self.assertEqual(resume_chunk.source_type, "resume-summary")
        self.assertEqual(resume_chunk.metadata["roles"], ["AI工程師"])
        self.assertIn("query_signature", resume_chunk.metadata)
        self.assertIn("履歷摘要：具備 Python 與 AI 專案經驗", resume_chunk.text)
        self.assertIn("核心技能：LLM；RAG", chunk_by_id["resume-core-skills"].text)
        self.assertIn("偏好工作內容：建置 RAG 流程", chunk_by_id["resume-preferred-tasks"].text)
        self.assertTrue(any(chunk.chunk_id.startswith("resume-window-") for chunk in chunks))

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

        self.assertEqual(selected[0].chunk_id, "market-skill-python")

    def test_citation_selection_supplements_top_market_skills_from_all_chunks(self) -> None:
        retrieved = [
            KnowledgeChunk(
                chunk_id="market-skill-python",
                source_type="market-skill-insight",
                label="市場技能：Python",
                text="Python\n重要度：高\n出現次數：18",
                metadata={"occurrences": "18", "importance": "高"},
            ),
            KnowledgeChunk(
                chunk_id="market-skill-collab",
                source_type="market-skill-insight",
                label="市場技能：Collaboration",
                text="Collaboration\n重要度：中\n出現次數：11",
                metadata={"occurrences": "11", "importance": "中"},
            ),
        ]
        all_chunks = [
            *retrieved,
            KnowledgeChunk(
                chunk_id="market-skill-ml",
                source_type="market-skill-insight",
                label="市場技能：Machine Learning",
                text="Machine Learning\n重要度：中\n出現次數：12",
                metadata={"occurrences": "12", "importance": "中"},
            ),
            KnowledgeChunk(
                chunk_id="market-skill-sql",
                source_type="market-skill-insight",
                label="市場技能：SQL",
                text="SQL\n重要度：中高\n出現次數：11",
                metadata={"occurrences": "11", "importance": "中高"},
            ),
        ]

        selected = _select_citation_chunks(
            question="目前市場最值得優先看的技能重點是什麼？",
            retrieved=retrieved,
            all_chunks=all_chunks,
            max_citations=4,
        )

        selected_ids = [chunk.chunk_id for chunk in selected]
        self.assertIn("market-skill-ml", selected_ids)
        self.assertIn("market-skill-sql", selected_ids)

    def test_citation_selection_uses_market_score_to_keep_snapshot_top_skills(self) -> None:
        all_chunks = [
            KnowledgeChunk(
                chunk_id="market-skill-python",
                source_type="market-skill-insight",
                label="市場技能：Python",
                text="Python\n重要度：高\n出現次數：18",
                metadata={"score": "92.98", "occurrences": "18", "importance": "高"},
            ),
            KnowledgeChunk(
                chunk_id="market-skill-sql",
                source_type="market-skill-insight",
                label="市場技能：SQL",
                text="SQL\n重要度：中高\n出現次數：11",
                metadata={"score": "58.93", "occurrences": "11", "importance": "中高"},
            ),
            KnowledgeChunk(
                chunk_id="market-skill-csharp",
                source_type="market-skill-insight",
                label="市場技能：C#",
                text="C#\n重要度：中高\n出現次數：8",
                metadata={"score": "44.98", "occurrences": "8", "importance": "中高"},
            ),
            KnowledgeChunk(
                chunk_id="market-skill-communication",
                source_type="market-skill-insight",
                label="市場技能：Communication",
                text="Communication\n重要度：中\n出現次數：13",
                metadata={"score": "38.8", "occurrences": "13", "importance": "中"},
            ),
            KnowledgeChunk(
                chunk_id="market-skill-machine-learning",
                source_type="market-skill-insight",
                label="市場技能：Machine Learning",
                text="Machine Learning\n重要度：中\n出現次數：6",
                metadata={"score": "37.96", "occurrences": "6", "importance": "中"},
            ),
            KnowledgeChunk(
                chunk_id="market-skill-collaboration",
                source_type="market-skill-insight",
                label="市場技能：Collaboration",
                text="Collaboration\n重要度：中\n出現次數：11",
                metadata={"score": "10.0", "occurrences": "11", "importance": "中"},
            ),
        ]
        selected = _select_citation_chunks(
            question="目前市場最值得優先看的技能重點是什麼？",
            retrieved=all_chunks[:2],
            all_chunks=all_chunks,
            max_citations=5,
        )
        selected_ids = [chunk.chunk_id for chunk in selected]
        self.assertIn("market-skill-machine-learning", selected_ids)
        self.assertNotIn("market-skill-collaboration", selected_ids)

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

    def test_citation_selection_covers_both_targets_for_comparison_question(self) -> None:
        chunks = [
            KnowledgeChunk(
                chunk_id="ai-summary",
                source_type="job-summary",
                label="AI工程師 @ Example AI",
                text="職稱：AI工程師\n地點：台北市\n薪資：月薪 70,000 - 90,000\n摘要：負責 LLM 與 RAG 應用開發。",
                metadata={"matched_role": "AI工程師", "title": "AI工程師"},
            ),
            KnowledgeChunk(
                chunk_id="pm-summary",
                source_type="job-summary",
                label="PM @ Example PM",
                text="職稱：PM\n地點：台北市\n薪資：月薪 65,000 - 85,000\n摘要：負責 roadmap、PRD 與跨部門協作。",
                metadata={"matched_role": "PM", "title": "PM"},
            ),
            KnowledgeChunk(
                chunk_id="market-skill",
                source_type="market-skill-insight",
                label="市場技能：Collaboration",
                text="Collaboration\n重要度：高\n出現次數：8",
                metadata={"occurrences": "8", "importance": "高"},
            ),
        ]

        selected = _select_citation_chunks(
            question="AI工程師和 PM 的差異是什麼？",
            retrieved=chunks,
            max_citations=3,
        )

        selected_ids = [chunk.chunk_id for chunk in selected]
        self.assertIn("ai-summary", selected_ids[:2])
        self.assertIn("pm-summary", selected_ids[:2])

    def test_ensure_comparison_coverage_injects_missing_target_chunk(self) -> None:
        all_chunks = [
            KnowledgeChunk(
                chunk_id="ai-skills",
                source_type="job-skills",
                label="AI應用工程師 技能需求",
                text="Python；LLM；RAG",
                metadata={"matched_role": "AI應用工程師", "title": "AI應用工程師", "relevance_score": 96.0},
            ),
            KnowledgeChunk(
                chunk_id="ai-summary",
                source_type="job-summary",
                label="AI應用工程師 @ Example AI",
                text="職稱：AI應用工程師\n摘要：負責 LLM 與 RAG 應用開發。",
                metadata={"matched_role": "AI應用工程師", "title": "AI應用工程師", "relevance_score": 96.0},
            ),
            KnowledgeChunk(
                chunk_id="automation-summary",
                source_type="job-summary",
                label="自動化工程師 @ Example Auto",
                text="職稱：自動化工程師\n摘要：負責流程自動化、系統整合與現場導入。",
                metadata={"matched_role": "自動化工程師", "title": "自動化工程師", "relevance_score": 88.0},
            ),
        ]
        retrieved = [all_chunks[0], all_chunks[1]]

        covered = _ensure_comparison_coverage(
            question="AI應用工程師 和 自動化工程師 的差異是什麼？",
            all_chunks=all_chunks,
            retrieved=retrieved,
            top_k=3,
        )

        covered_ids = [chunk.chunk_id for chunk in covered]
        self.assertIn("ai-summary", covered_ids[:2])
        self.assertIn("automation-summary", covered_ids[:2])

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

    def test_retrieval_prefers_exact_job_work_chunk_for_specific_job_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="market-skill",
                source_type="market-skill-insight",
                label="市場技能：Collaboration",
                text="Collaboration\n重要度：高\n出現次數：8",
                metadata={"occurrences": "8", "importance": "高"},
            ),
            KnowledgeChunk(
                chunk_id="ai-work",
                source_type="job-work-content",
                label="AI工程師 工作內容 1",
                text="職缺：AI工程師\n公司：Example AI\n角色：AI工程師\n內容：開發 LLM 應用",
                metadata={"title": "AI工程師", "company": "Example AI", "matched_role": "AI工程師"},
            ),
            KnowledgeChunk(
                chunk_id="ai-skill",
                source_type="job-skills",
                label="AI工程師 技能：Python",
                text="職缺：AI工程師\n公司：Example AI\n角色：AI工程師\n技能：Python",
                metadata={"title": "AI工程師", "company": "Example AI", "matched_role": "AI工程師"},
            ),
        ]
        results = retriever.retrieve(
            question="AI工程師 這個職缺主要在做什麼？",
            chunks=chunks,
            top_k=2,
        )
        self.assertEqual(results[0].chunk_id, "ai-work")

    def test_retrieval_prefers_exact_job_skill_chunk_for_specific_job_skill_question(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="market-skill",
                source_type="market-skill-insight",
                label="市場技能：Collaboration",
                text="Collaboration\n重要度：高\n出現次數：8",
                metadata={"occurrences": "8", "importance": "高"},
            ),
            KnowledgeChunk(
                chunk_id="auto-skill",
                source_type="job-skills",
                label="自動化工程師（台灣北部區域） 技能：PLC",
                text="職缺：自動化工程師（台灣北部區域）\n公司：谷林運算股份有限公司\n角色：自動化工程師\n技能：PLC",
                metadata={"title": "自動化工程師（台灣北部區域）", "company": "谷林運算股份有限公司", "matched_role": "自動化工程師"},
            ),
            KnowledgeChunk(
                chunk_id="other-skill",
                source_type="job-skills",
                label="Senior Automation Engineer 資深自動化工程師 技能：CI/CD",
                text="職缺：Senior Automation Engineer 資深自動化工程師\n公司：英屬維京群島商星科有限公司\n角色：Automation Engineer 自動化工程師\n技能：CI/CD",
                metadata={"title": "Senior Automation Engineer 資深自動化工程師", "company": "英屬維京群島商星科有限公司", "matched_role": "Automation Engineer 自動化工程師"},
            ),
        ]
        results = retriever.retrieve(
            question="自動化工程師（台灣北部區域） 這個職缺需要哪些技能？",
            chunks=chunks,
            top_k=2,
        )
        self.assertEqual(results[0].chunk_id, "auto-skill")

    def test_retrieval_prefers_exact_long_title_chunk_over_generic_title_match(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="market-task",
                source_type="market-task-insight",
                label="市場工作內容：流程自動化 / 效率優化",
                text="流程自動化 / 效率優化\n重要度：高\n出現次數：12",
                metadata={"occurrences": "12", "importance": "高"},
            ),
            KnowledgeChunk(
                chunk_id="generic-work",
                source_type="job-work-content",
                label="自動化工程師 工作內容：設備點檢",
                text="職缺：自動化工程師\n公司：其他公司\n角色：自動化工程師\n內容：設備點檢、維護、保養、異常排除。",
                metadata={"title": "自動化工程師", "company": "其他公司", "matched_role": "自動化工程師"},
            ),
            KnowledgeChunk(
                chunk_id="north-work",
                source_type="job-work-content",
                label="自動化工程師（台灣北部區域） 工作內容：規劃與執行工業物聯網（IIoT）專案",
                text="職缺：自動化工程師（台灣北部區域）\n公司：谷林運算股份有限公司\n角色：自動化工程師\n內容：規劃與執行工業物聯網（IIoT）專案",
                metadata={"title": "自動化工程師（台灣北部區域）", "company": "谷林運算股份有限公司", "matched_role": "自動化工程師"},
            ),
        ]
        results = retriever.retrieve(
            question="自動化工程師（台灣北部區域） 這個職缺主要在做什麼？",
            chunks=chunks,
            top_k=3,
        )
        self.assertEqual(results[0].chunk_id, "north-work")

    def test_retrieval_prefers_prefixed_title_chunk_over_generic_job_title(self) -> None:
        retriever = EmbeddingRetriever(
            client=FlatEmbeddingClient(),
            embedding_model="flat",
        )
        chunks = [
            KnowledgeChunk(
                chunk_id="generic-work",
                source_type="job-work-content",
                label="自動化工程師 工作內容：設備點檢",
                text="職缺：自動化工程師\n公司：其他公司\n角色：自動化工程師\n內容：設備點檢、維護、保養、異常排除。",
                metadata={"title": "自動化工程師", "company": "其他公司", "matched_role": "自動化工程師"},
            ),
            KnowledgeChunk(
                chunk_id="d4000-work",
                source_type="job-work-content",
                label="D4000 自動化工程師 工作內容：內部數據生產力平台開發與維護",
                text="職缺：D4000 自動化工程師\n公司：富邦媒體科技股份有限公司(富邦momo)\n角色：自動化工程師\n內容：協助內部數據生產力平台的開發與維護，並支援跨團隊專案推進。",
                metadata={"title": "D4000 自動化工程師", "company": "富邦媒體科技股份有限公司(富邦momo)", "matched_role": "自動化工程師"},
            ),
        ]
        results = retriever.retrieve(
            question="D4000 自動化工程師 這個職缺主要在做什麼？",
            chunks=chunks,
            top_k=2,
        )
        self.assertEqual(results[0].chunk_id, "d4000-work")


if __name__ == "__main__":
    unittest.main()
