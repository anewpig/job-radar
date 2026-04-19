#!/usr/bin/env python3
"""執行 Job Radar 的 training-readiness gate。"""

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
from job_radar_eval.reporting import build_run_dir, write_json
from job_radar_eval.training_readiness import (
    build_training_readiness,
    build_training_readiness_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="執行 Job Radar training-readiness gate")
    parser.add_argument("--ai-checks-summary", type=Path, default=None, help="ai_checks summary.json，可作為 snapshot health gate 基準")
    parser.add_argument("--assistant-summary", type=Path, required=True, help="assistant real-model eval summary.json")
    parser.add_argument("--retrieval-summary", type=Path, required=True, help="retrieval real-model eval summary.json")
    parser.add_argument("--resume-summary", type=Path, required=True, help="resume real-model eval summary.json")
    parser.add_argument("--resume-label-summary", type=Path, required=True, help="resume_label_eval summary.json")
    parser.add_argument("--human-review-summary", type=Path, default=None, help="formal_human_review 或 human_review_analysis summary.json")
    parser.add_argument("--fixtures-root", type=Path, default=None, help="fixtures 目錄，預設使用 job-radar-eval/fixtures")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    fixtures_root = args.fixtures_root.resolve() if args.fixtures_root else config.fixtures_dir
    run_dir = build_run_dir(config.results_dir, prefix="training_readiness")

    summary = build_training_readiness(
        ai_checks_summary_path=args.ai_checks_summary.resolve() if args.ai_checks_summary else None,
        assistant_summary_path=args.assistant_summary.resolve(),
        retrieval_summary_path=args.retrieval_summary.resolve(),
        resume_summary_path=args.resume_summary.resolve(),
        resume_label_summary_path=args.resume_label_summary.resolve(),
        human_review_summary_path=args.human_review_summary.resolve() if args.human_review_summary else None,
        fixtures_root=fixtures_root,
    )
    summary.update(
        {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "project_root": str(config.project_root),
            "fixtures_root": str(fixtures_root),
            "python_version": sys.version,
            "platform": platform.platform(),
        }
    )

    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    write_json(summary_path, summary)
    report_path.write_text(build_training_readiness_report(summary), encoding="utf-8")
    manifest = build_experiment_manifest(
        config=config,
        run_name="training_readiness",
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args=vars(args),
        source_paths={
            "ai_checks_summary": args.ai_checks_summary,
            "assistant_summary": args.assistant_summary,
            "retrieval_summary": args.retrieval_summary,
            "resume_summary": args.resume_summary,
            "resume_label_summary": args.resume_label_summary,
            "human_review_summary": args.human_review_summary,
        },
        fixtures_root=fixtures_root,
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)

    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] report:  {report_path}")


if __name__ == "__main__":
    main()
