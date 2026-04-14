"""Guide tab content for assistant launcher."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from .assistant_launcher_data import filter_guide_groups
from .common import _escape


def render_guide_tab(*, on_switch_page: Callable[[str], None]) -> None:
    """Render the launcher guide/help tab."""
    search_term = st.text_input(
        "搜尋說明",
        key="assistant-launcher-guide-search",
        placeholder="搜尋頁面或功能",
        label_visibility="collapsed",
    )
    grouped_items = filter_guide_groups(search_term)

    with st.container(key="assistant-launcher-guide-body"):
        if not grouped_items:
            st.markdown(
                """
<div class="assistant-launcher-empty-state assistant-launcher-empty-state-centered">
  <div class="assistant-launcher-empty-icon">⌕</div>
  <div class="assistant-launcher-empty-title">找不到相符的說明</div>
  <div class="assistant-launcher-empty-copy">換個關鍵字試試，或直接回首頁查看完整功能。</div>
</div>
                """,
                unsafe_allow_html=True,
            )
            return

        for group_index, (group_title, items) in enumerate(grouped_items, start=1):
            st.markdown(
                f"<div class='assistant-launcher-guide-section-label'>{_escape(group_title)}</div>",
                unsafe_allow_html=True,
            )
            for item_index, (title, description, tab_id, _action_label) in enumerate(items, start=1):
                with st.container(key=f"assistant-launcher-guide-row-{group_index}-{item_index}"):
                    row_cols = st.columns([5.2, 0.9], gap="small")
                    row_cols[0].markdown(
                        f"""
<div class="assistant-launcher-guide-title">{_escape(title)}</div>
<div class="assistant-launcher-guide-copy">{_escape(description)}</div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if row_cols[1].button(
                        "›",
                        key=f"assistant-launcher-guide-action-{group_index}-{item_index}-{tab_id}",
                        type="secondary",
                        use_container_width=True,
                    ):
                        on_switch_page(tab_id)
