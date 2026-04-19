from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from .fixtures import load_resume_cases
from .metrics import average


@dataclass(slots=True)
class ResumeWarmProbeCaseResult:
    case_id: str
    cold_build_profile_ms: float
    warm_build_profile_ms: float
    speedup_ratio: float
    output_consistent: bool


class ResumeWarmProbeService:
    def __init__(
        self,
        cache_dir: Path,
        *,
        openai_api_key: str = "",
        openai_base_url: str = "",
        llm_model: str = "gpt-4.1-mini",
        title_model: str = "gpt-4.1-mini",
        embedding_model: str = "text-embedding-3-large",
        use_fake_client: bool = True,
    ) -> None:
        from job_spy_tw.resume.service import ResumeAnalysisService
        from job_spy_tw.targets import DEFAULT_TARGET_ROLES
        from .fake_clients import FakeOpenAIClient

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

    def run_case(self, resume_text: str) -> dict[str, Any]:
        started = perf_counter()
        cold_profile = self._service.build_profile(resume_text, use_llm=True)
        cold_ms = (perf_counter() - started) * 1000

        started = perf_counter()
        warm_profile = self._service.build_profile(resume_text, use_llm=True)
        warm_ms = (perf_counter() - started) * 1000

        output_consistent = (
            cold_profile.summary == warm_profile.summary
            and cold_profile.target_roles == warm_profile.target_roles
            and cold_profile.core_skills == warm_profile.core_skills
            and cold_profile.tool_skills == warm_profile.tool_skills
            and cold_profile.domain_keywords == warm_profile.domain_keywords
        )

        speedup_ratio = cold_ms / max(warm_ms, 0.001)
        return {
            "cold_profile": cold_profile,
            "warm_profile": warm_profile,
            "timings": {
                "cold_build_profile_ms": cold_ms,
                "warm_build_profile_ms": warm_ms,
                "speedup_ratio": speedup_ratio,
            },
            "output_consistent": output_consistent,
        }


def evaluate_resume_warm_probe(
    config,
    cache_dir: Path | None = None,
    *,
    case_limit: int | None = None,
    openai_api_key: str = "",
    openai_base_url: str = "",
    llm_model: str = "gpt-4.1-mini",
    title_model: str = "gpt-4.1-mini",
    embedding_model: str = "text-embedding-3-large",
    use_fake_client: bool = True,
) -> dict[str, Any]:
    cases = load_resume_cases(config)
    if case_limit is not None:
        cases = cases[:case_limit]

    probe = ResumeWarmProbeService(
        cache_dir=cache_dir or (config.results_dir / ".cache" / "resume_warm_probe"),
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        llm_model=llm_model,
        title_model=title_model,
        embedding_model=embedding_model,
        use_fake_client=use_fake_client,
    )

    rows: list[dict[str, Any]] = []
    summaries: list[ResumeWarmProbeCaseResult] = []
    for case in cases:
        result = probe.run_case(case["resume_text"])
        timings = result["timings"]
        output_consistent = bool(result["output_consistent"])
        summaries.append(
            ResumeWarmProbeCaseResult(
                case_id=case["id"],
                cold_build_profile_ms=round(timings["cold_build_profile_ms"], 3),
                warm_build_profile_ms=round(timings["warm_build_profile_ms"], 3),
                speedup_ratio=round(timings["speedup_ratio"], 3),
                output_consistent=output_consistent,
            )
        )
        rows.append(
            {
                "case_id": case["id"],
                "cold_build_profile_ms": round(timings["cold_build_profile_ms"], 3),
                "warm_build_profile_ms": round(timings["warm_build_profile_ms"], 3),
                "speedup_ratio": round(timings["speedup_ratio"], 3),
                "output_consistent": output_consistent,
            }
        )

    return {
        "rows": rows,
        "summary": [asdict(item) for item in summaries],
        "aggregate": {
            "case_count": len(summaries),
            "cold_build_profile_ms_mean": round(average([item.cold_build_profile_ms for item in summaries]), 3),
            "warm_build_profile_ms_mean": round(average([item.warm_build_profile_ms for item in summaries]), 3),
            "speedup_ratio_mean": round(average([item.speedup_ratio for item in summaries]), 3),
            "output_consistency_rate": round(
                average([1.0 if item.output_consistent else 0.0 for item in summaries]),
                4,
            ),
        },
    }
