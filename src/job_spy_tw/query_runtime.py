"""Snapshot registry and crawl queue helpers for cache-first query execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import MarketSnapshot
from .sqlite_utils import connect_sqlite
from .storage import load_snapshot, save_snapshot
from .store.common import build_signature, now_iso
from .utils import ensure_directory


def build_query_signature(
    rows: list[dict[str, Any]],
    custom_queries_text: str,
    crawl_preset_label: str,
) -> str:
    """Build the stable cache key for a logical search query."""
    return build_signature(rows, custom_queries_text, crawl_preset_label)


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _future_iso(seconds: int | float) -> str:
    return (datetime.now() + timedelta(seconds=max(0.0, float(seconds)))).isoformat(
        timespec="seconds"
    )


@dataclass(slots=True)
class SnapshotRecord:
    query_signature: str
    status: str
    generated_at: str
    fresh_until: str
    storage_key: str
    last_accessed_at: str
    updated_at: str
    error_message: str = ""
    is_partial: bool = False
    snapshot: MarketSnapshot | None = None

    def is_fresh(self) -> bool:
        """Return whether the current snapshot should be treated as fresh."""
        if not self.fresh_until:
            return False
        return _parse_iso(self.fresh_until) >= datetime.now()


@dataclass(slots=True)
class CrawlJobRecord:
    id: int
    query_signature: str
    payload_json: str
    priority: int
    status: str
    attempt_count: int
    max_attempts: int
    lease_owner: str
    lease_expires_at: str
    next_retry_at: str
    created_at: str
    updated_at: str
    snapshot_ref: str
    error_message: str

    def payload(self) -> dict[str, Any]:
        """Decode the stored job payload."""
        if not self.payload_json:
            return {}
        return json.loads(self.payload_json)

    def lease_active(self) -> bool:
        """Return whether the current lease is still active."""
        if self.status != "leased" or not self.lease_expires_at:
            return False
        return _parse_iso(self.lease_expires_at) >= datetime.now()

    def retry_pending(self) -> bool:
        """Return whether the job is waiting for its retry backoff to elapse."""
        if self.status != "pending" or not self.next_retry_at:
            return False
        return _parse_iso(self.next_retry_at) > datetime.now()


@dataclass(slots=True)
class RuntimeSignalRecord:
    component_kind: str
    component_id: str
    status: str
    message: str
    payload_json: str
    created_at: str
    updated_at: str

    def payload(self) -> dict[str, Any]:
        if not self.payload_json:
            return {}
        return json.loads(self.payload_json)


class QuerySnapshotRegistry:
    """Persist latest query snapshots and freshness metadata."""

    def __init__(
        self,
        *,
        db_path: Path,
        snapshot_dir: Path,
        snapshot_ttl_seconds: int,
    ) -> None:
        self.db_path = db_path
        self.snapshot_dir = ensure_directory(snapshot_dir)
        self.snapshot_ttl_seconds = int(snapshot_ttl_seconds)
        self._initialize()

    def get_snapshot(self, query_signature: str) -> SnapshotRecord | None:
        """Return the latest cached snapshot and touch last access time."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    query_signature,
                    status,
                    generated_at,
                    fresh_until,
                    storage_key,
                    last_accessed_at,
                    updated_at,
                    error_message,
                    is_partial
                FROM query_snapshots
                WHERE query_signature = ?
                """,
                (query_signature,),
            ).fetchone()
            if row is None:
                return None
            now = now_iso()
            connection.execute(
                """
                UPDATE query_snapshots
                SET last_accessed_at = ?, updated_at = ?
                WHERE query_signature = ?
                """,
                (now, now, query_signature),
            )
            record = self._row_to_snapshot_record(row)
            record.last_accessed_at = now
            record.updated_at = now

        snapshot_path = self.snapshot_dir / record.storage_key
        if snapshot_path.exists():
            record.snapshot = load_snapshot(snapshot_path)
        return record

    def put_snapshot(
        self,
        query_signature: str,
        snapshot: MarketSnapshot,
        *,
        status: str,
        fresh_until: str | None = None,
        is_partial: bool = False,
        error_message: str = "",
    ) -> SnapshotRecord:
        """Store the latest usable snapshot for a query signature."""
        storage_key = self._storage_key_for(query_signature, is_partial=is_partial)
        save_snapshot(snapshot, self.snapshot_dir / storage_key)
        if not is_partial:
            partial_path = self.snapshot_dir / self._storage_key_for(
                query_signature,
                is_partial=True,
            )
            if partial_path.exists():
                partial_path.unlink()

        now = now_iso()
        record = SnapshotRecord(
            query_signature=query_signature,
            status=status,
            generated_at=snapshot.generated_at,
            fresh_until=fresh_until or self.compute_fresh_until(),
            storage_key=storage_key,
            last_accessed_at=now,
            updated_at=now,
            error_message=error_message,
            is_partial=is_partial,
            snapshot=snapshot,
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO query_snapshots (
                    query_signature,
                    status,
                    generated_at,
                    fresh_until,
                    storage_key,
                    last_accessed_at,
                    updated_at,
                    error_message,
                    is_partial
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(query_signature) DO UPDATE SET
                    status = excluded.status,
                    generated_at = excluded.generated_at,
                    fresh_until = excluded.fresh_until,
                    storage_key = excluded.storage_key,
                    last_accessed_at = excluded.last_accessed_at,
                    updated_at = excluded.updated_at,
                    error_message = excluded.error_message,
                    is_partial = excluded.is_partial
                """,
                (
                    record.query_signature,
                    record.status,
                    record.generated_at,
                    record.fresh_until,
                    record.storage_key,
                    record.last_accessed_at,
                    record.updated_at,
                    record.error_message,
                    int(record.is_partial),
                ),
            )
        return record

    def mark_snapshot_stale(self, query_signature: str) -> None:
        """Mark a cached snapshot stale while keeping it readable."""
        now = now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE query_snapshots
                SET status = 'stale',
                    fresh_until = ?,
                    updated_at = ?
                WHERE query_signature = ?
                """,
                (now, now, query_signature),
            )

    def compute_fresh_until(self, ttl_seconds: int | None = None) -> str:
        """Compute the next freshness cutoff timestamp."""
        ttl = self.snapshot_ttl_seconds if ttl_seconds is None else ttl_seconds
        return _future_iso(ttl)

    def list_snapshots(
        self,
        *,
        limit: int = 20,
        status: str | None = None,
        is_partial: bool | None = None,
    ) -> list[SnapshotRecord]:
        """Return recent snapshot metadata without touching access timestamps."""
        query = """
            SELECT
                query_signature,
                status,
                generated_at,
                fresh_until,
                storage_key,
                last_accessed_at,
                updated_at,
                error_message,
                is_partial
            FROM query_snapshots
        """
        clauses: list[str] = []
        params: list[Any] = []
        if status is not None:
            clauses.append("status = ?")
            params.append(str(status))
        if is_partial is not None:
            clauses.append("is_partial = ?")
            params.append(1 if is_partial else 0)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY updated_at DESC, query_signature ASC LIMIT ?"
        params.append(max(1, int(limit)))
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._row_to_snapshot_record(row) for row in rows]

    def count_snapshots(
        self,
        *,
        status: str | None = None,
        is_partial: bool | None = None,
    ) -> int:
        """Count snapshots matching one optional status/partial filter."""
        query = "SELECT COUNT(*) FROM query_snapshots"
        clauses: list[str] = []
        params: list[Any] = []
        if status is not None:
            clauses.append("status = ?")
            params.append(str(status))
        if is_partial is not None:
            clauses.append("is_partial = ?")
            params.append(1 if is_partial else 0)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        with self._connect() as connection:
            row = connection.execute(query, tuple(params)).fetchone()
        return int(row[0]) if row else 0

    def prune_snapshots(
        self,
        *,
        ready_retention_days: int,
        partial_retention_hours: int,
    ) -> dict[str, int]:
        """Delete stale snapshot rows/files and remove orphaned snapshot files."""
        now = datetime.now()
        ready_cutoff = (
            now - timedelta(days=int(ready_retention_days))
            if int(ready_retention_days) > 0
            else None
        )
        partial_cutoff = (
            now - timedelta(hours=int(partial_retention_hours))
            if int(partial_retention_hours) > 0
            else None
        )
        deleted_signatures: list[str] = []
        deleted_storage_keys: set[str] = set()

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT query_signature, storage_key, updated_at, is_partial
                FROM query_snapshots
                ORDER BY updated_at ASC, query_signature ASC
                """
            ).fetchall()
            for row in rows:
                updated_at = _parse_iso(str(row["updated_at"])) if str(row["updated_at"]).strip() else None
                is_partial_row = bool(row["is_partial"])
                should_delete = False
                if is_partial_row and partial_cutoff is not None:
                    should_delete = updated_at is None or updated_at < partial_cutoff
                elif (not is_partial_row) and ready_cutoff is not None:
                    should_delete = updated_at is None or updated_at < ready_cutoff
                if not should_delete:
                    continue
                deleted_signatures.append(str(row["query_signature"]))
                storage_key = str(row["storage_key"] or "").strip()
                if storage_key:
                    deleted_storage_keys.add(storage_key)

            deleted_rows = 0
            if deleted_signatures:
                placeholders = ", ".join("?" for _ in deleted_signatures)
                cursor = connection.execute(
                    f"DELETE FROM query_snapshots WHERE query_signature IN ({placeholders})",
                    tuple(deleted_signatures),
                )
                deleted_rows = max(0, int(cursor.rowcount))

            remaining_rows = connection.execute(
                "SELECT storage_key FROM query_snapshots WHERE storage_key != ''"
            ).fetchall()

        deleted_files = 0
        for storage_key in deleted_storage_keys:
            snapshot_path = self.snapshot_dir / storage_key
            if snapshot_path.exists():
                snapshot_path.unlink()
                deleted_files += 1

        referenced_storage_keys = {
            str(row[0]).strip()
            for row in remaining_rows
            if str(row[0]).strip()
        }
        orphan_deleted = 0
        for snapshot_path in self.snapshot_dir.glob("*.json"):
            if snapshot_path.name in referenced_storage_keys:
                continue
            snapshot_path.unlink()
            orphan_deleted += 1

        return {
            "deleted_rows": deleted_rows,
            "deleted_files": deleted_files,
            "deleted_orphan_files": orphan_deleted,
        }

    def _storage_key_for(self, query_signature: str, *, is_partial: bool) -> str:
        digest = hashlib.sha256(query_signature.encode("utf-8")).hexdigest()
        suffix = ".partial.json" if is_partial else ".json"
        return f"{digest}{suffix}"

    def _initialize(self) -> None:
        ensure_directory(self.db_path.parent)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS query_snapshots (
                    query_signature TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'pending',
                    generated_at TEXT NOT NULL DEFAULT '',
                    fresh_until TEXT NOT NULL DEFAULT '',
                    storage_key TEXT NOT NULL DEFAULT '',
                    last_accessed_at TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT '',
                    error_message TEXT NOT NULL DEFAULT '',
                    is_partial INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.db_path, row_factory=sqlite3.Row)

    def _ensure_column(
        self,
        connection: sqlite3.Connection,
        *,
        table_name: str,
        column_name: str,
        definition: str,
    ) -> None:
        columns = {
            str(row[1])
            for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        if column_name in columns:
            return
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )

    def _row_to_snapshot_record(self, row: sqlite3.Row) -> SnapshotRecord:
        return SnapshotRecord(
            query_signature=str(row["query_signature"]),
            status=str(row["status"]),
            generated_at=str(row["generated_at"]),
            fresh_until=str(row["fresh_until"]),
            storage_key=str(row["storage_key"]),
            last_accessed_at=str(row["last_accessed_at"]),
            updated_at=str(row["updated_at"]),
            error_message=str(row["error_message"]),
            is_partial=bool(row["is_partial"]),
        )


