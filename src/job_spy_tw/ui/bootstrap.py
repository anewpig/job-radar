"""提供應用層服務初始化與使用者執行期狀態整理的相容入口。"""

from __future__ import annotations

from .bootstrap_services import bootstrap_runtime
from .bootstrap_types import ActiveUserContext, AppRuntime
from .bootstrap_user_context import (
    ensure_guest_session,
    ensure_visit_tracking,
    hydrate_initial_snapshot,
    resolve_current_user,
    validate_active_saved_search,
)

__all__ = [
    "ActiveUserContext",
    "AppRuntime",
    "bootstrap_runtime",
    "ensure_guest_session",
    "ensure_visit_tracking",
    "hydrate_initial_snapshot",
    "resolve_current_user",
    "validate_active_saved_search",
]
