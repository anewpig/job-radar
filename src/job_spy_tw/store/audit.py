"""Store-layer helpers for audit logging."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..security import normalize_user_role
from ..sqlite_utils import connect_sqlite
from .auth import GUEST_USER_ID
from .common import now_iso


class AuditLogRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def record_event(
        self,
        *,
        event_type: str,
        status: str = "success",
        target_type: str = "",
        target_id: str = "",
        details: dict[str, Any] | None = None,
        user_id: int = GUEST_USER_ID,
        actor_role: str = "guest",
        trace_id: str = "",
    ) -> int:
        with connect_sqlite(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO audit_events (
                    user_id,
                    actor_role,
                    event_type,
                    status,
                    target_type,
                    target_id,
                    trace_id,
                    details_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(user_id),
                    normalize_user_role(actor_role),
                    str(event_type or "").strip(),
                    str(status or "success").strip() or "success",
                    str(target_type or "").strip(),
                    str(target_id or "").strip(),
                    str(trace_id or "").strip(),
                    json.dumps(details or {}, ensure_ascii=False, sort_keys=True),
                    now_iso(),
                ),
            )
            connection.commit()
        return int(cursor.lastrowid or 0)

    def list_recent_events(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with connect_sqlite(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    actor_role,
                    event_type,
                    status,
                    target_type,
                    target_id,
                    trace_id,
                    details_json,
                    created_at
                FROM audit_events
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            try:
                details = json.loads(str(row[8] or "{}"))
            except json.JSONDecodeError:
                details = {}
            events.append(
                {
                    "id": int(row[0]),
                    "user_id": int(row[1]),
                    "actor_role": str(row[2] or ""),
                    "event_type": str(row[3] or ""),
                    "status": str(row[4] or ""),
                    "target_type": str(row[5] or ""),
                    "target_id": str(row[6] or ""),
                    "trace_id": str(row[7] or ""),
                    "details": details,
                    "created_at": str(row[9] or ""),
                }
            )
        return events
