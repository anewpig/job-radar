from __future__ import annotations

import json
import secrets
from datetime import datetime
from typing import Any

from ..models import JobListing, SavedSearch


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def generate_line_bind_code(length: int = 6) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "LINE-" + "".join(secrets.choice(alphabet) for _ in range(length))


def generate_password_reset_code(length: int = 6) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def canonical_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                "enabled": bool(row.get("enabled", True)),
                "priority": int(row.get("priority", 1) or 1),
                "role": str(row.get("role", "")).strip(),
                "keywords": str(row.get("keywords", "")).strip(),
            }
        )
    return normalized


def signature_payload(
    rows: list[dict[str, Any]],
    custom_queries_text: str,
    crawl_preset_label: str,
) -> dict[str, Any]:
    custom_queries = [
        line.strip()
        for line in str(custom_queries_text).splitlines()
        if line.strip()
    ]
    return {
        "rows": canonical_rows(rows),
        "custom_queries": custom_queries,
        "crawl_preset_label": crawl_preset_label.strip() or "快速",
    }


def build_signature(
    rows: list[dict[str, Any]],
    custom_queries_text: str,
    crawl_preset_label: str,
) -> str:
    payload = signature_payload(rows, custom_queries_text, crawl_preset_label)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def row_to_saved_search(row: Any) -> SavedSearch:
    return SavedSearch(
        id=int(row[0]),
        name=str(row[1]),
        rows=json.loads(row[2] or "[]"),
        custom_queries_text=str(row[3]),
        crawl_preset_label=str(row[4]),
        signature=str(row[5]),
        known_job_urls=json.loads(row[6] or "[]"),
        last_run_at=str(row[7]),
        last_job_count=int(row[8]),
        last_new_job_count=int(row[9]),
        created_at=str(row[10]),
        updated_at=str(row[11]),
    )


def job_summary(job: JobListing) -> dict[str, Any]:
    return {
        "url": job.url,
        "title": job.title,
        "company": job.company,
        "source": job.source,
        "matched_role": job.matched_role,
        "relevance_score": round(job.relevance_score, 2),
        "salary": job.salary,
        "location": job.location,
    }
