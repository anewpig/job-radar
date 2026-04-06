"""Manual entrypoint for combined backend maintenance."""

from __future__ import annotations

import argparse

from .backend_maintenance_service import run_backend_maintenance
from .config import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run runtime cleanup and SQLite backup in one maintenance pass."
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Project base directory for loading .env and data paths.",
    )
    parser.add_argument(
        "--trigger",
        default="manual",
        help="Human-readable trigger label, for example manual or scheduled.",
    )
    parser.add_argument(
        "--force-cleanup",
        action="store_true",
        help="Ignore the runtime cleanup interval guard for this run.",
    )
    parser.add_argument(
        "--include-runtime-backup",
        action="store_true",
        help="Also include query_runtime.sqlite3 in the backup set.",
    )
    parser.add_argument(
        "--keep-last-backups",
        type=int,
        default=None,
        help="After backup completes, keep only the newest N backup sets.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(args.base_dir)
    result = run_backend_maintenance(
        settings=settings,
        trigger=str(args.trigger).strip() or "manual",
        force_cleanup=bool(args.force_cleanup),
        include_runtime_backup=bool(args.include_runtime_backup),
        keep_last_backups=args.keep_last_backups,
    )
    print(
        "Backend maintenance: "
        f"cleanup_status={result.cleanup.status} "
        f"deleted_jobs={result.cleanup.deleted_jobs} "
        f"deleted_snapshots={result.cleanup.deleted_snapshot_rows} "
        f"deleted_signals={result.cleanup.deleted_signals} "
        f"backup_dir={result.backup.backup_dir} "
        f"backup_databases={','.join(entry.database_key for entry in result.backup.entries) or '-'} "
        f"backup_skipped={','.join(result.backup.skipped_databases) or '-'} "
        f"backup_pruned={len(result.backup.pruned_backup_dirs)}"
    )
    if result.cleanup.skipped_reason:
        print(f"Cleanup reason: {result.cleanup.skipped_reason}")


if __name__ == "__main__":
    main()
