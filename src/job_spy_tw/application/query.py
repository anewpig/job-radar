"""Application-layer boundary for query construction helpers."""

from __future__ import annotations

from dataclasses import dataclass

from ..crawl_application_service import (
    build_crawl_queries,
    build_role_targets_from_rows,
)
from ..crawl_tuning import CrawlPreset
from ..models import TargetRole


@dataclass(slots=True)
class BuildQueriesRequest:
    role_targets: list[TargetRole]
    crawl_preset: CrawlPreset
    custom_queries: str


@dataclass(slots=True)
class BuildRoleTargetsRequest:
    rows: list[dict[str, object]]


class QueryApplication:
    """Application-level API for query preparation."""

    def build_queries(self, request: BuildQueriesRequest) -> list[str]:
        return build_crawl_queries(
            role_targets=request.role_targets,
            crawl_preset=request.crawl_preset,
            custom_queries=request.custom_queries,
        )

    def build_role_targets(self, request: BuildRoleTargetsRequest) -> list[TargetRole]:
        return build_role_targets_from_rows(request.rows)
