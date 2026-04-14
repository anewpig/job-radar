"""浮動導覽按鈕與抽屜面板。"""

from __future__ import annotations

import streamlit as st

from .common import _escape
from .dev_annotations import render_dev_card_annotation
from .navigation_scripts import render_drawer_auto_close_script
from .session import set_main_tab


def render_drawer_toggle(*, drawer_open: bool) -> None:
    """渲染右下角浮動漢堡按鈕。"""
    with st.container(key="nav-drawer-toggle-shell"):
        render_dev_card_annotation(
            "浮動導覽按鈕",
            element_id="nav-drawer-toggle-shell",
            description="右下角浮動漢堡按鈕，用來開啟更多功能抽屜。",
            text_nodes=[
                ("nav-drawer-toggle-button", "浮動漢堡 / 關閉按鈕。"),
            ],
            show_popover=True,
            popover_key="nav-drawer-toggle-shell",
        )
        with st.container(key="nav-drawer-toggle-button-shell"):
            if st.button(
                "✕" if drawer_open else "☰",
                key="nav-drawer-toggle-button",
                use_container_width=True,
                type="primary" if drawer_open else "secondary",
            ):
                st.session_state.nav_drawer_open = not drawer_open
                st.rerun()


def render_drawer_panel(
    *,
    drawer_sections: list[dict[str, object]],
    selected_tab: str,
) -> None:
    """渲染更多功能浮動抽屜面板。"""
    with st.container(border=True, key="nav-drawer-panel-shell"):
        st.markdown(
            """
<div class="nav-drawer-panel-header">
  <div class="nav-drawer-panel-kicker">TOOL PANEL</div>
  <div class="nav-drawer-panel-title">更多功能</div>
  <div class="nav-drawer-panel-desc">快速切換工作台與資料頁</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        for section in drawer_sections:
            section_key = str(section["key"])
            section_label = _escape(section["label"])
            section_items = section["items"]
            with st.container(key=f"nav-drawer-section-{section_key}"):
                st.markdown(
                    f"<div class='nav-drawer-section-label'>{section_label}</div>",
                    unsafe_allow_html=True,
                )
                for item in section_items:
                    tab_id = str(item["tab_id"])
                    label = str(item["label"])
                    is_active = tab_id == selected_tab
                    with st.container(key=f"nav-drawer-item-shell-{tab_id}"):
                        if st.button(
                            _escape(label),
                            key=f"nav-drawer-item-{tab_id}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary",
                        ):
                            st.session_state.nav_drawer_open = False
                            set_main_tab(tab_id)
                            st.rerun()
    render_drawer_auto_close_script()
