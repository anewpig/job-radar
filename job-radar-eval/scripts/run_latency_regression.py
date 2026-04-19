#!/usr/bin/env python3
"""執行 Job Radar latency-regression gate。"""

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

from job_radar_eval.config import build_config
from job_radar_eval.experiment_artifacts import build_experiment_manifest, write_experiment_manifest
from job_radar_eval.latency_regression import (
    build_latency_regression,
    build_latency_regression_report,
)
from job_radar_eval.reporting import build_run_dir, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="執行 Job Radar latency-regression gate")
    parser.add_argument("--assistant-summary", type=Path, required=True, help="assistant summary.json")
    parser.add_argument("--retrieval-summary", type=Path, required=True, help="retrieval summary.json")
    parser.add_argument("--resume-summary", type=Path, required=True, help="resume summary.json")
    parser.add_argument("--resume-warm-summary", type=Path, default=None, help="resume warm summary.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    run_dir = build_run_dir(config.results_dir, prefix="latency_regression")

    summary = build_latency_regression(
        assistant_summary_path=args.assistant_summary.resolve(),
        retrieval_summary_path=args.retrieval_summary.resolve(),
        resume_summary_path=args.resume_summary.resolve(),
        resume_warm_summary_path=args.resume_warm_summary.resolve() if args.resume_warm_summary else None,
    )
    summary.update(
        {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project_root": str(config.project_root),
            "python_version": sys.version,
            "platform": platform.platform(),
        }
    )

    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    write_json(summary_path, summary)
    report_path.write_text(build_latency_regression_report(summary), encoding="utf-8")
    manifest = build_experiment_manifest(
        config=config,
        run_name="latency_regression",
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args=vars(args),
        source_paths={
            "assistant_summary": args.assistant_summary,
            "retrieval_summary": args.retrieval_summary,
            "resume_summary": args.resume_summary,
            "resume_warm_summary": args.resume_warm_summary,
        },
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)

    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] report:  {report_path}")


if __name__ == "__main__":
    main()
