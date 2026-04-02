from __future__ import annotations

import sqlite3
from pathlib import Path

from ..models import FavoriteJob, JobListing
from .auth import GUEST_USER_ID
from .common import now_iso


class FavoriteRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def toggle_favorite(
        self,
        job: JobListing,
        *,
        user_id: int = GUEST_USER_ID,
        saved_search_id: int | None = None,
        saved_search_name: str = "",
    ) -> bool:
        with sqlite3.connect(self.db_path) as connection:
            existing = connection.execute(
                "SELECT id FROM favorite_jobs WHERE user_id = ? AND job_url = ?",
                (int(user_id), job.url),
            ).fetchone()
            if existing:
                connection.execute(
                    "DELETE FROM favorite_jobs WHERE user_id = ? AND job_url = ?",
                    (int(user_id), job.url),
                )
                connection.commit()
                return False

            connection.execute(
                """
                INSERT INTO favorite_jobs (
                    user_id,
                    saved_at,
                    job_url,
                    title,
                    company,
                    source,
                    saved_search_id,
                    saved_search_name,
                    matched_role,
                    location,
                    salary,
                    application_status,
                    application_date,
                    interview_date,
                    interview_notes,
                    notes,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(user_id),
                    now_iso(),
                    job.url,
                    job.title,
                    job.company,
                    job.source,
                    int(saved_search_id or 0),
                    saved_search_name.strip(),
                    job.matched_role,
                    job.location,
                    job.salary,
                    "未投遞",
                    "",
                    "",
                    "",
                    "",
                    now_iso(),
                ),
            )
            connection.commit()
            return True

    def is_favorite(self, job_url: str, *, user_id: int = GUEST_USER_ID) -> bool:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM favorite_jobs WHERE user_id = ? AND job_url = ? LIMIT 1",
                (int(user_id), job_url),
            ).fetchone()
        return bool(row)

    def list_favorites(self, *, user_id: int = GUEST_USER_ID) -> list[FavoriteJob]:
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    saved_at,
                    job_url,
                    title,
                    company,
                    source,
                    saved_search_id,
                    saved_search_name,
                    matched_role,
                    location,
                    salary,
                    application_status,
                    application_date,
                    interview_date,
                    interview_notes,
                    notes,
                    updated_at
                FROM favorite_jobs
                WHERE user_id = ?
                ORDER BY updated_at DESC, saved_at DESC, id DESC
                """,
                (int(user_id),),
            ).fetchall()
        return [
            FavoriteJob(
                id=int(row[0]),
                saved_at=str(row[1]),
                job_url=str(row[2]),
                title=str(row[3]),
                company=str(row[4]),
                source=str(row[5]),
                saved_search_id=int(row[6] or 0),
                saved_search_name=str(row[7]),
                matched_role=str(row[8]),
                location=str(row[9]),
                salary=str(row[10]),
                application_status=str(row[11]),
                application_date=str(row[12] or ""),
                interview_date=str(row[13] or ""),
                interview_notes=str(row[14] or ""),
                notes=str(row[15]),
                updated_at=str(row[16]),
            )
            for row in rows
        ]

    def list_favorites_for_search(
        self, search_id: int, *, user_id: int = GUEST_USER_ID
    ) -> list[FavoriteJob]:
        return [
            item
            for item in self.list_favorites(user_id=user_id)
            if int(item.saved_search_id or 0) == int(search_id)
        ]

    def update_favorite(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        job_url: str,
        application_status: str,
        notes: str,
        application_date: str = "",
        interview_date: str = "",
        interview_notes: str = "",
    ) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                UPDATE favorite_jobs
                SET application_status = ?, application_date = ?, interview_date = ?,
                    interview_notes = ?, notes = ?, updated_at = ?
                WHERE user_id = ? AND job_url = ?
                """,
                (
                    application_status.strip() or "未投遞",
                    application_date.strip(),
                    interview_date.strip(),
                    interview_notes.strip(),
                    notes.strip(),
                    now_iso(),
                    int(user_id),
                    job_url,
                ),
            )
            connection.commit()

    def delete_favorite(self, job_url: str, *, user_id: int = GUEST_USER_ID) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "DELETE FROM favorite_jobs WHERE user_id = ? AND job_url = ?",
                (int(user_id), job_url),
            )
            connection.commit()
