"""Persistence helpers for historical market snapshots."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from .models import MarketSnapshot, TargetRole
from .sqlite_utils import connect_sqlite
from .utils import ensure_directory


class MarketHistoryStore:
    """Persist finalized crawl snapshots into queryable history tables."""

    def __init__(
        self,
        db_path: Path,
        *,
        retention_days: int = 90,
        max_runs_per_query: int = 100,
    ) -> None:
        self.db_path = db_path
        self.retention_days = int(retention_days)
        self.max_runs_per_query = int(max_runs_per_query)
        ensure_directory(db_path.parent)
        self._initialize()

    def record_snapshot(self, snapshot: MarketSnapshot) -> int:
        role_targets_payload = self._role_targets_payload(snapshot.role_targets)
        queries_json = json.dumps(list(snapshot.queries), ensure_ascii=False)
        role_targets_json = json.dumps(role_targets_payload, ensure_ascii=False)
        skills_json = json.dumps(
            [skill.to_dict() for skill in snapshot.skills],
            ensure_ascii=False,
        )
        task_insights_json = json.dumps(
            [item.to_dict() for item in snapshot.task_insights],
            ensure_ascii=False,
        )
        errors_json = json.dumps(list(snapshot.errors), ensure_ascii=False)
        query_fingerprint = self._query_fingerprint(
            queries=list(snapshot.queries),
            role_targets=role_targets_payload,
        )

        with connect_sqlite(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO crawl_runs (
                    generated_at,
                    query_fingerprint,
                    queries_json,
                    role_targets_json,
                    job_count,
                    persisted_job_count,
                    skill_count,
                    task_count,
                    error_count,
                    skills_json,
                    task_insights_json,
                    errors_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.generated_at,
                    query_fingerprint,
                    queries_json,
                    role_targets_json,
                    len(snapshot.jobs),
                    len(snapshot.skills),
                    len(snapshot.task_insights),
                    len(snapshot.errors),
                    skills_json,
                    task_insights_json,
                    errors_json,
                    snapshot.generated_at,
                ),
            )
            crawl_run_id = int(cursor.lastrowid)
            persisted_job_count = 0

            for ordinal, job in enumerate(snapshot.jobs, start=1):
                job_url = str(job.url or "").strip()
                if not job_url:
                    continue
                persisted_job_count += 1
                job_payload_json = json.dumps(job.to_dict(), ensure_ascii=False)
                connection.execute(
                    """
                    INSERT INTO job_posts (
                        job_url,
                        source,
                        title,
                        company,
                        location,
                        salary,
                        posted_at,
                        matched_role,
                        first_seen_at,
                        last_seen_at,
                        first_crawl_run_id,
                        last_crawl_run_id,
                        latest_payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(job_url) DO UPDATE SET
                        source = excluded.source,
                        title = excluded.title,
                        company = excluded.company,
                        location = excluded.location,
                        salary = excluded.salary,
                        posted_at = excluded.posted_at,
                        matched_role = excluded.matched_role,
                        last_seen_at = excluded.last_seen_at,
                        last_crawl_run_id = excluded.last_crawl_run_id,
                        latest_payload_json = excluded.latest_payload_json
                    """,
                    (
                        job_url,
                        job.source,
                        job.title,
                        job.company,
                        job.location,
                        job.salary,
                        job.posted_at,
                        job.matched_role,
                        snapshot.generated_at,
                        snapshot.generated_at,
                        crawl_run_id,
                        crawl_run_id,
                        job_payload_json,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO crawl_run_jobs (
                        crawl_run_id,
                        job_url,
                        ordinal,
                        source,
                        title,
                        company,
                        location,
                        salary,
                        posted_at,
                        matched_role,
                        relevance_score,
                        job_snapshot_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        crawl_run_id,
                        job_url,
                        ordinal,
                        job.source,
                        job.title,
                        job.company,
                        job.location,
                        job.salary,
                        job.posted_at,
                        job.matched_role,
                        float(job.relevance_score),
                        job_payload_json,
                    ),
                )

            connection.execute(
                """
                UPDATE crawl_runs
                SET persisted_job_count = ?
                WHERE id = ?
                """,
                (persisted_job_count, crawl_run_id),
            )
            self._prune_history(connection)
            connection.commit()
        return crawl_run_id

    def _initialize(self) -> None:
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS crawl_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generated_at TEXT NOT NULL,
                    query_fingerprint TEXT NOT NULL DEFAULT '',
                    queries_json TEXT NOT NULL DEFAULT '[]',
                    role_targets_json TEXT NOT NULL DEFAULT '[]',
                    job_count INTEGER NOT NULL DEFAULT 0,
                    persisted_job_count INTEGER NOT NULL DEFAULT 0,
                    skill_count INTEGER NOT NULL DEFAULT 0,
                    task_count INTEGER NOT NULL DEFAULT 0,
                    error_count INTEGER NOT NULL DEFAULT 0,
                    skills_json TEXT NOT NULL DEFAULT '[]',
                    task_insights_json TEXT NOT NULL DEFAULT '[]',
                    errors_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL DEFAULT ''
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS job_posts (
                    job_url TEXT PRIMARY KEY,
                    source TEXT NOT NULL DEFAULT '',
                    title TEXT NOT NULL DEFAULT '',
                    company TEXT NOT NULL DEFAULT '',
                    location TEXT NOT NULL DEFAULT '',
                    salary TEXT NOT NULL DEFAULT '',
                    posted_at TEXT NOT NULL DEFAULT '',
                    matched_role TEXT NOT NULL DEFAULT '',
                    first_seen_at TEXT NOT NULL DEFAULT '',
                    last_seen_at TEXT NOT NULL DEFAULT '',
                    first_crawl_run_id INTEGER NOT NULL DEFAULT 0,
                    last_crawl_run_id INTEGER NOT NULL DEFAULT 0,
                    latest_payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS crawl_run_jobs (
                    crawl_run_id INTEGER NOT NULL,
                    job_url TEXT NOT NULL,
                    ordinal INTEGER NOT NULL DEFAULT 0,
                    source TEXT NOT NULL DEFAULT '',
                    title TEXT NOT NULL DEFAULT '',
                    company TEXT NOT NULL DEFAULT '',
                    location TEXT NOT NULL DEFAULT '',
                    salary TEXT NOT NULL DEFAULT '',
                    posted_at TEXT NOT NULL DEFAULT '',
                    matched_role TEXT NOT NULL DEFAULT '',
                    relevance_score REAL NOT NULL DEFAULT 0,
                    job_snapshot_json TEXT NOT NULL DEFAULT '{}',
                    PRIMARY KEY (crawl_run_id, job_url),
                    FOREIGN KEY (crawl_run_id) REFERENCES crawl_runs(id) ON DELETE CASCADE,
                    FOREIGN KEY (job_url) REFERENCES job_posts(job_url) ON DELETE CASCADE
                )
                """
            )
            for statement in (
                """
                CREATE INDEX IF NOT EXISTS idx_crawl_runs_generated_at
                ON crawl_runs(generated_at DESC, id DESC)
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_crawl_runs_query_fingerprint
                ON crawl_runs(query_fingerprint, generated_at DESC, id DESC)
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_job_posts_last_seen_at
                ON job_posts(last_seen_at DESC, job_url)
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_job_posts_source_last_seen
                ON job_posts(source, last_seen_at DESC, job_url)
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_crawl_run_jobs_job_url
                ON crawl_run_jobs(job_url, crawl_run_id DESC)
                """,
            ):
                connection.execute(statement)
            connection.commit()

    def _role_targets_payload(
        self,
        role_targets: list[TargetRole],
    ) -> list[dict[str, object]]:
        return [
            {
                "name": role.name,
                "priority": int(role.priority),
                "keywords": list(role.keywords),
            }
            for role in role_targets
        ]

    def _query_fingerprint(
        self,
        *,
        queries: list[str],
        role_targets: list[dict[str, object]],
    ) -> str:
        payload = json.dumps(
            {
                "queries": list(queries),
                "role_targets": list(role_targets),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _prune_history(self, connection: sqlite3.Connection) -> None:
        run_rows = connection.execute(
            """
            SELECT id, query_fingerprint, generated_at
            FROM crawl_runs
            ORDER BY generated_at DESC, id DESC
            """
        ).fetchall()
        if not run_rows:
            return

        ids_to_delete: set[int] = set()
        if self.retention_days > 0:
            cutoff = datetime.now() - timedelta(days=self.retention_days)
            for row in run_rows:
                generated_at = self._parse_iso(str(row[2] or ""))
                if generated_at is not None and generated_at < cutoff:
                    ids_to_delete.add(int(row[0]))

        if self.max_runs_per_query > 0:
            seen_counts: dict[str, int] = {}
            for row in run_rows:
                run_id = int(row[0])
                fingerprint = str(row[1] or "")
                seen_counts[fingerprint] = seen_counts.get(fingerprint, 0) + 1
                if seen_counts[fingerprint] > self.max_runs_per_query:
                    ids_to_delete.add(run_id)

        if ids_to_delete:
            placeholders = ", ".join("?" for _ in ids_to_delete)
            connection.execute(
                f"DELETE FROM crawl_runs WHERE id IN ({placeholders})",
                tuple(sorted(ids_to_delete)),
            )
            self._refresh_job_posts(connection)

    def _refresh_job_posts(self, connection: sqlite3.Connection) -> None:
        summaries = self._job_post_summaries(connection)
        referenced_job_urls = set(summaries)
        orphan_rows = connection.execute(
            """
            SELECT job_url
            FROM job_posts
            WHERE job_url NOT IN (
                SELECT DISTINCT job_url
                FROM crawl_run_jobs
            )
            """
        ).fetchall()
        if orphan_rows:
            connection.executemany(
                "DELETE FROM job_posts WHERE job_url = ?",
                [(str(row[0]),) for row in orphan_rows],
            )

        for job_url, summary in summaries.items():
            connection.execute(
                """
                INSERT INTO job_posts (
                    job_url,
                    source,
                    title,
                    company,
                    location,
                    salary,
                    posted_at,
                    matched_role,
                    first_seen_at,
                    last_seen_at,
                    first_crawl_run_id,
                    last_crawl_run_id,
                    latest_payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_url) DO UPDATE SET
                    source = excluded.source,
                    title = excluded.title,
                    company = excluded.company,
                    location = excluded.location,
                    salary = excluded.salary,
                    posted_at = excluded.posted_at,
                    matched_role = excluded.matched_role,
                    first_seen_at = excluded.first_seen_at,
                    last_seen_at = excluded.last_seen_at,
                    first_crawl_run_id = excluded.first_crawl_run_id,
                    last_crawl_run_id = excluded.last_crawl_run_id,
                    latest_payload_json = excluded.latest_payload_json
                """,
                (
                    job_url,
                    summary["source"],
                    summary["title"],
                    summary["company"],
                    summary["location"],
                    summary["salary"],
                    summary["posted_at"],
                    summary["matched_role"],
                    summary["first_seen_at"],
                    summary["last_seen_at"],
                    summary["first_crawl_run_id"],
                    summary["last_crawl_run_id"],
                    summary["latest_payload_json"],
                ),
            )

        if not referenced_job_urls:
            connection.execute("DELETE FROM job_posts")

    def _job_post_summaries(
        self,
        connection: sqlite3.Connection,
    ) -> dict[str, dict[str, object]]:
        rows = connection.execute(
            """
            SELECT
                jobs.job_url,
                jobs.source,
                jobs.title,
                jobs.company,
                jobs.location,
                jobs.salary,
                jobs.posted_at,
                jobs.matched_role,
                jobs.job_snapshot_json,
                runs.id,
                runs.generated_at
            FROM crawl_run_jobs AS jobs
            INNER JOIN crawl_runs AS runs
                ON runs.id = jobs.crawl_run_id
            ORDER BY runs.generated_at ASC, runs.id ASC, jobs.ordinal ASC
            """
        ).fetchall()
        summaries: dict[str, dict[str, object]] = {}
        for row in rows:
            job_url = str(row[0])
            crawl_run_id = int(row[9])
            generated_at = str(row[10] or "")
            payload = summaries.get(job_url)
            if payload is None:
                summaries[job_url] = {
                    "source": str(row[1] or ""),
                    "title": str(row[2] or ""),
                    "company": str(row[3] or ""),
                    "location": str(row[4] or ""),
                    "salary": str(row[5] or ""),
                    "posted_at": str(row[6] or ""),
                    "matched_role": str(row[7] or ""),
                    "first_seen_at": generated_at,
                    "last_seen_at": generated_at,
                    "first_crawl_run_id": crawl_run_id,
                    "last_crawl_run_id": crawl_run_id,
                    "latest_payload_json": str(row[8] or "{}"),
                }
                continue
            payload["source"] = str(row[1] or "")
            payload["title"] = str(row[2] or "")
            payload["company"] = str(row[3] or "")
            payload["location"] = str(row[4] or "")
            payload["salary"] = str(row[5] or "")
            payload["posted_at"] = str(row[6] or "")
            payload["matched_role"] = str(row[7] or "")
            payload["last_seen_at"] = generated_at
            payload["last_crawl_run_id"] = crawl_run_id
            payload["latest_payload_json"] = str(row[8] or "{}")
        return summaries

    def _parse_iso(self, value: str) -> datetime | None:
        try:
            return datetime.fromisoformat(str(value).strip())
        except Exception:  # noqa: BLE001
            return None
