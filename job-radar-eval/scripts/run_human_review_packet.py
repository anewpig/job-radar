#!/usr/bin/env python3
"""產生 assistant 人工評分 packet。"""

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
    _load_rows,
    resolve_latest_assistant_cases,
    write_assistant_review_packet,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="產生 assistant 人工評分 packet")
    parser.add_argument("--input", type=Path, default=None, help="assistant_cases.csv 或 assistant_cases.jsonl")
    parser.add_argument("--limit", type=int, default=12, help="人工評分 packet 筆數")
    parser.add_argument(
        "--case-ids",
        type=str,
        default="",
        help="只抽指定 case_id，逗號分隔。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    source_path = args.input.resolve() if args.input else resolve_latest_assistant_cases(config)
    rows = _load_rows(source_path)
    case_ids = [item.strip() for item in args.case_ids.split(",") if item.strip()]
    run_dir, summary = write_assistant_review_packet(
        config=config,
        source_path=source_path,
        rows=rows,
        limit=args.limit,
        case_ids=case_ids,
    )
    manifest = build_experiment_manifest(
        config=config,
        run_name="human_review_packet",
        run_dir=run_dir,
        summary_path=run_dir / "summary.json",
        report_path=run_dir / "summary.json",
        cli_args=vars(args),
        source_paths={"assistant_cases": source_path},
        case_exports=[
            {
                "section": "assistant_review_packet_blind",
                "row_count": summary["packet_size"],
                "csv_path": "assistant_review_packet_blind.csv",
                "jsonl_path": "assistant_review_packet_blind.jsonl",
            },
            {
                "section": "assistant_review_packet_research",
                "row_count": summary["packet_size"],
                "csv_path": "assistant_review_packet_research.csv",
                "jsonl_path": "assistant_review_packet_research.jsonl",
            }
        ],
    )
    manifest["environment"] = {
        "python_version": sys.version,
        "platform": platform.platform(),
    }
    write_experiment_manifest(run_dir / "manifest.json", manifest)
    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {run_dir / 'summary.json'}")
    print(f"[done] blind csv:     {run_dir / 'assistant_review_packet_blind.csv'}")
    print(f"[done] blind jsonl:   {run_dir / 'assistant_review_packet_blind.jsonl'}")
    print(f"[done] research csv:  {run_dir / 'assistant_review_packet_research.csv'}")
    print(f"[done] research jsonl:{run_dir / 'assistant_review_packet_research.jsonl'}")


if __name__ == "__main__":
    main()
