"""Store-layer helpers for feedback events."""

from __future__ import annotations

import json
from typing import Any

from ..sqlite_utils import connect_sqlite
from .common import now_iso


class FeedbackRepository:
    def __init__(self, db_path) -> None:
        self.db_path = db_path

    def record_feedback(
        self,
        *,
        user_id: int,
        target_type: str,
        target_id: str,
        rating: int,
        tags: list[str] | None = None,
        comment: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> int:
        created_at = now_iso()
        payload_tags = tags or []
        payload_metadata = metadata or {}
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO feedback_events (
                    user_id,
                    target_type,
                    target_id,
                    rating,
                    tags_json,
                    comment,
                    metadata_json,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, target_type, target_id)
                DO UPDATE SET
                    rating = excluded.rating,
                    tags_json = excluded.tags_json,
                    comment = excluded.comment,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    user_id,
                    target_type,
                    target_id,
                    int(rating),
                    json.dumps(payload_tags, ensure_ascii=False),
                    str(comment),
                    json.dumps(payload_metadata, ensure_ascii=False),
                    created_at,
                    created_at,
                ),
            )
            row = connection.execute(
                """
                SELECT id FROM feedback_events
                WHERE user_id = ? AND target_type = ? AND target_id = ?
                """,
                (user_id, target_type, target_id),
            ).fetchone()
            connection.commit()
        return int(row[0]) if row else 0

    def list_recent_feedback(
        self,
        *,
        user_id: int,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        with connect_sqlite(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    target_type,
                    target_id,
                    rating,
                    tags_json,
                    comment,
                    metadata_json,
                    created_at,
                    updated_at
                FROM feedback_events
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, int(limit)),
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            result.append(
                {
                    "id": int(row[0]),
                    "target_type": str(row[1]),
                    "target_id": str(row[2]),
                    "rating": int(row[3]),
                    "tags": json.loads(row[4] or "[]"),
                    "comment": str(row[5] or ""),
                    "metadata": json.loads(row[6] or "{}"),
                    "created_at": str(row[7]),
                    "updated_at": str(row[8] or ""),
                }
            )
        return result
