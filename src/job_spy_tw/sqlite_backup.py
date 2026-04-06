"""Manual entrypoint for SQLite backup and restore."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_settings
from .sqlite_backup_service import run_sqlite_backup, run_sqlite_restore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backup or restore operational SQLite databases.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup", help="Create a SQLite backup set.")
    backup_parser.add_argument(
        "--base-dir",
        default=".",
        help="Project base directory for loading .env and data paths.",
    )
    backup_parser.add_argument(
        "--include-runtime",
        action="store_true",
        help="Also include query_runtime.sqlite3 in the backup set.",
    )
    backup_parser.add_argument(
        "--keep-last",
        type=int,
        default=None,
        help="After the backup completes, keep only the newest N backup sets.",
    )

    restore_parser = subparsers.add_parser("restore", help="Restore SQLite databases from a backup set.")
    restore_parser.add_argument(
        "--base-dir",
        default=".",
        help="Project base directory for loading .env and data paths.",
    )
    restore_parser.add_argument(
        "--backup",
        required=True,
        help="Backup directory or manifest.json path to restore from.",
    )
    restore_parser.add_argument(
        "--include-runtime",
        action="store_true",
        help="Also restore query_runtime.sqlite3 if the backup set contains it.",
    )
    restore_parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm that app / worker / scheduler are stopped before restoring.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(args.base_dir)

    if args.command == "backup":
        result = run_sqlite_backup(
            settings=settings,
            include_runtime=bool(args.include_runtime),
            keep_last=args.keep_last,
        )
        print(
            "SQLite backup: "
            f"dir={result.backup_dir} "
            f"manifest={result.manifest_path} "
            f"databases={','.join(entry.database_key for entry in result.entries) or '-'} "
            f"skipped={','.join(result.skipped_databases) or '-'} "
            f"pruned={len(result.pruned_backup_dirs)}"
        )
        return

    if not bool(args.yes):
        parser.error("restore requires --yes after you stop app / worker / scheduler.")

    result = run_sqlite_restore(
        settings=settings,
        backup_path=Path(args.backup),
        include_runtime=bool(args.include_runtime),
        create_safety_backup=True,
    )
    print(
        "SQLite restore: "
        f"manifest={result.manifest_path} "
        f"restored={','.join(result.restored_databases) or '-'} "
        f"skipped={','.join(result.skipped_databases) or '-'}"
    )
    if result.safety_backup_manifest_path is not None:
        print(f"Safety backup: {result.safety_backup_manifest_path}")


if __name__ == "__main__":
    main()
