#!/usr/bin/env python3
"""執行 Job Radar 的整合 AI regression bundle。"""

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

from job_radar_eval.ai_regression import (
    build_ai_regression_bundle,
    resolve_regression_sources,
    write_ai_regression_bundle,
)
from job_radar_eval.config import build_config
from job_radar_eval.experiment_artifacts import build_experiment_manifest, write_experiment_manifest
from job_radar_eval.reporting import build_run_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="執行 Job Radar AI regression bundle")
    parser.add_argument("--ai-checks-summary", type=Path, default=None, help="指定 ai_checks summary.json")
    parser.add_argument("--assistant-summary", type=Path, default=None, help="指定 assistant real-model summary.json")
    parser.add_argument("--retrieval-summary", type=Path, default=None, help="指定 retrieval real-model summary.json")
    parser.add_argument("--resume-summary", type=Path, default=None, help="指定 resume real-model summary.json")
    parser.add_argument("--resume-label-summary", type=Path, default=None, help="指定 resume_label_eval summary.json")
    parser.add_argument("--resume-warm-summary", type=Path, default=None, help="指定 resume_warm_probe summary.json")
    parser.add_argument("--human-review-summary", type=Path, default=None, help="指定 formal_human_review 或 human_review_analysis summary.json")
    parser.add_argument("--fixtures-root", type=Path, default=None, help="fixtures 目錄，預設使用 job-radar-eval/fixtures")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    run_dir = build_run_dir(config.results_dir, prefix="ai_regression")
    sources = resolve_regression_sources(
        config=config,
        ai_checks_summary_path=args.ai_checks_summary,
        assistant_summary_path=args.assistant_summary,
        retrieval_summary_path=args.retrieval_summary,
        resume_summary_path=args.resume_summary,
        resume_label_summary_path=args.resume_label_summary,
        resume_warm_summary_path=args.resume_warm_summary,
        human_review_summary_path=args.human_review_summary,
    )
    summary = build_ai_regression_bundle(
        config=config,
        sources=sources,
        fixtures_root=args.fixtures_root,
    )
    summary.update(
        {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "python_version": sys.version,
            "platform": platform.platform(),
        }
    )
    write_ai_regression_bundle(run_dir=run_dir, summary=summary)
    manifest = build_experiment_manifest(
        config=config,
        run_name="ai_regression",
        run_dir=run_dir,
        summary_path=run_dir / "summary.json",
        report_path=run_dir / "report.md",
        cli_args=vars(args),
        source_paths=sources,
        fixtures_root=args.fixtures_root.resolve() if args.fixtures_root else config.fixtures_dir,
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)
    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {run_dir / 'summary.json'}")
    print(f"[done] report:  {run_dir / 'report.md'}")


if __name__ == "__main__":
    main()
