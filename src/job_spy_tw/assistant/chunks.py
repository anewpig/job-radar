"""Assistant helpers for chunks."""

from __future__ import annotations

import hashlib
import json
from collections import Counter

from ..models import ItemInsight, JobListing, MarketSnapshot, ResumeProfile, SkillInsight
from .models import KnowledgeChunk


def build_chunks(
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    query_signature = build_query_signature(snapshot=snapshot, resume_profile=resume_profile)
    for index, job in enumerate(snapshot.jobs):
        role_label = job.matched_role or job.title
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"job-summary-{index}",
                source_type="job-summary",
                label=f"{job.title} @ {job.company}",
                url=job.url,
                text=job_summary_chunk(job),
                metadata=job_chunk_metadata(
                    job=job,
                    query_signature=query_signature,
                    source_type="job-summary",
                    role_label=role_label,
                ),
            )
        )
        if job.salary:
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"job-salary-{index}",
                    source_type="job-salary",
                    label=f"{job.title} 薪資資訊",
                    url=job.url,
                    text=job_salary_chunk(job),
                    metadata=job_chunk_metadata(
                        job=job,
                        query_signature=query_signature,
                        source_type="job-salary",
                        role_label=role_label,
                    ),
                )
            )
        if job.required_skill_items:
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"job-skills-{index}",
                    source_type="job-skills",
                    label=f"{job.title} 技能需求",
                    url=job.url,
                    text="；".join(job.required_skill_items[:12]),
                    metadata={
                        **job_chunk_metadata(
                            job=job,
                            query_signature=query_signature,
                            source_type="job-skills",
                            role_label=role_label,
                        ),
                        "skills": job.required_skill_items[:12],
                    },
                )
            )
        if job.work_content_items:
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"job-work-{index}",
                    source_type="job-work-content",
                    label=f"{job.title} 工作內容",
                    url=job.url,
                    text="；".join(job.work_content_items[:12]),
                    metadata={
                        **job_chunk_metadata(
                            job=job,
                            query_signature=query_signature,
                            source_type="job-work-content",
                            role_label=role_label,
                        ),
                        "tasks": job.work_content_items[:12],
                    },
                )
            )

    chunks.extend(
        insight_chunks(
            snapshot.skills,
            "market-skill-insight",
            "市場技能",
            query_signature=query_signature,
        )
    )
    chunks.extend(
        insight_chunks(
            snapshot.task_insights,
            "market-task-insight",
            "市場工作內容",
            query_signature=query_signature,
        )
    )
    chunks.extend(summary_chunks(snapshot=snapshot, query_signature=query_signature))

    if resume_profile is not None:
        chunks.append(
            KnowledgeChunk(
                chunk_id="resume-summary",
                source_type="resume-summary",
                label="履歷摘要",
                text=resume_profile.searchable_text(),
                metadata={
                    "roles": resume_profile.target_roles,
                    "core_skills": resume_profile.core_skills,
                    "tool_skills": resume_profile.tool_skills,
                    "domain_keywords": resume_profile.domain_keywords,
                    "source_name": resume_profile.source_name,
                    "query_signature": query_signature,
                    "source_type": "resume-summary",
                },
            )
        )
    return chunks


