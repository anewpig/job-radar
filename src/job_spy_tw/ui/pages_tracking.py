"""提供追蹤中心頁面的渲染函式。"""

from __future__ import annotations

import streamlit as st

from .common import render_section_header
from .page_context import PageContext
from .pages_tracking_sections import (
    _render_favorite_shortcuts_section,
    _render_notification_stream,
    _render_saved_searches_section,
    _render_tracking_summary,
)


def render_tracking_page(ctx: PageContext) -> None:
    """渲染追蹤中心，包括已儲存搜尋、通知與收藏捷徑。"""
    render_section_header(
        "追蹤中心",
        "集中看已儲存的搜尋條件、收藏職缺與最新通知，讓你之後可以用同一套設定反覆追蹤市場變化。",
        "Tracking",
    )
    _render_tracking_summary(ctx)

    _render_notification_stream(ctx)

    saved_search_col, favorites_col = st.columns([1.35, 0.95], gap="large")
    with saved_search_col:
        _render_saved_searches_section(ctx)

    with favorites_col:
        _render_favorite_shortcuts_section(ctx)
