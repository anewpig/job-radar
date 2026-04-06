"""Resume-analysis helpers for service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import JobListing, ResumeJobMatch, ResumeProfile, TargetRole
from ..utils import unique_preserving_order
from .extractors import OpenAIResumeExtractor, RuleBasedResumeExtractor
from .matchers import OpenAIResumeMatcher, ResumeMatcher
from .schemas import LLMResumeProfile, OpenAI


class ResumeAnalysisService:
    def __init__(
        self,
        role_targets: list[TargetRole],
        openai_api_key: str = "",
        openai_base_url: str = "",
        llm_model: str = "gpt-4.1-mini",
        title_model: str = "gpt-4.1-mini",
        embedding_model: str = "text-embedding-3-large",
        cache_dir: Path | None = None,
        openai_client: Any | None = None,
    ) -> None:
        self.rule_extractor = RuleBasedResumeExtractor(role_targets)
        self.matcher = ResumeMatcher(role_targets)
        self.ai_matcher = None
        self.openai_extractor = None
        if (
            (openai_api_key or openai_client is not None)
            and OpenAI is not None
            and LLMResumeProfile is not None
        ):
            self.openai_extractor = OpenAIResumeExtractor(
                role_targets=role_targets,
                api_key=openai_api_key,
                model=llm_model,
                base_url=openai_base_url,
                client=openai_client,
            )
            self.ai_matcher = OpenAIResumeMatcher(
                role_targets=role_targets,
                fallback_matcher=self.matcher,
                api_key=openai_api_key,
                title_model=title_model,
                embedding_model=embedding_model,
                base_url=openai_base_url,
                cache_dir=cache_dir,
                client=openai_client,
            )

    def build_profile(
        self,
        text: str,
        source_name: str = "",
        use_llm: bool = True,
    ) -> ResumeProfile:
        fallback_profile = self.rule_extractor.extract(text=text, source_name=source_name)
        if not use_llm:
            return fallback_profile
        if self.openai_extractor is None:
            fallback_profile.notes = unique_preserving_order(
                fallback_profile.notes + ["未設定 OPENAI_API_KEY，已改用規則分析。"]
            )
            return fallback_profile
        try:
            return self.openai_extractor.extract(
                text=text,
                source_name=source_name,
                fallback_profile=fallback_profile,
            )
        except Exception as exc:  # noqa: BLE001
            fallback_profile.notes = unique_preserving_order(
                fallback_profile.notes + [f"LLM 擷取失敗，已改用規則分析：{exc}"]
            )
            return fallback_profile

    def match_jobs(
        self,
        profile: ResumeProfile,
        jobs: list[JobListing],
    ) -> list[ResumeJobMatch]:
        if self.ai_matcher is None:
            profile.notes = unique_preserving_order(
                profile.notes + ["未設定 OPENAI_API_KEY，職缺匹配改用規則分析。"]
            )
            return self.matcher.match_jobs(profile, jobs)
        try:
            return self.ai_matcher.match_jobs(profile, jobs)
        except Exception as exc:  # noqa: BLE001
            profile.notes = unique_preserving_order(
                profile.notes + [f"AI 匹配失敗，已改用規則分析：{exc}"]
            )
            return self.matcher.match_jobs(profile, jobs)