def build_query_signature(
    *,
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
) -> str:
    payload = {
        "queries": snapshot.queries,
        "role_targets": [
            {
                "name": role.name,
                "priority": role.priority,
                "keywords": role.keywords,
            }
            for role in snapshot.role_targets
        ],
        "resume_roles": resume_profile.target_roles if resume_profile else [],
        "resume_skills": (
            unique_ordered(resume_profile.core_skills + resume_profile.tool_skills)
            if resume_profile
            else []
        ),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def unique_ordered(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def job_chunk_metadata(
    *,
    job: JobListing,
    query_signature: str,
    source_type: str,
    role_label: str,
) -> dict[str, str]:
    return {
        "source": job.source,
        "url": job.url,
        "matched_role": role_label,
        "location": job.location,
        "salary": job.salary,
        "updated_at": job.posted_at,
        "source_type": source_type,
        "query_signature": query_signature,
        "company": job.company,
        "title": job.title,
    }


def job_summary_chunk(job: JobListing) -> str:
    return "\n".join(
        filter(
            None,
            [
                f"職稱：{job.title}",
                f"公司：{job.company}",
                f"來源：{job.source}",
                f"地點：{job.location}",
                f"薪資：{job.salary}",
                f"角色：{job.matched_role}",
                f"摘要：{job.summary}",
                f"技能：{'、'.join(job.extracted_skills)}",
            ],
        )
    )


def job_salary_chunk(job: JobListing) -> str:
    return "\n".join(
        filter(
            None,
            [
                f"職稱：{job.title}",
                f"公司：{job.company}",
                f"地點：{job.location}",
                f"薪資：{job.salary}",
                f"更新：{job.posted_at}",
                f"摘要：{job.summary}",
            ],
        )
    )


def insight_chunks(
    items: list[SkillInsight] | list[ItemInsight],
    source_type: str,
    label_prefix: str,
    *,
    query_signature: str,
) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for index, item in enumerate(items[:20]):
        item_name = getattr(item, "skill", getattr(item, "item", ""))
        text = "\n".join(
            filter(
                None,
                [
                    item_name,
                    f"重要度：{item.importance}",
                    f"出現次數：{item.occurrences}",
                    f"範例職缺：{'；'.join(item.sample_jobs[:3])}",
                ],
            )
        )
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{source_type}-{index}",
                source_type=source_type,
                label=f"{label_prefix}：{item_name}",
                text=text,
                metadata={
                    "query_signature": query_signature,
                    "source_type": source_type,
                    "occurrences": str(item.occurrences),
                    "importance": item.importance,
                    "sample_jobs": item.sample_jobs[:3],
                    "sources": item.sources[:4],
                },
            )
        )
    return chunks


def summary_chunks(
    *,
    snapshot: MarketSnapshot,
    query_signature: str,
) -> list[KnowledgeChunk]:
    jobs = snapshot.jobs
    source_counts = Counter(job.source for job in jobs if job.source)
    role_counts = Counter(job.matched_role for job in jobs if job.matched_role)
    location_counts = Counter(job.location for job in jobs if job.location)
    chunks: list[KnowledgeChunk] = []

    if source_counts:
        chunks.append(
            KnowledgeChunk(
                chunk_id="market-source-summary",
                source_type="market-source-summary",
                label="來源分布摘要",
                text=_counter_summary_text("來源", source_counts, jobs),
                metadata={
                    "query_signature": query_signature,
                    "source_type": "market-source-summary",
                    "top_sources": [name for name, _ in source_counts.most_common(5)],
                    "jobs_count": len(jobs),
                },
            )
        )
    if role_counts:
        chunks.append(
            KnowledgeChunk(
                chunk_id="market-role-summary",
                source_type="market-role-summary",
                label="角色分布摘要",
                text=_counter_summary_text("匹配角色", role_counts, jobs),
                metadata={
                    "query_signature": query_signature,
                    "source_type": "market-role-summary",
                    "top_roles": [name for name, _ in role_counts.most_common(5)],
                    "jobs_count": len(jobs),
                },
            )
        )
    if location_counts:
        chunks.append(
            KnowledgeChunk(
                chunk_id="market-location-summary",
                source_type="market-location-summary",
                label="地點分布摘要",
                text=_counter_summary_text("地點", location_counts, jobs),
                metadata={
                    "query_signature": query_signature,
                    "source_type": "market-location-summary",
                    "top_locations": [name for name, _ in location_counts.most_common(5)],
                    "jobs_count": len(jobs),
                },
            )
        )
    return chunks


def _counter_summary_text(label: str, counts: Counter[str], jobs: list[JobListing]) -> str:
    top_items = counts.most_common(5)
    lines = [
        f"總職缺數：{len(jobs)}",
        f"{label}分布：",
    ]
    lines.extend(f"- {name}：{count} 筆" for name, count in top_items)
    if top_items:
        lines.append(f"最多的是：{top_items[0][0]}（{top_items[0][1]} 筆）")
    return "\n".join(lines)
