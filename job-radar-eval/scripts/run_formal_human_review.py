#!/usr/bin/env python3
"""正式 human review：先驗證，再彙整。"""

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
from job_radar_eval.human_review_analysis import (
    build_human_review_latex_tables,
    build_human_review_report,
    build_human_review_tables,
    load_review_rows,
    summarize_human_reviews,
)
from job_radar_eval.human_review_validation import validate_human_review_csv
from job_radar_eval.reporting import build_run_dir, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="正式 human review：先驗證 reviewer CSV，再產出 aggregation")
    parser.add_argument("inputs", nargs="+", type=Path, help="一個或多個 reviewer CSV")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    input_paths = [path.resolve() for path in args.inputs]

    validations = [
        validate_human_review_csv(path, require_completed=True)
        for path in input_paths
    ]
    if any(item["status"] != "PASS" for item in validations):
        raise SystemExit("reviewer CSV validation failed; fix the files before running formal human review.")

    rows = load_review_rows(input_paths)
    summary_payload = summarize_human_reviews(rows)

    run_dir = build_run_dir(config.results_dir, prefix="formal_human_review")
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "formal_human_review",
        "project_root": str(config.project_root),
        "python_version": sys.version,
        "platform": platform.platform(),
        "input_paths": [str(path) for path in input_paths],
        "validation": {
            "status": "PASS",
            "validations": validations,
        },
        **summary_payload,
    }

    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    thesis_tables_path = run_dir / "thesis_tables.md"
    thesis_latex_path = run_dir / "thesis_tables.tex"
    validation_report_path = run_dir / "validation_report.md"

    write_json(summary_path, summary)
    report_path.write_text(build_human_review_report(summary), encoding="utf-8")
    thesis_tables_path.write_text(build_human_review_tables(summary), encoding="utf-8")
    thesis_latex_path.write_text(build_human_review_latex_tables(summary), encoding="utf-8")

    validation_lines = ["# Human Review Validation", "", "- Status: `PASS`", ""]
    for item in validations:
        validation_lines.extend(
            [
                f"## {item['path']}",
                f"- Rows: `{item['row_count']}`",
                f"- Reviewer IDs: `{', '.join(item['reviewer_ids'])}`",
                "- Issues: none",
                "",
            ]
        )
    validation_report_path.write_text("\n".join(validation_lines), encoding="utf-8")

    manifest = build_experiment_manifest(
        config=config,
        run_name="formal_human_review",
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args={"inputs": input_paths},
        source_paths={f"input_{index+1}": path for index, path in enumerate(input_paths)},
        extra_artifacts=[
            {"name": "validation_report", "path": str(validation_report_path.resolve()), "format": "markdown"},
            {"name": "thesis_tables", "path": str(thesis_tables_path.resolve()), "format": "markdown"},
            {"name": "thesis_tables_latex", "path": str(thesis_latex_path.resolve()), "format": "latex"},
        ],
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)

    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] report:  {report_path}")
    print(f"[done] validation report: {validation_report_path}")
    print(f"[done] thesis tables: {thesis_tables_path}")
    print(f"[done] thesis latex: {thesis_latex_path}")


if __name__ == "__main__":
    main()
