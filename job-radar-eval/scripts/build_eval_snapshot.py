#!/usr/bin/env python3
"""Build a composite evaluation snapshot for comparison-mode checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
EVAL_ROOT = SCRIPT_PATH.parents[1]
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from job_radar_eval.config import build_config, ensure_project_importable
from job_radar_eval.eval_snapshot_builder import build_composite_eval_snapshot
from job_radar_eval.reporting import build_run_dir, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="建立 comparison-ready 的 eval snapshot")
    parser.add_argument(
        "--snapshot-path",
        action="append",
        dest="snapshot_paths",
        default=[],
        help="可重複指定多個 snapshot path；若未指定，預設只用目前的 jobs_latest.json。",
    )
    parser.add_argument("--top-roles", type=int, default=3, help="保留前幾個角色")
    parser.add_argument("--per-role-limit", type=int, default=15, help="每個角色最多保留幾筆職缺")
    parser.add_argument("--min-roles", type=int, default=2, help="至少需要幾個角色才算 comparison-ready")
    parser.add_argument("--output-path", type=Path, default=None, help="指定輸出的 snapshot json 路徑")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_config()
    ensure_project_importable(config.project_root)

    snapshot_paths = [Path(path).expanduser().resolve() for path in args.snapshot_paths]
    if not snapshot_paths:
        snapshot_paths = [config.snapshot_path]

    run_dir = build_run_dir(config.results_dir, prefix="eval_snapshot")
    output_path = args.output_path.resolve() if args.output_path else run_dir / "comparison_snapshot.json"
    metadata_path = run_dir / "metadata.json"

    from job_spy_tw.storage import save_snapshot

    snapshot, metadata = build_composite_eval_snapshot(
        config,
        snapshot_paths,
        top_roles=args.top_roles,
        per_role_limit=args.per_role_limit,
        min_roles=args.min_roles,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_snapshot(snapshot, output_path)
    write_json(metadata_path, metadata)

    print(f"[done] snapshot: {output_path}")
    print(f"[done] metadata: {metadata_path}")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
