"""Tests for historical market snapshot persistence."""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.market_history_store import MarketHistoryStore  # noqa: E402
from job_spy_tw.models import JobListing, MarketSnapshot, TargetRole  # noqa: E402


class MarketHistoryStoreTests(unittest.TestCase):
    def _snapshot(self, *, generated_at: str, jobs: list[JobListing]) -> MarketSnapshot:
        return MarketSnapshot(
            generated_at=generated_at,
            queries=["AI工程師", "LLM"],
            role_targets=[TargetRole(name="AI工程師", priority=1, keywords=["LLM"])],
            jobs=jobs,
            skills=[],
            task_insights=[],
            errors=[],
        )

    def test_record_snapshot_persists_runs_jobs_and_latest_job_state(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "market_history.sqlite3"
        store = MarketHistoryStore(db_path)
        first_job = JobListing(
            source="104",
            title="AI工程師",
            company="Example",
            location="台北市",
            url="https://example.com/jobs/1",
            salary="月薪 80,000",
            matched_role="AI工程師",
            relevance_score=41.5,
        )
        second_job = JobListing(
            source="1111",
            title="資料工程師",
            company="Data Corp",
            location="新北市",
            url="https://example.com/jobs/2",
            matched_role="資料工程師",
            relevance_score=35.0,
        )

        run_id = store.record_snapshot(
            self._snapshot(
                generated_at="2026-04-06T10:00:00",
                jobs=[first_job, second_job],
            )
        )

        self.assertGreater(run_id, 0)
        with sqlite3.connect(db_path) as connection:
            run_row = connection.execute(
                """
                SELECT job_count, persisted_job_count, query_fingerprint
                FROM crawl_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()
            job_rows = connection.execute(
                "SELECT COUNT(*) FROM job_posts"
            ).fetchone()
            run_job_rows = connection.execute(
                "SELECT COUNT(*) FROM crawl_run_jobs WHERE crawl_run_id = ?",
                (run_id,),
            ).fetchone()

        self.assertEqual(int(run_row[0]), 2)
        self.assertEqual(int(run_row[1]), 2)
        self.assertTrue(str(run_row[2]))
        self.assertEqual(int(job_rows[0]), 2)
        self.assertEqual(int(run_job_rows[0]), 2)

    def test_record_snapshot_updates_existing_job_post_and_keeps_run_history(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "market_history.sqlite3"
        store = MarketHistoryStore(db_path)
        original_job = JobListing(
            source="104",
            title="AI工程師",
            company="Example",
            location="台北市",
            url="https://example.com/jobs/1",
            matched_role="AI工程師",
            relevance_score=30.0,
        )
        updated_job = JobListing(
            source="104",
            title="資深 AI 工程師",
            company="Example",
            location="台北市",
            url="https://example.com/jobs/1",
            matched_role="AI工程師",
            relevance_score=44.0,
        )

        first_run_id = store.record_snapshot(
            self._snapshot(
                generated_at="2026-04-06T10:00:00",
                jobs=[original_job],
            )
        )
        second_run_id = store.record_snapshot(
            self._snapshot(
                generated_at="2026-04-07T10:00:00",
                jobs=[updated_job],
            )
        )

        with sqlite3.connect(db_path) as connection:
            post_row = connection.execute(
                """
                SELECT title, first_seen_at, last_seen_at, first_crawl_run_id, last_crawl_run_id
                FROM job_posts
                WHERE job_url = ?
                """,
                (updated_job.url,),
            ).fetchone()
            run_history = connection.execute(
                """
                SELECT crawl_run_id, title, relevance_score
                FROM crawl_run_jobs
                WHERE job_url = ?
                ORDER BY crawl_run_id ASC
                """,
                (updated_job.url,),
            ).fetchall()

        self.assertEqual(str(post_row[0]), "資深 AI 工程師")
        self.assertEqual(str(post_row[1]), "2026-04-06T10:00:00")
        self.assertEqual(str(post_row[2]), "2026-04-07T10:00:00")
        self.assertEqual(int(post_row[3]), first_run_id)
        self.assertEqual(int(post_row[4]), second_run_id)
        self.assertEqual(
            [(int(row[0]), str(row[1]), float(row[2])) for row in run_history],
            [
                (first_run_id, "AI工程師", 30.0),
                (second_run_id, "資深 AI 工程師", 44.0),
            ],
        )

    def test_record_snapshot_skips_jobs_without_urls(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "market_history.sqlite3"
        store = MarketHistoryStore(db_path)
        snapshot = self._snapshot(
            generated_at="2026-04-06T10:00:00",
            jobs=[
                JobListing(
                    source="104",
                    title="No URL Job",
                    company="Example",
                    location="台北市",
                    url="",
                )
            ],
        )

        run_id = store.record_snapshot(snapshot)

        with sqlite3.connect(db_path) as connection:
            run_row = connection.execute(
                "SELECT job_count, persisted_job_count FROM crawl_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
            job_count_row = connection.execute("SELECT COUNT(*) FROM job_posts").fetchone()
            payload_row = connection.execute(
                "SELECT queries_json, role_targets_json FROM crawl_runs WHERE id = ?",
                (run_id,),
            ).fetchone()

        self.assertEqual(int(run_row[0]), 1)
        self.assertEqual(int(run_row[1]), 0)
        self.assertEqual(int(job_count_row[0]), 0)
        self.assertEqual(json.loads(str(payload_row[0])), ["AI工程師", "LLM"])
        self.assertEqual(len(json.loads(str(payload_row[1]))), 1)

    def test_record_snapshot_prunes_runs_beyond_per_query_limit(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "market_history.sqlite3"
        store = MarketHistoryStore(
            db_path,
            retention_days=0,
            max_runs_per_query=2,
        )

        for generated_at, title, score in (
            ("2026-04-01T10:00:00", "AI工程師", 30.0),
            ("2026-04-02T10:00:00", "資深 AI 工程師", 35.0),
            ("2026-04-03T10:00:00", "Lead AI 工程師", 40.0),
        ):
            store.record_snapshot(
                self._snapshot(
                    generated_at=generated_at,
                    jobs=[
                        JobListing(
                            source="104",
                            title=title,
                            company="Example",
                            location="台北市",
                            url="https://example.com/jobs/1",
                            matched_role="AI工程師",
                            relevance_score=score,
                        )
                    ],
                )
            )

        with sqlite3.connect(db_path) as connection:
            run_rows = connection.execute(
                "SELECT generated_at FROM crawl_runs ORDER BY generated_at ASC"
            ).fetchall()
            post_row = connection.execute(
                """
                SELECT title, first_seen_at, last_seen_at
                FROM job_posts
                WHERE job_url = ?
                """,
                ("https://example.com/jobs/1",),
            ).fetchone()
            run_job_rows = connection.execute(
                """
                SELECT title
                FROM crawl_run_jobs
                WHERE job_url = ?
                ORDER BY crawl_run_id ASC
                """,
                ("https://example.com/jobs/1",),
            ).fetchall()

        self.assertEqual(
            [str(row[0]) for row in run_rows],
            ["2026-04-02T10:00:00", "2026-04-03T10:00:00"],
        )
        self.assertEqual(str(post_row[0]), "Lead AI 工程師")
        self.assertEqual(str(post_row[1]), "2026-04-02T10:00:00")
        self.assertEqual(str(post_row[2]), "2026-04-03T10:00:00")
        self.assertEqual(
            [str(row[0]) for row in run_job_rows],
            ["資深 AI 工程師", "Lead AI 工程師"],
        )

    def test_record_snapshot_prunes_runs_older_than_retention_window(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "market_history.sqlite3"
        store = MarketHistoryStore(
            db_path,
            retention_days=30,
            max_runs_per_query=0,
        )

        store.record_snapshot(
            self._snapshot(
                generated_at="2020-01-01T10:00:00",
                jobs=[
                    JobListing(
                        source="104",
                        title="Very Old Job",
                        company="Legacy",
                        location="台北市",
                        url="https://example.com/jobs/old",
                        matched_role="AI工程師",
                    )
                ],
            )
        )
        store.record_snapshot(
            self._snapshot(
                generated_at=datetime.now().isoformat(timespec="seconds"),
                jobs=[
                    JobListing(
                        source="104",
                        title="Recent Job",
                        company="Current",
                        location="台北市",
                        url="https://example.com/jobs/recent",
                        matched_role="AI工程師",
                    )
                ],
            )
        )

        with sqlite3.connect(db_path) as connection:
            run_rows = connection.execute(
                "SELECT generated_at FROM crawl_runs ORDER BY generated_at ASC"
            ).fetchall()
            job_urls = connection.execute(
                "SELECT job_url FROM job_posts ORDER BY job_url ASC"
            ).fetchall()

        self.assertEqual(len(run_rows), 1)
        self.assertEqual([str(row[0]) for row in job_urls], ["https://example.com/jobs/recent"])


if __name__ == "__main__":
    unittest.main()
