"""Resume-analysis helpers for service."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import JobListing, ResumeJobMatch, ResumeProfile, TargetRole
from ..openai_usage import merge_openai_usage
from ..prompt_versions import RESUME_EXTRACTION_PROMPT_VERSION, TITLE_SIMILARITY_PROMPT_VERSION
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
        self.last_build_profile_usage = merge_openai_usage()
        self.last_match_jobs_usage = merge_openai_usage()
        self.last_build_profile_metrics: dict[str, Any] = {}
        self.last_match_jobs_metrics: dict[str, Any] = {}
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
                cache_dir=cache_dir,
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
        self.last_build_profile_usage = merge_openai_usage()
        self.last_build_profile_metrics = {
            "extraction_method": "rule_based",
            "prompt_version": RESUME_EXTRACTION_PROMPT_VERSION,
            "profile_cache_memory_hit": False,
            "profile_cache_disk_hit": False,
            "profile_cache_write": False,
        }
        fallback_profile = self.rule_extractor.extract(text=text, source_name=source_name)
        if not use_llm:
            return fallback_profile
        if self.openai_extractor is None:
            fallback_profile.notes = unique_preserving_order(
                fallback_profile.notes + ["未設定 OPENAI_API_KEY，已改用規則分析。"]
            )
            return fallback_profile
        try:
            profile = self.openai_extractor.extract(
                text=text,
                source_name=source_name,
                fallback_profile=fallback_profile,
            )
            self.last_build_profile_usage = merge_openai_usage(
                self.openai_extractor.last_usage,
            )
            self.last_build_profile_metrics = {
                "extraction_method": profile.extraction_method,
                **getattr(self.openai_extractor, "last_metrics", {}),
            }
            return profile
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
        self.last_match_jobs_usage = merge_openai_usage()
        self.last_match_jobs_metrics = {
            "matching_method": "rule_based",
            "title_prompt_version": TITLE_SIMILARITY_PROMPT_VERSION,
            "candidate_jobs": 0,
            "title_llm_jobs": 0,
            "semantic_jobs": 0,
        }
        if self.ai_matcher is None:
            profile.notes = unique_preserving_order(
                profile.notes + ["未設定 OPENAI_API_KEY，職缺匹配改用規則分析。"]
            )
            return self.matcher.match_jobs(profile, jobs)
        try:
            matches = self.ai_matcher.match_jobs(profile, jobs)
            self.last_match_jobs_usage = merge_openai_usage(
                self.ai_matcher.last_usage,
            )
            self.last_match_jobs_metrics = {
                "matching_method": "llm_embedding",
                **getattr(self.ai_matcher, "last_metrics", {}),
            }
            return matches
        except Exception as exc:  # noqa: BLE001
            profile.notes = unique_preserving_order(
                profile.notes + [f"AI 匹配失敗，已改用規則分析：{exc}"]
            )
            return self.matcher.match_jobs(profile, jobs)
