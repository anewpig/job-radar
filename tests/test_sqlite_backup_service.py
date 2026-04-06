"""Tests for SQLite backup and restore helpers."""

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

from job_spy_tw.config import Settings  # noqa: E402
from job_spy_tw.sqlite_backup_service import (  # noqa: E402
    prune_sqlite_backups,
    run_sqlite_backup,
    run_sqlite_restore,
)


class SQLiteBackupServiceTests(unittest.TestCase):
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

    def _write_marker(self, db_path: Path, value: str) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS markers (value TEXT NOT NULL)")
            connection.execute("DELETE FROM markers")
            connection.execute("INSERT INTO markers(value) VALUES (?)", (value,))
            connection.commit()

    def _read_marker(self, db_path: Path) -> str:
        with sqlite3.connect(db_path) as connection:
            row = connection.execute("SELECT value FROM markers LIMIT 1").fetchone()
        self.assertIsNotNone(row)
        assert row is not None
        return str(row[0])

    def test_backup_copies_persistent_databases_by_default(self) -> None:
        settings = self.build_settings()
        self._write_marker(settings.product_state_db_path, "product-v1")
        self._write_marker(settings.user_data_db_path, "user-v1")
        self._write_marker(settings.market_history_db_path, "history-v1")
        self._write_marker(settings.query_state_db_path, "runtime-v1")

        result = run_sqlite_backup(settings=settings, include_runtime=False)

        self.assertTrue(result.manifest_path.exists())
        self.assertEqual(
            [entry.database_key for entry in result.entries],
            ["product_state", "user_submissions", "market_history"],
        )
        self.assertNotIn("query_runtime", [entry.database_key for entry in result.entries])
        self.assertEqual(
            self._read_marker(result.backup_dir / settings.product_state_db_path.name),
            "product-v1",
        )
        self.assertEqual(
            self._read_marker(result.backup_dir / settings.user_data_db_path.name),
            "user-v1",
        )
        self.assertEqual(
            self._read_marker(result.backup_dir / settings.market_history_db_path.name),
            "history-v1",
        )

    def test_restore_replaces_current_databases_and_creates_safety_backup(self) -> None:
        settings = self.build_settings()
        self._write_marker(settings.product_state_db_path, "product-v1")
        self._write_marker(settings.user_data_db_path, "user-v1")
        self._write_marker(settings.market_history_db_path, "history-v1")

        backup = run_sqlite_backup(settings=settings)

        self._write_marker(settings.product_state_db_path, "product-v2")
        self._write_marker(settings.user_data_db_path, "user-v2")
        self._write_marker(settings.market_history_db_path, "history-v2")

        restored = run_sqlite_restore(
            settings=settings,
            backup_path=backup.manifest_path,
            include_runtime=False,
            create_safety_backup=True,
        )

        self.assertEqual(restored.restored_databases, ["product_state", "user_submissions", "market_history"])
        self.assertEqual(self._read_marker(settings.product_state_db_path), "product-v1")
        self.assertEqual(self._read_marker(settings.user_data_db_path), "user-v1")
        self.assertEqual(self._read_marker(settings.market_history_db_path), "history-v1")
        self.assertIsNotNone(restored.safety_backup_manifest_path)
        assert restored.safety_backup_manifest_path is not None
        safety_dir = restored.safety_backup_manifest_path.parent
        self.assertEqual(
            self._read_marker(safety_dir / settings.product_state_db_path.name),
            "product-v2",
        )
        self.assertEqual(
            self._read_marker(safety_dir / settings.user_data_db_path.name),
            "user-v2",
        )
        self.assertEqual(
            self._read_marker(safety_dir / settings.market_history_db_path.name),
            "history-v2",
        )

    def test_backup_with_keep_last_prunes_older_backup_sets(self) -> None:
        settings = self.build_settings()
        self._write_marker(settings.product_state_db_path, "product-v1")

        first = run_sqlite_backup(
            settings=settings,
            backup_slug="20260406T100000Z",
        )
        second = run_sqlite_backup(
            settings=settings,
            backup_slug="20260406T110000Z",
        )
        third = run_sqlite_backup(
            settings=settings,
            backup_slug="20260406T120000Z",
            keep_last=2,
        )

        self.assertFalse(first.backup_dir.exists())
        self.assertTrue(second.backup_dir.exists())
        self.assertTrue(third.backup_dir.exists())
        self.assertEqual(
            [path.name for path in third.pruned_backup_dirs],
            ["20260406T100000Z"],
        )

    def test_prune_sqlite_backups_ignores_non_backup_directories(self) -> None:
        settings = self.build_settings()
        backup_root = settings.data_dir / "backups" / "sqlite"
        backup_root.mkdir(parents=True, exist_ok=True)
        (backup_root / "notes").mkdir()

        deleted = prune_sqlite_backups(backup_root=backup_root, keep_last=3)

        self.assertEqual(deleted, [])
        self.assertTrue((backup_root / "notes").exists())


if __name__ == "__main__":
    unittest.main()
