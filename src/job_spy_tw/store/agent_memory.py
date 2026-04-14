"""Store-layer helpers for assistant agent memory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models import AgentMemoryRecord
from ..sqlite_utils import connect_sqlite
from .auth import GUEST_USER_ID
from .common import now_iso


class AgentMemoryRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def upsert_memory(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        memory_type: str,
        key: str,
        value: dict[str, Any] | None = None,
        summary: str = "",
        source: str = "",
        confidence: float = 1.0,
        expires_at: str = "",
        is_active: bool = True,
    ) -> int:
        now = now_iso()
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO agent_memories (
                    user_id,
                    memory_type,
                    key,
                    summary,
                    value_json,
                    source,
                    confidence,
                    last_used_at,
                    created_at,
                    updated_at,
                    expires_at,
                    is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, memory_type, key) DO UPDATE SET
                    summary = excluded.summary,
                    value_json = excluded.value_json,
                    source = excluded.source,
                    confidence = excluded.confidence,
                    last_used_at = excluded.last_used_at,
                    updated_at = excluded.updated_at,
                    expires_at = excluded.expires_at,
                    is_active = excluded.is_active
                """,
                (
                    int(user_id),
                    str(memory_type or "").strip(),
                    str(key or "").strip(),
                    str(summary or "").strip(),
                    json.dumps(value or {}, ensure_ascii=False, sort_keys=True),
                    str(source or "").strip(),
                    float(confidence),
                    now,
                    now,
                    now,
                    str(expires_at or "").strip(),
                    1 if is_active else 0,
                ),
            )
            row = connection.execute(
                """
                SELECT id
                FROM agent_memories
                WHERE user_id = ? AND memory_type = ? AND key = ?
                """,
                (int(user_id), str(memory_type or "").strip(), str(key or "").strip()),
            ).fetchone()
            connection.commit()
        return int(row[0]) if row else 0

    def get_memory(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        memory_type: str,
        key: str,
        active_only: bool = True,
    ) -> AgentMemoryRecord | None:
        filters = [
            "user_id = ?",
            "memory_type = ?",
            "key = ?",
        ]
        params: list[Any] = [int(user_id), str(memory_type or "").strip(), str(key or "").strip()]
        if active_only:
            filters.append("is_active = 1")
        filters.append("(expires_at = '' OR expires_at > ?)")
        params.append(now_iso())
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                f"""
                SELECT
                    id,
                    user_id,
                    memory_type,
                    key,
                    summary,
                    value_json,
                    source,
                    confidence,
                    last_used_at,
                    created_at,
                    updated_at,
                    expires_at,
                    is_active
                FROM agent_memories
                WHERE {' AND '.join(filters)}
                ORDER BY updated_at DESC, id DESC
                LIMIT 1
                """,
                tuple(params),
            ).fetchone()
        return self._row_to_memory(row) if row is not None else None

    def list_memories(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        memory_type: str = "",
        limit: int = 20,
        active_only: bool = True,
    ) -> list[AgentMemoryRecord]:
        filters = ["user_id = ?"]
        params: list[Any] = [int(user_id)]
        if str(memory_type or "").strip():
            filters.append("memory_type = ?")
            params.append(str(memory_type or "").strip())
        if active_only:
            filters.append("is_active = 1")
        filters.append("(expires_at = '' OR expires_at > ?)")
        params.append(now_iso())
        params.append(int(limit))
        with connect_sqlite(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT
                    id,
                    user_id,
                    memory_type,
                    key,
                    summary,
                    value_json,
                    source,
                    confidence,
                    last_used_at,
                    created_at,
                    updated_at,
                    expires_at,
                    is_active
                FROM agent_memories
                WHERE {' AND '.join(filters)}
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [self._row_to_memory(row) for row in rows]

    def touch_memory(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        memory_type: str,
        key: str,
    ) -> None:
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                UPDATE agent_memories
                SET last_used_at = ?, updated_at = updated_at
                WHERE user_id = ? AND memory_type = ? AND key = ?
                """,
                (
                    now_iso(),
                    int(user_id),
                    str(memory_type or "").strip(),
                    str(key or "").strip(),
                ),
            )
            connection.commit()

    def _row_to_memory(self, row: Any) -> AgentMemoryRecord:
        try:
            value = json.loads(str(row[5] or "{}"))
        except json.JSONDecodeError:
            value = {}
        return AgentMemoryRecord(
            id=int(row[0]),
            user_id=int(row[1]),
            memory_type=str(row[2] or ""),
            key=str(row[3] or ""),
            summary=str(row[4] or ""),
            value=value if isinstance(value, dict) else {},
            source=str(row[6] or ""),
            confidence=float(row[7] or 0.0),
            last_used_at=str(row[8] or ""),
            created_at=str(row[9] or ""),
            updated_at=str(row[10] or ""),
            expires_at=str(row[11] or ""),
            is_active=bool(int(row[12] or 0)),
        )
