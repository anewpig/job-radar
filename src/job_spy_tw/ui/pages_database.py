"""提供資料庫報告頁的渲染入口。"""

from __future__ import annotations

import streamlit as st

from .page_context import PageContext
from .pages_database_data import _load_database_report
from .pages_database_sections import (
    _render_learning_section,
    _render_overview_section,
    _render_risk_section,
    _render_status_chips,
)
from .pages_database_views import _inject_database_report_styles, _render_intro


def render_database_page(ctx: PageContext) -> None:
    """渲染資料庫報告頁。"""
    _inject_database_report_styles()
    report = _load_database_report(
        data_dir=str(ctx.settings.data_dir),
        cache_backend=ctx.settings.cache_backend,
        queue_backend=ctx.settings.queue_backend,
        database_backend=ctx.settings.database_backend,
    )

    with st.container(border=True, key="database-shell"):
        _render_intro(report)
        with st.container(key="database-body"):
            _render_status_chips(report)

            overview_tab, learning_tab, risk_tab = st.tabs(
                ["現況總覽", "Database 教學", "擴充風險"]
            )

            with overview_tab:
                _render_overview_section(report)

            with learning_tab:
                _render_learning_section(report)

            with risk_tab:
                _render_risk_section(report)
