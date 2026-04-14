"""Bootstrap 階段共用的 dataclass 型別。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models import NotificationPreference, SavedSearch, UserAccount
from ..product_store import ProductStore
from ..search_keyword_recommender import RoleKeywordRecommender
from ..settings import Settings
from ..user_data_store import UserDataStore


@dataclass(frozen=True, slots=True)
class AppRuntime:
    """封裝整個 UI 執行期間共用的長生命週期服務與設定。"""

    root: Path
    settings: Settings
    keyword_recommender: RoleKeywordRecommender
    user_data_store: UserDataStore
    product_store: ProductStore
    notification_service: object
    guest_user: UserAccount


@dataclass(frozen=True, slots=True)
class ActiveUserContext:
    """封裝目前 Streamlit session 對應的使用者狀態。"""

    user: UserAccount
    current_user_id: int
    current_user_is_guest: bool
    current_user_role: str
    notification_preferences: NotificationPreference
    saved_searches: list[SavedSearch]
