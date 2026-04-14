"""Assistant tab content for assistant launcher."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from .assistant_launcher_data import QUICK_PROMPTS


def render_assistant_tab(
    *,
    on_submit_question: Callable[[str], None],
    on_switch_page: Callable[[str], None],
) -> None:
    """Render the launcher assistant tab."""
    with st.container(key="assistant-launcher-assistant-body"):
        st.markdown(
            """
<div class="assistant-launcher-hero-card">
  <div class="assistant-launcher-hero-kicker">AI Copilot</div>
  <div class="assistant-launcher-hero-title">直接問職涯方向、技能缺口與履歷策略。</div>
  <div class="assistant-launcher-hero-copy">
    可以先用快捷提問開場，或直接輸入你現在最卡的問題。
  </div>
  <ul class="assistant-launcher-hero-list">
    <li>整理下一步該補的技能</li>
    <li>判斷優先投遞的職缺方向</li>
    <li>協助你調整履歷與作品集重點</li>
  </ul>
</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='assistant-launcher-section-kicker'>快捷提問</div>",
            unsafe_allow_html=True,
        )
        with st.container(key="assistant-launcher-quick-chip-grid"):
            for row_index in range(0, len(QUICK_PROMPTS), 2):
                prompt_row = QUICK_PROMPTS[row_index : row_index + 2]
                row_cols = st.columns(len(prompt_row), gap="small")
                for col_index, prompt in enumerate(prompt_row):
                    if row_cols[col_index].button(
                        prompt,
                        key=f"assistant-launcher-chip-{row_index + col_index}",
                        type="secondary",
                        use_container_width=True,
                    ):
                        on_submit_question(prompt)

        with st.container(key="assistant-launcher-composer-shell"):
            composer_cols = st.columns([5.2, 1], gap="small")
            with composer_cols[0]:
                question = st.text_input(
                    "詢問 AI 助手",
                    key="assistant_launcher_question_input",
                    placeholder="例如：我該先補哪些技能？",
                    label_visibility="collapsed",
                )
            with composer_cols[1]:
                if st.button(
                    "↗",
                    key="assistant-launcher-send",
                    type="primary",
                    use_container_width=True,
                ):
                    on_submit_question(question)

        if st.button(
            "打開完整 AI 助理",
            key="assistant-launcher-open-page",
            type="secondary",
            use_container_width=True,
        ):
            on_switch_page("assistant")
