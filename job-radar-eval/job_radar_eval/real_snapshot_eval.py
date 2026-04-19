"""真實快照評估：讀取 jobs_latest.json 做 smoke / health 檢查。"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

from .fake_clients import FakeEmbeddingsAPI
from .fixtures import build_resume_profile_fixture, load_real_snapshot, top_counter_values
from .metrics import average, keyword_recall, p95, set_recall
from .reporting import _render_mode_breakdown_markdown


class StructuredSmokeResponsesAPI:
    """回傳固定結構化 JSON，讓真實快照只檢查流程與引用，不評分語意生成。"""

    def create(self, **kwargs):
        payload = {
            "summary": "已根據目前快照整理答案。",
            "key_points": ["已引用與問題相關的職缺或統計片段。"],
            "limitations": ["這是 smoke eval，只檢查流程穩定性與引用可用性，不評分語意正確性。"],
            "next_step": "檢查引用內容是否和問題對齊。",
        }
        return SimpleNamespace(output_text=json.dumps(payload, ensure_ascii=False))


class RealSnapshotFakeOpenAIClient:
    """真實快照評估用 fake client：embedding 真跑、response 只回固定 JSON。"""

    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsAPI()
        self.responses = StructuredSmokeResponsesAPI()


@dataclass(slots=True)
class RealAssistantCaseResult:
    case_id: str
    question: str
    answer_mode: str
    iterations: int
    total_ms_mean: float
    total_ms_p95: float
    response_nonempty_rate: float
    structured_output_rate: float
    citation_ok_rate: float
    top_citation_type_hit_rate: float
    citation_keyword_recall_mean: float
    evidence_sufficiency_rate: float
    used_chunks_mean: float


@dataclass(slots=True)
class RealRetrievalCaseResult:
    case_id: str
    question: str
    iterations: int
    cold_ms_mean: float
    warm_ms_mean: float
    cold_ms_p95: float
    warm_ms_p95: float
    speedup_ratio_mean: float
    top1_type_hit_rate: float
    expected_type_recall_mean: float
    latest_top_chunk_type: str
    latest_top_chunk_label: str


@dataclass(slots=True)
class RealResumeCaseResult:
    case_id: str
    iterations: int
    build_profile_ms_mean: float
    match_jobs_ms_mean: float
    total_ms_mean: float
    total_ms_p95: float
    top3_url_hit_rate: float
    top1_role_match_rate: float
    matched_skill_recall_mean: float
    latest_top_job_url: str


def _coverage_rate(flags: list[bool]) -> float:
    return (sum(1 for flag in flags if flag) / len(flags)) if flags else 0.0


def build_snapshot_health(config, snapshot_path: Path | None = None) -> dict:
    snapshot = load_real_snapshot(config, snapshot_path=snapshot_path)
    jobs = snapshot.jobs
    return {
        "snapshot_path": str((snapshot_path or config.snapshot_path).resolve()),
        "generated_at": snapshot.generated_at,
        "jobs_count": len(jobs),
        "queries_count": len(snapshot.queries),
        "role_targets_count": len(snapshot.role_targets),
        "role_target_names": [role.name for role in snapshot.role_targets],
        "sources_count": len({job.source for job in jobs if job.source}),
        "roles_count": len({job.matched_role for job in jobs if job.matched_role}),
        "salary_coverage_rate": round(_coverage_rate([bool(job.salary.strip()) for job in jobs]), 4),
        "description_coverage_rate": round(_coverage_rate([bool(job.description.strip()) for job in jobs]), 4),
        "work_content_coverage_rate": round(
            _coverage_rate([bool(job.work_content_items or job.detail_sections.get("work_content", "").strip()) for job in jobs]),
            4,
        ),
        "required_skill_coverage_rate": round(_coverage_rate([bool(job.required_skill_items) for job in jobs]), 4),
        "task_insights_count": len(snapshot.task_insights),
        "skills_count": len(snapshot.skills),
        "errors_count": len(snapshot.errors),
        "top_sources": top_counter_values([job.source for job in jobs], limit=5),
        "top_roles": top_counter_values([job.matched_role for job in jobs], limit=5),
        "top_locations": top_counter_values([job.location for job in jobs], limit=5),
    }


def _build_real_question_cases(snapshot) -> list[dict]:
    jobs = snapshot.jobs
    top_source = Counter(job.source for job in jobs if job.source).most_common(1)
    top_roles = Counter(job.matched_role for job in jobs if job.matched_role).most_common(2)
    top_role = top_roles[:1]
    top_location = Counter(job.location for job in jobs if job.location).most_common(1)
    top_skills = [item.skill for item in snapshot.skills[:5] if item.skill]
    top_task = snapshot.task_insights[0].item if snapshot.task_insights else ""
    has_salary = any(job.salary.strip() for job in jobs)
    resume_profile = build_resume_profile_fixture()

    cases = [
        {
            "id": "real_skill_focus",
            "question": "目前市場最值得優先看的技能重點是什麼？",
            "expected_source_types": ["market-skill-insight", "job-skills"],
            "min_citations": 2,
            "resume_profile": None,
        },
        {
            "id": "real_task_focus",
            "question": "目前職缺常見的工作內容重點是什麼？",
            "expected_source_types": ["market-task-insight", "job-work-content"],
            "min_citations": 2,
            "resume_profile": None,
        },
        {
            "id": "real_source_focus",
            "question": "目前哪個來源的職缺量最多？",
            "expected_source_types": ["market-source-summary"],
            "min_citations": 1,
            "resume_profile": None,
        },
        {
            "id": "real_role_focus",
            "question": "目前職缺主要集中在哪些匹配角色？",
            "expected_source_types": ["market-role-summary"],
            "min_citations": 1,
            "resume_profile": None,
        },
        {
            "id": "real_location_focus",
            "question": "目前職缺主要集中在哪些地點？",
            "expected_source_types": ["market-location-summary"],
            "min_citations": 1,
            "resume_profile": None,
        },
    ]
    if has_salary:
        cases.append(
            {
                "id": "real_salary_focus",
                "question": "目前這批職缺的薪資帶大概怎麼看？",
                "expected_source_types": ["job-salary", "job-summary"],
                "min_citations": 2,
                "resume_profile": None,
            }
        )
    if top_skills:
        cases.append(
            {
                "id": "real_personalized_gap",
                "question": "以我目前履歷來看，現在最優先要補哪些技能？",
                "expected_source_types": ["resume-summary", "market-skill-insight", "job-skills"],
                "min_citations": 2,
                "resume_profile": resume_profile,
            }
        )
    if len(top_roles) >= 2:
        left_role, right_role = top_roles[0][0], top_roles[1][0]
        cases.append(
            {
                "id": "real_role_comparison",
                "question": f"{left_role} 和 {right_role} 的差異是什麼？",
                "expected_source_types": ["market-role-summary", "job-summary", "job-skills", "job-work-content"],
                "min_citations": 2,
                "resume_profile": None,
            }
        )

    for case in cases:
        if case["id"] == "real_skill_focus" and top_skills:
            case["expected_keywords"] = top_skills
        elif case["id"] == "real_task_focus" and top_task:
            case["expected_keywords"] = [top_task]
        elif case["id"] == "real_source_focus" and top_source:
            case["expected_keywords"] = [top_source[0][0]]
        elif case["id"] == "real_role_focus" and top_role:
            case["expected_keywords"] = [top_role[0][0]]
        elif case["id"] == "real_location_focus" and top_location:
            case["expected_keywords"] = [top_location[0][0]]
        elif case["id"] == "real_salary_focus":
            case["expected_keywords"] = ["薪資"]
        elif case["id"] == "real_personalized_gap" and top_skills:
            case["expected_keywords"] = [top_skills[0]]
        elif case["id"] == "real_role_comparison" and len(top_roles) >= 2:
            case["expected_keywords"] = [top_roles[0][0], top_roles[1][0]]
        else:
            case["expected_keywords"] = []
    return cases


def _citation_text(citation) -> str:
    return " ".join(
        part.strip()
        for part in (
            citation.label,
            citation.snippet,
            citation.source_type,
        )
        if isinstance(part, str) and part.strip()
    )


def _build_real_eval_client(*, use_fake_client: bool):
    return RealSnapshotFakeOpenAIClient() if use_fake_client else None


def evaluate_real_assistant(
    config,
    iterations: int,
    cache_dir: Path | None = None,
    snapshot_path: Path | None = None,
    *,
    case_limit: int | None = None,
    answer_model: str = "fake-answer",
    embedding_model: str = "fake-embedding",
    api_key: str = "fake",
    base_url: str = "",
    use_fake_client: bool = True,
) -> dict:
    from job_spy_tw.assistant.service import JobMarketRAGAssistant

    snapshot = load_real_snapshot(config, snapshot_path=snapshot_path)
    cases = _build_real_question_cases(snapshot)
    if case_limit is not None:
        cases = cases[:case_limit]
    assistant = JobMarketRAGAssistant(
        api_key=api_key,
        answer_model=answer_model,
        embedding_model=embedding_model,
        base_url=base_url,
        client=_build_real_eval_client(use_fake_client=use_fake_client),
        cache_dir=cache_dir,
    )

    rows = []
    summaries: list[RealAssistantCaseResult] = []
    for case in cases:
        answer_mode = assistant.classify_answer_mode(
            question=case["question"],
            resume_profile=case.get("resume_profile"),
        )
        total_values = []
        response_hits = []
        structured_hits = []
        citation_hits = []
        top_type_hits = []
        keyword_recalls = []
        evidence_hits = []
        used_chunks_values = []

        for iteration in range(iterations):
            started = perf_counter()
            response = assistant.answer_question(
                case["question"],
                snapshot=snapshot,
                resume_profile=case.get("resume_profile"),
                top_k=8,
            )
            total_ms = (perf_counter() - started) * 1000

            response_ok = bool(response.answer.strip())
            structured_ok = bool(response.summary.strip())
            citation_ok = len(response.citations) >= 1
            top_type_ok = bool(
                response.citations and response.citations[0].source_type in case["expected_source_types"]
            )
            citation_types = {citation.source_type for citation in response.citations}
            citation_text = "\n".join(_citation_text(citation) for citation in response.citations)
            expected_keywords = case.get("expected_keywords", [])
            keyword_hit_rate = keyword_recall(citation_text, expected_keywords) if expected_keywords else 1.0
            evidence_ok = bool(
                len(response.citations) >= int(case.get("min_citations", 1))
                and any(source_type in citation_types for source_type in case["expected_source_types"])
                and keyword_hit_rate >= 1.0
            )

            total_values.append(total_ms)
            response_hits.append(1.0 if response_ok else 0.0)
            structured_hits.append(1.0 if structured_ok else 0.0)
            citation_hits.append(1.0 if citation_ok else 0.0)
            top_type_hits.append(1.0 if top_type_ok else 0.0)
            keyword_recalls.append(keyword_hit_rate)
            evidence_hits.append(1.0 if evidence_ok else 0.0)
            used_chunks_values.append(float(response.used_chunks))
            rows.append(
                {
                    "case_id": case["id"],
                    "answer_mode": answer_mode,
                    "iteration": iteration + 1,
                    "question": case["question"],
                    "total_ms": round(total_ms, 3),
                    "response_nonempty": response_ok,
                    "structured_output": structured_ok,
                    "citation_ok": citation_ok,
                    "top_citation_type_hit": top_type_ok,
                    "citation_keyword_recall": round(keyword_hit_rate, 4),
                    "evidence_sufficient": evidence_ok,
                    "used_chunks": response.used_chunks,
                    "top_citation_type": response.citations[0].source_type if response.citations else "",
                    "citation_count": len(response.citations),
                    "answer": response.answer,
                    "summary": response.summary,
                    "key_points": " | ".join(response.key_points),
                    "limitations": " | ".join(response.limitations),
                    "next_step": response.next_step,
                    "citation_labels": " | ".join(citation.label for citation in response.citations),
                    "citation_snippets": " || ".join(citation.snippet for citation in response.citations),
                }
            )

        summaries.append(
            RealAssistantCaseResult(
                case_id=case["id"],
                question=case["question"],
                answer_mode=answer_mode,
                iterations=iterations,
                total_ms_mean=round(average(total_values), 3),
                total_ms_p95=round(p95(total_values), 3),
                response_nonempty_rate=round(average(response_hits), 4),
                structured_output_rate=round(average(structured_hits), 4),
                citation_ok_rate=round(average(citation_hits), 4),
                top_citation_type_hit_rate=round(average(top_type_hits), 4),
                citation_keyword_recall_mean=round(average(keyword_recalls), 4),
                evidence_sufficiency_rate=round(average(evidence_hits), 4),
                used_chunks_mean=round(average(used_chunks_values), 3),
            )
        )

    mode_breakdown: dict[str, dict[str, float | int]] = {}
    for answer_mode in sorted({item.answer_mode for item in summaries}):
        bucket = [item for item in summaries if item.answer_mode == answer_mode]
        mode_breakdown[answer_mode] = {
            "case_count": len(bucket),
            "total_ms_mean": round(average([item.total_ms_mean for item in bucket]), 3),
            "total_ms_p95": round(p95([item.total_ms_p95 for item in bucket]), 3),
            "structured_output_rate": round(average([item.structured_output_rate for item in bucket]), 4),
            "citation_ok_rate": round(average([item.citation_ok_rate for item in bucket]), 4),
            "top_citation_type_hit_rate": round(average([item.top_citation_type_hit_rate for item in bucket]), 4),
            "citation_keyword_recall_mean": round(average([item.citation_keyword_recall_mean for item in bucket]), 4),
            "evidence_sufficiency_rate": round(average([item.evidence_sufficiency_rate for item in bucket]), 4),
        }

    return {
        "rows": rows,
        "summary": [asdict(item) for item in summaries],
        "aggregate": {
            "total_ms_mean": round(average([item.total_ms_mean for item in summaries]), 3),
            "total_ms_p95": round(p95([item.total_ms_p95 for item in summaries]), 3),
            "response_nonempty_rate": round(average([item.response_nonempty_rate for item in summaries]), 4),
            "structured_output_rate": round(average([item.structured_output_rate for item in summaries]), 4),
            "citation_ok_rate": round(average([item.citation_ok_rate for item in summaries]), 4),
            "top_citation_type_hit_rate": round(average([item.top_citation_type_hit_rate for item in summaries]), 4),
            "citation_keyword_recall_mean": round(average([item.citation_keyword_recall_mean for item in summaries]), 4),
            "evidence_sufficiency_rate": round(average([item.evidence_sufficiency_rate for item in summaries]), 4),
            "used_chunks_mean": round(average([item.used_chunks_mean for item in summaries]), 3),
        },
        "mode_breakdown": mode_breakdown,
    }


def evaluate_real_retrieval(
    config,
    iterations: int,
    cache_dir: Path | None = None,
    snapshot_path: Path | None = None,
    *,
    case_limit: int | None = None,
    embedding_model: str = "fake-embedding",
    api_key: str = "fake",
    base_url: str = "",
    use_fake_client: bool = True,
) -> dict:
    from job_spy_tw.assistant.chunks import build_chunks
    from job_spy_tw.assistant.retrieval import EmbeddingRetriever
    from openai import OpenAI

    snapshot = load_real_snapshot(config, snapshot_path=snapshot_path)
    cases = _build_real_question_cases(snapshot)
    if case_limit is not None:
        cases = cases[:case_limit]
    rows = []
    summaries: list[RealRetrievalCaseResult] = []

    for case in cases:
        chunks = build_chunks(snapshot=snapshot, resume_profile=case.get("resume_profile"))
        cold_values = []
        warm_values = []
        speedup_values = []
        top_type_hits = []
        type_recalls = []
        latest_top_chunk_type = ""
        latest_top_chunk_label = ""

        for iteration in range(iterations):
            iteration_cache_dir = (
                (cache_dir or (config.results_dir / ".cache" / "real_retrieval"))
                / case["id"]
                / f"iter_{iteration + 1}"
            )
            if use_fake_client:
                client = RealSnapshotFakeOpenAIClient()
            else:
                client_kwargs = {"api_key": api_key}
                if base_url:
                    client_kwargs["base_url"] = base_url
                client = OpenAI(**client_kwargs)
            retriever = EmbeddingRetriever(
                client=client,
                embedding_model=embedding_model,
                cache_dir=iteration_cache_dir,
            )

            started = perf_counter()
            cold_result = retriever.retrieve(question=case["question"], chunks=chunks, top_k=8)
            cold_ms = (perf_counter() - started) * 1000

            started = perf_counter()
            warm_result = retriever.retrieve(question=case["question"], chunks=chunks, top_k=8)
            warm_ms = (perf_counter() - started) * 1000

            retrieved_types = [chunk.source_type for chunk in warm_result]
            latest_top_chunk_type = retrieved_types[0] if retrieved_types else ""
            latest_top_chunk_label = warm_result[0].label if warm_result else ""
            expected_types = set(case["expected_source_types"])
            top_type_hit = latest_top_chunk_type in expected_types
            type_recall = len(expected_types & set(retrieved_types)) / len(expected_types) if expected_types else 1.0
            speedup_ratio = (cold_ms / warm_ms) if warm_ms > 0 else 0.0

            cold_values.append(cold_ms)
            warm_values.append(warm_ms)
            speedup_values.append(speedup_ratio)
            top_type_hits.append(1.0 if top_type_hit else 0.0)
            type_recalls.append(type_recall)
            rows.append(
                {
                    "case_id": case["id"],
                    "iteration": iteration + 1,
                    "question": case["question"],
                    "cold_ms": round(cold_ms, 3),
                    "warm_ms": round(warm_ms, 3),
                    "top_chunk_type": latest_top_chunk_type,
                    "top_chunk_label": latest_top_chunk_label,
                    "top1_type_hit": top_type_hit,
                    "expected_type_recall": round(type_recall, 4),
                }
            )

        summaries.append(
            RealRetrievalCaseResult(
                case_id=case["id"],
                question=case["question"],
                iterations=iterations,
                cold_ms_mean=round(average(cold_values), 3),
                warm_ms_mean=round(average(warm_values), 3),
                cold_ms_p95=round(p95(cold_values), 3),
                warm_ms_p95=round(p95(warm_values), 3),
                speedup_ratio_mean=round(average(speedup_values), 4),
                top1_type_hit_rate=round(average(top_type_hits), 4),
                expected_type_recall_mean=round(average(type_recalls), 4),
                latest_top_chunk_type=latest_top_chunk_type,
                latest_top_chunk_label=latest_top_chunk_label,
            )
        )

    return {
        "rows": rows,
        "summary": [asdict(item) for item in summaries],
        "aggregate": {
            "cold_ms_mean": round(average([item.cold_ms_mean for item in summaries]), 3),
            "warm_ms_mean": round(average([item.warm_ms_mean for item in summaries]), 3),
            "speedup_ratio_mean": round(average([item.speedup_ratio_mean for item in summaries]), 4),
            "top1_type_hit_rate": round(average([item.top1_type_hit_rate for item in summaries]), 4),
            "expected_type_recall_mean": round(average([item.expected_type_recall_mean for item in summaries]), 4),
        },
    }


def _synthesized_resume_text(job) -> str:
    skills = list(
        dict.fromkeys(
            list(job.extracted_skills or []) + list(job.required_skill_items or [])
        )
    )
    work_items = job.work_content_items
    skill_text = "、".join(skills[:8]) if skills else ""
    task_text = "、".join(work_items[:3]) if work_items else ""
    return f"{job.title}\n技能：{skill_text}\n工作內容：{task_text}\n"


def _build_pseudo_resume_cases(snapshot, limit: int = 8) -> list[dict]:
    cases = []
    for index, job in enumerate(snapshot.jobs):
        skills = list(dict.fromkeys((job.extracted_skills or []) + (job.required_skill_items or [])))
        if not job.matched_role or len(skills) < 2:
            continue
        cases.append(
            {
                "id": f"real_resume_{index + 1}",
                "resume_text": _synthesized_resume_text(job),
                "expected_top_job_url": job.url,
                "expected_top_role": job.matched_role,
                "expected_matched_skills": skills[:4],
            }
        )
        if len(cases) >= limit:
            break
    return cases


def evaluate_real_resume(
    config,
    iterations: int,
    cache_dir: Path | None = None,
    snapshot_path: Path | None = None,
    *,
    case_limit: int | None = None,
    openai_api_key: str = "",
    openai_base_url: str = "",
    llm_model: str = "gpt-4.1-mini",
    title_model: str = "gpt-4.1-mini",
    embedding_model: str = "text-embedding-3-large",
    use_fake_client: bool = True,
    use_llm: bool = False,
) -> dict:
    from job_spy_tw.resume.service import ResumeAnalysisService
    from job_spy_tw.targets import DEFAULT_TARGET_ROLES

    snapshot = load_real_snapshot(config, snapshot_path=snapshot_path)
    jobs = snapshot.jobs
    cases = _build_pseudo_resume_cases(snapshot)
    if case_limit is not None:
        cases = cases[:case_limit]
    service = ResumeAnalysisService(
        DEFAULT_TARGET_ROLES,
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        llm_model=llm_model,
        title_model=title_model,
        embedding_model=embedding_model,
        openai_client=RealSnapshotFakeOpenAIClient() if use_fake_client else None,
        cache_dir=cache_dir,
    )

    rows = []
    summaries: list[RealResumeCaseResult] = []
    for case in cases:
        build_values = []
        match_values = []
        total_values = []
        top3_url_hits = []
        top1_role_hits = []
        matched_skill_recalls = []
        latest_top_job_url = ""

        for iteration in range(iterations):
            started = perf_counter()
            profile = service.build_profile(case["resume_text"], use_llm=use_llm)
            build_ms = (perf_counter() - started) * 1000

            started = perf_counter()
            matches = service.match_jobs(profile, jobs)
            match_ms = (perf_counter() - started) * 1000
            total_ms = build_ms + match_ms

            top_match = matches[0] if matches else None
            latest_top_job_url = top_match.job_url if top_match else ""
            top3_urls = {match.job_url for match in matches[:3]}
            top3_url_hit = case["expected_top_job_url"] in top3_urls
            top1_role_hit = bool(top_match and top_match.matched_role == case["expected_top_role"])
            matched_skill_recall = set_recall(
                top_match.matched_skills if top_match else [],
                case["expected_matched_skills"],
            )

            build_values.append(build_ms)
            match_values.append(match_ms)
            total_values.append(total_ms)
            top3_url_hits.append(1.0 if top3_url_hit else 0.0)
            top1_role_hits.append(1.0 if top1_role_hit else 0.0)
            matched_skill_recalls.append(matched_skill_recall)
            rows.append(
                {
                    "case_id": case["id"],
                    "iteration": iteration + 1,
                    "build_profile_ms": round(build_ms, 3),
                    "match_jobs_ms": round(match_ms, 3),
                    "total_ms": round(total_ms, 3),
                    "top1_job_url": latest_top_job_url,
                    "top1_role": top_match.matched_role if top_match else "",
                    "top3_url_hit": top3_url_hit,
                    "top1_role_match": top1_role_hit,
                    "matched_skill_recall": round(matched_skill_recall, 4),
                }
            )

        summaries.append(
            RealResumeCaseResult(
                case_id=case["id"],
                iterations=iterations,
                build_profile_ms_mean=round(average(build_values), 3),
                match_jobs_ms_mean=round(average(match_values), 3),
                total_ms_mean=round(average(total_values), 3),
                total_ms_p95=round(p95(total_values), 3),
                top3_url_hit_rate=round(average(top3_url_hits), 4),
                top1_role_match_rate=round(average(top1_role_hits), 4),
                matched_skill_recall_mean=round(average(matched_skill_recalls), 4),
                latest_top_job_url=latest_top_job_url,
            )
        )

    return {
        "rows": rows,
        "summary": [asdict(item) for item in summaries],
        "aggregate": {
            "build_profile_ms_mean": round(average([item.build_profile_ms_mean for item in summaries]), 3),
            "match_jobs_ms_mean": round(average([item.match_jobs_ms_mean for item in summaries]), 3),
            "total_ms_mean": round(average([item.total_ms_mean for item in summaries]), 3),
            "top3_url_hit_rate": round(average([item.top3_url_hit_rate for item in summaries]), 4),
            "top1_role_match_rate": round(average([item.top1_role_match_rate for item in summaries]), 4),
            "matched_skill_recall_mean": round(average([item.matched_skill_recall_mean for item in summaries]), 4),
            "case_count": len(cases),
        },
    }


def build_real_snapshot_report(summary: dict) -> str:
    health = summary["snapshot_health"]
    gate = summary.get("snapshot_health_gate")
    assistant = {
        "total_ms_mean": 0.0,
        "total_ms_p95": 0.0,
        "response_nonempty_rate": 0.0,
        "structured_output_rate": 0.0,
        "citation_ok_rate": 0.0,
        "top_citation_type_hit_rate": 0.0,
        "citation_keyword_recall_mean": 0.0,
        "evidence_sufficiency_rate": 0.0,
    }
    assistant.update(summary.get("assistant", {}).get("aggregate", {}))
    resume = {
        "build_profile_ms_mean": 0.0,
        "match_jobs_ms_mean": 0.0,
        "total_ms_mean": 0.0,
        "top3_url_hit_rate": 0.0,
        "top1_role_match_rate": 0.0,
        "matched_skill_recall_mean": 0.0,
        "case_count": 0,
    }
    resume.update(summary.get("resume", {}).get("aggregate", {}))
    retrieval = {
        "cold_ms_mean": 0.0,
        "warm_ms_mean": 0.0,
        "speedup_ratio_mean": 0.0,
        "top1_type_hit_rate": 0.0,
        "expected_type_recall_mean": 0.0,
    }
    retrieval.update(summary.get("retrieval", {}).get("aggregate", {}))
    assistant_mode_breakdown = _render_mode_breakdown_markdown(
        "Assistant 模式拆解",
        summary.get("assistant", {}).get("mode_breakdown"),
    )
    gate_section = ""
    if gate:
        gate_lines = "\n".join(
            f"- {item['label']}：`{item['actual']}` / 門檻 `>= {item['minimum']}` {'PASS' if item['passed'] else 'FAIL'}"
            for item in gate["checks"]
        )
        gate_section = f"""

