"""Tests for Colab post-training helpers."""

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

from job_radar_eval.post_training_colab import (  # noqa: E402
    build_default_repo_ids,
    build_page_env_suggestions,
    normalize_dpo_rows,
    normalize_sft_rows,
    resolve_training_inputs,
)


class PostTrainingColabHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="posttrain-colab-"))
        self.results_dir = self.temp_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)

    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
            encoding="utf-8",
        )

    def test_build_default_repo_ids_and_page_env(self) -> None:
        repo_ids = build_default_repo_ids("alice", "Qwen/Qwen3-4B-Instruct-2507")
        env = build_page_env_suggestions(
            repo_ids,
            base_model="Qwen/Qwen3-4B-Instruct-2507",
            trackio_project="job-radar-posttrain",
            latest_sft_run_id="sft-run",
            latest_dpo_run_id="dpo-run",
        )

        self.assertEqual(repo_ids.sft_adapter_repo, "alice/job-radar-qwen3-4b-posttrain-sft-adapter")
        self.assertEqual(repo_ids.dpo_model_repo, "alice/job-radar-qwen3-4b-posttrain-dpo")
        self.assertIn("datasets/sft/latest/summary.json", env["JOB_RADAR_POSTTRAIN_SFT_MANIFEST_URL"])
        self.assertIn("eval/latest/summary.json", env["JOB_RADAR_POSTTRAIN_EVAL_MANIFEST_URL"])
        self.assertIn("review/latest/summary.json", env["JOB_RADAR_POSTTRAIN_REVIEW_MANIFEST_URL"])
        self.assertIn("training/dpo/latest/trackio_metrics.json", env["JOB_RADAR_POSTTRAIN_TRACKIO_DPO_URL"])
        self.assertEqual(env["JOB_RADAR_POSTTRAIN_BASE_MODEL"], "Qwen/Qwen3-4B-Instruct-2507")
        self.assertEqual(env["JOB_RADAR_POSTTRAIN_TRACKIO_PROJECT"], "job-radar-posttrain")
        self.assertEqual(env["JOB_RADAR_POSTTRAIN_TRACKIO_SFT_RUN_ID"], "sft-run")
        self.assertEqual(env["JOB_RADAR_POSTTRAIN_TRACKIO_DPO_RUN_ID"], "dpo-run")

    def test_normalize_sft_rows_keeps_messages(self) -> None:
        rows = normalize_sft_rows(
            [
                {
                    "id": "row-1",
                    "question": "q1",
                    "answer_mode": "market_summary",
                    "messages": [
                        {"role": "system", "content": "sys"},
                        {"role": "user", "content": "user"},
                        {"role": "assistant", "content": "assistant"},
                    ],
                    "split": "train",
                }
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["messages"][2]["role"], "assistant")
        self.assertEqual(rows[0]["split"], "train")

    def test_normalize_dpo_rows_creates_conversational_prompt(self) -> None:
        rows = normalize_dpo_rows(
            [
                {
                    "id": "pair-1",
                    "question": "哪個技能最重要？",
                    "answer_mode": "market_summary",
                    "prompt": json.dumps({"answer_mode": "market_summary", "question": "哪個技能最重要？"}, ensure_ascii=False),
                    "chosen": "{\"summary\": \"Python 最重要\"}",
                    "rejected": "{\"summary\": \"Docker 最重要\"}",
                    "split": "val",
                    "pair_rule": "quality_gap",
                }
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["prompt"][0]["role"], "system")
        self.assertEqual(rows[0]["prompt"][1]["role"], "user")
        self.assertEqual(rows[0]["chosen"][0]["role"], "assistant")
        self.assertEqual(rows[0]["split"], "val")

    def test_resolve_training_inputs_reads_latest_artifacts(self) -> None:
        sft_dir = self.results_dir / "posttrain_sft_dataset_20260419_000001"
        dpo_dir = self.results_dir / "posttrain_dpo_pairs_20260419_000001"
        self._write_json(sft_dir / "summary.json", {"dataset_version": "sft-v1"})
        self._write_jsonl(sft_dir / "sft_rows.jsonl", [{"id": "1"}])
        self._write_json(dpo_dir / "summary.json", {"dataset_version": "dpo-v1"})
        self._write_jsonl(dpo_dir / "dpo_pairs.jsonl", [{"id": "1"}])

        bundle = resolve_training_inputs(results_dir=self.results_dir)

        self.assertEqual(bundle.sft_dataset_version, "sft-v1")
        self.assertEqual(bundle.dpo_dataset_version, "dpo-v1")
        self.assertEqual(bundle.sft_rows_path.name, "sft_rows.jsonl")
        self.assertEqual(bundle.dpo_rows_path.name, "dpo_pairs.jsonl")


if __name__ == "__main__":
    unittest.main()
