from __future__ import annotations

import sqlite3
from pathlib import Path

from ..utils import ensure_directory
from .auth import GUEST_EMAIL, GUEST_USER_ID, hash_password
from .common import now_iso


class ProductStoreDatabase:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        ensure_directory(self.db_path.parent)
        with sqlite3.connect(self.db_path) as connection:
            self._initialize_users(connection)
            self._initialize_password_reset_tokens(connection)
            self._initialize_app_metrics(connection)
            self._initialize_user_resume_profiles(connection)
            self._migrate_saved_searches(connection)
            self._migrate_favorite_jobs(connection)
            self._migrate_job_notifications(connection)
            self._migrate_notification_preferences(connection)
            connection.commit()

    def _initialize_users(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL DEFAULT '',
                password_salt TEXT NOT NULL DEFAULT '',
                password_hash TEXT NOT NULL DEFAULT '',
                is_guest INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_login_at TEXT NOT NULL DEFAULT ''
            )
            """
        )
        now = now_iso()
        guest_salt = "guest-user"
        guest_hash = hash_password("guest-user", guest_salt)
        connection.execute(
            """
            INSERT INTO users (
                id,
                email,
                display_name,
                password_salt,
                password_hash,
                is_guest,
                created_at,
                updated_at,
                last_login_at
            )
            SELECT ?, ?, '訪客模式', ?, ?, 1, ?, ?, ''
            WHERE NOT EXISTS (SELECT 1 FROM users WHERE id = ?)
            """,
            (
                GUEST_USER_ID,
                GUEST_EMAIL,
                guest_salt,
                guest_hash,
                now,
                now,
                GUEST_USER_ID,
            ),
        )

    def _initialize_user_resume_profiles(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_resume_profiles (
                user_id INTEGER PRIMARY KEY,
                source_name TEXT NOT NULL DEFAULT '',
                profile_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL
            )
            """
        )

    def _initialize_password_reset_tokens(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reset_code TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT '',
                expires_at TEXT NOT NULL DEFAULT '',
                consumed_at TEXT NOT NULL DEFAULT ''
            )
            """
        )

    def _initialize_app_metrics(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_metrics (
                metric_key TEXT PRIMARY KEY,
                metric_value INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            INSERT INTO app_metrics (metric_key, metric_value, updated_at)
            SELECT 'total_visits', 0, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM app_metrics WHERE metric_key = 'total_visits'
            )
            """,
            (now_iso(),),
        )

    def _migrate_saved_searches(self, connection: sqlite3.Connection) -> None:
        if not self._table_exists(connection, "saved_searches"):
            self._create_saved_searches_table(connection)
            return

        columns = self._table_columns(connection, "saved_searches")
        if "user_id" in columns:
            return

        connection.execute("ALTER TABLE saved_searches RENAME TO saved_searches_legacy")
        self._create_saved_searches_table(connection)
        connection.execute(
            """
            INSERT INTO saved_searches (
                id,
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
            )
            SELECT
                id,
                ?,
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
            FROM saved_searches_legacy
            """,
            (GUEST_USER_ID,),
        )
        connection.execute("DROP TABLE saved_searches_legacy")

    def _migrate_favorite_jobs(self, connection: sqlite3.Connection) -> None:
        if not self._table_exists(connection, "favorite_jobs"):
            self._create_favorite_jobs_table(connection)
            return

        columns = self._table_columns(connection, "favorite_jobs")
        needs_rebuild = (
            "user_id" not in columns
            or "application_date" not in columns
            or "interview_date" not in columns
            or "interview_notes" not in columns
        )
        if not needs_rebuild:
            return

        connection.execute("ALTER TABLE favorite_jobs RENAME TO favorite_jobs_legacy")
        self._create_favorite_jobs_table(connection)
        legacy_columns = self._table_columns(connection, "favorite_jobs_legacy")
        application_date_expr = "application_date" if "application_date" in legacy_columns else "''"
        interview_date_expr = "interview_date" if "interview_date" in legacy_columns else "''"
        interview_notes_expr = "interview_notes" if "interview_notes" in legacy_columns else "''"
        connection.execute(
            f"""
            INSERT INTO favorite_jobs (
                id,
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
            )
            SELECT
                id,
                ?,
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
                {application_date_expr},
                {interview_date_expr},
                {interview_notes_expr},
                notes,
                updated_at
            FROM favorite_jobs_legacy
            """,
            (GUEST_USER_ID,),
        )
        connection.execute("DROP TABLE favorite_jobs_legacy")

    def _migrate_job_notifications(self, connection: sqlite3.Connection) -> None:
        if not self._table_exists(connection, "job_notifications"):
            self._create_job_notifications_table(connection)
            return

        columns = self._table_columns(connection, "job_notifications")
        if "user_id" in columns:
            return

        connection.execute("ALTER TABLE job_notifications RENAME TO job_notifications_legacy")
        self._create_job_notifications_table(connection)
        connection.execute(
            """
            INSERT INTO job_notifications (
                id,
                user_id,
                saved_search_id,
                saved_search_name,
                created_at,
                new_jobs_json,
                is_read,
                email_sent,
                line_sent,
                delivery_notes
            )
            SELECT
                id,
                ?,
                saved_search_id,
                saved_search_name,
                created_at,
                new_jobs_json,
                is_read,
                email_sent,
                line_sent,
                delivery_notes
            FROM job_notifications_legacy
            """,
            (GUEST_USER_ID,),
        )
        connection.execute("DROP TABLE job_notifications_legacy")

    def _migrate_notification_preferences(self, connection: sqlite3.Connection) -> None:
        if not self._table_exists(connection, "notification_preferences"):
            self._create_notification_preferences_table(connection)
            self._ensure_default_notification_preferences(connection, GUEST_USER_ID)
            return

        columns = self._table_columns(connection, "notification_preferences")
        if "user_id" not in columns:
            connection.execute(
                "ALTER TABLE notification_preferences RENAME TO notification_preferences_legacy"
            )
            self._create_notification_preferences_table(connection)
            connection.execute(
                """
                INSERT INTO notification_preferences (
                    user_id,
                    site_enabled,
                    email_enabled,
                    line_enabled,
                    email_recipients,
                    line_target,
                    line_bind_code,
                    line_bind_requested_at,
                    line_bind_expires_at,
                    line_bound_at,
                    min_relevance_score,
                    max_jobs_per_alert,
                    frequency
                )
                SELECT
                    ?,
                    site_enabled,
                    email_enabled,
                    line_enabled,
                    email_recipients,
                    line_target,
                    line_bind_code,
                    line_bind_requested_at,
                    line_bind_expires_at,
                    line_bound_at,
                    min_relevance_score,
                    max_jobs_per_alert,
                    frequency
                FROM notification_preferences_legacy
                LIMIT 1
                """,
                (GUEST_USER_ID,),
            )
            connection.execute("DROP TABLE notification_preferences_legacy")

        self._ensure_default_notification_preferences(connection, GUEST_USER_ID)

    def _create_saved_searches_table(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE saved_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                name TEXT NOT NULL,
                rows_json TEXT NOT NULL DEFAULT '[]',
                custom_queries_text TEXT NOT NULL DEFAULT '',
                crawl_preset_label TEXT NOT NULL DEFAULT '快速',
                signature TEXT NOT NULL DEFAULT '',
                known_job_urls TEXT NOT NULL DEFAULT '[]',
                last_run_at TEXT NOT NULL DEFAULT '',
                last_job_count INTEGER NOT NULL DEFAULT 0,
                last_new_job_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, name)
            )
            """
        )

    def _create_favorite_jobs_table(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE favorite_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                saved_at TEXT NOT NULL,
                job_url TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                company TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                saved_search_id INTEGER NOT NULL DEFAULT 0,
                saved_search_name TEXT NOT NULL DEFAULT '',
                matched_role TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                salary TEXT NOT NULL DEFAULT '',
                application_status TEXT NOT NULL DEFAULT '未投遞',
                application_date TEXT NOT NULL DEFAULT '',
                interview_date TEXT NOT NULL DEFAULT '',
                interview_notes TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT '',
                UNIQUE(user_id, job_url)
            )
            """
        )

    def _create_job_notifications_table(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE job_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                saved_search_id INTEGER NOT NULL,
                saved_search_name TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                new_jobs_json TEXT NOT NULL DEFAULT '[]',
                is_read INTEGER NOT NULL DEFAULT 0,
                email_sent INTEGER NOT NULL DEFAULT 0,
                line_sent INTEGER NOT NULL DEFAULT 0,
                delivery_notes TEXT NOT NULL DEFAULT '[]'
            )
            """
        )

    def _create_notification_preferences_table(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE notification_preferences (
                user_id INTEGER PRIMARY KEY,
                site_enabled INTEGER NOT NULL DEFAULT 1,
                email_enabled INTEGER NOT NULL DEFAULT 0,
                line_enabled INTEGER NOT NULL DEFAULT 0,
                email_recipients TEXT NOT NULL DEFAULT '',
                line_target TEXT NOT NULL DEFAULT '',
                line_bind_code TEXT NOT NULL DEFAULT '',
                line_bind_requested_at TEXT NOT NULL DEFAULT '',
                line_bind_expires_at TEXT NOT NULL DEFAULT '',
                line_bound_at TEXT NOT NULL DEFAULT '',
                min_relevance_score REAL NOT NULL DEFAULT 20,
                max_jobs_per_alert INTEGER NOT NULL DEFAULT 8,
                frequency TEXT NOT NULL DEFAULT '即時'
            )
            """
        )

    def _ensure_default_notification_preferences(
        self, connection: sqlite3.Connection, user_id: int
    ) -> None:
        connection.execute(
            """
            INSERT INTO notification_preferences (
                user_id,
                site_enabled,
                email_enabled,
                line_enabled,
                min_relevance_score,
                max_jobs_per_alert,
                frequency
            )
            SELECT ?, 1, 0, 0, 20, 8, '即時'
            WHERE NOT EXISTS (
                SELECT 1 FROM notification_preferences WHERE user_id = ?
            )
            """,
            (user_id, user_id),
        )

    def _table_exists(self, connection: sqlite3.Connection, table_name: str) -> bool:
        row = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        return bool(row)

    def _table_columns(self, connection: sqlite3.Connection, table_name: str) -> set[str]:
        return {
            str(row[1])
            for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
