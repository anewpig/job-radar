"""Tests for fine-tuning dashboard data loading."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.ui.pages_fine_tuning_data import load_post_training_dashboard_data  # noqa: E402


class FineTuningDashboardDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="fine-tuning-data-"))
        self.results_dir = self.temp_dir / "job-radar-eval" / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)

    def _write_json(self, path: Path, payload: dict) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path.resolve())

    def test_loader_reads_local_manifests_and_trackio_env(self) -> None:
        self._write_json(
            self.results_dir / "posttrain_sft_dataset_20260419_000001" / "summary.json",
            {
                "dataset_version": "sft-v1",
                "generated_at": "2026-04-19T10:00:00",
                "total_rows": 12,
                "rows": [{"id": "1"}],
            },
        )
        self._write_json(
            self.results_dir / "posttrain_dpo_pairs_20260419_000001" / "summary.json",
            {
                "dataset_version": "dpo-v1",
                "generated_at": "2026-04-19T10:05:00",
                "total_pairs": 6,
                "rows": [{"id": "p1"}],
            },
        )
        self._write_json(
            self.results_dir / "posttrain_eval_comparison_20260419_000001" / "summary.json",
            {
                "generated_at": "2026-04-19T10:10:00",
                "base_model": "base",
                "sft_model": "sft",
                "dpo_model": "dpo",
                "assistant_metrics_overall": {"dpo": {"keyword_f1_mean": 0.9}},
                "assistant_case_rows": [{"case_id": "case-1"}],
                "sample_size": 1,
            },
        )
        self._write_json(
            self.results_dir / "posttrain_review_manifest_20260419_000001" / "summary.json",
            {
                "generated_at": "2026-04-19T10:15:00",
                "aggregate": {"reviewed_row_count": 3},
                "review_rows": [{"review_id": "r1"}],
            },
        )
        trackio_path = self._write_json(
            self.temp_dir / "trackio_sft.json",
            {
                "updated_at": "2026-04-19T10:20:00",
                "metrics": {
                    "train_loss": [
                        {"step": 1, "value": 1.5, "timestamp": "2026-04-19T10:16:00"},
                        {"step": 2, "value": 1.2, "timestamp": "2026-04-19T10:17:00"},
                    ]
                },
            },
        )

        dashboard = load_post_training_dashboard_data(
            project_root=self.temp_dir,
            env={
                "JOB_RADAR_POSTTRAIN_TRACKIO_SFT_URL": trackio_path,
                "JOB_RADAR_POSTTRAIN_TRACKIO_PROJECT": "demo-project",
                "JOB_RADAR_POSTTRAIN_TRACKIO_SFT_RUN_ID": "run-sft-1",
            },
        )

        self.assertTrue(dashboard["has_any_data"])
        self.assertEqual(dashboard["sft_manifest"]["payload"]["dataset_version"], "sft-v1")
        self.assertEqual(dashboard["artifact_registry"]["dataset_version"], "dpo-v1")
        self.assertEqual(len(dashboard["trackio_sft"]["rows"]), 2)
        self.assertEqual(dashboard["trackio_sft"]["project"], "demo-project")

    def test_loader_keeps_previous_success_on_failed_refresh(self) -> None:
        valid_path = self._write_json(
            self.temp_dir / "sft.json",
            {
                "dataset_version": "sft-v2",
                "generated_at": "2026-04-19T12:00:00",
                "total_rows": 4,
                "rows": [{"id": "1"}],
            },
        )
        previous = load_post_training_dashboard_data(
            project_root=self.temp_dir,
            env={"JOB_RADAR_POSTTRAIN_SFT_MANIFEST_URL": valid_path},
        )

        refreshed = load_post_training_dashboard_data(
            project_root=self.temp_dir,
            env={"JOB_RADAR_POSTTRAIN_SFT_MANIFEST_URL": str(self.temp_dir / "missing.json")},
            previous_data=previous,
        )

        self.assertEqual(refreshed["sft_manifest"]["payload"]["dataset_version"], "sft-v2")
        self.assertTrue(refreshed["sft_manifest"]["stale"])
        self.assertTrue(any("sft_manifest" in warning for warning in refreshed["warnings"]))


if __name__ == "__main__":
    unittest.main()
