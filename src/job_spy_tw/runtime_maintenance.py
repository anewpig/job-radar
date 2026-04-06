"""Manual entrypoint for runtime cleanup."""

from __future__ import annotations

import argparse

from .config import load_settings
from .runtime_maintenance_service import run_runtime_cleanup


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clean old query runtime artifacts.")
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Project base directory for loading .env and runtime state.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run cleanup immediately and ignore the cleanup interval guard.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(args.base_dir)
    result = run_runtime_cleanup(
        settings=settings,
        trigger="manual",
        force=bool(args.force),
    )
    print(
        "Runtime cleanup: "
        f"status={result.status} "
        f"jobs={result.deleted_jobs} "
        f"snapshots={result.deleted_snapshot_rows} "
        f"snapshot_files={result.deleted_snapshot_files} "
        f"orphans={result.deleted_orphan_snapshot_files} "
        f"signals={result.deleted_signals}"
    )
    if result.skipped_reason:
        print(f"Reason: {result.skipped_reason}")


if __name__ == "__main__":
    main()
