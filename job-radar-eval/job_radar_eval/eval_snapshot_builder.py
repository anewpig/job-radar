"""Helpers for building composite evaluation snapshots."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .config import EvalConfig


def build_composite_eval_snapshot(
    config: EvalConfig,
    snapshot_paths: list[Path],
    *,
    top_roles: int = 3,
    per_role_limit: int = 15,
    min_roles: int = 2,
):
    """Merge one or more snapshots into a comparison-ready eval snapshot."""
    from job_spy_tw.market_analysis.analyzer import JobAnalyzer
    from job_spy_tw.models import MarketSnapshot, TargetRole
    from job_spy_tw.storage import load_snapshot

    resolved_paths = [path.resolve() for path in snapshot_paths]
    loaded = []
    for path in resolved_paths:
        snapshot = load_snapshot(path)
        if snapshot is None:
            raise FileNotFoundError(f"找不到或無法解析快照：{path}")
        loaded.append((path, snapshot))

    jobs_by_url: dict[str, object] = {}
    role_targets_map: dict[str, TargetRole] = {}
    merged_queries: list[str] = []
    source_snapshots: list[str] = []

    for path, snapshot in loaded:
        source_snapshots.append(str(path))
        for query in snapshot.queries:
            if query not in merged_queries:
                merged_queries.append(query)
        for role in snapshot.role_targets:
            role_targets_map.setdefault(role.name, deepcopy(role))
        for job in snapshot.jobs:
            if not job.url or job.url in jobs_by_url:
                continue
            jobs_by_url[job.url] = deepcopy(job)

    jobs = list(jobs_by_url.values())
    role_counts = Counter(job.matched_role for job in jobs if job.matched_role)
    selected_role_names = [name for name, _ in role_counts.most_common(max(1, top_roles))]
    selected_role_names = [name for name in selected_role_names if name]
    if len(selected_role_names) < min_roles:
        raise ValueError(
            f"可用角色不足：目前只有 {selected_role_names or '[]'}，需要至少 {min_roles} 個角色。"
        )

    selected_jobs = []
    for role_name in selected_role_names:
        role_jobs = [job for job in jobs if job.matched_role == role_name]
        role_jobs.sort(key=lambda job: float(job.relevance_score), reverse=True)
        selected_jobs.extend(role_jobs[: max(1, per_role_limit)])

    selected_jobs.sort(key=lambda job: (job.matched_role, -float(job.relevance_score), job.title))
    selected_role_targets = [
        deepcopy(role_targets_map.get(role_name, TargetRole(name=role_name, priority=index + 1, keywords=[role_name])))
        for index, role_name in enumerate(selected_role_names)
    ]

    analyzer = JobAnalyzer(selected_role_targets)
    skills = analyzer.summarize_skills(selected_jobs)
    task_insights = analyzer.summarize_tasks(selected_jobs)

    snapshot = MarketSnapshot(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        queries=merged_queries,
        role_targets=selected_role_targets,
        jobs=selected_jobs,
        skills=skills,
        task_insights=task_insights,
        errors=[
            "composite_eval_snapshot",
            f"source_snapshots={len(source_snapshots)}",
        ],
    )
    metadata = {
        "source_snapshots": source_snapshots,
        "selected_role_names": selected_role_names,
        "selected_role_counts": {role: role_counts.get(role, 0) for role in selected_role_names},
        "job_count": len(selected_jobs),
        "query_count": len(merged_queries),
        "role_targets": [asdict(role) for role in selected_role_targets],
    }
    return snapshot, metadata
