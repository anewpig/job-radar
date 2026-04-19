#!/usr/bin/env python3
"""彙整人工評分結果。"""

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
from job_radar_eval.experiment_artifacts import (
    build_experiment_manifest,
    write_case_exports,
    write_experiment_manifest,
)
from job_radar_eval.human_review_analysis import (
    build_human_review_latex_tables,
    build_human_review_tables,
    build_human_review_report,
    load_review_rows,
    summarize_human_reviews,
)
from job_radar_eval.reporting import build_run_dir, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="彙整 assistant 人工評分結果")
    parser.add_argument("inputs", nargs="+", type=Path, help="一個或多個 reviewer CSV")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    input_paths = [path.resolve() for path in args.inputs]
    rows = load_review_rows(input_paths)
    summary_payload = summarize_human_reviews(rows)

    run_dir = build_run_dir(config.results_dir, prefix="human_review_analysis")
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "human_review_analysis",
        "project_root": str(config.project_root),
        "python_version": sys.version,
        "platform": platform.platform(),
        "input_paths": [str(path) for path in input_paths],
        **summary_payload,
    }
    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    thesis_tables_path = run_dir / "thesis_tables.md"
    thesis_latex_path = run_dir / "thesis_tables.tex"
    write_json(summary_path, summary)
    case_exports = write_case_exports(
        run_dir=run_dir,
        case_sections={
            "human_review_rows": summary_payload["review_rows"],
            "human_review_case_summary": summary_payload["case_rows"],
            "human_review_reviewer_summary": summary_payload["reviewer_rows"],
        },
    )
    report_path.write_text(build_human_review_report(summary), encoding="utf-8")
    thesis_tables_path.write_text(build_human_review_tables(summary), encoding="utf-8")
    thesis_latex_path.write_text(build_human_review_latex_tables(summary), encoding="utf-8")
    manifest = build_experiment_manifest(
        config=config,
        run_name="human_review_analysis",
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args={"inputs": input_paths},
        source_paths={f"input_{index+1}": path for index, path in enumerate(input_paths)},
        case_exports=case_exports,
        extra_artifacts=[
            {
                "name": "thesis_tables",
                "path": str(thesis_tables_path.resolve()),
                "format": "markdown",
            },
            {
                "name": "thesis_tables_latex",
                "path": str(thesis_latex_path.resolve()),
                "format": "latex",
            },
        ],
    )
    write_experiment_manifest(run_dir / "manifest.json", manifest)
    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] report:  {report_path}")
    print(f"[done] thesis tables: {thesis_tables_path}")
    print(f"[done] thesis latex: {thesis_latex_path}")


if __name__ == "__main__":
    main()
