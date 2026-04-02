from __future__ import annotations

import io
import json
import re
import zipfile

import pandas as pd

from ..models import FavoriteJob, ItemInsight, MarketSnapshot, ResumeJobMatch, SkillInsight


def sanitize_export_name(value: str, fallback: str = "job_radar") -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", str(value or "").strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")
    return cleaned or fallback


def flatten_job_download_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    download_frame = frame.copy()
    for column in ("work_content_items", "required_skill_items", "requirement_items"):
        if column in download_frame.columns:
            download_frame[column] = download_frame[column].apply(
                lambda items: " | ".join(items or [])
            )
    return download_frame


def filter_jobs_frame(
    frame: pd.DataFrame,
    *,
    source_filter: list[str] | None = None,
    role_filter: list[str] | None = None,
    skill_filter: list[str] | None = None,
) -> pd.DataFrame:
    if frame.empty or "relevance_score" not in frame.columns:
        return frame.copy()
    filtered = frame.copy()
    if source_filter:
        filtered = filtered[filtered["source"].isin(source_filter)]
    if role_filter:
        filtered = filtered[filtered["matched_role"].isin(role_filter)]
    if skill_filter:
        regex = "|".join(re.escape(item) for item in skill_filter if item)
        if regex:
            filtered = filtered[filtered["skills"].str.contains(regex, na=False)]
    return filtered.sort_values("relevance_score", ascending=False)


def build_export_bundle(
    *,
    full_jobs_frame: pd.DataFrame,
    filtered_jobs_frame: pd.DataFrame,
    skill_frame: pd.DataFrame,
    task_frame: pd.DataFrame,
    resume_match_frame: pd.DataFrame | None,
    metadata: dict[str, object],
) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "jobs_full.csv",
            flatten_job_download_frame(full_jobs_frame).to_csv(index=False).encode("utf-8-sig"),
        )
        archive.writestr(
            "jobs_filtered.csv",
            flatten_job_download_frame(filtered_jobs_frame).to_csv(index=False).encode("utf-8-sig"),
        )
        archive.writestr(
            "skills.csv",
            skill_frame.to_csv(index=False).encode("utf-8-sig"),
        )
        archive.writestr(
            "tasks.csv",
            task_frame.to_csv(index=False).encode("utf-8-sig"),
        )
        if resume_match_frame is not None and not resume_match_frame.empty:
            archive.writestr(
                "resume_matches.csv",
                resume_match_frame.to_csv(index=False).encode("utf-8-sig"),
            )
        archive.writestr(
            "metadata.json",
            json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"),
        )
    return buffer.getvalue()


def jobs_to_frame(snapshot: MarketSnapshot) -> pd.DataFrame:
    rows = []
    for job in snapshot.jobs:
        rows.append(
            {
                "source": job.source,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary": job.salary,
                "posted_at": job.posted_at,
                "matched_role": job.matched_role,
                "relevance_score": job.relevance_score,
                "skills": ", ".join(job.extracted_skills),
                "work_content_items": job.work_content_items,
                "required_skill_items": job.required_skill_items,
                "requirement_items": job.requirement_items,
                "work_content_count": len(job.work_content_items),
                "required_skill_count": len(job.required_skill_items),
                "summary": job.summary,
                "url": job.url,
            }
        )
    return pd.DataFrame(rows)


def skills_to_frame(skills: list[SkillInsight]) -> pd.DataFrame:
    rows = []
    for skill in skills:
        rows.append(
            {
                "skill": skill.skill,
                "category": skill.category,
                "importance": skill.importance,
                "score": skill.score,
                "occurrences": skill.occurrences,
                "sources": ", ".join(skill.sources),
                "sample_jobs": " | ".join(skill.sample_jobs),
            }
        )
    return pd.DataFrame(rows)


def task_insights_to_frame(items: list[ItemInsight]) -> pd.DataFrame:
    rows = []
    for item in items:
        rows.append(
            {
                "item": item.item,
                "importance": item.importance,
                "score": item.score,
                "occurrences": item.occurrences,
                "sources": ", ".join(item.sources),
                "sample_jobs": " | ".join(item.sample_jobs),
            }
        )
    return pd.DataFrame(rows)


def resume_matches_to_frame(matches: list[ResumeJobMatch]) -> pd.DataFrame:
    rows = []
    for match in matches:
        rows.append(
            {
                "overall_score": match.overall_score,
                "market_fit_score": match.market_fit_score,
                "role_score": match.role_score,
                "skill_score": match.skill_score,
                "task_score": match.task_score,
                "exact_match_score": match.exact_match_score,
                "keyword_score": match.keyword_score,
                "title_similarity": match.title_similarity,
                "semantic_similarity": match.semantic_similarity,
                "title_reason": match.title_reason,
                "scoring_method": match.scoring_method,
                "matched_role": match.matched_role,
                "source": match.source,
                "title": match.title,
                "company": match.company,
                "matched_skills": "、".join(match.matched_skills),
                "matched_tasks": "、".join(match.matched_tasks),
                "matched_keywords": "、".join(match.matched_keywords),
                "missing_skills": "、".join(match.missing_skills),
                "missing_tasks": "、".join(match.missing_tasks),
                "fit_summary": match.fit_summary,
                "reasons": " | ".join(match.reasons),
                "url": match.job_url,
            }
        )
    return pd.DataFrame(rows)


def favorites_to_frame(favorites: list[FavoriteJob]) -> pd.DataFrame:
    rows = []
    for favorite in favorites:
        rows.append(
            {
                "saved_at": favorite.saved_at,
                "source": favorite.source,
                "title": favorite.title,
                "company": favorite.company,
                "matched_role": favorite.matched_role,
                "location": favorite.location,
                "salary": favorite.salary,
                "job_url": favorite.job_url,
            }
        )
    return pd.DataFrame(rows)
