"""Store-layer helpers for notifications."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from ..models import JobNotification, NotificationPreference
from ..sqlite_utils import connect_sqlite
from .auth import GUEST_USER_ID
from .common import generate_line_bind_code, now_iso


class NotificationRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def get_notification_preferences(
        self, *, user_id: int = GUEST_USER_ID
    ) -> NotificationPreference:
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT
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
                FROM notification_preferences
                WHERE user_id = ?
                """,
                (int(user_id),),
            ).fetchone()
        if not row:
            return NotificationPreference()
        return NotificationPreference(
            site_enabled=bool(row[0]),
            email_enabled=bool(row[1]),
            line_enabled=bool(row[2]),
            email_recipients=str(row[3] or ""),
            line_target=str(row[4] or ""),
            line_bind_code=str(row[5] or ""),
            line_bind_requested_at=str(row[6] or ""),
            line_bind_expires_at=str(row[7] or ""),
            line_bound_at=str(row[8] or ""),
            min_relevance_score=float(row[9]),
            max_jobs_per_alert=int(row[10]),
            frequency=str(row[11]),
        )

    def save_notification_preferences(
        self,
        preferences: NotificationPreference,
        *,
        user_id: int = GUEST_USER_ID,
    ) -> None:
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO notification_preferences (
                    user_id,
                    site_enabled,
                    email_enabled,
                    line_enabled,
                    email_recipients,
                    line_target,
                    min_relevance_score,
                    max_jobs_per_alert,
                    frequency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    site_enabled = excluded.site_enabled,
                    email_enabled = excluded.email_enabled,
                    line_enabled = excluded.line_enabled,
                    email_recipients = excluded.email_recipients,
                    line_target = excluded.line_target,
                    min_relevance_score = excluded.min_relevance_score,
                    max_jobs_per_alert = excluded.max_jobs_per_alert,
                    frequency = excluded.frequency
                """,
                (
                    int(user_id),
                    1 if preferences.site_enabled else 0,
                    1 if preferences.email_enabled else 0,
                    1 if preferences.line_enabled else 0,
                    preferences.email_recipients.strip(),
                    preferences.line_target.strip(),
                    float(preferences.min_relevance_score),
                    int(preferences.max_jobs_per_alert),
                    preferences.frequency,
                ),
            )
            connection.commit()

    def issue_line_bind_code(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        ttl_minutes: int = 15,
    ) -> NotificationPreference:
        code = generate_line_bind_code()
        now = now_iso()
        expires_at = (datetime.now() + timedelta(minutes=ttl_minutes)).isoformat(
            timespec="seconds"
        )
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO notification_preferences (
                    user_id,
                    line_bind_code,
                    line_bind_requested_at,
                    line_bind_expires_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    line_bind_code = excluded.line_bind_code,
                    line_bind_requested_at = excluded.line_bind_requested_at,
                    line_bind_expires_at = excluded.line_bind_expires_at
                """,
                (
                    int(user_id),
                    code,
                    now,
                    expires_at,
                ),
            )
            connection.commit()
        return self.get_notification_preferences(user_id=user_id)

    def consume_line_bind_code(
        self,
        bind_code: str,
        user_id_text: str,
        *,
        user_id: int | None = None,
    ) -> dict[str, str | bool]:
        cleaned_code = bind_code.strip().upper()
        cleaned_user_id = user_id_text.strip()
        if not cleaned_code:
            return {"ok": False, "message": "綁定碼不可為空。"}
        if not cleaned_user_id:
            return {"ok": False, "message": "找不到可綁定的 LINE userId。"}

        with connect_sqlite(self.db_path) as connection:
            if user_id is None:
                row = connection.execute(
                    """
                    SELECT user_id, line_bind_expires_at
                    FROM notification_preferences
                    WHERE UPPER(TRIM(line_bind_code)) = ?
                    LIMIT 1
                    """,
                    (cleaned_code,),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT user_id, line_bind_expires_at
                    FROM notification_preferences
                    WHERE user_id = ? AND UPPER(TRIM(line_bind_code)) = ?
                    LIMIT 1
                    """,
                    (int(user_id), cleaned_code),
                ).fetchone()

            if row is None:
                return {"ok": False, "message": "目前沒有待綁定的 LINE 綁定碼。"}

            target_user_id = int(row[0])
            expires_at_text = str(row[1] or "")
            if expires_at_text:
                expires_at = datetime.fromisoformat(expires_at_text)
                if expires_at < datetime.now():
                    connection.execute(
                        """
                        UPDATE notification_preferences
                        SET line_bind_code = '', line_bind_requested_at = '', line_bind_expires_at = ''
                        WHERE user_id = ?
                        """,
                        (target_user_id,),
                    )
                    connection.commit()
                    return {"ok": False, "message": "綁定碼已過期，請回到網站重新產生。"}

            connection.execute(
                """
                UPDATE notification_preferences
                SET line_target = ?, line_bind_code = '', line_bind_requested_at = '',
                    line_bind_expires_at = '', line_bound_at = ?
                WHERE user_id = ?
                """,
                (
                    cleaned_user_id,
                    now_iso(),
                    target_user_id,
                ),
            )
            connection.commit()
        return {"ok": True, "message": "LINE 綁定成功。"}

    def clear_line_target(self, *, user_id: int = GUEST_USER_ID) -> None:
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                UPDATE notification_preferences
                SET line_target = '', line_bound_at = ''
                WHERE user_id = ?
                """,
                (int(user_id),),
            )
            connection.commit()

    def update_notification_delivery(
        self,
        notification_id: int,
        *,
        user_id: int = GUEST_USER_ID,
        email_sent: bool,
        line_sent: bool,
        delivery_notes: list[str],
    ) -> None:
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                UPDATE job_notifications
                SET email_sent = ?, line_sent = ?, delivery_notes = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    1 if email_sent else 0,
                    1 if line_sent else 0,
                    json.dumps(delivery_notes, ensure_ascii=False),
                    notification_id,
                    int(user_id),
                ),
            )
            connection.commit()

    def list_notifications(
        self, limit: int = 20, *, user_id: int = GUEST_USER_ID
    ) -> list[JobNotification]:
        with connect_sqlite(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    saved_search_id,
                    saved_search_name,
                    created_at,
                    new_jobs_json,
                    is_read,
                    email_sent,
                    line_sent,
                    delivery_notes
                FROM job_notifications
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (int(user_id), limit),
            ).fetchall()
        notifications: list[JobNotification] = []
        for row in rows:
            notifications.append(
                JobNotification(
                    id=int(row[0]),
                    saved_search_id=int(row[1]),
                    saved_search_name=str(row[2]),
                    created_at=str(row[3]),
                    new_jobs=json.loads(row[4] or "[]"),
                    is_read=bool(row[5]),
                    email_sent=bool(row[6]),
                    line_sent=bool(row[7]),
                    delivery_notes=json.loads(row[8] or "[]"),
                )
            )
        return notifications

    def unread_notification_count(self, *, user_id: int = GUEST_USER_ID) -> int:
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM job_notifications WHERE user_id = ? AND is_read = 0",
                (int(user_id),),
            ).fetchone()
        return int(row[0]) if row else 0

    def mark_all_notifications_read(self, *, user_id: int = GUEST_USER_ID) -> None:
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                "UPDATE job_notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
                (int(user_id),),
            )
            connection.commit()
