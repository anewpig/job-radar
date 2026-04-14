"""Offline helpers for chunking and retrieval evaluation."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Callable

from ..models import JobListing, MarketSnapshot, ResumeProfile
from .chunks import (
    build_chunks,
    build_query_signature,
    insight_chunks,
    job_chunk_metadata,
    job_salary_chunk,
    job_summary_chunk,
    summary_chunks,
    unique_ordered,
)
from .models import KnowledgeChunk
from .retrieval import EmbeddingRetriever, prepare_embedding_text


ChunkBuilder = Callable[[MarketSnapshot, ResumeProfile | None], list[KnowledgeChunk]]


@dataclass(slots=True)
class RetrievalEvalCase:
    question: str
    expected_source_types: tuple[str, ...] = ()
    target_terms: tuple[str, ...] = ()
    description: str = ""


@dataclass(slots=True)
class RetrievalEvalCaseResult:
    case: RetrievalEvalCase
    retrieved: list[KnowledgeChunk]
    reciprocal_rank: float
    hit_at_1: bool
    hit_at_3: bool
    hit_at_5: bool
    source_hit: bool
    target_hit: bool


@dataclass(slots=True)
class RetrievalEvalSummary:
    strategy_name: str
    chunks_count: int
    cases: list[RetrievalEvalCaseResult]

    @property
    def case_count(self) -> int:
        return len(self.cases)

    @property
    def hit_at_1(self) -> float:
        return _average(1.0 if case.hit_at_1 else 0.0 for case in self.cases)

    @property
    def hit_at_3(self) -> float:
        return _average(1.0 if case.hit_at_3 else 0.0 for case in self.cases)

    @property
    def hit_at_5(self) -> float:
        return _average(1.0 if case.hit_at_5 else 0.0 for case in self.cases)

    @property
    def mrr(self) -> float:
        return _average(case.reciprocal_rank for case in self.cases)

    @property
    def source_hit_rate(self) -> float:
        return _average(1.0 if case.source_hit else 0.0 for case in self.cases)

    @property
    def target_hit_rate(self) -> float:
        targeted = [case for case in self.cases if case.case.target_terms]
        if not targeted:
            return 0.0
        return _average(1.0 if case.target_hit else 0.0 for case in targeted)


def _average(values) -> float:
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)


def build_itemized_chunks(
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
) -> list[KnowledgeChunk]:
    return _build_itemized_chunks(
        snapshot=snapshot,
        resume_profile=resume_profile,
        anchor_text=False,
        detail_window_size=3,
    )


def build_anchored_itemized_chunks(
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
) -> list[KnowledgeChunk]:
    return _build_itemized_chunks(
        snapshot=snapshot,
        resume_profile=resume_profile,
        anchor_text=True,
        detail_window_size=3,
    )


def build_anchored_windowed_chunks(
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
) -> list[KnowledgeChunk]:
    return _build_itemized_chunks(
        snapshot=snapshot,
        resume_profile=resume_profile,
        anchor_text=True,
        detail_window_size=2,
    )


def _build_itemized_chunks(
    *,
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
    anchor_text: bool,
    detail_window_size: int,
) -> list[KnowledgeChunk]:
    query_signature = build_query_signature(snapshot=snapshot, resume_profile=resume_profile)
    chunks: list[KnowledgeChunk] = []

    for job_index, job in enumerate(snapshot.jobs):
        role_label = job.matched_role or job.title
        base_metadata = job_chunk_metadata(
            job=job,
            query_signature=query_signature,
            source_type="job-summary",
            role_label=role_label,
        )

        chunks.append(
            KnowledgeChunk(
                chunk_id=f"job-summary-{job_index}",
                source_type="job-summary",
                label=f"{job.title} @ {job.company}",
                url=job.url,
                text=_anchored_job_text(
                    job=job,
                    body=job_summary_chunk(job),
                    anchor_text=anchor_text,
                    section_label="摘要",
                ),
                metadata=base_metadata,
            )
        )

        if job.salary:
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"job-salary-{job_index}",
                    source_type="job-salary",
                    label=f"{job.title} 薪資資訊",
                    url=job.url,
                    text=_anchored_job_text(
                        job=job,
                        body=job_salary_chunk(job),
                        anchor_text=anchor_text,
                        section_label="薪資",
                    ),
                    metadata={
                        **base_metadata,
                        "source_type": "job-salary",
                    },
                )
            )

        skill_items = unique_ordered(job.required_skill_items or job.extracted_skills)
        for skill_index, skill in enumerate(skill_items[:16]):
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"job-skill-item-{job_index}-{skill_index}",
                    source_type="job-skills",
                    label=f"{job.title} 技能：{skill}",
                    url=job.url,
                    text=_anchored_job_text(
                        job=job,
                        body=skill,
                        anchor_text=anchor_text,
                        section_label="技能",
                    ),
                    metadata={
                        **base_metadata,
                        "source_type": "job-skills",
                        "skills": [skill],
                    },
                )
            )

        for task_index, task in enumerate(job.work_content_items[:18]):
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"job-task-item-{job_index}-{task_index}",
                    source_type="job-work-content",
                    label=f"{job.title} 工作內容 {task_index + 1}",
                    url=job.url,
                    text=_anchored_job_text(
                        job=job,
                        body=task,
                        anchor_text=anchor_text,
                        section_label="工作內容",
                    ),
                    metadata={
                        **base_metadata,
                        "source_type": "job-work-content",
                        "tasks": [task],
                    },
                )
            )

        for requirement_index, requirement in enumerate(job.requirement_items[:12]):
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"job-requirement-item-{job_index}-{requirement_index}",
                    source_type="job-skills",
                    label=f"{job.title} 條件 {requirement_index + 1}",
                    url=job.url,
                    text=_anchored_job_text(
                        job=job,
                        body=requirement,
                        anchor_text=anchor_text,
                        section_label="條件",
                    ),
                    metadata={
                        **base_metadata,
                        "source_type": "job-skills",
                        "requirements": [requirement],
                    },
                )
            )

        chunks.extend(
            _detail_section_chunks(
                job=job,
                job_index=job_index,
                query_signature=query_signature,
                role_label=role_label,
                anchor_text=anchor_text,
                detail_window_size=detail_window_size,
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
        for label, values in (
            ("目標角色", resume_profile.target_roles),
            ("核心技能", resume_profile.core_skills),
            ("工具技能", resume_profile.tool_skills),
            ("領域關鍵字", resume_profile.domain_keywords),
        ):
            if not values:
                continue
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"resume-{label}",
                    source_type="resume-summary",
                    label=f"履歷{label}",
                    text="；".join(values),
                    metadata={
                        "query_signature": query_signature,
                        "source_type": "resume-summary",
                        "roles": resume_profile.target_roles,
                        "core_skills": resume_profile.core_skills,
                        "tool_skills": resume_profile.tool_skills,
                        "domain_keywords": resume_profile.domain_keywords,
                        "source_name": resume_profile.source_name,
                    },
                )
            )
    return chunks


def build_hybrid_chunks(
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
) -> list[KnowledgeChunk]:
    deduped: list[KnowledgeChunk] = []
    seen: set[tuple[str, str, str, str]] = set()
    for chunk in [*build_chunks(snapshot, resume_profile), *build_itemized_chunks(snapshot, resume_profile)]:
        key = (chunk.source_type, chunk.label, chunk.text, chunk.url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(chunk)
    return deduped


def build_anchored_hybrid_chunks(
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
) -> list[KnowledgeChunk]:
    deduped: list[KnowledgeChunk] = []
    seen: set[tuple[str, str, str, str]] = set()
    for chunk in [*build_chunks(snapshot, resume_profile), *build_anchored_itemized_chunks(snapshot, resume_profile)]:
        key = (chunk.source_type, chunk.label, chunk.text, chunk.url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(chunk)
    return deduped


def build_anchored_compact_market_hybrid_chunks(
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
) -> list[KnowledgeChunk]:
    query_signature = build_query_signature(snapshot=snapshot, resume_profile=resume_profile)
    base_chunks = _build_itemized_chunks(
        snapshot=snapshot,
        resume_profile=resume_profile,
        anchor_text=True,
        detail_window_size=3,
    )
    base_chunks = [
        chunk
        for chunk in base_chunks
        if chunk.source_type
        not in {
            "market-skill-insight",
            "market-task-insight",
            "market-source-summary",
            "market-role-summary",
            "market-location-summary",
        }
    ]

    compact_market_chunks = [
        *insight_chunks(
            snapshot.skills[:8],
            "market-skill-insight",
            "市場技能",
            query_signature=query_signature,
        ),
        *insight_chunks(
            snapshot.task_insights[:8],
            "market-task-insight",
            "市場工作內容",
            query_signature=query_signature,
        ),
        *summary_chunks(snapshot=snapshot, query_signature=query_signature),
    ]

    deduped: list[KnowledgeChunk] = []
    seen: set[tuple[str, str, str, str]] = set()
    for chunk in [*build_chunks(snapshot, resume_profile), *base_chunks, *compact_market_chunks]:
        key = (chunk.source_type, chunk.label, chunk.text, chunk.url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(chunk)
    return deduped


def _detail_section_chunks(
    *,
    job: JobListing,
    job_index: int,
    query_signature: str,
    role_label: str,
    anchor_text: bool,
    detail_window_size: int,
) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    if not job.detail_sections:
        return chunks

    for section_name, raw_text in job.detail_sections.items():
        lines = [line.strip(" \t•-") for line in str(raw_text).splitlines() if line.strip()]
        if not lines:
            continue
        source_type = _section_source_type(section_name)
        for window_start in range(0, len(lines), detail_window_size):
            window = lines[window_start : window_start + detail_window_size]
            if not window:
                continue
            chunks.append(
                KnowledgeChunk(
                    chunk_id=f"job-section-{job_index}-{section_name}-{window_start}",
                    source_type=source_type,
                    label=f"{job.title} {section_name} {window_start // detail_window_size + 1}",
                    url=job.url,
                    text=_anchored_job_text(
                        job=job,
                        body="\n".join(window),
                        anchor_text=anchor_text,
                        section_label=section_name,
                    ),
                    metadata={
                        **job_chunk_metadata(
                            job=job,
                            query_signature=query_signature,
                            source_type=source_type,
                            role_label=role_label,
                        ),
                        "detail_section": section_name,
                    },
                )
            )
    return chunks


def _section_source_type(section_name: str) -> str:
    normalized = section_name.strip().lower()
    if normalized in {"work_content", "job_description", "responsibilities"}:
        return "job-work-content"
    if normalized in {"required_skills", "requirements", "qualifications"}:
        return "job-skills"
    return "job-summary"


def _anchored_job_text(
    *,
    job: JobListing,
    body: str,
    anchor_text: bool,
    section_label: str,
) -> str:
    if not anchor_text:
        return body
    anchor_lines = [
        f"職缺：{job.title}",
        f"公司：{job.company}",
    ]
    if job.matched_role:
        anchor_lines.append(f"角色：{job.matched_role}")
    if section_label:
        anchor_lines.append(f"段落：{section_label}")
    anchor_lines.append(f"內容：{body}")
    return "\n".join(anchor_lines)


def _market_eval_cases(*, realistic: bool) -> list[RetrievalEvalCase]:
    if realistic:
        return [
            RetrievalEvalCase(
                question="如果先看整體市場，這批職缺最常提到哪些技能？",
                expected_source_types=("market-skill-insight", "job-skills"),
                description="市場技能題",
            ),
            RetrievalEvalCase(
                question="這波職缺大多在做哪些事情？",
                expected_source_types=("market-task-insight", "job-work-content"),
                description="市場工作內容題",
            ),
            RetrievalEvalCase(
                question="這批缺主要都來自哪些平台？",
                expected_source_types=("market-source-summary",),
                description="來源分布題",
            ),
            RetrievalEvalCase(
                question="這批機會比較集中在哪些地區？",
                expected_source_types=("market-location-summary",),
                description="地點分布題",
            ),
            RetrievalEvalCase(
                question="如果看整體，這批職缺大多對應什麼角色？",
                expected_source_types=("market-role-summary",),
                description="角色分布題",
            ),
        ]

    return [
        RetrievalEvalCase(
            question="目前這批職缺最常見的技能是什麼？",
            expected_source_types=("market-skill-insight", "job-skills"),
            description="市場技能題",
        ),
        RetrievalEvalCase(
            question="目前這批職缺常見的工作內容是什麼？",
            expected_source_types=("market-task-insight", "job-work-content"),
            description="市場工作內容題",
        ),
        RetrievalEvalCase(
            question="目前這批職缺的來源分布如何？",
            expected_source_types=("market-source-summary",),
            description="來源分布題",
        ),
        RetrievalEvalCase(
            question="目前這批職缺主要集中在哪些地點？",
            expected_source_types=("market-location-summary",),
            description="地點分布題",
        ),
        RetrievalEvalCase(
            question="目前這批職缺主要對應哪些角色？",
            expected_source_types=("market-role-summary",),
            description="角色分布題",
        ),
    ]


def _salary_eval_case(*, realistic: bool) -> RetrievalEvalCase:
    if realistic:
        return RetrievalEvalCase(
            question="如果先看整體，這批職缺的薪資大概落在哪個範圍？",
            expected_source_types=("job-salary", "job-summary"),
            description="薪資分布題",
        )
    return RetrievalEvalCase(
        question="目前這批職缺的薪資大概落在哪個區間？",
        expected_source_types=("job-salary", "job-summary"),
        description="薪資分布題",
    )


def _job_specific_eval_cases(snapshot: MarketSnapshot, *, realistic: bool) -> list[RetrievalEvalCase]:
    cases: list[RetrievalEvalCase] = []
    content_rich_jobs = [
        job
        for job in snapshot.jobs
        if job.work_content_items or job.required_skill_items or job.extracted_skills
    ]

    for index, job in enumerate(content_rich_jobs[:6]):
        target_terms = tuple(term for term in (job.title, job.company) if term)
        if job.work_content_items:
            work_question = (
                _build_realistic_job_work_question(job.title, index)
                if realistic
                else f"{job.title} 這個職缺主要在做什麼？"
            )
            cases.append(
                RetrievalEvalCase(
                    question=work_question,
                    expected_source_types=("job-work-content", "job-summary"),
                    target_terms=target_terms,
                    description="職缺工作內容題",
                )
            )
        if job.required_skill_items or job.extracted_skills:
            skill_question = (
                _build_realistic_job_skill_question(job.title, index)
                if realistic
                else f"{job.title} 這個職缺需要哪些技能？"
            )
            cases.append(
                RetrievalEvalCase(
                    question=skill_question,
                    expected_source_types=("job-skills", "job-summary"),
                    target_terms=target_terms,
                    description="職缺技能題",
                )
            )
        if job.salary:
            salary_question = (
                _build_realistic_job_salary_question(job.title, index)
                if realistic
                else f"{job.title} 這個職缺的薪資怎麼寫？"
            )
            cases.append(
                RetrievalEvalCase(
                    question=salary_question,
                    expected_source_types=("job-salary", "job-summary"),
                    target_terms=target_terms,
                    description="職缺薪資題",
                )
            )
    return cases


def _build_realistic_job_work_question(title: str, index: int) -> str:
    variants = (
        f"如果看 {title} 這個缺，主要會負責哪些事情？",
        f"{title} 這份工作日常大多在做什麼？",
        f"我想知道 {title} 這個職缺的工作重點是什麼。",
    )
    return variants[index % len(variants)]


def _build_realistic_job_skill_question(title: str, index: int) -> str:
    variants = (
        f"如果要投 {title}，通常要先準備哪些技能？",
        f"{title} 這個缺大概需要會哪些工具或能力？",
        f"{title} 這份工作比較看重哪些技能？",
    )
    return variants[index % len(variants)]


def _build_realistic_job_salary_question(title: str, index: int) -> str:
    variants = (
        f"如果投 {title}，薪資大概開多少？",
        f"{title} 這個缺的薪資範圍大概怎麼看？",
        f"{title} 這份工作的待遇通常怎麼寫？",
    )
    return variants[index % len(variants)]


def build_default_eval_cases(snapshot: MarketSnapshot) -> list[RetrievalEvalCase]:
    cases: list[RetrievalEvalCase] = _market_eval_cases(realistic=False)

    if any(job.salary for job in snapshot.jobs):
        cases.append(_salary_eval_case(realistic=False))

    cases.extend(_job_specific_eval_cases(snapshot, realistic=False))
    return cases


def build_realistic_eval_cases(snapshot: MarketSnapshot) -> list[RetrievalEvalCase]:
    cases: list[RetrievalEvalCase] = _market_eval_cases(realistic=True)

    if any(job.salary for job in snapshot.jobs):
        cases.append(_salary_eval_case(realistic=True))

    cases.extend(_job_specific_eval_cases(snapshot, realistic=True))
    return cases


def build_all_eval_cases(snapshot: MarketSnapshot) -> list[RetrievalEvalCase]:
    deduped: list[RetrievalEvalCase] = []
    seen: set[tuple[str, tuple[str, ...], tuple[str, ...], str]] = set()
    for case in [*build_default_eval_cases(snapshot), *build_realistic_eval_cases(snapshot)]:
        key = (
            case.question,
            case.expected_source_types,
            case.target_terms,
            case.description,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(case)
    return deduped


def evaluate_chunking_strategy(
    *,
    strategy_name: str,
    chunk_builder: ChunkBuilder,
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
    cases: list[RetrievalEvalCase],
    retriever: EmbeddingRetriever,
    top_k: int = 5,
) -> RetrievalEvalSummary:
    chunks = chunk_builder(snapshot, resume_profile)
    results = [
        _evaluate_case(
            case=case,
            chunks=chunks,
            retriever=retriever,
            top_k=top_k,
        )
        for case in cases
    ]
    return RetrievalEvalSummary(
        strategy_name=strategy_name,
        chunks_count=len(chunks),
        cases=results,
    )


def _evaluate_case(
    *,
    case: RetrievalEvalCase,
    chunks: list[KnowledgeChunk],
    retriever: EmbeddingRetriever,
    top_k: int,
) -> RetrievalEvalCaseResult:
    retrieved = retriever.retrieve(question=case.question, chunks=chunks, top_k=top_k)
    reciprocal_rank = 0.0
    for index, chunk in enumerate(retrieved, start=1):
        if _chunk_matches_case(chunk, case):
            reciprocal_rank = 1.0 / index
            break

    hit_at_1 = any(_chunk_matches_case(chunk, case) for chunk in retrieved[:1])
    hit_at_3 = any(_chunk_matches_case(chunk, case) for chunk in retrieved[:3])
    hit_at_5 = any(_chunk_matches_case(chunk, case) for chunk in retrieved[:5])
    source_hit = any(_chunk_matches_source(chunk, case.expected_source_types) for chunk in retrieved)
    target_hit = any(_chunk_matches_target(chunk, case.target_terms) for chunk in retrieved)
    return RetrievalEvalCaseResult(
        case=case,
        retrieved=retrieved,
        reciprocal_rank=reciprocal_rank,
        hit_at_1=hit_at_1,
        hit_at_3=hit_at_3,
        hit_at_5=hit_at_5,
        source_hit=source_hit,
        target_hit=target_hit,
    )


def _chunk_matches_case(chunk: KnowledgeChunk, case: RetrievalEvalCase) -> bool:
    source_ok = _chunk_matches_source(chunk, case.expected_source_types)
    target_ok = _chunk_matches_target(chunk, case.target_terms)
    if case.expected_source_types and case.target_terms:
        return source_ok and target_ok
    if case.expected_source_types:
        return source_ok
    if case.target_terms:
        return target_ok
    return True


def _chunk_matches_source(chunk: KnowledgeChunk, expected_source_types: tuple[str, ...]) -> bool:
    if not expected_source_types:
        return True
    return chunk.source_type in expected_source_types


def _chunk_matches_target(chunk: KnowledgeChunk, target_terms: tuple[str, ...]) -> bool:
    if not target_terms:
        return True
    haystack = prepare_embedding_text(chunk.combined_text()).lower()
    return any(prepare_embedding_text(term).lower() in haystack for term in target_terms if term.strip())


class LocalHashEmbeddingsAPI:
    def __init__(self, *, dimensions: int = 96) -> None:
        self.dimensions = dimensions

    def create(self, *, model, input):  # noqa: A002
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=_hash_embed(text, self.dimensions)) for text in input]
        )


class LocalHashEmbeddingClient:
    def __init__(self, *, dimensions: int = 96) -> None:
        self.embeddings = LocalHashEmbeddingsAPI(dimensions=dimensions)


def _hash_embed(text: str, dimensions: int) -> list[float]:
    vector = [0.0] * dimensions
    tokens = prepare_embedding_text(text).lower().split()
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dimensions
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
