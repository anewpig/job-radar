"""Scheduler entrypoint for automatic saved-search refresh."""

from __future__ import annotations

import argparse
import socket
import time
from uuid import uuid4

from .config import load_settings
from .crawl_application_service import schedule_due_saved_searches
from .logging_utils import configure_logging
from .product_store import ProductStore
from .query_runtime import RuntimeSignalStore
from .runtime_maintenance_service import run_runtime_cleanup


def default_scheduler_worker_id() -> str:
    host = socket.gethostname().split(".", 1)[0]
    return f"crawl-scheduler:{host}:{uuid4().hex[:8]}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Enqueue due saved-search refresh jobs.")
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Project base directory for loading .env and runtime state.",
    )
    parser.add_argument(
        "--worker-id",
        default="",
        help="Worker id attached to enqueued crawl jobs.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=60.0,
        help="Seconds to wait between scheduler passes when not using --once.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one scheduler pass, then exit.",
    )
    return parser


def run_scheduler_loop(
    *,
    base_dir: str,
    worker_id: str,
    poll_interval: float,
    once: bool,
) -> int:
    settings = load_settings(base_dir)
    logger = configure_logging(
        service_name="crawl_scheduler",
        data_dir=settings.data_dir,
    )
    product_store = ProductStore(settings.product_state_db_path)
    effective_worker_id = worker_id.strip() or default_scheduler_worker_id()
    signal_store = RuntimeSignalStore(db_path=settings.query_state_db_path)

    while True:
        run_runtime_cleanup(
            settings=settings,
            trigger="scheduler",
        )
        result = schedule_due_saved_searches(
            settings=settings,
            product_store=product_store,
            worker_id=effective_worker_id,
        )
        signal_store.put_signal(
            component_kind="scheduler",
            component_id=effective_worker_id,
            status="completed" if result.checked_count or result.enqueued_count else "idle",
            message=(
                "Scheduler pass: "
                f"checked={result.checked_count} "
                f"enqueued={result.enqueued_count} "
                f"skipped={result.skipped_count} "
                f"invalid={result.invalid_count}"
            ),
            payload={
                "poll_interval": float(poll_interval),
                "once": bool(once),
                "checked_count": int(result.checked_count),
                "enqueued_count": int(result.enqueued_count),
                "skipped_count": int(result.skipped_count),
                "invalid_count": int(result.invalid_count),
            },
        )
        logger.info(
            "Scheduler pass: checked=%s enqueued=%s skipped=%s invalid=%s",
            result.checked_count,
            result.enqueued_count,
            result.skipped_count,
            result.invalid_count,
        )
        for detail in result.details:
            logger.info(detail)
        if once:
            return 0
        time.sleep(max(1.0, float(poll_interval)))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(
        run_scheduler_loop(
            base_dir=args.base_dir,
            worker_id=args.worker_id,
            poll_interval=args.poll_interval,
            once=bool(args.once),
        )
    )


if __name__ == "__main__":
    main()
