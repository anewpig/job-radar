"""Application-layer boundary for AI assistant use cases."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models import AssistantResponse, MarketSnapshot, ResumeProfile
from ..rag_assistant import JobMarketRAGAssistant


@dataclass(slots=True)
class AssistantConfig:
    api_key: str
    answer_model: str
    general_chat_model: str
    prompt_variant: str
    latency_profile: str
    embedding_model: str
    base_url: str
    cache_dir: Path
    persistent_index_sync_interval_seconds: int = 900
    persistent_index_enabled: bool = True
    persistent_index_sources: tuple[str, ...] = ("snapshot_file",)
    persistent_index_max_snapshots: int = 1
    persistent_index_max_history_rows: int = 500
    external_search_enabled: bool = False
    external_search_provider: str = "duckduckgo"
    external_search_max_results: int = 3
    external_search_timeout_seconds: float = 4.0
    external_search_cache_ttl_seconds: int = 900
    salary_prediction_enabled: bool = True
    salary_prediction_model_path: Path | None = None


class AssistantApplication:
    """Facade for the AI assistant use case."""

    def __init__(self, rag_assistant: JobMarketRAGAssistant) -> None:
        self._rag = rag_assistant

    @classmethod
    def from_config(cls, config: AssistantConfig) -> "AssistantApplication":
        assistant = JobMarketRAGAssistant(
            api_key=config.api_key,
            answer_model=config.answer_model,
            general_chat_model=config.general_chat_model,
            prompt_variant=config.prompt_variant,
            latency_profile=config.latency_profile,
            embedding_model=config.embedding_model,
            base_url=config.base_url,
            cache_dir=config.cache_dir,
            persistent_index_sync_interval_seconds=config.persistent_index_sync_interval_seconds,
            persistent_index_enabled=config.persistent_index_enabled,
            persistent_index_sources=config.persistent_index_sources,
            persistent_index_max_snapshots=config.persistent_index_max_snapshots,
            persistent_index_max_history_rows=config.persistent_index_max_history_rows,
            external_search_enabled=config.external_search_enabled,
            external_search_provider=config.external_search_provider,
            external_search_max_results=config.external_search_max_results,
            external_search_timeout_seconds=config.external_search_timeout_seconds,
            external_search_cache_ttl_seconds=config.external_search_cache_ttl_seconds,
            salary_prediction_enabled=config.salary_prediction_enabled,
            salary_prediction_model_path=config.salary_prediction_model_path,
        )
        return cls(assistant)

    @property
    def last_usage(self) -> dict[str, object]:
        return getattr(self._rag, "last_usage", {}) or {}

    @property
    def last_request_metrics(self) -> dict[str, object]:
        return getattr(self._rag, "last_request_metrics", {}) or {}

    def classify_answer_mode(
        self,
        *,
        question: str,
        resume_profile: ResumeProfile | None,
        conversation_context: list[AssistantResponse],
    ) -> str:
        return self._rag.classify_answer_mode(
            question=question,
            resume_profile=resume_profile,
            conversation_context=conversation_context,
        )

    def answer_question(
        self,
        *,
        question: str,
        snapshot: MarketSnapshot,
        resume_profile: ResumeProfile | None,
        conversation_context: list[AssistantResponse],
    ) -> AssistantResponse:
        return self._rag.answer_question(
            question=question,
            snapshot=snapshot,
            resume_profile=resume_profile,
            conversation_context=conversation_context,
        )

    def generate_report(
        self,
        *,
        snapshot: MarketSnapshot,
        resume_profile: ResumeProfile,
    ) -> AssistantResponse:
        return self._rag.generate_report(
            snapshot=snapshot,
            resume_profile=resume_profile,
        )
