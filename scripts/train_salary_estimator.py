#!/usr/bin/env python3
"""Train the v1 salary estimator from snapshot + market history."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.salary_prediction import (  # noqa: E402
    SKLEARN_AVAILABLE,
    build_salary_training_frame,
    load_salary_training_jobs,
    save_salary_estimator,
    train_salary_estimator,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train salary estimator v1.")
    parser.add_argument(
        "--snapshot-path",
        type=Path,
        default=ROOT / "data" / "jobs_latest.json",
        help="Path to jobs_latest.json",
    )
    parser.add_argument(
        "--history-db-path",
        type=Path,
        default=ROOT / "data" / "market_history.sqlite3",
        help="Path to market_history.sqlite3",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "models" / "salary_estimator.joblib",
        help="Output model path",
    )
    parser.add_argument(
        "--meta-output",
        type=Path,
        default=ROOT / "data" / "models" / "salary_estimator_meta.json",
        help="Output metadata json path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not SKLEARN_AVAILABLE:
        print("scikit-learn 不可用，無法訓練薪資模型。", file=sys.stderr)
        return 1

    jobs = load_salary_training_jobs(
        snapshot_path=args.snapshot_path,
        history_db_path=args.history_db_path,
    )
    training_frame = build_salary_training_frame(jobs)
    if training_frame.empty:
        print("找不到可訓練的薪資樣本。", file=sys.stderr)
        return 1

    artifact, metadata = train_salary_estimator(training_frame)
    save_salary_estimator(
        artifact,
        model_path=args.output,
        meta_path=args.meta_output,
    )
    args.meta_output.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "model_path": str(args.output),
                "meta_path": str(args.meta_output),
                "sample_count": int(metadata.get("sample_count") or 0),
                "evaluation": metadata.get("evaluation") or {},
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
