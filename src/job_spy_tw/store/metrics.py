from __future__ import annotations

import sqlite3
from pathlib import Path

from .common import now_iso


class AppMetricsRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def get_metric(self, metric_key: str) -> int:
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                """
                SELECT metric_value
                FROM app_metrics
                WHERE metric_key = ?
                """,
                (metric_key.strip(),),
            ).fetchone()
        return int(row[0]) if row else 0

    def increment_metric(self, metric_key: str, amount: int = 1) -> int:
        cleaned_key = metric_key.strip()
        step = int(amount)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO app_metrics (metric_key, metric_value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(metric_key) DO UPDATE SET
                    metric_value = app_metrics.metric_value + excluded.metric_value,
                    updated_at = excluded.updated_at
                """,
                (
                    cleaned_key,
                    step,
                    now_iso(),
                ),
            )
            row = connection.execute(
                """
                SELECT metric_value
                FROM app_metrics
                WHERE metric_key = ?
                """,
                (cleaned_key,),
            ).fetchone()
            connection.commit()
        return int(row[0]) if row else 0

    def get_total_visits(self) -> int:
        return self.get_metric("total_visits")

    def record_visit(self) -> int:
        return self.increment_metric("total_visits", amount=1)
