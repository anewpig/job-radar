"""Tests for shared SQLite connection pragmas."""

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

from job_spy_tw.sqlite_utils import DEFAULT_BUSY_TIMEOUT_MS, connect_sqlite  # noqa: E402


class SQLiteUtilsTests(unittest.TestCase):
    def test_connect_sqlite_enables_runtime_pragmas(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "runtime.sqlite3"

        with connect_sqlite(db_path) as connection:
            journal_mode = connection.execute("PRAGMA journal_mode").fetchone()
            foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()
            busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()

        self.assertEqual(str(journal_mode[0]).lower(), "wal")
        self.assertEqual(int(foreign_keys[0]), 1)
        self.assertEqual(int(busy_timeout[0]), DEFAULT_BUSY_TIMEOUT_MS)
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")

    def test_connect_sqlite_supports_row_factory_override(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "rows.sqlite3"

        with connect_sqlite(db_path, row_factory=sqlite3.Row) as connection:
            connection.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
            connection.execute("INSERT INTO demo (name) VALUES ('job-radar')")
            row = connection.execute("SELECT id, name FROM demo").fetchone()

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row["name"], "job-radar")


if __name__ == "__main__":
    unittest.main()
