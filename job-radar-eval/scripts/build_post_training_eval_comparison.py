#!/usr/bin/env python3
"""建立 post-training Base / SFT / DPO evaluation comparison manifest。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_PATH = Path(__file__).resolve()
EVAL_ROOT = SCRIPT_PATH.parents[1]
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from job_radar_eval.config import build_config
from job_radar_eval.experiment_artifacts import build_experiment_manifest, write_experiment_manifest, write_jsonl
from job_radar_eval.post_training import EVAL_RUN_PREFIX, build_eval_comparison_manifest
from job_radar_eval.reporting import build_run_dir, write_csv, write_json


def _load_assistant_summary(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "assistant" in payload:
        return payload["assistant"]
    for section_name in ("baseline", "real_snapshot"):
        section = payload.get(section_name)
        if isinstance(section, dict) and "assistant" in section:
            return section["assistant"]
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="建立 post-training evaluation comparison manifest")
    parser.add_argument("--base-summary", type=Path, required=True, help="Base assistant eval summary.json")
    parser.add_argument("--sft-summary", type=Path, required=True, help="SFT assistant eval summary.json")
    parser.add_argument("--dpo-summary", type=Path, required=True, help="DPO assistant eval summary.json")
    parser.add_argument("--base-model", type=str, required=True, help="Base model id")
    parser.add_argument("--sft-model", type=str, required=True, help="SFT model id")
    parser.add_argument("--dpo-model", type=str, required=True, help="DPO model id")
    parser.add_argument("--dataset-version", type=str, required=True, help="Dataset version")
    return parser.parse_args()


def _build_report(summary: dict) -> str:
    overall = summary.get("assistant_metrics_overall", {})
    return f"""# Post-Training Eval Comparison

- Generated at: `{summary.get('generated_at', '')}`
- Dataset version: `{summary.get('dataset_version', '')}`
- Base model: `{summary.get('base_model', '')}`
- SFT model: `{summary.get('sft_model', '')}`
- DPO model: `{summary.get('dpo_model', '')}`
- Cases: `{summary.get('sample_size', 0)}`
- DPO keyword F1: `{overall.get('dpo', {}).get('keyword_f1_mean', 0.0)}`
- DPO evidence sufficiency: `{overall.get('dpo', {}).get('evidence_sufficiency_rate', 0.0)}`
"""


def main() -> None:
    args = parse_args()
    config = build_config()
    run_dir = build_run_dir(config.results_dir, prefix=EVAL_RUN_PREFIX)

    summary = build_eval_comparison_manifest(
        base_summary=_load_assistant_summary(args.base_summary.resolve()),
        sft_summary=_load_assistant_summary(args.sft_summary.resolve()),
        dpo_summary=_load_assistant_summary(args.dpo_summary.resolve()),
        base_model=args.base_model,
        sft_model=args.sft_model,
        dpo_model=args.dpo_model,
        dataset_version=args.dataset_version,
    )

    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    case_rows_jsonl_path = run_dir / "assistant_case_rows.jsonl"
    case_rows_csv_path = run_dir / "assistant_case_rows.csv"

    write_json(summary_path, summary)
    write_jsonl(case_rows_jsonl_path, summary.get("assistant_case_rows", []))
    write_csv(case_rows_csv_path, summary.get("assistant_case_rows", []))
    report_path.write_text(_build_report(summary), encoding="utf-8")

    manifest = build_experiment_manifest(
        config=config,
        run_name=EVAL_RUN_PREFIX,
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args={key: str(value) for key, value in vars(args).items()},
        extra_artifacts=[
            {
                "name": "assistant_case_rows_jsonl",
                "path": str(case_rows_jsonl_path.resolve()),
                "row_count": len(summary.get("assistant_case_rows", [])),
            },
            {
                "name": "assistant_case_rows_csv",
                "path": str(case_rows_csv_path.resolve()),
                "row_count": len(summary.get("assistant_case_rows", [])),
            },
        ],
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)

    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] rows:    {case_rows_jsonl_path}")


if __name__ == "__main__":
    main()
