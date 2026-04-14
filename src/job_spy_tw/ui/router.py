"""提供主應用 router 的相容入口。"""

from __future__ import annotations

from .router_config import (
    DRAWER_ICON_TOKENS,
    LEGACY_TAB_MAP,
    PAGE_SHELL_METADATA,
    PAGE_SURFACE_KEYS,
)
from .router_dispatch import dispatch_main_tab
from .router_navigation import (
    build_drawer_items,
    build_drawer_sections,
    build_main_tab_items,
    peek_selected_main_tab,
    resolve_selected_main_tab,
)

__all__ = [
    "DRAWER_ICON_TOKENS",
    "LEGACY_TAB_MAP",
    "PAGE_SHELL_METADATA",
    "PAGE_SURFACE_KEYS",
    "build_drawer_items",
    "build_drawer_sections",
    "build_main_tab_items",
    "dispatch_main_tab",
    "peek_selected_main_tab",
    "resolve_selected_main_tab",
]
