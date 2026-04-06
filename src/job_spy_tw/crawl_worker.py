"""Background worker entrypoint for queued crawl jobs."""

from __future__ import annotations

import argparse
import socket
import time
from uuid import uuid4

from .config import load_settings
from .crawl_application_service import build_query_runtime, process_queued_crawl_job
from .query_runtime import RuntimeSignalStore
from .runtime_maintenance_service import run_runtime_cleanup


def default_worker_id() -> str:
    host = socket.gethostname().split(".", 1)[0]
    return f"crawl-worker:{host}:{uuid4().hex[:8]}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run queued crawl jobs in a detached worker.")
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Project base directory for loading .env and runtime state.",
    )
    parser.add_argument(
        "--worker-id",
        default="",
        help="Stable worker identifier shown in queue leases.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Seconds to wait before polling the queue again when idle.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process at most one job, then exit.",
    )
    return parser


def run_worker_loop(
    *,
    base_dir: str,
    worker_id: str,
    poll_interval: float,
    once: bool,
) -> int:
    settings = load_settings(base_dir)
    registry, queue = build_query_runtime(settings)
    del registry
    effective_worker_id = worker_id.strip() or default_worker_id()
    signal_store = RuntimeSignalStore(db_path=settings.query_state_db_path)

    while True:
        run_runtime_cleanup(
            settings=settings,
            trigger="worker",
        )
        job = queue.lease_job(effective_worker_id)
        if job is None:
            signal_store.put_signal(
                component_kind="worker",
                component_id=effective_worker_id,
                status="idle",
                message="No pending crawl job found.",
                payload={
                    "poll_interval": float(poll_interval),
                    "once": bool(once),
                },
            )
            if once:
                print("No pending crawl job found.")
                return 0
            time.sleep(max(0.2, float(poll_interval)))
            continue

        signal_store.put_signal(
            component_kind="worker",
            component_id=effective_worker_id,
            status="processing",
            message=f"Processing crawl job #{job.id}",
            payload={
                "poll_interval": float(poll_interval),
                "once": bool(once),
                "job_id": int(job.id),
                "query_signature": job.query_signature,
            },
        )
        print(f"Processing crawl job #{job.id} for signature {job.query_signature}")
        result = process_queued_crawl_job(settings=settings, job=job)
        if result.status == "completed":
            signal_store.put_signal(
                component_kind="worker",
                component_id=effective_worker_id,
                status="completed",
                message=f"Completed crawl job #{job.id}",
                payload={
                    "poll_interval": float(poll_interval),
                    "once": bool(once),
                    "job_id": int(job.id),
                    "query_signature": job.query_signature,
                    "job_count": (
                        len(result.snapshot.jobs) if result.snapshot is not None else 0
                    ),
                },
            )
            print(
                f"Completed crawl job #{job.id} with "
                f"{len(result.snapshot.jobs) if result.snapshot is not None else 0} jobs."
            )
            if once:
                return 0
            continue

        if result.status == "retry_scheduled":
            signal_store.put_signal(
                component_kind="worker",
                component_id=effective_worker_id,
                status="retry_scheduled",
                message=(
                    f"Retry scheduled for crawl job #{job.id} "
                    f"({result.attempt_count}/{result.max_attempts})"
                ),
                payload={
                    "poll_interval": float(poll_interval),
                    "once": bool(once),
                    "job_id": int(job.id),
                    "query_signature": job.query_signature,
                    "attempt_count": int(result.attempt_count),
                    "max_attempts": int(result.max_attempts),
                    "next_retry_at": result.next_retry_at,
                },
            )
            print(
                f"Retry scheduled for crawl job #{job.id} "
                f"at {result.next_retry_at} "
                f"({result.attempt_count}/{result.max_attempts})."
            )
            if once:
                return 0
            continue

        signal_store.put_signal(
            component_kind="worker",
            component_id=effective_worker_id,
            status="failed",
            message=result.error_message,
            payload={
                "poll_interval": float(poll_interval),
                "once": bool(once),
                "job_id": int(job.id),
                "query_signature": job.query_signature,
            },
        )
        print(f"Failed crawl job #{job.id}: {result.error_message}")
        if once:
            return 1


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(
        run_worker_loop(
            base_dir=args.base_dir,
            worker_id=args.worker_id,
            poll_interval=args.poll_interval,
            once=bool(args.once),
        )
    )


if __name__ == "__main__":
    main()
