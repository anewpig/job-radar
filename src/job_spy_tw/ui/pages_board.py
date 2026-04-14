"""提供投遞看板頁面的渲染函式。"""

from __future__ import annotations

from .common import render_section_header
from .page_context import PageContext
from .pages_board_sections import _render_board_kanban, _render_board_summary


def render_board_page(ctx: PageContext) -> None:
    """渲染看板式投遞流程管理頁。"""
    render_section_header(
        "投遞流程管理看板",
        "把收藏職缺依投遞狀態分欄管理。你可以在卡片裡直接移動狀態、補備註，追蹤目前的求職進度。",
        "Application Board",
    )
    _render_board_summary(ctx)
    _render_board_kanban(ctx)
