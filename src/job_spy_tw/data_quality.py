"""Data lineage and snapshot quality helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from .models import JobListing

QUALITY_TRACKED_FIELDS: tuple[str, ...] = (
    "title",
    "company",
    "location",
    "url",
    "summary",
    "description",
    "salary",
    "posted_at",
    "extracted_skills",
    "work_content_items",
    "required_skill_items",
)


def build_snapshot_data_quality_report(
    *,
    connector_sources: list[str],
    raw_jobs: list[JobListing],
    deduped_jobs: list[JobListing],
    final_jobs: list[JobListing],
    errors: list[str],
    snapshot_kind: str,
) -> dict[str, Any]:
    raw_count = len(raw_jobs)
    deduped_count = len(deduped_jobs)
    final_count = len(final_jobs)
    merged_duplicates = max(0, raw_count - deduped_count)
    filtered_out = max(0, deduped_count - final_count)

    unique_sources = list(dict.fromkeys(str(source).strip() for source in connector_sources if str(source).strip()))
    raw_by_source = Counter(str(job.source).strip() for job in raw_jobs if str(job.source).strip())
    deduped_by_source = Counter(str(job.source).strip() for job in deduped_jobs if str(job.source).strip())
    final_by_source = Counter(str(job.source).strip() for job in final_jobs if str(job.source).strip())
    source_error_counts = Counter(
        source
        for error in errors
        for source in [_extract_error_source(error, unique_sources)]
        if source
    )
    sources_with_errors = sum(1 for source in unique_sources if source_error_counts.get(source, 0) > 0)

    field_missing_rates = {
        field_name: _rate(
            sum(1 for job in final_jobs if _field_is_missing(job, field_name)),
            final_count,
        )
        for field_name in QUALITY_TRACKED_FIELDS
    }

    source_record_coverage = _job_coverage_rate(
        final_jobs,
        lambda job: bool(job.source_record_id or str((job.metadata or {}).get("source_record_id", "")).strip()),
    )
    canonical_identity_coverage = _job_coverage_rate(
        final_jobs,
        lambda job: bool(job.canonical_identity_key or str((job.metadata or {}).get("canonical_identity_key", "")).strip()),
    )
    lineage_coverage = _job_coverage_rate(
        final_jobs,
        lambda job: bool(job.lineage_trail or (job.metadata or {}).get("lineage_trail")),
    )
    cross_source_merge_count = sum(
        1
        for job in deduped_jobs
        if bool((job.metadata or {}).get("cross_source_merged"))
    )

    return {
        "snapshot_kind": snapshot_kind,
        "job_counts": {
            "raw_collected": raw_count,
            "deduped": deduped_count,
            "final": final_count,
            "merged_duplicates": merged_duplicates,
            "filtered_out": filtered_out,
        },
        "dedupe_rate": _rate(merged_duplicates, raw_count),
        "cross_source_merge_rate": _rate(cross_source_merge_count, deduped_count),
        "source_failure_rate": _rate(sources_with_errors, len(unique_sources)),
        "source_failure_count": sources_with_errors,
        "source_count": len(unique_sources),
        "source_record_coverage_rate": source_record_coverage,
        "canonical_identity_coverage_rate": canonical_identity_coverage,
        "lineage_coverage_rate": lineage_coverage,
        "field_missing_rates": field_missing_rates,
        "source_stats": [
            {
                "source": source,
                "raw_count": int(raw_by_source.get(source, 0)),
                "deduped_count": int(deduped_by_source.get(source, 0)),
                "final_count": int(final_by_source.get(source, 0)),
                "error_count": int(source_error_counts.get(source, 0)),
                "failed": bool(source_error_counts.get(source, 0)),
            }
            for source in unique_sources
        ],
    }


def _extract_error_source(error: str, connector_sources: Iterable[str]) -> str:
    normalized = str(error or "").strip()
    for source in connector_sources:
        if normalized.startswith(f"{source}:") or normalized.startswith(f"{source} "):
            return source
    return ""


def _field_is_missing(job: JobListing, field_name: str) -> bool:
    value = getattr(job, field_name, "")
    if isinstance(value, list):
        return len(value) == 0
    if isinstance(value, dict):
        return len(value) == 0
    return not str(value or "").strip()


def _job_coverage_rate(jobs: list[JobListing], predicate) -> float:
    return _rate(sum(1 for job in jobs if predicate(job)), len(jobs))


def _rate(part: int, whole: int) -> float:
    if whole <= 0:
        return 0.0
    return round(float(part) / float(whole), 4)
