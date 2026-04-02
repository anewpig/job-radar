from __future__ import annotations

from ..models import ItemInsight, JobListing, MarketSnapshot, ResumeProfile, SkillInsight
from .models import KnowledgeChunk


def build_chunks(
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for index, job in enumerate(snapshot.jobs):
        role_label = job.matched_role or job.title
        chunks.append(
            KnowledgeChunk(
                chunk_id=f"job-summary-{index}",
                source_type="job",
                label=f"{job.title} @ {job.company}",
                url=job.url,
                text=job_summary_chunk(job),
                metadata={"role": role_label, "source": job.source},
            )
        )
        if job.required_skill_items:
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"job-skills-{index}",
                    source_type="job-skill",
                    label=f"{job.title} 技能需求",
                    url=job.url,
                    text="；".join(job.required_skill_items[:12]),
                    metadata={"role": role_label},
                )
            )
        if job.work_content_items:
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"job-work-{index}",
                    source_type="job-work",
                    label=f"{job.title} 工作內容",
                    url=job.url,
                    text="；".join(job.work_content_items[:12]),
                    metadata={"role": role_label},
                )
            )

    chunks.extend(insight_chunks(snapshot.skills, "market-skill", "市場技能"))
    chunks.extend(insight_chunks(snapshot.task_insights, "market-task", "市場工作內容"))

    if resume_profile is not None:
        chunks.append(
            KnowledgeChunk(
                chunk_id="resume-summary",
                source_type="resume",
                label="履歷摘要",
                text=resume_profile.searchable_text(),
                metadata={"roles": resume_profile.target_roles},
            )
        )
    return chunks


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


def insight_chunks(
    items: list[SkillInsight] | list[ItemInsight],
    source_type: str,
    label_prefix: str,
) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for index, item in enumerate(items[:20]):
        text = "\n".join(
            filter(
                None,
                [
                    getattr(item, "skill", getattr(item, "item", "")),
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
                label=f"{label_prefix}：{getattr(item, 'skill', getattr(item, 'item', ''))}",
                text=text,
            )
        )
    return chunks
