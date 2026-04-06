"""Snapshot persistence helpers for crawl results."""

from __future__ import annotations

from datetime import datetime

from .models import ItemInsight, JobListing, MarketSnapshot, SkillInsight, TargetRole
from .utils import dump_json, load_json


def _format_salary_from_metadata(job_payload: dict) -> str:
    salary = str(job_payload.get("salary", "") or "").strip()
    if salary:
        return salary
    metadata = job_payload.get("metadata", {}) or {}
    low_value = int(metadata.get("salary_low") or 0)
    high_value = int(metadata.get("salary_high") or 0)
    if low_value <= 0 and high_value <= 0:
        return ""

    unit = "年薪" if max(low_value, high_value) >= 300_000 else "月薪"
    if high_value >= 9_999_999 and low_value > 0:
        return f"{unit} {low_value:,} 元以上"
    if low_value > 0 and high_value > 0:
        if low_value == high_value:
            return f"{unit} {low_value:,} 元"
        return f"{unit} {low_value:,} - {high_value:,} 元"
    if low_value > 0:
        return f"{unit} {low_value:,} 元以上"
    return f"{unit}最高 {high_value:,} 元"


def save_snapshot(snapshot: MarketSnapshot, path) -> None:
    dump_json(path, snapshot.to_dict())


def load_snapshot(path) -> MarketSnapshot | None:
    payload = load_json(path)
    if not payload:
        return None
    jobs_payload = []
    for job in payload["jobs"]:
        normalized = dict(job)
        normalized["salary"] = _format_salary_from_metadata(normalized)
        jobs_payload.append(normalized)
    return MarketSnapshot(
        generated_at=payload["generated_at"],
        queries=payload["queries"],
        role_targets=[TargetRole(**role) for role in payload["role_targets"]],
        jobs=[JobListing(**job) for job in jobs_payload],
        skills=[SkillInsight(**skill) for skill in payload["skills"]],
        task_insights=[ItemInsight(**item) for item in payload.get("task_insights", [])],
        errors=payload.get("errors", []),
    )


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
