"""Manual entrypoint for backend runtime status."""

from __future__ import annotations

import argparse
import json

from .backend_status_service import collect_backend_status_report
from .config import load_settings
from .product_store import ProductStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show backend runtime and backup status.")
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Project base directory for loading .env and data paths.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the status report as JSON.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 when the report contains any issues.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(args.base_dir)
    product_store = ProductStore(settings.product_state_db_path)
    report = collect_backend_status_report(
        settings=settings,
        product_store=product_store,
    )

    if bool(args.json):
        print(
            json.dumps(
                report.as_dict(),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1 if bool(args.strict) and bool(report.issues) else 0

    print(
        "Build: "
        f"version={report.build.package_version} "
        f"api={report.build.api_version} "
        f"env={report.build.deploy_env} "
        f"channel={report.build.release_channel} "
        f"sha={report.build.git_sha}"
    )
    print(
        "Backend status: "
        f"mode={report.execution_mode} "
        f"due_saved_searches={report.operations.due_saved_search_count} "
        f"pending_jobs={report.operations.pending_job_count} "
        f"leased_jobs={report.operations.leased_job_count} "
        f"failed_jobs={report.operations.failed_job_count} "
        f"ready_snapshots={report.operations.ready_snapshot_count} "
        f"partial_snapshots={report.operations.partial_snapshot_count}"
    )
    print(
        "Activity: "
        f"scheduler={report.operations.last_scheduler_pass_at or '-'} "
        f"worker={report.operations.last_worker_activity_at or '-'} "
        f"jobs={report.operations.last_job_activity_at or '-'} "
        f"snapshots={report.operations.last_snapshot_update_at or '-'}"
    )
    print(
        "Backups: "
        f"count={report.backups.backup_count} "
        f"latest={report.backups.latest_backup_id or '-'} "
        f"created_at={report.backups.latest_created_at or '-'} "
        f"databases={','.join(report.backups.latest_database_keys) or '-'}"
    )
    print(
        "AI health: "
        f"latency_status={report.ai_health.get('latency_budgets', {}).get('status', 'NO_DATA')} "
        f"cache_hit_rate={report.ai_health.get('cache_efficiency', {}).get('chunk_cache_hit_rate', 0.0)} "
        f"audit_events={report.security.get('recent_audit_events', 0)}"
    )
    if report.issues:
        print(f"Issues: {', '.join(report.issues)}")
    else:
        print("Issues: none")
    if bool(args.strict) and bool(report.issues):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
