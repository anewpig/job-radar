"""Application-layer boundary for resume analysis use case."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models import JobListing, ResumeJobMatch, ResumeProfile, TargetRole
from ..resume_analysis import ResumeAnalysisService


@dataclass(slots=True)
class ResumeConfig:
    role_targets: list[TargetRole]
    openai_api_key: str = ""
    openai_base_url: str = ""
    llm_model: str = "gpt-4.1-mini"
    title_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-large"
    cache_dir: Path | None = None
    openai_client: Any | None = None


class ResumeApplication:
    """Facade for resume analysis."""

    def __init__(self, service: ResumeAnalysisService) -> None:
        self._service = service

    @classmethod
    def from_config(cls, config: ResumeConfig) -> "ResumeApplication":
        service = ResumeAnalysisService(
            role_targets=config.role_targets,
            openai_api_key=config.openai_api_key,
            openai_base_url=config.openai_base_url,
            llm_model=config.llm_model,
            title_model=config.title_model,
            embedding_model=config.embedding_model,
            cache_dir=config.cache_dir,
            openai_client=config.openai_client,
        )
        return cls(service)

    @property
    def last_build_profile_usage(self) -> dict[str, object]:
        return getattr(self._service, "last_build_profile_usage", {}) or {}

    @property
    def last_match_jobs_usage(self) -> dict[str, object]:
        return getattr(self._service, "last_match_jobs_usage", {}) or {}

    def build_profile(
        self,
        *,
        text: str,
        source_name: str = "",
        use_llm: bool = True,
    ) -> ResumeProfile:
        return self._service.build_profile(
            text=text,
            source_name=source_name,
            use_llm=use_llm,
        )

    def match_jobs(
        self,
        *,
        profile: ResumeProfile,
        jobs: list[JobListing],
    ) -> list[ResumeJobMatch]:
        return self._service.match_jobs(profile, jobs)
