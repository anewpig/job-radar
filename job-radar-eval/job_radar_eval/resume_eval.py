"""履歷解析與職缺匹配 baseline 評估。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

from .fake_clients import FakeOpenAIClient
from .fixtures import build_market_snapshot_fixture, load_resume_cases
from .metrics import average, p95, set_recall


@dataclass(slots=True)
class ResumeCaseResult:
    """單一履歷測例的聚合結果。"""

    case_id: str
    iterations: int
    build_profile_ms_mean: float
    match_jobs_ms_mean: float
    total_ms_mean: float
    total_ms_p95: float
    top1_url_match_rate: float
    top1_role_match_rate: float
    matched_skill_recall_mean: float
    missing_skill_recall_mean: float
    latest_top_job_url: str


class InstrumentedResumeAnalysisService:
    """包裝正式的履歷分析服務，量測解析與匹配耗時。"""

    def __init__(
        self,
        cache_dir: Path | None = None,
        *,
        openai_api_key: str = "",
        openai_base_url: str = "",
        llm_model: str = "gpt-4.1-mini",
        title_model: str = "gpt-4.1-mini",
        embedding_model: str = "text-embedding-3-large",
        use_fake_client: bool = True,
        use_llm: bool = False,
    ) -> None:
        from job_spy_tw.resume.service import ResumeAnalysisService
        from job_spy_tw.targets import DEFAULT_TARGET_ROLES

        self._use_llm = use_llm
        self._service = ResumeAnalysisService(
            DEFAULT_TARGET_ROLES,
            openai_api_key=openai_api_key,
            openai_base_url=openai_base_url,
            llm_model=llm_model,
            title_model=title_model,
            embedding_model=embedding_model,
            openai_client=FakeOpenAIClient() if use_fake_client else None,
            cache_dir=cache_dir,
        )

    def run_case(self, resume_text: str, jobs):
        started = perf_counter()

        stage_started = perf_counter()
        profile = self._service.build_profile(resume_text, use_llm=self._use_llm)
        build_profile_ms = (perf_counter() - stage_started) * 1000

        stage_started = perf_counter()
        matches = self._service.match_jobs(profile, jobs)
        match_jobs_ms = (perf_counter() - stage_started) * 1000

        total_ms = (perf_counter() - started) * 1000
        return {
            "profile": profile,
            "matches": matches,
            "timings": {
                "build_profile_ms": build_profile_ms,
                "match_jobs_ms": match_jobs_ms,
                "total_ms": total_ms,
            },
        }


def evaluate_resume(
    config,
    iterations: int,
    cache_dir: Path | None = None,
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
    """執行履歷 baseline 並回傳原始資料與聚合統計。"""
    snapshot = build_market_snapshot_fixture()
    jobs = snapshot.jobs
    cases = load_resume_cases(config)
    if case_limit is not None:
        cases = cases[:case_limit]
    service = InstrumentedResumeAnalysisService(
        cache_dir=cache_dir or (config.results_dir / ".cache" / "resume"),
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        llm_model=llm_model,
        title_model=title_model,
        embedding_model=embedding_model,
        use_fake_client=use_fake_client,
        use_llm=use_llm,
    )

    case_rows = []
    summaries: list[ResumeCaseResult] = []

    for case in cases:
        build_values = []
        match_values = []
        total_values = []
        top1_url_hits = []
        top1_role_hits = []
        matched_skill_recalls = []
        missing_skill_recalls = []
        latest_top_job_url = ""

        for iteration in range(iterations):
            result = service.run_case(case["resume_text"], jobs)
            matches = result["matches"]
            top_match = matches[0] if matches else None
            latest_top_job_url = top_match.job_url if top_match else ""
            top1_url_match = bool(top_match and top_match.job_url == case["expected_top_job_url"])
            top1_role_match = bool(top_match and top_match.matched_role == case["expected_top_role"])
            matched_skill_recall = set_recall(
                top_match.matched_skills if top_match else [],
                case["expected_matched_skills"],
            )
            missing_skill_recall = set_recall(
                top_match.missing_skills if top_match else [],
                case["expected_missing_skills"],
            )
            timings = result["timings"]
            build_values.append(timings["build_profile_ms"])
            match_values.append(timings["match_jobs_ms"])
            total_values.append(timings["total_ms"])
            top1_url_hits.append(1.0 if top1_url_match else 0.0)
            top1_role_hits.append(1.0 if top1_role_match else 0.0)
            matched_skill_recalls.append(matched_skill_recall)
            missing_skill_recalls.append(missing_skill_recall)
            case_rows.append(
                {
                    "case_id": case["id"],
                    "iteration": iteration + 1,
                    "build_profile_ms": round(timings["build_profile_ms"], 3),
                    "match_jobs_ms": round(timings["match_jobs_ms"], 3),
                    "total_ms": round(timings["total_ms"], 3),
                    "top1_job_url": top_match.job_url if top_match else "",
                    "top1_role": top_match.matched_role if top_match else "",
                    "top1_url_match": top1_url_match,
                    "top1_role_match": top1_role_match,
                    "matched_skill_recall": round(matched_skill_recall, 4),
                    "missing_skill_recall": round(missing_skill_recall, 4),
                }
            )

        summaries.append(
            ResumeCaseResult(
                case_id=case["id"],
                iterations=iterations,
                build_profile_ms_mean=round(average(build_values), 3),
                match_jobs_ms_mean=round(average(match_values), 3),
                total_ms_mean=round(average(total_values), 3),
                total_ms_p95=round(p95(total_values), 3),
                top1_url_match_rate=round(average(top1_url_hits), 4),
                top1_role_match_rate=round(average(top1_role_hits), 4),
                matched_skill_recall_mean=round(average(matched_skill_recalls), 4),
                missing_skill_recall_mean=round(average(missing_skill_recalls), 4),
                latest_top_job_url=latest_top_job_url,
            )
        )

    return {
        "rows": case_rows,
        "summary": [asdict(item) for item in summaries],
        "aggregate": {
            "build_profile_ms_mean": round(average([item.build_profile_ms_mean for item in summaries]), 3),
            "match_jobs_ms_mean": round(average([item.match_jobs_ms_mean for item in summaries]), 3),
            "total_ms_mean": round(average([item.total_ms_mean for item in summaries]), 3),
            "total_ms_p95": round(p95([item.total_ms_p95 for item in summaries]), 3),
            "top1_url_match_rate": round(average([item.top1_url_match_rate for item in summaries]), 4),
            "top1_role_match_rate": round(average([item.top1_role_match_rate for item in summaries]), 4),
            "matched_skill_recall_mean": round(average([item.matched_skill_recall_mean for item in summaries]), 4),
            "missing_skill_recall_mean": round(average([item.missing_skill_recall_mean for item in summaries]), 4),
        },
    }
