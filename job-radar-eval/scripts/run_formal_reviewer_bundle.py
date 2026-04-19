#!/usr/bin/env python3
"""產生正式 reviewer bundle。"""

from __future__ import annotations

import argparse
import platform
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
EVAL_ROOT = SCRIPT_PATH.parents[1]
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from job_radar_eval.config import build_config
from job_radar_eval.experiment_artifacts import build_experiment_manifest, write_experiment_manifest
from job_radar_eval.human_review import (
    resolve_latest_human_review_packet,
    write_formal_reviewer_bundle,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="產生正式 reviewer bundle")
    parser.add_argument("--packet-summary", type=Path, default=None, help="human_review_packet 的 summary.json")
    parser.add_argument("--reviewer-ids", type=str, default="r1,r2", help="reviewer ids，逗號分隔")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    packet_summary_path = args.packet_summary.resolve() if args.packet_summary else resolve_latest_human_review_packet(config)
    reviewer_ids = [item.strip() for item in args.reviewer_ids.split(",") if item.strip()]
    run_dir, summary = write_formal_reviewer_bundle(
        config=config,
        packet_summary_path=packet_summary_path,
        reviewer_ids=reviewer_ids,
    )
    manifest = build_experiment_manifest(
        config=config,
        run_name="formal_reviewer_bundle",
        run_dir=run_dir,
        summary_path=run_dir / "summary.json",
        report_path=run_dir / "README.md",
        cli_args=vars(args),
        source_paths={"packet_summary": packet_summary_path},
        extra_artifacts=[
            {"name": "rubric", "path": "human_review_rubric.md"},
            {"name": "workflow", "path": "formal_human_review_workflow.md"},
            {"name": "reviewer_invitation_template", "path": "reviewer_invitation_template.md"},
            {"name": "readme", "path": "README.md"},
        ],
    )
    manifest["environment"] = {
        "python_version": sys.version,
        "platform": platform.platform(),
    }
    write_experiment_manifest(run_dir / "manifest.json", manifest)
    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {run_dir / 'summary.json'}")
    for item in summary["reviewer_files"]:
        print(f"[done] {item['reviewer_id']}: {item['csv_path']}")


if __name__ == "__main__":
    main()
