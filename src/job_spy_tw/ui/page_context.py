"""定義傳入各 UI 頁面函式的型別化上下文物件。"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..models import (
    FavoriteJob,
    JobListing,
    JobNotification,
    MarketSnapshot,
    NotificationPreference,
    SavedSearch,
)
from ..notification_service import NotificationService
from ..product_store import ProductStore
from ..settings import Settings
from ..user_data_store import UserDataStore


@dataclass(slots=True)
class PageContext:
    """封裝每個頁面渲染時共用的型別化資料。"""
    settings: Settings
    snapshot: MarketSnapshot
    crawl_phase: str
    crawl_detail_cursor: int
    crawl_detail_total: int
    job_frame: pd.DataFrame
    skill_frame: pd.DataFrame
    task_frame: pd.DataFrame
    jobs_by_url: dict[str, JobListing]
    product_store: ProductStore
    user_data_store: UserDataStore
    notification_service: NotificationService
    current_user_id: int
    current_user_is_guest: bool
    active_saved_search: SavedSearch | None
    favorite_jobs: list[FavoriteJob]
    favorite_urls: set[str]
    notifications: list[JobNotification]
    unread_notification_count: int
    saved_searches: list[SavedSearch]
    notification_preferences: NotificationPreference
    default_rows: list[dict[str, object]]
    current_signature: str
    current_search_name: str
