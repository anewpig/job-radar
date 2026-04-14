"""Helpers for global scheduled searches."""

from __future__ import annotations

from dataclasses import dataclass

from .models import NotificationPreference
from .product_store import ProductStore
from .security import USER_ROLE_OPERATOR
from .settings import Settings
from .store.common import canonical_rows


DEFAULT_GLOBAL_SEARCH_NAME = "系統定期追蹤"
DEFAULT_GLOBAL_SEARCH_USER_NAME = "System Scheduler"


@dataclass(slots=True)
class GlobalSearchContext:
    user_id: int
    search_id: int
    search_name: str


def _format_frequency_label(days: int) -> str:
    normalized_days = max(1, int(days))
    if normalized_days == 1:
        return "每日"
    if normalized_days == 2:
        return "每兩天"
    return f"每{normalized_days}天"


def build_global_search_rows(keywords: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, keyword in enumerate(keywords, start=1):
        cleaned = str(keyword).strip()
        if not cleaned:
            continue
        rows.append(
            {
                "enabled": True,
                "priority": index,
                "role": cleaned,
                "keywords": "",
            }
        )
    return rows


def ensure_global_saved_search(
    *,
    settings: Settings,
    product_store: ProductStore,
) -> GlobalSearchContext | None:
    if not settings.global_search_enabled:
        return None
    keywords = [str(keyword).strip() for keyword in settings.global_search_keywords if str(keyword).strip()]
    if not keywords:
        return None

    system_user = product_store.ensure_system_user(
        email=settings.global_search_user_email or "system@job-radar.local",
        display_name=DEFAULT_GLOBAL_SEARCH_USER_NAME,
        role=USER_ROLE_OPERATOR,
    )
    frequency_label = _format_frequency_label(settings.global_search_frequency_days)
    product_store.save_notification_preferences(
        NotificationPreference(
            site_enabled=False,
            email_enabled=False,
            line_enabled=False,
            email_recipients="",
            line_target="",
            min_relevance_score=0,
            max_jobs_per_alert=0,
            frequency=frequency_label,
        ),
        user_id=int(system_user.id),
    )

    target_name = settings.global_search_name or DEFAULT_GLOBAL_SEARCH_NAME
    rows = build_global_search_rows(keywords)
    existing = None
    for saved_search in product_store.list_saved_searches(user_id=int(system_user.id)):
        if saved_search.name == target_name:
            existing = saved_search
            break

    if existing is not None:
        if (
            canonical_rows(existing.rows) == canonical_rows(rows)
            and str(existing.custom_queries_text or "").strip() == ""
            and str(existing.crawl_preset_label or "").strip() == settings.global_search_preset_label
        ):
            return GlobalSearchContext(
                user_id=int(system_user.id),
                search_id=int(existing.id),
                search_name=existing.name,
            )
        search_id = product_store.save_search(
            user_id=int(system_user.id),
            name=target_name,
            rows=rows,
            custom_queries_text="",
            crawl_preset_label=settings.global_search_preset_label,
            search_id=int(existing.id),
        )
    else:
        search_id = product_store.save_search(
            user_id=int(system_user.id),
            name=target_name,
            rows=rows,
            custom_queries_text="",
            crawl_preset_label=settings.global_search_preset_label,
        )

    return GlobalSearchContext(
        user_id=int(system_user.id),
        search_id=int(search_id),
        search_name=target_name,
    )
