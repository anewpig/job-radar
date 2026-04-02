from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ..models import MarketSnapshot, SavedSearch
from .auth import GUEST_USER_ID
from .common import build_signature, canonical_rows, job_summary, now_iso, row_to_saved_search


class SavedSearchRepository:
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
        known_job_urls = [job.url for job in snapshot.jobs] if snapshot is not None else []
        with sqlite3.connect(self.db_path) as connection:
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
                        json.dumps(known_job_urls, ensure_ascii=False),
                        snapshot.generated_at if snapshot is not None else "",
                        len(snapshot.jobs) if snapshot is not None else 0,
                        0,
                        created_at,
                        int(search_id),
                        int(user_id),
                    ),
                )
                if cursor.rowcount:
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
                        json.dumps(known_job_urls, ensure_ascii=False),
                        snapshot.generated_at if snapshot is not None else "",
                        len(snapshot.jobs) if snapshot is not None else 0,
                        0,
                        created_at,
                        int(existing[0]),
                    ),
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
                    json.dumps(known_job_urls, ensure_ascii=False),
                    snapshot.generated_at if snapshot is not None else "",
                    len(snapshot.jobs) if snapshot is not None else 0,
                    0,
                    created_at,
                    created_at,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def list_saved_searches(self, *, user_id: int = GUEST_USER_ID) -> list[SavedSearch]:
        with sqlite3.connect(self.db_path) as connection:
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
        return [row_to_saved_search(row) for row in rows]

    def get_saved_search(
        self,
        search_id: int,
        *,
        user_id: int = GUEST_USER_ID,
    ) -> SavedSearch | None:
        with sqlite3.connect(self.db_path) as connection:
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
        return row_to_saved_search(row) if row else None

    def find_saved_search_by_signature(
        self,
        rows: list[dict[str, Any]],
        custom_queries_text: str,
        crawl_preset_label: str,
        *,
        user_id: int = GUEST_USER_ID,
    ) -> SavedSearch | None:
        signature = self.build_signature(rows, custom_queries_text, crawl_preset_label)
        with sqlite3.connect(self.db_path) as connection:
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
        return row_to_saved_search(row) if row else None

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
        saved_search = self.get_saved_search(search_id, user_id=user_id)
        if saved_search is None:
            raise ValueError("找不到指定的搜尋條件。")

        current_urls = [job.url for job in snapshot.jobs if job.url]
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
        merged_urls = list(dict.fromkeys(saved_search.known_job_urls + current_urls))[-5000:]
        updated_at = now_iso()
        signature = self.build_signature(rows, custom_queries_text, crawl_preset_label)

        with sqlite3.connect(self.db_path) as connection:
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
                    json.dumps(merged_urls, ensure_ascii=False),
                    snapshot.generated_at,
                    len(snapshot.jobs),
                    0 if is_first_sync else len(filtered_new_jobs),
                    updated_at,
                    search_id,
                    int(user_id),
                ),
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
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "DELETE FROM job_notifications WHERE saved_search_id = ? AND user_id = ?",
                (int(search_id), int(user_id)),
            )
            connection.execute(
                "DELETE FROM saved_searches WHERE id = ? AND user_id = ?",
                (int(search_id), int(user_id)),
            )
            connection.commit()
