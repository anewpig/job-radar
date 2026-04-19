#!/usr/bin/env python3
"""執行 Job Radar 的真實快照評估。"""

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
from job_radar_eval.real_snapshot_eval import (
    build_real_snapshot_report,
    build_snapshot_health,
    evaluate_real_assistant,
    evaluate_real_resume,
    evaluate_real_retrieval,
)
from job_radar_eval.reporting import build_run_dir, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="執行 Job Radar 真實快照評估")
    parser.add_argument("--iterations", type=int, default=3, help="每個測例重跑次數")
    parser.add_argument(
        "--snapshot-path",
        type=Path,
        default=None,
        help="指定要評估的 jobs_latest.json 路徑",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    ensure_project_importable(config.project_root)
    snapshot_path = args.snapshot_path.resolve() if args.snapshot_path else config.snapshot_path
    run_dir = build_run_dir(config.results_dir, prefix="real_snapshot")
    run_cache_dir = run_dir / ".cache"

    snapshot_health = build_snapshot_health(config, snapshot_path=snapshot_path)
    assistant_results = evaluate_real_assistant(
        config,
        iterations=args.iterations,
        cache_dir=run_cache_dir / "assistant",
        snapshot_path=snapshot_path,
    )
    resume_results = evaluate_real_resume(
        config,
        iterations=args.iterations,
        cache_dir=run_cache_dir / "resume",
        snapshot_path=snapshot_path,
    )
    retrieval_results = evaluate_real_retrieval(
        config,
        iterations=args.iterations,
        cache_dir=run_cache_dir / "retrieval",
        snapshot_path=snapshot_path,
    )

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "real_snapshot_eval",
        "iterations": args.iterations,
        "project_root": str(config.project_root),
        "snapshot_path": str(snapshot_path),
        "python_version": sys.version,
        "platform": platform.platform(),
        "snapshot_health": snapshot_health,
        "assistant": assistant_results,
        "resume": resume_results,
        "retrieval": retrieval_results,
    }

    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    write_json(summary_path, summary)
    case_exports = write_case_exports(
        run_dir=run_dir,
        case_sections={
            "assistant": assistant_results["rows"],
            "resume": resume_results["rows"],
            "retrieval": retrieval_results["rows"],
        },
    )
    report_path.write_text(build_real_snapshot_report(summary), encoding="utf-8")
    manifest = build_experiment_manifest(
        config=config,
        run_name="real_snapshot_eval",
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args=vars(args),
        snapshot_path=snapshot_path,
        case_exports=case_exports,
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)

    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] report:  {report_path}")


if __name__ == "__main__":
    main()
