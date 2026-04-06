"""Store-layer helpers for profiles."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..models import ResumeProfile, StoredResumeProfile
from ..sqlite_utils import connect_sqlite
from .common import now_iso
from .auth import GUEST_USER_ID


class UserProfileRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def get_resume_profile(self, *, user_id: int = GUEST_USER_ID) -> StoredResumeProfile | None:
        with connect_sqlite(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT user_id, source_name, profile_json, updated_at
                FROM user_resume_profiles
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        payload = json.loads(row[2] or "{}")
        profile = ResumeProfile(**payload) if payload else None
        return StoredResumeProfile(
            user_id=int(row[0]),
            source_name=str(row[1] or ""),
            profile=profile,
            updated_at=str(row[3] or ""),
        )

    def save_resume_profile(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        profile: ResumeProfile,
    ) -> None:
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO user_resume_profiles (
                    user_id,
                    source_name,
                    profile_json,
                    updated_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    source_name = excluded.source_name,
                    profile_json = excluded.profile_json,
                    updated_at = excluded.updated_at
                """,
                (
                    user_id,
                    profile.source_name,
                    json.dumps(profile.to_dict(), ensure_ascii=False),
                    now_iso(),
                ),
            )
            connection.commit()

    def clear_resume_profile(self, *, user_id: int = GUEST_USER_ID) -> None:
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                "DELETE FROM user_resume_profiles WHERE user_id = ?",
                (user_id,),
            )
            connection.commit()
