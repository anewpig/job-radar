from __future__ import annotations

from datetime import datetime

from .models import ItemInsight, JobListing, MarketSnapshot, SkillInsight, TargetRole
from .utils import dump_json, load_json


def save_snapshot(snapshot: MarketSnapshot, path) -> None:
    dump_json(path, snapshot.to_dict())


def load_snapshot(path) -> MarketSnapshot | None:
    payload = load_json(path)
    if not payload:
        return None
    return MarketSnapshot(
        generated_at=payload["generated_at"],
        queries=payload["queries"],
        role_targets=[TargetRole(**role) for role in payload["role_targets"]],
        jobs=[JobListing(**job) for job in payload["jobs"]],
        skills=[SkillInsight(**skill) for skill in payload["skills"]],
        task_insights=[ItemInsight(**item) for item in payload.get("task_insights", [])],
        errors=payload.get("errors", []),
    )


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
