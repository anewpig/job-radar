"""Header renderer for assistant launcher panel."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from .assistant_launcher_data import PANEL_COPY
from .common import _escape


def render_panel_header(tab_id: str, *, on_close: Callable[[], None]) -> None:
    """Render launcher header for current tab."""
    title, subtitle = PANEL_COPY[tab_id]
    header_cols = st.columns([0.95, 4.8, 0.9], gap="small")
    with header_cols[0]:
        st.markdown(
            """
<div class="assistant-launcher-header-brand">
  <span>JR</span>
</div>
            """,
            unsafe_allow_html=True,
        )
    with header_cols[1]:
        st.markdown(
            f"""
<div class="assistant-launcher-header-kicker">Career Support</div>
<div class="assistant-launcher-header-title">{_escape(title)}</div>
<div class="assistant-launcher-header-subtitle">{_escape(subtitle)}</div>
            """,
            unsafe_allow_html=True,
        )
    with header_cols[2]:
        if st.button(
            "✕",
            key="assistant-launcher-panel-close",
            type="secondary",
            use_container_width=True,
        ):
            on_close()
