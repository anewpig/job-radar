"""Persistence helpers for stored user submissions and resume data."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from .models import ResumeProfile
from .resume_analysis import mask_personal_items, mask_personal_text
from .sqlite_utils import connect_sqlite
from .utils import ensure_directory


class UserDataStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        ensure_directory(db_path.parent)
        self._initialize()

    def save_profile(
        self,
        profile: ResumeProfile,
        source_type: str,
    ) -> int:
        payload = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "source_type": source_type,
            "source_name": profile.source_name,
            "summary": self._mask_summary(profile.summary),
            "raw_text_masked": mask_personal_text(profile.raw_text),
            "target_roles": mask_personal_items(profile.target_roles),
            "core_skills": mask_personal_items(profile.core_skills),
            "tool_skills": mask_personal_items(profile.tool_skills),
            "domain_keywords": mask_personal_items(profile.domain_keywords),
            "preferred_tasks": mask_personal_items(profile.preferred_tasks),
            "generated_prompts": mask_personal_items(profile.generated_prompts),
            "match_keywords": mask_personal_items(profile.match_keywords),
            "extraction_method": profile.extraction_method,
            "llm_model": profile.llm_model,
            "notes": mask_personal_items(profile.notes),
        }
        with connect_sqlite(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO user_submissions (
                    created_at,
                    source_type,
                    source_name,
                    summary,
                    raw_text_masked,
                    target_roles,
                    core_skills,
                    tool_skills,
                    domain_keywords,
                    preferred_tasks,
                    generated_prompts,
                    match_keywords,
                    extraction_method,
                    llm_model,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["created_at"],
                    payload["source_type"],
                    payload["source_name"],
                    payload["summary"],
                    payload["raw_text_masked"],
                    json.dumps(payload["target_roles"], ensure_ascii=False),
                    json.dumps(payload["core_skills"], ensure_ascii=False),
                    json.dumps(payload["tool_skills"], ensure_ascii=False),
                    json.dumps(payload["domain_keywords"], ensure_ascii=False),
                    json.dumps(payload["preferred_tasks"], ensure_ascii=False),
                    json.dumps(payload["generated_prompts"], ensure_ascii=False),
                    json.dumps(payload["match_keywords"], ensure_ascii=False),
                    payload["extraction_method"],
                    payload["llm_model"],
                    json.dumps(payload["notes"], ensure_ascii=False),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def count_submissions(self) -> int:
        with connect_sqlite(self.db_path) as connection:
            cursor = connection.execute("SELECT COUNT(*) FROM user_submissions")
            row = cursor.fetchone()
        return int(row[0]) if row else 0

    def _initialize(self) -> None:
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_name TEXT NOT NULL DEFAULT '',
                    summary TEXT NOT NULL DEFAULT '',
                    raw_text_masked TEXT NOT NULL DEFAULT '',
                    target_roles TEXT NOT NULL DEFAULT '[]',
                    core_skills TEXT NOT NULL DEFAULT '[]',
                    tool_skills TEXT NOT NULL DEFAULT '[]',
                    domain_keywords TEXT NOT NULL DEFAULT '[]',
                    preferred_tasks TEXT NOT NULL DEFAULT '[]',
                    generated_prompts TEXT NOT NULL DEFAULT '[]',
                    match_keywords TEXT NOT NULL DEFAULT '[]',
                    extraction_method TEXT NOT NULL DEFAULT '',
                    llm_model TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '[]'
                )
                """
            )
            connection.commit()

    def _mask_summary(self, summary: str) -> str:
        masked = mask_personal_text(summary)
        masked = re.sub(
            r"^([A-Za-z\u4e00-\u9fff]{2,8})(?=(具備|熟悉|曾|擁有|主導|負責))",
            "***",
            masked,
        )
        return masked
