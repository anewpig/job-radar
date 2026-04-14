"""Assistant helpers for chunks."""

from __future__ import annotations

import hashlib
import json
from collections import Counter

from ..models import ItemInsight, JobListing, MarketSnapshot, ResumeProfile, SkillInsight
from ..resume.text import build_resume_line_windows
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
        skill_items = _job_skill_items(job)
        if skill_items or job.requirement_items:
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"job-skills-{index}",
                    source_type="job-skills",
                    label=f"{job.title} 技能需求",
                    url=job.url,
                    text=job_skills_chunk(
                        job=job,
                        role_label=role_label,
                        skill_items=skill_items,
                    ),
                    metadata={
                        **job_chunk_metadata(
                            job=job,
                            query_signature=query_signature,
                            source_type="job-skills",
                            role_label=role_label,
                        ),
                        "skills": skill_items[:12],
                        "requirements": job.requirement_items[:6],
                    },
                )
            )
            chunks.extend(
                job_item_chunks(
                    job=job,
                    query_signature=query_signature,
                    role_label=role_label,
                    source_type="job-skills",
                    items=skill_items[:8] or job.requirement_items[:4],
                    chunk_prefix=f"job-skill-item-{index}",
                    label_prefix="技能",
                )
            )
        if job.work_content_items:
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"job-work-{index}",
                    source_type="job-work-content",
                    label=f"{job.title} 工作內容",
                    url=job.url,
                    text=job_work_chunk(
                        job=job,
                        role_label=role_label,
                    ),
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
                job_item_chunks(
                    job=job,
                    query_signature=query_signature,
                    role_label=role_label,
                    source_type="job-work-content",
                    items=job.work_content_items[:8],
                    chunk_prefix=f"job-task-item-{index}",
                    label_prefix="工作內容",
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
        chunks.extend(
            resume_chunks(
                resume_profile=resume_profile,
                query_signature=query_signature,
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


def resume_chunks(
    *,
    resume_profile: ResumeProfile,
    query_signature: str,
) -> list[KnowledgeChunk]:
    """Build structured resume chunks for more grounded personalized retrieval."""
    base_metadata = {
        "roles": resume_profile.target_roles,
        "core_skills": resume_profile.core_skills,
        "tool_skills": resume_profile.tool_skills,
        "domain_keywords": resume_profile.domain_keywords,
        "preferred_tasks": resume_profile.preferred_tasks,
        "source_name": resume_profile.source_name,
        "query_signature": query_signature,
        "source_type": "resume-summary",
    }
    chunks = [
        KnowledgeChunk(
            chunk_id="resume-summary",
            source_type="resume-summary",
            label="履歷摘要",
            text=resume_summary_chunk(resume_profile),
            metadata={**base_metadata, "chunk_kind": "summary"},
        )
    ]
    field_specs = (
        ("resume-target-roles", "履歷目標角色", "目標角色", resume_profile.target_roles),
        ("resume-core-skills", "履歷核心技能", "核心技能", resume_profile.core_skills),
        ("resume-tool-skills", "履歷工具技能", "工具技能", resume_profile.tool_skills),
        ("resume-domain-keywords", "履歷領域關鍵字", "領域關鍵字", resume_profile.domain_keywords),
        ("resume-preferred-tasks", "履歷偏好工作內容", "偏好工作內容", resume_profile.preferred_tasks),
        ("resume-match-keywords", "履歷匹配關鍵字", "匹配關鍵字", resume_profile.match_keywords),
    )
    for chunk_id, label, prefix, values in field_specs:
        normalized_values = unique_ordered([str(value).strip() for value in values if str(value).strip()])
        if not normalized_values:
            continue
        chunks.append(
            KnowledgeChunk(
                chunk_id=chunk_id,
                source_type="resume-summary",
                label=label,
                text=f"{prefix}：{'；'.join(normalized_values[:12])}",
                metadata={**base_metadata, "chunk_kind": prefix},
            )
        )
    for index, window in enumerate(build_resume_line_windows(resume_profile.raw_text), start=1):
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"resume-window-{index}",
                source_type="resume-summary",
                label=f"履歷經歷片段 {index}",
                text=f"履歷片段：{window}",
                metadata={**base_metadata, "chunk_kind": "raw_window"},
            )
        )
    return chunks


def resume_summary_chunk(resume_profile: ResumeProfile) -> str:
    lines = [
        f"履歷摘要：{resume_profile.summary}" if resume_profile.summary else "",
        f"目標角色：{'；'.join(unique_ordered(resume_profile.target_roles)[:6])}" if resume_profile.target_roles else "",
        f"核心技能：{'；'.join(unique_ordered(resume_profile.core_skills)[:10])}" if resume_profile.core_skills else "",
        f"工具技能：{'；'.join(unique_ordered(resume_profile.tool_skills)[:10])}" if resume_profile.tool_skills else "",
        f"領域關鍵字：{'；'.join(unique_ordered(resume_profile.domain_keywords)[:10])}" if resume_profile.domain_keywords else "",
        f"偏好工作內容：{'；'.join(unique_ordered(resume_profile.preferred_tasks)[:8])}" if resume_profile.preferred_tasks else "",
    ]
    return "\n".join(line for line in lines if line)


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


def job_skills_chunk(
    *,
    job: JobListing,
    role_label: str,
    skill_items: list[str],
) -> str:
    return "\n".join(
        filter(
            None,
            [
                f"職缺：{job.title}",
                f"公司：{job.company}",
                f"角色：{role_label}",
                f"技能：{'；'.join(skill_items[:12])}" if skill_items else "",
                f"條件：{'；'.join(job.requirement_items[:6])}" if job.requirement_items else "",
            ],
        )
    )


def job_work_chunk(
    *,
    job: JobListing,
    role_label: str,
) -> str:
    return "\n".join(
        filter(
            None,
            [
                f"職缺：{job.title}",
                f"公司：{job.company}",
                f"角色：{role_label}",
                f"內容：{'；'.join(job.work_content_items[:12])}",
            ],
        )
    )


def job_item_chunks(
    *,
    job: JobListing,
    query_signature: str,
    role_label: str,
    source_type: str,
    items: list[str],
    chunk_prefix: str,
    label_prefix: str,
) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for index, item in enumerate(items):
        normalized = str(item).strip()
        if not normalized:
            continue
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"{chunk_prefix}-{index}",
                source_type=source_type,
                label=f"{job.title} {label_prefix}：{normalized}",
                url=job.url,
                text="\n".join(
                    filter(
                        None,
                        [
                            f"職缺：{job.title}",
                            f"公司：{job.company}",
                            f"角色：{role_label}",
                            f"{label_prefix}：{normalized}",
                        ],
                    )
                ),
                metadata={
                    **job_chunk_metadata(
                        job=job,
                        query_signature=query_signature,
                        source_type=source_type,
                        role_label=role_label,
                    ),
                    "item": normalized,
                },
            )
        )
    return chunks


def _job_skill_items(job: JobListing) -> list[str]:
    if job.required_skill_items:
        return unique_ordered(job.required_skill_items)
    if job.extracted_skills:
        return unique_ordered(job.extracted_skills)
    return []


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
                    "score": str(getattr(item, "score", 0)),
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
