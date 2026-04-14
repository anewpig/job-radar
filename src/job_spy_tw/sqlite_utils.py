"""SQLite connection helpers with shared runtime pragmas."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_BUSY_TIMEOUT_MS = 5_000


def _busy_timeout_ms() -> int:
    raw = os.getenv("JOB_SPY_SQLITE_BUSY_TIMEOUT_MS", "").strip()
    if not raw:
        return DEFAULT_BUSY_TIMEOUT_MS
    try:
        return max(100, int(raw))
    except ValueError:
        return DEFAULT_BUSY_TIMEOUT_MS


class ManagedSQLiteConnection(sqlite3.Connection):
    """SQLite connection that closes itself after context-manager usage."""

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        try:
            return bool(super().__exit__(exc_type, exc_value, traceback))
        finally:
            self.close()


def connect_sqlite(
    db_path: Path,
    *,
    row_factory: Any | None = None,
) -> sqlite3.Connection:
    """Open a SQLite connection with the project's baseline pragmas."""
    timeout_seconds = _busy_timeout_ms() / 1000
    connection = sqlite3.connect(
        db_path,
        timeout=timeout_seconds,
        factory=ManagedSQLiteConnection,
    )
    if row_factory is not None:
        connection.row_factory = row_factory
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {_busy_timeout_ms()}")
    connection.execute("PRAGMA synchronous = NORMAL")
    return connection