## Snapshot Health Gate
- 判定：`{gate['status']}`
- 結論：{gate['verdict']}
{gate_lines}
"""
    return f"""# Job Radar Real Snapshot Eval

## 快照資訊
- 快照路徑：{health['snapshot_path']}
- 產生時間：{health['generated_at']}
- 職缺數：`{health['jobs_count']}`
- 查詢數：`{health['queries_count']}`
- 來源數：`{health['sources_count']}`
- 角色數：`{health['roles_count']}`
- 薪資覆蓋率：`{health['salary_coverage_rate']}`
- 工作內容覆蓋率：`{health['work_content_coverage_rate']}`
- 必備技能覆蓋率：`{health['required_skill_coverage_rate']}`
{gate_section}

## Assistant Smoke
- 平均總延遲：`{assistant['total_ms_mean']} ms`
- P95 總延遲：`{assistant['total_ms_p95']} ms`
- 非空回答率：`{assistant['response_nonempty_rate']}`
- 結構化輸出率：`{assistant['structured_output_rate']}`
- 引用命中率：`{assistant['citation_ok_rate']}`
- Top1 引用型別命中率：`{assistant['top_citation_type_hit_rate']}`
- 引用關鍵詞召回率：`{assistant['citation_keyword_recall_mean']}`
- 證據充分率：`{assistant['evidence_sufficiency_rate']}`

