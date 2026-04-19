#!/usr/bin/env python3
"""執行 resume_match_labels 排序評估。"""

from __future__ import annotations

import argparse
from datetime import datetime
import platform
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
EVAL_ROOT = SCRIPT_PATH.parents[1]
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from job_radar_eval.config import build_config, ensure_project_importable
from job_radar_eval.experiment_artifacts import (
    build_experiment_manifest,
    write_case_exports,
    write_experiment_manifest,
)
from job_radar_eval.reporting import build_resume_label_report, build_run_dir, write_json
from job_radar_eval.resume_label_eval import evaluate_resume_labels


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="執行 Job Radar resume_match_labels 排序評估")
    parser.add_argument("--iterations", type=int, default=3, help="每個測例重跑次數")
    parser.add_argument("--case-limit", type=int, default=None, help="只跑前 N 個 resume_id")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    ensure_project_importable(config.project_root)
    run_dir = build_run_dir(config.results_dir, prefix="resume_label_eval")
    run_cache_dir = run_dir / ".cache"

    resume_label_results = evaluate_resume_labels(
        config,
        iterations=args.iterations,
        cache_dir=run_cache_dir / "resume_labels",
        case_limit=args.case_limit,
    )
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "iterations": args.iterations,
        "project_root": str(config.project_root),
        "python_version": sys.version,
        "platform": platform.platform(),
        "resume_label": resume_label_results,
    }

    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    write_json(summary_path, summary)
    case_exports = write_case_exports(
        run_dir=run_dir,
        case_sections={"resume_label": resume_label_results["rows"]},
    )
    report_path.write_text(build_resume_label_report(summary), encoding="utf-8")
    manifest = build_experiment_manifest(
        config=config,
        run_name="resume_label_eval",
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args=vars(args),
        case_exports=case_exports,
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)

    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] report:  {report_path}")


if __name__ == "__main__":
    main()
