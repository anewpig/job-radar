"""Render a consolidated backend development console."""

from __future__ import annotations

import streamlit as st

from .common import render_section_header
from .crawl_runtime import render_crawl_runtime_panel
from .page_context import PageContext
from .pages_backend_architecture import render_backend_architecture_page
from .pages_backend_operations import render_backend_operations_page


def render_backend_console_page(ctx: PageContext) -> None:
    """Render all backend development interfaces in one place."""
    render_section_header(
        "後端控制台",
        "把開發期需要的後端介面集中在一起。之後如果你要從正式網站移除，只需要刪這個入口與相關頁面。",
        "Backend Console",
    )
    st.info(
        "這頁是開發期用的後端整合入口，集中查看目前查詢 runtime、後端營運監控，以及整體架構說明。"
    )

    runtime_tab, operations_tab, architecture_tab = st.tabs(
        ["目前查詢狀態", "後端營運", "架構說明"]
    )

    with runtime_tab:
        render_section_header(
            "目前查詢 Runtime",
            "這裡保留 queue / snapshot / retry 的即時狀態，方便你在開發期觀察當前查詢是不是有順利 enqueue、lease、retry 或完成。",
            "Current Query",
        )
        render_crawl_runtime_panel(
            settings=ctx.settings,
            query_signature=ctx.current_signature,
        )

    with operations_tab:
        render_backend_operations_page(ctx)

    with architecture_tab:
        render_backend_architecture_page(ctx)
