"""Tests for post-training dataset and comparison builders."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = ROOT / "job-radar-eval"
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from job_radar_eval.config import EvalConfig  # noqa: E402
from job_radar_eval.post_training import (  # noqa: E402
    build_dpo_pairs_manifest,
    build_eval_comparison_manifest,
    build_sft_dataset_manifest,
)


def _structured_answer(summary: str, *key_points: str) -> str:
    return json.dumps(
        {
            "summary": summary,
            "key_points": list(key_points) or [summary],
            "limitations": ["需要更多資料"],
            "next_step": "持續驗證",
        },
        ensure_ascii=False,
    )


class PostTrainingPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="posttrain-tests-"))
        self.results_dir = self.temp_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.fixtures_dir = self.temp_dir / "fixtures"
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        self.config = EvalConfig(
            project_root=self.temp_dir,
            snapshot_path=self.temp_dir / "snapshot.json",
            fixtures_dir=self.fixtures_dir,
            results_dir=self.results_dir,
        )
        self._write_real_model_summary()
        self._write_review_summary()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)

    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_real_model_summary(self) -> None:
        summary = {
            "baseline": {
                "assistant": {
                    "rows": [
                        {
                            "case_id": "q1-good",
                            "question": "目前市場最值得優先看的技能重點是什麼？",
                            "answer_mode": "market_summary",
                            "answer": _structured_answer("優先看 Python 與 LLM", "Python", "LLM"),
                            "citation_count": 2,
                            "keyword_recall": 1.0,
                            "citation_keyword_recall": 1.0,
                            "citation_ok": True,
                            "evidence_sufficient": True,
                            "structured_output": True,
                            "top_citation_type_hit": True,
                        },
                        {
                            "case_id": "q1-weak",
                            "question": "目前市場最值得優先看的技能重點是什麼？",
                            "answer_mode": "market_summary",
                            "answer": _structured_answer("先看 Python", "Python"),
                            "citation_count": 1,
                            "keyword_recall": 0.4,
                            "citation_keyword_recall": 0.4,
                            "citation_ok": False,
                            "evidence_sufficient": False,
                            "structured_output": True,
                            "top_citation_type_hit": False,
                        },
                        {
                            "case_id": "q2-good",
                            "question": "以我目前履歷來看，現在最優先要補哪些技能？",
                            "answer_mode": "personalized_guidance",
                            "answer": _structured_answer("先補 RAG 與 AWS", "RAG", "AWS"),
                            "citation_count": 2,
                            "keyword_recall": 1.0,
                            "citation_keyword_recall": 1.0,
                            "citation_ok": True,
                            "evidence_sufficient": True,
                            "structured_output": True,
                            "top_citation_type_hit": True,
                        },
                        {
                            "case_id": "q2-weak",
                            "question": "以我目前履歷來看，現在最優先要補哪些技能？",
                            "answer_mode": "personalized_guidance",
                            "answer": _structured_answer("先補 Docker", "Docker"),
                            "citation_count": 1,
                            "keyword_recall": 0.3,
                            "citation_keyword_recall": 0.3,
                            "citation_ok": False,
                            "evidence_sufficient": False,
                            "structured_output": True,
                            "top_citation_type_hit": False,
                        },
                    ]
                }
            },
            "real_snapshot": {
                "assistant": {
                    "rows": [
                        {
                            "case_id": "q1-good-dup",
                            "question": "目前市場最值得優先看的技能重點是什麼？",
                            "answer_mode": "market_summary",
                            "answer": _structured_answer("優先看 Python 與 LLM", "Python", "LLM"),
                            "citation_count": 2,
                            "citation_keyword_recall": 1.0,
                            "citation_ok": True,
                            "evidence_sufficient": True,
                            "structured_output": True,
                            "top_citation_type_hit": True,
                        },
                        {
                            "case_id": "q3-good",
                            "question": "AI 應用工程師 和 Product Manager 的差異是什麼？",
                            "answer_mode": "job_comparison",
                            "answer": _structured_answer("AI 偏技術，PM 偏協作", "AI 應用工程師", "Product Manager"),
                            "citation_count": 2,
                            "citation_keyword_recall": 1.0,
                            "citation_ok": True,
                            "evidence_sufficient": True,
                            "structured_output": True,
                            "top_citation_type_hit": True,
                        },
                        {
                            "case_id": "q3-weak",
                            "question": "AI 應用工程師 和 Product Manager 的差異是什麼？",
                            "answer_mode": "job_comparison",
                            "answer": _structured_answer("差異在職能", "職能"),
                            "citation_count": 1,
                            "citation_keyword_recall": 0.2,
                            "citation_ok": False,
                            "evidence_sufficient": False,
                            "structured_output": True,
                            "top_citation_type_hit": False,
                        },
                    ]
                }
            },
        }
        self._write_json(self.results_dir / "real_model_eval_20260419_000001" / "summary.json", summary)

    def _write_review_summary(self) -> None:
        summary = {
            "aggregate": {
                "reviewed_row_count": 2,
                "case_count": 2,
                "reviewer_count": 2,
                "correctness_score_mean": 4.5,
                "grounding_score_mean": 4.5,
                "usefulness_score_mean": 4.25,
                "clarity_score_mean": 4.0,
                "overall_score_mean": 4.5,
                "verdict_distribution": {"Accept": 1, "minor_issue": 1},
                "pairwise_verdict_agreement_rate": 0.5,
                "cohens_kappa_verdict": 0.2,
            },
            "case_rows": [
                {"case_id": "case-1", "overall_score_mean": 4.5},
                {"case_id": "case-2", "overall_score_mean": 3.5},
            ],
            "review_rows": [
                {
                    "review_id": "r1",
                    "case_id": "case-1",
                    "question": "目前市場最值得優先看的技能重點是什麼？",
                    "summary": "優先看 Python、LLM 與 RAG。",
                    "key_points": ["Python", "LLM", "RAG"],
                    "limitations": ["需要更多職缺樣本"],
                    "next_step": "補更多資料",
                    "citation_count": 3,
                    "correctness_score": 5,
                    "grounding_score": 5,
                    "usefulness_score": 4.5,
                    "clarity_score": 4.5,
                    "overall_score": 4.8,
                    "verdict": "Accept",
                    "notes": "引文完整",
                },
                {
                    "review_id": "r2",
                    "case_id": "case-2",
                    "question": "以我目前履歷來看，現在最優先要補哪些技能？",
                    "summary": "優先補 Docker。",
                    "key_points": ["Docker"],
                    "limitations": ["grounding 不足"],
                    "next_step": "補 citation",
                    "citation_count": 1,
                    "correctness_score": 3,
                    "grounding_score": 2.5,
                    "usefulness_score": 3.5,
                    "clarity_score": 3.0,
                    "overall_score": 3.0,
                    "verdict": "minor_issue",
                    "notes": "證據不足",
                },
            ],
        }
        self._write_json(self.results_dir / "formal_human_review_20260419_000001" / "summary.json", summary)

    def test_build_sft_dataset_manifest_applies_filters_and_stats(self) -> None:
        manifest = build_sft_dataset_manifest(self.config)

        self.assertEqual(manifest["unique_questions"], 3)
        self.assertEqual(manifest["gold_counts"]["human_review_gold_count"], 1)
        self.assertEqual(manifest["dedup_counts"]["dedup_removed_count"], 1)
        self.assertEqual(manifest["source_artifact_count"], 2)
        self.assertEqual(
            set(manifest["mode_counts"].keys()),
            {"market_summary", "personalized_guidance", "job_comparison"},
        )
        self.assertEqual(manifest["total_rows"], len(manifest["rows"]))

    def test_build_dpo_pairs_manifest_builds_traceable_pairs(self) -> None:
        manifest = build_dpo_pairs_manifest(self.config)

        self.assertGreaterEqual(manifest["total_pairs"], 3)
        self.assertEqual(manifest["total_pairs"], len(manifest["rows"]))
        self.assertGreater(manifest["score_gap_stats"]["avg_score_gap"], 0.0)
        self.assertGreaterEqual(manifest["source_artifact_count"], 2)
        for row in manifest["rows"]:
            self.assertTrue(row["question"])
            self.assertIn(row["answer_mode"], {"market_summary", "personalized_guidance", "job_comparison"})
            self.assertTrue(row["pair_rule"])
            self.assertNotEqual(row["chosen"], row["rejected"])

    def test_build_eval_comparison_manifest_has_stage_deltas(self) -> None:
        base_summary = {
            "aggregate": {
                "keyword_precision_mean": 0.5,
                "keyword_recall_mean": 0.5,
                "keyword_f1_mean": 0.5,
                "source_type_precision_mean": 0.5,
                "source_type_recall_mean": 0.5,
                "source_type_f1_mean": 0.5,
                "citation_min_count_accuracy": 0.5,
                "structured_output_rate": 1.0,
                "top_citation_type_hit_rate": 0.5,
                "citation_keyword_recall_mean": 0.5,
                "evidence_sufficiency_rate": 0.5,
                "total_ms_mean": 100.0,
                "total_ms_p95": 120.0,
                "case_count": 2,
            },
            "mode_breakdown": {
                "market_summary": {"keyword_f1_mean": 0.5, "case_count": 1},
            },
            "rows": [
                {
                    "case_id": "case-1",
                    "answer_mode": "market_summary",
                    "question": "q1",
                    "answer": "base",
                    "keyword_precision": 0.5,
                    "keyword_recall": 0.5,
                    "keyword_f1": 0.5,
                    "source_type_precision": 0.5,
                    "source_type_recall": 0.5,
                    "source_type_f1": 0.5,
                    "citation_min_count_accuracy": True,
                    "structured_output": True,
                    "top_citation_type_hit": True,
                    "citation_keyword_recall": 0.5,
                    "evidence_sufficient": False,
                    "total_ms": 100,
                }
            ],
        }
        sft_summary = {
            "aggregate": {**base_summary["aggregate"], "keyword_f1_mean": 0.7},
            "mode_breakdown": {"market_summary": {"keyword_f1_mean": 0.7, "case_count": 1}},
            "rows": [{**base_summary["rows"][0], "answer": "sft", "keyword_f1": 0.7}],
        }
        dpo_summary = {
            "aggregate": {**base_summary["aggregate"], "keyword_f1_mean": 0.9},
            "mode_breakdown": {"market_summary": {"keyword_f1_mean": 0.9, "case_count": 1}},
            "rows": [{**base_summary["rows"][0], "answer": "dpo", "keyword_f1": 0.9}],
        }

        manifest = build_eval_comparison_manifest(
            base_summary=base_summary,
            sft_summary=sft_summary,
            dpo_summary=dpo_summary,
            base_model="base-model",
            sft_model="sft-model",
            dpo_model="dpo-model",
            dataset_version="dataset-v1",
        )

        self.assertEqual(manifest["assistant_metrics_overall"]["dpo"]["keyword_f1_mean"], 0.9)
        self.assertEqual(manifest["assistant_case_rows"][0]["base_answer"], "base")
        self.assertEqual(manifest["assistant_case_rows"][0]["sft_answer"], "sft")
        self.assertEqual(manifest["assistant_case_rows"][0]["dpo_answer"], "dpo")
        self.assertAlmostEqual(manifest["stage_deltas"]["dpo_vs_base"]["keyword_f1_mean"], 0.4)


if __name__ == "__main__":
    unittest.main()