class CrawlJobQueue:
    """Persist crawl jobs so multiple app instances can deduplicate refresh work."""

    def __init__(
        self,
        *,
        db_path: Path,
        lease_seconds: int,
    ) -> None:
        self.db_path = db_path
        self.lease_seconds = int(lease_seconds)
        self._initialize()

    def enqueue_crawl(
        self,
        query_signature: str,
        *,
        priority: int,
        max_attempts: int = 1,
        payload_json: str = "",
    ) -> CrawlJobRecord:
        """Enqueue a crawl unless the same query already has an active job."""
        now = now_iso()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._release_expired_leases(connection)
            existing = connection.execute(
                """
                SELECT * FROM crawl_jobs
                WHERE query_signature = ?
                  AND status IN ('pending', 'leased')
                ORDER BY id DESC
                LIMIT 1
                """,
                (query_signature,),
            ).fetchone()
            if existing is not None:
                connection.commit()
                return self._row_to_job_record(existing)

            cursor = connection.execute(
                """
                INSERT INTO crawl_jobs (
                    query_signature,
                    payload_json,
                    priority,
                    status,
                    attempt_count,
                    max_attempts,
                    lease_owner,
                    lease_expires_at,
                    next_retry_at,
                    created_at,
                    updated_at,
                    snapshot_ref,
                    error_message
                )
                VALUES (?, ?, ?, 'pending', 0, ?, '', '', '', ?, ?, '', '')
                """,
                (
                    query_signature,
                    payload_json,
                    int(priority),
                    max(1, int(max_attempts)),
                    now,
                    now,
                ),
            )
            job_id = int(cursor.lastrowid)
            row = connection.execute(
                "SELECT * FROM crawl_jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
            connection.commit()
            if row is None:
                raise RuntimeError("Failed to read back inserted crawl job")
            return self._row_to_job_record(row)

    def lease_job(self, worker_id: str) -> CrawlJobRecord | None:
        """Lease the next pending crawl job."""
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._release_expired_leases(connection)
            row = connection.execute(
                """
                SELECT * FROM crawl_jobs
                WHERE status = 'pending'
                  AND (next_retry_at = '' OR next_retry_at <= ?)
                ORDER BY priority DESC, created_at ASC, id ASC
                LIMIT 1
                """
                ,
                (now_iso(),),
            ).fetchone()
            if row is None:
                connection.commit()
                return None
            leased = self._mark_leased(connection, int(row["id"]), worker_id)
            connection.commit()
            return leased

    def lease_job_for_signature(
        self,
        query_signature: str,
        *,
        worker_id: str,
    ) -> CrawlJobRecord | None:
        """Lease the pending job for one signature if another worker does not own it."""
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._release_expired_leases(connection)
            leased = connection.execute(
                """
                SELECT * FROM crawl_jobs
                WHERE query_signature = ?
                  AND status = 'leased'
                ORDER BY id DESC
                LIMIT 1
                """,
                (query_signature,),
            ).fetchone()
            if leased is not None:
                record = self._row_to_job_record(leased)
                if record.lease_owner == worker_id or not record.lease_active():
                    leased_record = self._mark_leased(connection, record.id, worker_id)
                    connection.commit()
                    return leased_record
                connection.commit()
                return None

            pending = connection.execute(
                """
                SELECT * FROM crawl_jobs
                WHERE query_signature = ?
                  AND status = 'pending'
                  AND (next_retry_at = '' OR next_retry_at <= ?)
                ORDER BY priority DESC, created_at ASC, id ASC
                LIMIT 1
                """,
                (query_signature, now_iso()),
            ).fetchone()
            if pending is None:
                connection.commit()
                return None
            leased_record = self._mark_leased(connection, int(pending["id"]), worker_id)
            connection.commit()
            return leased_record

    def get_job(self, job_id: int) -> CrawlJobRecord | None:
        """Return one job by id."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM crawl_jobs WHERE id = ?",
                (int(job_id),),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_job_record(row)

    def get_active_job_for_signature(self, query_signature: str) -> CrawlJobRecord | None:
        """Return the most recent job for a query signature."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM crawl_jobs
                WHERE query_signature = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (query_signature,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_job_record(row)

    def list_jobs(
        self,
        *,
        limit: int = 20,
        statuses: list[str] | None = None,
    ) -> list[CrawlJobRecord]:
        """Return recent jobs, optionally filtered by status."""
        query = "SELECT * FROM crawl_jobs"
        params: list[Any] = []
        if statuses:
            placeholders = ", ".join("?" for _ in statuses)
            query += f" WHERE status IN ({placeholders})"
            params.extend([str(status) for status in statuses])
        query += " ORDER BY updated_at DESC, id DESC LIMIT ?"
        params.append(max(1, int(limit)))
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._row_to_job_record(row) for row in rows]

    def count_jobs(self, *, status: str | None = None) -> int:
        """Count jobs, optionally filtered by one status."""
        query = "SELECT COUNT(*) FROM crawl_jobs"
        params: list[Any] = []
        if status is not None:
            query += " WHERE status = ?"
            params.append(str(status))
        with self._connect() as connection:
            row = connection.execute(query, tuple(params)).fetchone()
        return int(row[0]) if row else 0

    def prune_jobs(self, *, retention_days: int) -> int:
        """Delete terminal jobs older than the configured retention window."""
        if int(retention_days) <= 0:
            return 0
        cutoff = (datetime.now() - timedelta(days=int(retention_days))).isoformat(
            timespec="seconds"
        )
        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM crawl_jobs
                WHERE status IN ('completed', 'failed')
                  AND updated_at != ''
                  AND updated_at < ?
                """,
                (cutoff,),
            )
        return max(0, int(cursor.rowcount))

    def record_attempt_failure(
        self,
        job_id: int,
        error: str,
        *,
        allow_retry: bool,
        retry_backoff_seconds: int,
    ) -> CrawlJobRecord:
        """Persist one failed attempt, scheduling one retry when policy allows it."""
        job = self.get_job(job_id)
        if job is None:
            raise RuntimeError(f"Failed to find crawl job #{job_id} for failure handling")

        now = now_iso()
        with self._connect() as connection:
            if allow_retry and int(job.attempt_count) < int(job.max_attempts):
                next_retry_at = _future_iso(max(0, int(retry_backoff_seconds)))
                connection.execute(
                    """
                    UPDATE crawl_jobs
                    SET status = 'pending',
                        lease_owner = '',
                        lease_expires_at = '',
                        next_retry_at = ?,
                        error_message = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        next_retry_at,
                        str(error),
                        now,
                        int(job_id),
                    ),
                )
            else:
                connection.execute(
                    """
                    UPDATE crawl_jobs
                    SET status = 'failed',
                        lease_owner = '',
                        lease_expires_at = '',
                        next_retry_at = '',
                        error_message = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        str(error),
                        now,
                        int(job_id),
                    ),
                )
        updated_job = self.get_job(job_id)
        if updated_job is None:
            raise RuntimeError(f"Failed to read back crawl job #{job_id} after failure handling")
        return updated_job

    def complete_job(self, job_id: int, snapshot_ref: str) -> None:
        """Mark a leased crawl job completed."""
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE crawl_jobs
                SET status = 'completed',
                    lease_owner = '',
                    lease_expires_at = '',
                    next_retry_at = '',
                    snapshot_ref = ?,
                    error_message = '',
                    updated_at = ?
                WHERE id = ?
                """,
                (snapshot_ref, now_iso(), int(job_id)),
            )

    def fail_job(self, job_id: int, error: str) -> None:
        """Mark a leased crawl job failed."""
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE crawl_jobs
                SET status = 'failed',
                    lease_owner = '',
                    lease_expires_at = '',
                    next_retry_at = '',
                    error_message = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (str(error), now_iso(), int(job_id)),
            )

    def _initialize(self) -> None:
        ensure_directory(self.db_path.parent)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS crawl_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_signature TEXT NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '',
                    priority INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'pending',
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 1,
                    lease_owner TEXT NOT NULL DEFAULT '',
                    lease_expires_at TEXT NOT NULL DEFAULT '',
                    next_retry_at TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT '',
                    snapshot_ref TEXT NOT NULL DEFAULT '',
                    error_message TEXT NOT NULL DEFAULT ''
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_crawl_jobs_signature_status
                ON crawl_jobs(query_signature, status, id DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_crawl_jobs_pending_order
                ON crawl_jobs(status, priority DESC, created_at ASC, id ASC)
                """
            )
            self._ensure_column(
                connection,
                table_name="crawl_jobs",
                column_name="attempt_count",
                definition="INTEGER NOT NULL DEFAULT 0",
            )
            self._ensure_column(
                connection,
                table_name="crawl_jobs",
                column_name="max_attempts",
                definition="INTEGER NOT NULL DEFAULT 1",
            )
            self._ensure_column(
                connection,
                table_name="crawl_jobs",
                column_name="next_retry_at",
                definition="TEXT NOT NULL DEFAULT ''",
            )

    def _connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.db_path, row_factory=sqlite3.Row)

    def _ensure_column(
        self,
        connection: sqlite3.Connection,
        *,
        table_name: str,
        column_name: str,
        definition: str,
    ) -> None:
        columns = {
            str(row[1])
            for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        if column_name in columns:
            return
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )

    def _release_expired_leases(self, connection: sqlite3.Connection) -> None:
        now = now_iso()
        connection.execute(
            """
            UPDATE crawl_jobs
            SET status = 'pending',
                lease_owner = '',
                lease_expires_at = '',
                next_retry_at = '',
                updated_at = ?
            WHERE status = 'leased'
              AND lease_expires_at != ''
              AND lease_expires_at < ?
            """,
            (now, now),
        )

    def _mark_leased(
        self,
        connection: sqlite3.Connection,
        job_id: int,
        worker_id: str,
    ) -> CrawlJobRecord:
        lease_expires_at = _future_iso(self.lease_seconds)
        updated_at = now_iso()
        connection.execute(
            """
            UPDATE crawl_jobs
            SET status = 'leased',
                attempt_count = attempt_count + 1,
                lease_owner = ?,
                lease_expires_at = ?,
                next_retry_at = '',
                updated_at = ?
            WHERE id = ?
            """,
            (worker_id, lease_expires_at, updated_at, int(job_id)),
        )
        row = connection.execute(
            "SELECT * FROM crawl_jobs WHERE id = ?",
            (int(job_id),),
        ).fetchone()
        if row is None:
            raise RuntimeError("Failed to read leased crawl job")
        return self._row_to_job_record(row)

    def _row_to_job_record(self, row: sqlite3.Row) -> CrawlJobRecord:
        return CrawlJobRecord(
            id=int(row["id"]),
            query_signature=str(row["query_signature"]),
            payload_json=str(row["payload_json"]),
            priority=int(row["priority"]),
            status=str(row["status"]),
            attempt_count=int(row["attempt_count"]),
            max_attempts=int(row["max_attempts"]),
            lease_owner=str(row["lease_owner"]),
            lease_expires_at=str(row["lease_expires_at"]),
            next_retry_at=str(row["next_retry_at"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            snapshot_ref=str(row["snapshot_ref"]),
            error_message=str(row["error_message"]),
        )


class RuntimeSignalStore:
    """Persist recent scheduler/worker heartbeats for operations monitoring."""

    def __init__(self, *, db_path: Path) -> None:
        self.db_path = db_path
        self._initialize()

    def put_signal(
        self,
        *,
        component_kind: str,
        component_id: str,
        status: str,
        message: str = "",
        payload: dict[str, Any] | None = None,
    ) -> RuntimeSignalRecord:
        now = now_iso()
        cleaned_kind = str(component_kind).strip() or "unknown"
        cleaned_id = str(component_id).strip() or "anonymous"
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO runtime_signals (
                    component_kind,
                    component_id,
                    status,
                    message,
                    payload_json,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(component_kind, component_id) DO UPDATE SET
                    status = excluded.status,
                    message = excluded.message,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (
                    cleaned_kind,
                    cleaned_id,
                    str(status).strip() or "unknown",
                    str(message).strip(),
                    json.dumps(payload or {}, ensure_ascii=False),
                    now,
                    now,
                ),
            )
            row = connection.execute(
                """
                SELECT *
                FROM runtime_signals
                WHERE component_kind = ? AND component_id = ?
                """,
                (cleaned_kind, cleaned_id),
            ).fetchone()
        if row is None:
            raise RuntimeError("Failed to read runtime signal after upsert")
        return self._row_to_signal_record(row)

    def list_signals(
        self,
        *,
        component_kind: str | None = None,
        limit: int = 20,
    ) -> list[RuntimeSignalRecord]:
        query = "SELECT * FROM runtime_signals"
        params: list[Any] = []
        if component_kind is not None:
            query += " WHERE component_kind = ?"
            params.append(str(component_kind))
        query += " ORDER BY updated_at DESC, component_kind ASC, component_id ASC LIMIT ?"
        params.append(max(1, int(limit)))
        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [self._row_to_signal_record(row) for row in rows]

    def prune_signals(self, *, retention_days: int) -> int:
        """Delete signals older than the configured retention window."""
        if int(retention_days) <= 0:
            return 0
        cutoff = (datetime.now() - timedelta(days=int(retention_days))).isoformat(
            timespec="seconds"
        )
        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM runtime_signals
                WHERE updated_at != ''
                  AND updated_at < ?
                """,
                (cutoff,),
            )
        return max(0, int(cursor.rowcount))

    def _initialize(self) -> None:
        ensure_directory(self.db_path.parent)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_signals (
                    component_kind TEXT NOT NULL,
                    component_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT '',
                    message TEXT NOT NULL DEFAULT '',
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (component_kind, component_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_runtime_signals_updated_at
                ON runtime_signals(updated_at DESC)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return connect_sqlite(self.db_path, row_factory=sqlite3.Row)

    def _row_to_signal_record(self, row: sqlite3.Row) -> RuntimeSignalRecord:
        return RuntimeSignalRecord(
            component_kind=str(row["component_kind"]),
            component_id=str(row["component_id"]),
            status=str(row["status"]),
            message=str(row["message"]),
            payload_json=str(row["payload_json"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
