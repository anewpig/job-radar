#!/usr/bin/env python3
"""驗證 human review CSV。"""

from __future__ import annotations

import argparse
import platform
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
EVAL_ROOT = SCRIPT_PATH.parents[1]
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from job_radar_eval.config import build_config
from job_radar_eval.experiment_artifacts import build_experiment_manifest, write_experiment_manifest
from job_radar_eval.human_review_validation import validate_human_review_csv
from job_radar_eval.reporting import build_run_dir, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="驗證 human review CSV")
    parser.add_argument("inputs", nargs="+", type=Path, help="一個或多個 reviewer CSV")
    parser.add_argument(
        "--require-completed",
        action="store_true",
        help="要求 reviewer submission 已完整填寫評分欄位。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    input_paths = [path.resolve() for path in args.inputs]
    validations = [
        validate_human_review_csv(path, require_completed=args.require_completed)
        for path in input_paths
    ]
    status = "PASS"
    if any(item["status"] == "FAIL" for item in validations):
        status = "FAIL"
    elif any(item["status"] == "WARN" for item in validations):
        status = "WARN"

    run_dir = build_run_dir(config.results_dir, prefix="human_review_validation")
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "human_review_validation",
        "project_root": str(config.project_root),
        "python_version": sys.version,
        "platform": platform.platform(),
        "status": status,
        "require_completed": args.require_completed,
        "validations": validations,
    }
    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    write_json(summary_path, summary)
    report_lines = ["# Human Review Validation", "", f"- Status: `{status}`", ""]
    for item in validations:
        report_lines.extend(
            [
                f"## {item['path']}",
                f"- Status: `{item['status']}`",
                f"- Rows: `{item['row_count']}`",
                f"- Reviewer IDs: `{', '.join(item['reviewer_ids']) if item['reviewer_ids'] else '-'}`",
            ]
        )
        if item["issues"]:
            report_lines.append("- Issues:")
            for issue in item["issues"]:
                row_text = f" row={issue['row_index']}" if issue["row_index"] else ""
                report_lines.append(f"  - [{issue['severity']}] {issue['code']}{row_text}: {issue['message']}")
        else:
            report_lines.append("- Issues: none")
        report_lines.append("")
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    manifest = build_experiment_manifest(
        config=config,
        run_name="human_review_validation",
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args={"inputs": input_paths, "require_completed": args.require_completed},
        source_paths={f"input_{index+1}": path for index, path in enumerate(input_paths)},
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)
    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] report:  {report_path}")


if __name__ == "__main__":
    main()
