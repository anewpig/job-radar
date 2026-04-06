"""SQLite connection helpers with shared runtime pragmas."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_BUSY_TIMEOUT_MS = 5_000


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
    connection = sqlite3.connect(db_path, factory=ManagedSQLiteConnection)
    if row_factory is not None:
        connection.row_factory = row_factory
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {DEFAULT_BUSY_TIMEOUT_MS}")
    connection.execute("PRAGMA synchronous = NORMAL")
    return connection
