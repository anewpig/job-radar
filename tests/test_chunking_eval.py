"""Tests for chunking evaluation helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.assistant.chunking_eval import (  # noqa: E402
    LocalHashEmbeddingClient,
    build_all_eval_cases,
    build_anchored_itemized_chunks,
    build_anchored_windowed_chunks,
    build_default_eval_cases,
    build_realistic_eval_cases,
    build_hybrid_chunks,
    build_itemized_chunks,
    evaluate_chunking_strategy,
)
from job_spy_tw.assistant.chunks import build_chunks  # noqa: E402
from job_spy_tw.assistant.retrieval import EmbeddingRetriever  # noqa: E402
from job_spy_tw.models import JobListing, MarketSnapshot, SkillInsight, TargetRole  # noqa: E402


class ChunkingEvalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = MarketSnapshot(
            generated_at="2026-04-09T10:00:00",
            queries=["AI工程師"],
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM", "RAG"])],
            jobs=[
                JobListing(
                    source="104",
                    title="AI工程師",
                    company="Example AI",
                    location="台北市",
                    url="https://example.com/jobs/1",
                    summary="負責 LLM 應用與 RAG 系統",
                    salary="月薪 60,000 - 80,000",
                    matched_role="AI工程師",
                    extracted_skills=["Python", "LLM", "RAG"],
                    work_content_items=["開發 LLM 應用", "建置 RAG 流程", "串接 API"],
                    required_skill_items=["Python", "LLM", "RAG"],
                    requirement_items=["熟悉 Linux", "具備 API 經驗"],
                    detail_sections={
                        "work_content": "開發 LLM 應用\n建置 RAG 流程\n串接 API\n與產品合作",
                        "requirements": "熟悉 Linux\n具備 API 經驗\n能閱讀技術文件",
                    },
                ),
            ],
            skills=[
                SkillInsight(
                    skill="Python",
                    category="language",
                    score=0.9,
                    importance="高",
                    occurrences=8,
                    sample_jobs=["AI工程師 @ Example AI"],
                    sources=["104"],
                )
            ],
            task_insights=[],
        )

    def test_itemized_chunks_are_more_granular_than_current_chunks(self) -> None:
        current_chunks = build_chunks(self.snapshot, None)
        itemized_chunks = build_itemized_chunks(self.snapshot, None)
        self.assertGreater(len(itemized_chunks), len(current_chunks))
        self.assertTrue(any(chunk.chunk_id.startswith("job-skill-item-") for chunk in itemized_chunks))
        self.assertTrue(any(chunk.chunk_id.startswith("job-task-item-") for chunk in itemized_chunks))

    def test_hybrid_chunks_include_current_and_granular_views(self) -> None:
        hybrid_chunks = build_hybrid_chunks(self.snapshot, None)
        self.assertTrue(any(chunk.chunk_id == "job-summary-0" for chunk in hybrid_chunks))
        self.assertTrue(any(chunk.chunk_id.startswith("job-skill-item-") for chunk in hybrid_chunks))

    def test_anchored_chunks_embed_job_identity_inside_text(self) -> None:
        anchored_chunks = build_anchored_itemized_chunks(self.snapshot, None)
        skill_chunk = next(chunk for chunk in anchored_chunks if chunk.chunk_id.startswith("job-skill-item-"))
        self.assertIn("職缺：AI工程師", skill_chunk.text)
        self.assertIn("公司：Example AI", skill_chunk.text)

    def test_anchored_windowed_chunks_use_smaller_section_windows(self) -> None:
        windowed_chunks = build_anchored_windowed_chunks(self.snapshot, None)
        work_section_chunks = [
            chunk for chunk in windowed_chunks if chunk.chunk_id.startswith("job-section-0-work_content")
        ]
        self.assertGreaterEqual(len(work_section_chunks), 2)

    def test_evaluate_chunking_strategy_returns_case_metrics(self) -> None:
        cases = build_default_eval_cases(self.snapshot)
        retriever = EmbeddingRetriever(
            client=LocalHashEmbeddingClient(),
            embedding_model="local-hash-96",
            cache_dir=None,
        )
        summary = evaluate_chunking_strategy(
            strategy_name="current_structured",
            chunk_builder=build_chunks,
            snapshot=self.snapshot,
            resume_profile=None,
            cases=cases,
            retriever=retriever,
            top_k=5,
        )
        self.assertEqual(summary.case_count, len(cases))
        self.assertGreater(summary.chunks_count, 0)
        self.assertGreaterEqual(summary.hit_at_5, 0.0)
        self.assertLessEqual(summary.hit_at_5, 1.0)

    def test_realistic_eval_cases_use_more_natural_phrasings(self) -> None:
        cases = build_realistic_eval_cases(self.snapshot)
        self.assertTrue(any("如果先看整體市場" in case.question for case in cases))
        self.assertTrue(any("如果要投 AI工程師" in case.question for case in cases))
        self.assertTrue(any(case.target_terms for case in cases))

    def test_all_eval_cases_include_default_and_realistic_sets(self) -> None:
        default_cases = build_default_eval_cases(self.snapshot)
        realistic_cases = build_realistic_eval_cases(self.snapshot)
        all_cases = build_all_eval_cases(self.snapshot)
        self.assertGreaterEqual(len(all_cases), len(default_cases))
        self.assertGreaterEqual(len(all_cases), len(realistic_cases))
        self.assertTrue(any(case.question == default_cases[0].question for case in all_cases))
        self.assertTrue(any(case.question == realistic_cases[0].question for case in all_cases))


if __name__ == "__main__":
    unittest.main()
