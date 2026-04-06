"""Tests for SQLite restore drill helper."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.config import Settings  # noqa: E402
from job_spy_tw.sqlite_backup_service import run_sqlite_backup  # noqa: E402
from job_spy_tw.sqlite_restore_drill import run_sqlite_restore_drill  # noqa: E402


class SQLiteRestoreDrillTests(unittest.TestCase):
    def build_settings(self) -> Settings:
        return Settings(
            data_dir=Path(tempfile.mkdtemp()),
            request_timeout=5.0,
            request_delay=0.2,
            max_concurrent_requests=4,
            max_pages_per_source=2,
            max_detail_jobs_per_source=8,
            min_relevance_score=0.0,
            location="台灣",
            enable_cake=True,
            enable_linkedin=True,
            allow_insecure_ssl_fallback=True,
            user_agent="test-agent",
            openai_api_key="",
            openai_base_url="",
            resume_llm_model="gpt-4.1-mini",
            title_similarity_model="gpt-4.1-mini",
            embedding_model="text-embedding-3-large",
            assistant_model="gpt-4.1-mini",
        )

    def test_run_sqlite_restore_drill_verifies_latest_backup(self) -> None:
        settings = self.build_settings()
        settings.product_state_db_path.parent.mkdir(parents=True, exist_ok=True)
        settings.product_state_db_path.write_bytes(b"")
        run_sqlite_backup(settings=settings)

        result = run_sqlite_restore_drill(settings=settings)

        self.assertTrue(result.report_path.exists())
        self.assertEqual(result.restored_databases, ["product_state"])
        self.assertEqual(result.verified_databases, ["product_state"])


if __name__ == "__main__":
    unittest.main()