{assistant_mode_breakdown}

## Resume Smoke
- 平均履歷解析延遲：`{resume['build_profile_ms_mean']} ms`
- 平均匹配延遲：`{resume['match_jobs_ms_mean']} ms`
- 平均總延遲：`{resume['total_ms_mean']} ms`
- Top3 URL 命中率：`{resume['top3_url_hit_rate']}`
- Top1 角色命中率：`{resume['top1_role_match_rate']}`
- 命中技能召回率：`{resume['matched_skill_recall_mean']}`
- 測例數：`{resume['case_count']}`

## Retrieval Smoke
- 平均冷快取延遲：`{retrieval['cold_ms_mean']} ms`
- 平均熱快取延遲：`{retrieval['warm_ms_mean']} ms`
- 平均快取加速倍率：`{retrieval['speedup_ratio_mean']}`
- Top1 型別命中率：`{retrieval['top1_type_hit_rate']}`
- 預期型別召回率：`{retrieval['expected_type_recall_mean']}`

## 解讀
- 這份報告不是黃金標註 benchmark，而是用真實快照檢查流程穩定性。
- 如果 `coverage rate` 太低，代表資料本身不夠完整，先不要急著調模型。
- 如果 `assistant` 或 `retrieval` 的型別命中率明顯偏低，再回頭調 chunk / metadata / rerank。
- 如果 `assistant.evidence_sufficiency_rate` 偏低，代表引用雖然存在，但支撐答案的證據量或關鍵詞覆蓋還不夠。
- 如果 `resume` 的 `top3_url_hit_rate` 偏低，再檢查 matcher 是否只對 fixture 有效。"""
