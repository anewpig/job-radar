"""提供市場相關頁面的相容入口。"""

from __future__ import annotations

from .page_context import PageContext
from .pages_market_insights import (
    render_export_page as _render_export_page,
    render_skills_page as _render_skills_page,
    render_sources_page as _render_sources_page,
    render_tasks_page as _render_tasks_page,
)
from .pages_market_overview import render_overview_page as _render_overview_page


def render_overview_page(ctx: PageContext) -> None:
    """渲染職缺總覽頁。"""
    _render_overview_page(ctx)


def render_tasks_page(ctx: PageContext) -> None:
    """渲染工作內容 / 技能頁。"""
    _render_tasks_page(ctx)


def render_skills_page(ctx: PageContext) -> None:
    """保留舊技能頁路由的相容入口。"""
    _render_skills_page(ctx)


def render_sources_page(ctx: PageContext) -> None:
    """渲染來源比較頁。"""
    _render_sources_page(ctx)


def render_export_page(ctx: PageContext) -> None:
    """渲染下載資料頁。"""
    _render_export_page(ctx)
