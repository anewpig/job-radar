"""Command-line entrypoints for local project utilities."""

from __future__ import annotations

import argparse

from .pipeline import JobMarketPipeline
from .targets import build_default_queries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl and analyze job listings.")
    parser.add_argument(
        "--query",
        action="append",
        dest="queries",
        help="Custom query. Can be used multiple times.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    pipeline = JobMarketPipeline(perform_cache_maintenance=True)
    queries = args.queries or build_default_queries()
    snapshot = pipeline.run(queries=queries)
    print(
        f"抓取完成，共 {len(snapshot.jobs)} 筆職缺，輸出到 {pipeline.settings.snapshot_path}"
    )
