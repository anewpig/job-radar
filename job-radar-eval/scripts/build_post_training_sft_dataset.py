#!/usr/bin/env python3
"""建立 post-training SFT dataset 與 manifest。"""

from __future__ import annotations

import json
from pathlib import Path
import sys

SCRIPT_PATH = Path(__file__).resolve()
EVAL_ROOT = SCRIPT_PATH.parents[1]
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from job_radar_eval.config import build_config
from job_radar_eval.experiment_artifacts import build_experiment_manifest, write_experiment_manifest, write_jsonl
from job_radar_eval.post_training import SFT_RUN_PREFIX, build_sft_dataset_manifest
from job_radar_eval.reporting import build_run_dir, write_csv, write_json


def _csv_rows(rows: list[dict]) -> list[dict]:
    return [
        {
            **{key: value for key, value in row.items() if key != "messages"},
            "messages_json": json.dumps(row.get("messages", []), ensure_ascii=False),
        }
        for row in rows
    ]


def _build_report(summary: dict) -> str:
    return f"""# SFT Dataset Manifest

- Dataset version: `{summary.get('dataset_version', '')}`
- Generated at: `{summary.get('generated_at', '')}`
- Total rows: `{summary.get('total_rows', 0)}`
- Unique questions: `{summary.get('unique_questions', 0)}`
- Source artifacts: `{summary.get('source_artifact_count', 0)}`
- Human review gold rows: `{summary.get('gold_counts', {}).get('human_review_gold_count', 0)}`
- Dedup removed: `{summary.get('dedup_counts', {}).get('dedup_removed_count', 0)}`
- Mode-balanced dropped: `{summary.get('dedup_counts', {}).get('mode_balance_dropped_count', 0)}`
"""


def main() -> None:
    config = build_config()
    run_dir = build_run_dir(config.results_dir, prefix=SFT_RUN_PREFIX)
    summary = build_sft_dataset_manifest(config)

    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    rows_jsonl_path = run_dir / "sft_rows.jsonl"
    rows_csv_path = run_dir / "sft_rows.csv"

    write_json(summary_path, summary)
    write_jsonl(rows_jsonl_path, summary.get("rows", []))
    write_csv(rows_csv_path, _csv_rows(summary.get("rows", [])))
    report_path.write_text(_build_report(summary), encoding="utf-8")

    manifest = build_experiment_manifest(
        config=config,
        run_name=SFT_RUN_PREFIX,
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        extra_artifacts=[
            {"name": "sft_rows_jsonl", "path": str(rows_jsonl_path.resolve()), "row_count": len(summary.get("rows", []))},
            {"name": "sft_rows_csv", "path": str(rows_csv_path.resolve()), "row_count": len(summary.get("rows", []))},
        ],
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)

    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] rows:    {rows_jsonl_path}")


if __name__ == "__main__":
    main()
