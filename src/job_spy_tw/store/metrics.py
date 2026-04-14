"""Store-layer helpers for metrics."""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any

from ..sqlite_utils import connect_sqlite
from .auth import GUEST_USER_ID
from .common import now_iso

AI_LATENCY_BUDGETS: dict[str, dict[str, float]] = {
    "assistant.answer_question": {
        "avg_warn_ms": 5_000.0,
        "avg_fail_ms": 7_000.0,
        "p95_warn_ms": 7_500.0,
        "p95_fail_ms": 10_000.0,
        "error_warn_rate": 0.05,
        "error_fail_rate": 0.15,
    },
    "assistant.generate_report": {
        "avg_warn_ms": 6_500.0,
        "avg_fail_ms": 9_000.0,
        "p95_warn_ms": 9_500.0,
        "p95_fail_ms": 13_000.0,
        "error_warn_rate": 0.05,
        "error_fail_rate": 0.15,
    },
    "resume.build_profile": {
        "avg_warn_ms": 5_500.0,
        "avg_fail_ms": 8_000.0,
        "p95_warn_ms": 7_500.0,
        "p95_fail_ms": 10_000.0,
        "error_warn_rate": 0.05,
        "error_fail_rate": 0.15,
    },
    "resume.match_jobs": {
        "avg_warn_ms": 3_500.0,
        "avg_fail_ms": 5_000.0,
        "p95_warn_ms": 5_500.0,
        "p95_fail_ms": 7_500.0,
        "error_warn_rate": 0.05,
        "error_fail_rate": 0.15,
    },
    "resume.analyze_resume": {
        "avg_warn_ms": 9_000.0,
        "avg_fail_ms": 12_000.0,
        "p95_warn_ms": 12_500.0,
        "p95_fail_ms": 16_000.0,
        "error_warn_rate": 0.05,
        "error_fail_rate": 0.15,
    },
}

AI_TOKEN_BUDGETS: dict[str, dict[str, int]] = {
    "assistant.answer_question": {
        "avg_total_tokens_warn": 5_500,
        "avg_total_tokens_fail": 8_000,
        "p95_total_tokens_warn": 7_500,
        "p95_total_tokens_fail": 10_000,
    },
    "assistant.generate_report": {
        "avg_total_tokens_warn": 6_500,
        "avg_total_tokens_fail": 9_500,
        "p95_total_tokens_warn": 8_500,
        "p95_total_tokens_fail": 12_000,
    },
    "resume.build_profile": {
        "avg_total_tokens_warn": 4_000,
        "avg_total_tokens_fail": 6_000,
        "p95_total_tokens_warn": 5_500,
        "p95_total_tokens_fail": 8_000,
    },
    "resume.match_jobs": {
        "avg_total_tokens_warn": 6_000,
        "avg_total_tokens_fail": 9_000,
        "p95_total_tokens_warn": 8_500,
        "p95_total_tokens_fail": 12_000,
    },
    "resume.analyze_resume": {
        "avg_total_tokens_warn": 9_000,
        "avg_total_tokens_fail": 13_000,
        "p95_total_tokens_warn": 12_000,
        "p95_total_tokens_fail": 16_000,
    },
}


class AppMetricsRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def get_metric(self, metric_key: str) -> int:
        with connect_sqlite(self.db_path) as connection:
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
        with connect_sqlite(self.db_path) as connection:
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


class AIMonitoringRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def record_event(
        self,
        *,
        event_type: str,
        status: str = "success",
        latency_ms: float = 0.0,
        model_name: str = "",
        query_signature: str = "",
        metadata: dict[str, Any] | None = None,
        user_id: int = GUEST_USER_ID,
    ) -> int:
        payload = json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)
        with connect_sqlite(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO ai_monitoring_events (
                    user_id,
                    event_type,
                    status,
                    latency_ms,
                    model_name,
                    query_signature,
                    metadata_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(user_id),
                    event_type.strip(),
                    status.strip() or "success",
                    float(latency_ms),
                    model_name.strip(),
                    query_signature.strip(),
                    payload,
                    now_iso(),
                ),
            )
            connection.commit()
        return int(cursor.lastrowid or 0)

    def list_recent_events(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        with connect_sqlite(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    event_type,
                    status,
                    latency_ms,
                    model_name,
                    query_signature,
                    metadata_json,
                    created_at
                FROM ai_monitoring_events
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (int(user_id), int(limit)),
            ).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            try:
                metadata = json.loads(row[7] or "{}")
            except json.JSONDecodeError:
                metadata = {}
            events.append(
                {
                    "id": int(row[0]),
                    "user_id": int(row[1]),
                    "event_type": str(row[2] or ""),
                    "status": str(row[3] or ""),
                    "latency_ms": float(row[4] or 0.0),
                    "model_name": str(row[5] or ""),
                    "query_signature": str(row[6] or ""),
                    "metadata": metadata,
                    "created_at": str(row[8] or ""),
                }
            )
        return events

    def summarize_recent(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        limit: int = 200,
    ) -> dict[str, dict[str, float | int]]:
        events = self.list_recent_events(user_id=user_id, limit=limit)
        summary: dict[str, dict[str, float | int]] = {}
        for event in events:
            event_type = str(event["event_type"])
            bucket = summary.setdefault(
                event_type,
                {
                    "count": 0,
                    "error_count": 0,
                    "avg_latency_ms": 0.0,
                    "max_latency_ms": 0.0,
                },
            )
            bucket["count"] = int(bucket["count"]) + 1
            if str(event["status"]) != "success":
                bucket["error_count"] = int(bucket["error_count"]) + 1
            latency_ms = float(event["latency_ms"])
            bucket["avg_latency_ms"] = float(bucket["avg_latency_ms"]) + latency_ms
            bucket["max_latency_ms"] = max(float(bucket["max_latency_ms"]), latency_ms)
        for bucket in summary.values():
            count = max(1, int(bucket["count"]))
            bucket["avg_latency_ms"] = round(float(bucket["avg_latency_ms"]) / count, 3)
        return summary

    def summarize_assistant_modes(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        limit: int = 500,
    ) -> dict[str, dict[str, Any]]:
        events = self.list_recent_events(user_id=user_id, limit=limit)
        grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for event in events:
            event_type = str(event.get("event_type") or "")
            if event_type not in {"assistant.answer_question", "assistant.generate_report"}:
                continue
            metadata = event.get("metadata") or {}
            answer_mode = str(metadata.get("answer_mode") or "").strip() or "unknown"
            grouped.setdefault(event_type, {}).setdefault(answer_mode, []).append(event)

        summarized: dict[str, dict[str, Any]] = {}
        for event_type, modes in grouped.items():
            summarized[event_type] = {}
            for answer_mode, bucket in modes.items():
                summarized[event_type][answer_mode] = self._summarize_event_bucket(
                    event_type=event_type,
                    events=bucket,
                )
        return summarized

    def summarize_cache_efficiency(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        limit: int = 500,
    ) -> dict[str, Any]:
        events = self.list_recent_events(user_id=user_id, limit=limit)
        summary: dict[str, Any] = {
            "request_count": 0,
            "chunk_cache_hits": 0,
            "profile_cache_memory_hits": 0,
            "profile_cache_disk_hits": 0,
            "title_cache_memory_hits": 0,
            "title_cache_disk_hits": 0,
            "embedding_memory_hits": 0,
            "embedding_disk_hits": 0,
            "embedding_remote_texts": 0,
            "assistant_persistent_ann_candidates": 0,
            "event_breakdown": {},
            "version_breakdown": {
                "prompt_version": {},
                "prompt_variant": {},
                "selected_model": {},
                "retrieval_policy_version": {},
                "chunking_policy_version": {},
                "persistent_index_version": {},
            },
        }
        for event in events:
            metadata = event.get("metadata") or {}
            event_type = str(event.get("event_type") or "")
            if event_type in {
                "assistant.answer_question",
                "assistant.generate_report",
                "resume.build_profile",
                "resume.match_jobs",
                "resume.analyze_resume",
            }:
                summary["request_count"] = int(summary["request_count"]) + 1
            if bool(metadata.get("chunk_cache_hit")):
                summary["chunk_cache_hits"] = int(summary["chunk_cache_hits"]) + 1
            if bool(metadata.get("profile_cache_memory_hit")):
                summary["profile_cache_memory_hits"] = int(summary["profile_cache_memory_hits"]) + 1
            if bool(metadata.get("profile_cache_disk_hit")):
                summary["profile_cache_disk_hits"] = int(summary["profile_cache_disk_hits"]) + 1
            summary["title_cache_memory_hits"] = int(summary["title_cache_memory_hits"]) + int(
                metadata.get("title_cache_memory_hits", 0) or 0
            )
            summary["title_cache_disk_hits"] = int(summary["title_cache_disk_hits"]) + int(
                metadata.get("title_cache_disk_hits", 0) or 0
            )
            summary["embedding_memory_hits"] = int(summary["embedding_memory_hits"]) + int(
                metadata.get("embedding_memory_hits", 0) or 0
            )
            summary["embedding_disk_hits"] = int(summary["embedding_disk_hits"]) + int(
                metadata.get("embedding_disk_hits", 0) or 0
            )
            summary["embedding_remote_texts"] = int(summary["embedding_remote_texts"]) + int(
                metadata.get("embedding_remote_texts", 0) or 0
            )
            summary["assistant_persistent_ann_candidates"] = int(
                summary["assistant_persistent_ann_candidates"]
            ) + int(metadata.get("persistent_ann_candidates", 0) or 0)
            event_bucket = summary["event_breakdown"].setdefault(
                event_type or "unknown",
                {
                    "requests": 0,
                    "chunk_cache_hits": 0,
                    "embedding_memory_hits": 0,
                    "embedding_disk_hits": 0,
                    "embedding_remote_texts": 0,
                    "profile_cache_memory_hits": 0,
                    "profile_cache_disk_hits": 0,
                    "title_cache_memory_hits": 0,
                    "title_cache_disk_hits": 0,
                    "persistent_ann_candidates": 0,
                },
            )
            event_bucket["requests"] = int(event_bucket["requests"]) + 1
            if bool(metadata.get("chunk_cache_hit")):
                event_bucket["chunk_cache_hits"] = int(event_bucket["chunk_cache_hits"]) + 1
            for key in (
                "embedding_memory_hits",
                "embedding_disk_hits",
                "embedding_remote_texts",
                "profile_cache_memory_hits",
                "profile_cache_disk_hits",
                "title_cache_memory_hits",
                "title_cache_disk_hits",
            ):
                event_bucket[key] = int(event_bucket[key]) + int(metadata.get(key, 0) or 0)
            event_bucket["persistent_ann_candidates"] = int(
                event_bucket["persistent_ann_candidates"]
            ) + int(metadata.get("persistent_ann_candidates", 0) or 0)
            for field_name in summary["version_breakdown"]:
                field_value = str(metadata.get(field_name, "") or "").strip()
                if field_value:
                    bucket = summary["version_breakdown"][field_name]
                    bucket[field_value] = int(bucket.get(field_value, 0)) + 1
        request_count = max(1, int(summary["request_count"]))
        summary["chunk_cache_hit_rate"] = round(
            int(summary["chunk_cache_hits"]) / request_count,
            4,
        )
        for event_bucket in summary["event_breakdown"].values():
            requests = max(1, int(event_bucket["requests"]))
            event_bucket["chunk_cache_hit_rate"] = round(
                int(event_bucket["chunk_cache_hits"]) / requests,
                4,
            )
            event_bucket["avg_persistent_ann_candidates"] = round(
                int(event_bucket["persistent_ann_candidates"]) / requests,
                3,
            )
        return summary

    def evaluate_latency_budgets(
        self,
        *,
        user_id: int = GUEST_USER_ID,
        limit: int = 500,
    ) -> dict[str, Any]:
        events = self.list_recent_events(user_id=user_id, limit=limit)
        grouped: dict[str, list[dict[str, Any]]] = {}
        for event in events:
            grouped.setdefault(str(event["event_type"]), []).append(event)

        budgets: dict[str, Any] = {}
        overall_status = "PASS"
        token_budgets: dict[str, Any] = {}
        overall_cost_status = "PASS"
        for event_type, thresholds in AI_LATENCY_BUDGETS.items():
            bucket = grouped.get(event_type, [])
            if not bucket:
                budgets[event_type] = {
                    "status": "NO_DATA",
                    "count": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "error_rate": 0.0,
                    "avg_latency_ms": 0.0,
                    "p95_latency_ms": 0.0,
                    "thresholds": thresholds,
                }
                token_budgets[event_type] = {
                    "status": "NO_DATA",
                    "count": 0,
                    "events_with_usage": 0,
                    "avg_total_tokens": 0.0,
                    "p95_total_tokens": 0.0,
                    "thresholds": AI_TOKEN_BUDGETS.get(event_type, {}),
                }
                continue

            latencies = sorted(float(item["latency_ms"]) for item in bucket)
            count = len(bucket)
            error_count = sum(1 for item in bucket if str(item["status"]) != "success")
            success_count = count - error_count
            error_rate = error_count / count if count else 0.0
            avg_latency_ms = sum(latencies) / count if count else 0.0
            p95_latency_ms = self._percentile(latencies, 0.95)
            status = self._evaluate_budget_status(
                avg_latency_ms=avg_latency_ms,
                p95_latency_ms=p95_latency_ms,
                error_rate=error_rate,
                thresholds=thresholds,
            )
            budgets[event_type] = {
                "status": status,
                "count": count,
                "success_count": success_count,
                "error_count": error_count,
                "error_rate": round(error_rate, 4),
                "avg_latency_ms": round(avg_latency_ms, 3),
                "p95_latency_ms": round(p95_latency_ms, 3),
                "thresholds": thresholds,
            }
            overall_status = self._merge_status(overall_status, status)
            token_budgets[event_type] = self._evaluate_token_budget(
                event_type=event_type,
                events=bucket,
            )
            overall_cost_status = self._merge_status(
                overall_cost_status,
                str(token_budgets[event_type]["status"]),
            )

        return {
            "status": overall_status,
            "event_budgets": budgets,
            "cost_tracking": {
                "status": overall_cost_status,
                "type": "token_budget",
                "event_budgets": token_budgets,
            },
        }

    def _evaluate_budget_status(
        self,
        *,
        avg_latency_ms: float,
        p95_latency_ms: float,
        error_rate: float,
        thresholds: dict[str, float],
    ) -> str:
        if (
            avg_latency_ms >= thresholds["avg_fail_ms"]
            or p95_latency_ms >= thresholds["p95_fail_ms"]
            or error_rate >= thresholds["error_fail_rate"]
        ):
            return "FAIL"
        if (
            avg_latency_ms >= thresholds["avg_warn_ms"]
            or p95_latency_ms >= thresholds["p95_warn_ms"]
            or error_rate >= thresholds["error_warn_rate"]
        ):
            return "WARN"
        return "PASS"

    def _merge_status(self, current: str, incoming: str) -> str:
        order = {"PASS": 0, "WARN": 1, "FAIL": 2, "NO_DATA": 1}
        return incoming if order.get(incoming, 0) > order.get(current, 0) else current

    def _summarize_event_bucket(
        self,
        *,
        event_type: str,
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        thresholds = AI_LATENCY_BUDGETS.get(event_type, {})
        token_thresholds = AI_TOKEN_BUDGETS.get(event_type, {})
        latencies = sorted(float(event.get("latency_ms", 0.0) or 0.0) for event in events)
        count = len(events)
        error_count = sum(1 for event in events if str(event.get("status") or "") != "success")
        success_count = count - error_count
        error_rate = error_count / count if count else 0.0
        avg_latency_ms = sum(latencies) / count if count else 0.0
        p95_latency_ms = self._percentile(latencies, 0.95)
        latency_status = (
            self._evaluate_budget_status(
                avg_latency_ms=avg_latency_ms,
                p95_latency_ms=p95_latency_ms,
                error_rate=error_rate,
                thresholds=thresholds,
            )
            if thresholds
            else "NO_DATA"
        )
        token_budget = self._evaluate_token_budget(event_type=event_type, events=events)
        overall_status = self._merge_status(latency_status, str(token_budget.get("status", "NO_DATA")))
        return {
            "status": overall_status,
            "count": count,
            "success_count": success_count,
            "error_count": error_count,
            "error_rate": round(error_rate, 4),
            "avg_latency_ms": round(avg_latency_ms, 3),
            "p95_latency_ms": round(p95_latency_ms, 3),
            "avg_total_tokens": float(token_budget.get("avg_total_tokens", 0.0) or 0.0),
            "p95_total_tokens": float(token_budget.get("p95_total_tokens", 0.0) or 0.0),
            "latency_status": latency_status,
            "token_status": str(token_budget.get("status", "NO_DATA")),
            "thresholds": thresholds,
            "token_thresholds": token_thresholds,
        }

    def _percentile(self, values: list[float], percentile: float) -> float:
        if not values:
            return 0.0
        index = max(0, min(len(values) - 1, math.ceil(len(values) * percentile) - 1))
        return float(values[index])

    def _evaluate_token_budget(
        self,
        *,
        event_type: str,
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        thresholds = AI_TOKEN_BUDGETS.get(event_type, {})
        token_values = sorted(
            int(event.get("metadata", {}).get("usage_total_tokens", 0) or 0)
            for event in events
            if int(event.get("metadata", {}).get("usage_total_tokens", 0) or 0) > 0
        )
        if not token_values or not thresholds:
            return {
                "status": "NO_DATA",
                "count": len(events),
                "events_with_usage": len(token_values),
                "avg_total_tokens": 0.0,
                "p95_total_tokens": 0.0,
                "thresholds": thresholds,
            }

        avg_total_tokens = sum(token_values) / len(token_values)
        p95_total_tokens = self._percentile([float(value) for value in token_values], 0.95)
        if (
            avg_total_tokens >= thresholds["avg_total_tokens_fail"]
            or p95_total_tokens >= thresholds["p95_total_tokens_fail"]
        ):
            status = "FAIL"
        elif (
            avg_total_tokens >= thresholds["avg_total_tokens_warn"]
            or p95_total_tokens >= thresholds["p95_total_tokens_warn"]
        ):
            status = "WARN"
        else:
            status = "PASS"
        return {
            "status": status,
            "count": len(events),
            "events_with_usage": len(token_values),
            "avg_total_tokens": round(avg_total_tokens, 3),
            "p95_total_tokens": round(p95_total_tokens, 3),
            "thresholds": thresholds,
        }
