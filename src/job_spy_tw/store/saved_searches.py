"""Store-layer helpers for saved searches."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ..models import MarketSnapshot, SavedSearch
from ..sqlite_utils import connect_sqlite
from .auth import GUEST_USER_ID
from .common import build_signature, canonical_rows, job_summary, now_iso, row_to_saved_search


class SavedSearchRepository:
    MAX_SEEN_JOB_URLS = 5_000

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def build_signature(
        self,
        rows: list[dict[str, Any]],
        custom_queries_text: str,
        crawl_preset_label: str,
    ) -> str:
        return build_signature(rows, custom_queries_text, crawl_preset_label)

    def save_search(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        name: str,
        rows: list[dict[str, Any]],
        custom_queries_text: str,
        crawl_preset_label: str,
        snapshot: MarketSnapshot | None = None,
        search_id: int | None = None,
    ) -> int:
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("搜尋名稱不可為空。")
        created_at = now_iso()
        signature = self.build_signature(rows, custom_queries_text, crawl_preset_label)
        known_job_urls = self._normalize_job_urls(
            job.url for job in snapshot.jobs
        ) if snapshot is not None else []
        observed_at = snapshot.generated_at if snapshot is not None else created_at
        with connect_sqlite(self.db_path) as connection:
            if search_id is not None:
                cursor = connection.execute(
                    """
                    UPDATE saved_searches
                    SET name = ?, rows_json = ?, custom_queries_text = ?, crawl_preset_label = ?,
                        signature = ?, known_job_urls = ?, last_run_at = ?, last_job_count = ?,
                        last_new_job_count = ?, updated_at = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    (
                        cleaned_name,
                        json.dumps(canonical_rows(rows), ensure_ascii=False),
                        custom_queries_text.strip(),
                        crawl_preset_label.strip() or "快速",
                        signature,
                        "[]",
                        snapshot.generated_at if snapshot is not None else "",
                        len(snapshot.jobs) if snapshot is not None else 0,
                        0,
                        created_at,
                        int(search_id),
                        int(user_id),
                    ),
                )
                if cursor.rowcount:
                    self._replace_seen_job_urls(
                        connection,
                        int(search_id),
                        known_job_urls,
                        observed_at=observed_at,
                    )
                    connection.commit()
                    return int(search_id)

            existing = connection.execute(
                "SELECT id FROM saved_searches WHERE user_id = ? AND name = ?",
                (int(user_id), cleaned_name),
            ).fetchone()
            if existing:
                connection.execute(
                    """
                    UPDATE saved_searches
                    SET rows_json = ?, custom_queries_text = ?, crawl_preset_label = ?,
                        signature = ?, known_job_urls = ?, last_run_at = ?, last_job_count = ?,
                        last_new_job_count = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        json.dumps(canonical_rows(rows), ensure_ascii=False),
                        custom_queries_text.strip(),
                        crawl_preset_label.strip() or "快速",
                        signature,
                        "[]",
                        snapshot.generated_at if snapshot is not None else "",
                        len(snapshot.jobs) if snapshot is not None else 0,
                        0,
                        created_at,
                        int(existing[0]),
                    ),
                )
                self._replace_seen_job_urls(
                    connection,
                    int(existing[0]),
                    known_job_urls,
                    observed_at=observed_at,
                )
                connection.commit()
                return int(existing[0])

            cursor = connection.execute(
                """
                INSERT INTO saved_searches (
                    user_id,
                    name,
                    rows_json,
                    custom_queries_text,
                    crawl_preset_label,
                    signature,
                    known_job_urls,
                    last_run_at,
                    last_job_count,
                    last_new_job_count,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(user_id),
                    cleaned_name,
                    json.dumps(canonical_rows(rows), ensure_ascii=False),
                    custom_queries_text.strip(),
                    crawl_preset_label.strip() or "快速",
                    signature,
                    "[]",
                    snapshot.generated_at if snapshot is not None else "",
                    len(snapshot.jobs) if snapshot is not None else 0,
                    0,
                    created_at,
                    created_at,
                ),
            )
            saved_search_id = int(cursor.lastrowid)
            self._replace_seen_job_urls(
                connection,
                saved_search_id,
                known_job_urls,
                observed_at=observed_at,
            )
            connection.commit()
            return saved_search_id

    def list_saved_searches(self, *, user_id: int = GUEST_USER_ID) -> list[SavedSearch]:
        with connect_sqlite(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    rows_json,
                    custom_queries_text,
                    crawl_preset_label,
                    signature,
                    known_job_urls,
                    last_run_at,
                    last_job_count,
                    last_new_job_count,
                    created_at,
                    updated_at
                FROM saved_searches
                WHERE user_id = ?
                ORDER BY updated_at DESC, id DESC
                """,
                (int(user_id),),
            ).fetchall()
            known_job_urls_by_search = self._load_known_job_urls_by_search_ids(
                connection,
                [int(row[0]) for row in rows],
            )
        return [
            row_to_saved_search(
                row,
                known_job_urls=known_job_urls_by_search.get(int(row[0]), []),
            )
            for row in rows
        ]

    def list_saved_search_subscribers(
        self,
        *,
        signature: str,
    ) -> list[tuple[int, SavedSearch]]:
        cleaned_signature = signature.strip()
        if not cleaned_signature:
            return []
        with connect_sqlite(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    name,
                    rows_json,
                    custom_queries_text,
                    crawl_preset_label,
                    signature,
                    known_job_urls,
                    last_run_at,
                    last_job_count,
                    last_new_job_count,
                    created_at,
                    updated_at,
                    user_id
                FROM saved_searches
                WHERE signature = ?
                ORDER BY user_id ASC, updated_at DESC, id DESC
                """,
                (cleaned_signature,),
            ).fetchall()
            known_job_urls_by_search = self._load_known_job_urls_by_search_ids(
                connection,
                [int(row[0]) for row in rows],
            )
        return [
            (
                int(row[12]),
                row_to_saved_search(
                    row,
                    known_job_urls=known_job_urls_by_search.get(int(row[0]), []),
                ),
            )
            for row in rows
        ]

    def get_saved_search(
        self,
        search_id: int,
        *,
        user_id: int = GUEST_USER_ID,
    ) -> SavedSearch | None:
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    name,
                    rows_json,
                    custom_queries_text,
                    crawl_preset_label,
                    signature,
                    known_job_urls,
                    last_run_at,
                    last_job_count,
                    last_new_job_count,
                    created_at,
                    updated_at
                FROM saved_searches
                WHERE id = ? AND user_id = ?
                """,
                (int(search_id), int(user_id)),
            ).fetchone()
            known_job_urls = self._load_known_job_urls(connection, int(search_id)) if row else []
        return row_to_saved_search(row, known_job_urls=known_job_urls) if row else None

    def find_saved_search_by_signature(
        self,
        rows: list[dict[str, Any]],
        custom_queries_text: str,
        crawl_preset_label: str,
        *,
        user_id: int = GUEST_USER_ID,
    ) -> SavedSearch | None:
        signature = self.build_signature(rows, custom_queries_text, crawl_preset_label)
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    name,
                    rows_json,
                    custom_queries_text,
                    crawl_preset_label,
                    signature,
                    known_job_urls,
                    last_run_at,
                    last_job_count,
                    last_new_job_count,
                    created_at,
                    updated_at
                FROM saved_searches
                WHERE signature = ? AND user_id = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (signature, int(user_id)),
            ).fetchone()
            known_job_urls = self._load_known_job_urls(connection, int(row[0])) if row else []
        return row_to_saved_search(row, known_job_urls=known_job_urls) if row else None

    def sync_saved_search_results(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        search_id: int,
        rows: list[dict[str, Any]],
        custom_queries_text: str,
        crawl_preset_label: str,
        snapshot: MarketSnapshot,
        min_relevance_score: float = 0.0,
        max_jobs: int = 20,
        create_notification: bool = True,
    ) -> dict[str, Any]:
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    name,
                    rows_json,
                    custom_queries_text,
                    crawl_preset_label,
                    signature,
                    known_job_urls,
                    last_run_at,
                    last_job_count,
                    last_new_job_count,
                    created_at,
                    updated_at
                FROM saved_searches
                WHERE id = ? AND user_id = ?
                """,
                (int(search_id), int(user_id)),
            ).fetchone()
            if row is None:
                raise ValueError("找不到指定的搜尋條件。")
            existing_known_job_urls = self._load_known_job_urls(connection, int(search_id))
            saved_search = row_to_saved_search(
                row,
                known_job_urls=existing_known_job_urls,
            )
            current_urls = self._normalize_job_urls(job.url for job in snapshot.jobs)
            seen_urls = set(saved_search.known_job_urls)
            is_first_sync = not saved_search.known_job_urls
            new_jobs = [
                job_summary(job)
                for job in snapshot.jobs
                if job.url and job.url not in seen_urls
            ]
            filtered_new_jobs = [
                job
                for job in new_jobs
                if float(job.get("relevance_score", 0.0)) >= float(min_relevance_score)
            ]
            if max_jobs > 0:
                filtered_new_jobs = filtered_new_jobs[:max_jobs]
            merged_urls = self._merge_seen_job_urls(
                saved_search.known_job_urls,
                current_urls,
            )
            updated_at = now_iso()
            signature = self.build_signature(rows, custom_queries_text, crawl_preset_label)
            connection.execute(
                """
                UPDATE saved_searches
                    SET rows_json = ?, custom_queries_text = ?, crawl_preset_label = ?,
                        signature = ?, known_job_urls = ?, last_run_at = ?, last_job_count = ?,
                    last_new_job_count = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    json.dumps(canonical_rows(rows), ensure_ascii=False),
                    custom_queries_text.strip(),
                    crawl_preset_label.strip() or "快速",
                    signature,
                    "[]",
                    snapshot.generated_at,
                    len(snapshot.jobs),
                    0 if is_first_sync else len(filtered_new_jobs),
                    updated_at,
                    search_id,
                    int(user_id),
                ),
            )
            self._replace_seen_job_urls(
                connection,
                int(search_id),
                merged_urls,
                observed_at=snapshot.generated_at or updated_at,
            )
            notification_id = 0
            if filtered_new_jobs and not is_first_sync and create_notification:
                cursor = connection.execute(
                    """
                    INSERT INTO job_notifications (
                        user_id,
                        saved_search_id,
                        saved_search_name,
                        created_at,
                        new_jobs_json,
                        is_read,
                        email_sent,
                        line_sent,
                        delivery_notes
                    ) VALUES (?, ?, ?, ?, ?, 0, 0, 0, '[]')
                    """,
                    (
                        int(user_id),
                        search_id,
                        saved_search.name,
                        updated_at,
                        json.dumps(filtered_new_jobs[:20], ensure_ascii=False),
                    ),
                )
                notification_id = int(cursor.lastrowid)
            connection.commit()

        return {
            "search_id": search_id,
            "search_name": saved_search.name,
            "baseline_created": is_first_sync,
            "new_jobs": filtered_new_jobs,
            "notification_id": notification_id,
        }

    def delete_saved_search(self, search_id: int, *, user_id: int = GUEST_USER_ID) -> None:
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                "DELETE FROM job_notifications WHERE saved_search_id = ? AND user_id = ?",
                (int(search_id), int(user_id)),
            )
            connection.execute(
                "DELETE FROM saved_searches WHERE id = ? AND user_id = ?",
                (int(search_id), int(user_id)),
            )
            connection.commit()

    def _normalize_job_urls(self, urls: Any) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for raw_url in urls:
            job_url = str(raw_url or "").strip()
            if not job_url or job_url in seen:
                continue
            seen.add(job_url)
            normalized.append(job_url)
        return normalized[-self.MAX_SEEN_JOB_URLS :]

    def _merge_seen_job_urls(
        self,
        existing_urls: list[str],
        current_urls: list[str],
    ) -> list[str]:
        merged_urls = list(dict.fromkeys(existing_urls + current_urls))
        return merged_urls[-self.MAX_SEEN_JOB_URLS :]

    def _load_known_job_urls(self, connection: sqlite3.Connection, search_id: int) -> list[str]:
        return self._load_known_job_urls_by_search_ids(connection, [int(search_id)]).get(
            int(search_id),
            [],
        )

    def _load_known_job_urls_by_search_ids(
        self,
        connection: sqlite3.Connection,
        search_ids: list[int],
    ) -> dict[int, list[str]]:
        normalized_search_ids = [int(search_id) for search_id in search_ids]
        if not normalized_search_ids:
            return {}
        placeholders = ", ".join("?" for _ in normalized_search_ids)
        rows = connection.execute(
            f"""
            SELECT search_id, job_url
            FROM saved_search_seen_jobs
            WHERE search_id IN ({placeholders})
            ORDER BY search_id ASC, ordinal ASC
            """,
            normalized_search_ids,
        ).fetchall()
        grouped: dict[int, list[str]] = {search_id: [] for search_id in normalized_search_ids}
        for row in rows:
            grouped.setdefault(int(row[0]), []).append(str(row[1]))
        return grouped

    def _replace_seen_job_urls(
        self,
        connection: sqlite3.Connection,
        search_id: int,
        job_urls: list[str],
        *,
        observed_at: str,
    ) -> None:
        connection.execute(
            "DELETE FROM saved_search_seen_jobs WHERE search_id = ?",
            (int(search_id),),
        )
        normalized_job_urls = self._normalize_job_urls(job_urls)
        if not normalized_job_urls:
            return
        connection.executemany(
            """
            INSERT INTO saved_search_seen_jobs (
                search_id,
                job_url,
                ordinal,
                first_seen_at,
                last_seen_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    int(search_id),
                    job_url,
                    ordinal,
                    observed_at,
                    observed_at,
                )
                for ordinal, job_url in enumerate(normalized_job_urls, start=1)
            ],
        )
