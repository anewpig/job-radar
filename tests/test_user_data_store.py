from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.models import ResumeProfile  # noqa: E402
from job_spy_tw.user_data_store import UserDataStore  # noqa: E402


class UserDataStoreTests(unittest.TestCase):
    def test_save_profile_persists_masked_submission(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "submissions.sqlite3"
        store = UserDataStore(db_path)
        profile = ResumeProfile(
            source_name="王小明_履歷.pdf",
            raw_text="姓名：王小明\n電話：0907-509-233\nabc123@gmail.com",
            summary="王小明具備 Python 與 RAG 經驗",
            target_roles=["AI工程師"],
            core_skills=["LLM"],
            tool_skills=["Python"],
            preferred_tasks=["流程自動化"],
            notes=["來自履歷上傳"],
        )

        row_id = store.save_profile(profile=profile, source_type="resume_upload")

        self.assertGreater(row_id, 0)
        self.assertEqual(store.count_submissions(), 1)

        with sqlite3.connect(db_path) as connection:
            row = connection.execute(
                "SELECT source_type, summary, raw_text_masked FROM user_submissions"
            ).fetchone()

        self.assertEqual(row[0], "resume_upload")
        self.assertNotIn("王小明", row[1])
        self.assertNotIn("0907-509-233", row[2])
        self.assertNotIn("abc123@gmail.com", row[2])


if __name__ == "__main__":
    unittest.main()
