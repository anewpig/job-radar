"""Tests for combined backend maintenance helpers."""

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

from job_spy_tw.backend_maintenance_service import run_backend_maintenance  # noqa: E402
from job_spy_tw.config import Settings  # noqa: E402


class BackendMaintenanceServiceTests(unittest.TestCase):
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
            runtime_cleanup_interval_seconds=3600,
        )

    def _write_marker(self, db_path: Path, value: str) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS markers (value TEXT NOT NULL)")
            connection.execute("DELETE FROM markers")
            connection.execute("INSERT INTO markers(value) VALUES (?)", (value,))
            connection.commit()

    def test_run_backend_maintenance_runs_cleanup_and_backup(self) -> None:
        settings = self.build_settings()
        self._write_marker(settings.product_state_db_path, "product-v1")

        result = run_backend_maintenance(
            settings=settings,
            trigger="test",
            force_cleanup=True,
            include_runtime_backup=False,
            keep_last_backups=5,
        )

        self.assertEqual(result.cleanup.status, "completed")
        self.assertTrue(result.backup.manifest_path.exists())
        self.assertEqual(
            [entry.database_key for entry in result.backup.entries],
            ["product_state"],
        )
        self.assertIn("user_submissions", result.backup.skipped_databases)
        self.assertIn("market_history", result.backup.skipped_databases)


if __name__ == "__main__":
    unittest.main()
