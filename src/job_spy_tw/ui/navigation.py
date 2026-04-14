"""處理頂部導覽列與導覽抽屜的相容入口。"""

from __future__ import annotations

import streamlit as st

from .navigation_drawer import render_drawer_panel, render_drawer_toggle
from .navigation_tabs import render_primary_tab_bar


def render_main_navigation(
    *,
    tab_items: list[tuple[str, str]],
    drawer_items: list[tuple[str, str]],
    drawer_sections: list[dict[str, object]],
    selected_tab: str,
) -> str:
    """渲染頂部頁籤列與可展開的左側導覽抽屜。"""
    _ = drawer_items
    drawer_open = bool(st.session_state.get("nav_drawer_open"))
    chosen_tab, default_tab, tab_labels = render_primary_tab_bar(
        tab_items=tab_items,
        selected_tab=selected_tab,
    )
    render_drawer_toggle(drawer_open=drawer_open)

    if chosen_tab in tab_labels:
        st.session_state.last_primary_tab = chosen_tab

    if drawer_open:
        render_drawer_panel(
            drawer_sections=drawer_sections,
            selected_tab=selected_tab,
        )

    if selected_tab not in tab_labels and chosen_tab == default_tab:
        return selected_tab
    return chosen_tab
