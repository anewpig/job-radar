"""Preset definitions and helpers for crawl-speed tradeoffs."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .config import Settings


@dataclass(frozen=True, slots=True)
class CrawlPreset:
    key: str
    label: str
    description: str
    request_delay: float | None = None
    max_concurrent_requests: int | None = None
    max_pages_per_source: int | None = None
    max_detail_jobs_per_source: int | None = None
    min_relevance_score: float | None = None
    keywords_per_role: int = 2


CRAWL_PRESETS: tuple[CrawlPreset, ...] = (
    CrawlPreset(
        key="quick",
        label="快速",
        description="每個來源抓 1 頁，原文解析前 12 筆，最快看到結果。",
        request_delay=0.15,
        max_concurrent_requests=6,
        max_pages_per_source=1,
        max_detail_jobs_per_source=12,
        keywords_per_role=1,
    ),
    CrawlPreset(
        key="balanced",
        label="平衡",
        description="每個來源抓 1 頁，原文解析前 24 筆，兼顧速度與完整度。",
        request_delay=0.35,
        max_concurrent_requests=4,
        max_pages_per_source=1,
        max_detail_jobs_per_source=24,
        keywords_per_role=2,
    ),
    CrawlPreset(
        key="full",
        label="完整",
        description="依照環境設定抓取與解析，最完整也最慢。",
        min_relevance_score=0.0,
        keywords_per_role=2,
    ),
)


def get_crawl_preset(label: str) -> CrawlPreset:
    for preset in CRAWL_PRESETS:
        if preset.label == label or preset.key == label:
            return preset
    return CRAWL_PRESETS[0]


def apply_crawl_preset(settings: Settings, preset: CrawlPreset) -> Settings:
    return replace(
        settings,
        request_delay=(
            preset.request_delay if preset.request_delay is not None else settings.request_delay
        ),
        max_concurrent_requests=(
            preset.max_concurrent_requests
            if preset.max_concurrent_requests is not None
            else settings.max_concurrent_requests
        ),
        max_pages_per_source=(
            preset.max_pages_per_source
            if preset.max_pages_per_source is not None
            else settings.max_pages_per_source
        ),
        max_detail_jobs_per_source=(
            preset.max_detail_jobs_per_source
            if preset.max_detail_jobs_per_source is not None
            else settings.max_detail_jobs_per_source
        ),
        min_relevance_score=(
            preset.min_relevance_score
            if preset.min_relevance_score is not None
            else settings.min_relevance_score
        ),
    )
