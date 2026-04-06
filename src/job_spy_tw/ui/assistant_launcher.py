"""提供可從任意頁面開啟 AI 助理的浮動入口。"""

from __future__ import annotations

import streamlit as st

from .session import set_main_tab


def render_assistant_launcher() -> None:
    """渲染右下角的 AI 助理浮動入口。"""
    with st.container(key="assistant-launcher-trigger-shell"):
        if st.button("✦", key="assistant-launcher-trigger", type="secondary", help="打開 AI 助理"):
            st.session_state.assistant_launcher_open = True
            st.rerun()

    if not bool(st.session_state.get("assistant_launcher_open")):
        return

    with st.container(border=True, key="assistant-launcher-card-shell"):
        pass
        st.markdown(
            """
<div style="
  background: linear-gradient(180deg, #f2cf63 0%, #efc24d 58%, #e9b33b 100%);
  border-radius: 24px;
  padding: 1.15rem 1.15rem 1.35rem;
  box-shadow: 0 22px 44px rgba(153, 110, 23, 0.20);
">
  <div style="display:flex; align-items:center; justify-content:space-between; gap:0.8rem;">
    <div style="display:inline-flex; align-items:center; gap:0.75rem;">
      <span style="
        display:inline-flex;
        align-items:center;
        justify-content:center;
        width:3rem;
        height:3rem;
        border-radius:18px;
        background:rgba(255,255,255,0.98);
        color:#6f56f6;
        font-weight:900;
        font-size:1rem;
      ">JR</span>
      <span style="color:#3e2b07; font-size:1.35rem; line-height:1; font-weight:900;">Job Radar</span>
    </div>
    <span style="color:rgba(62,43,7,0.74); font-size:1rem; font-weight:700;">AI Assistant</span>
  </div>
  <div style="margin-top:1.15rem; color:rgba(62,43,7,0.64); font-size:0.72rem; letter-spacing:0.12em; text-transform:uppercase; font-weight:800;">
    AI Assistant
  </div>
  <div style="margin-top:0.45rem; color:#281a04; font-size:2rem; line-height:1.2; font-weight:900;">
    您好，想問什麼？
  </div>
  <div style="margin-top:0.45rem; color:rgba(40,26,4,0.78); font-size:0.92rem; line-height:1.6;">
    可直接詢問技能缺口、薪資、工作內容與履歷方向。
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )

        close_cols = st.columns([1, 1, 0.42], gap="small")
        with close_cols[2]:
            if st.button(
                "✕",
                key="assistant-launcher-close-top",
                type="secondary",
                use_container_width=True,
            ):
                st.session_state.assistant_launcher_open = False
                st.rerun()

        st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
        with st.container(border=True, key="assistant-launcher-form-shell"):
            pass
            st.markdown("<div class='assistant-launcher-form-label'>詢問客服</div>", unsafe_allow_html=True)
            assistant_launcher_question = st.text_input(
                "詢問客服",
                key="assistant_launcher_question_input",
                placeholder="例如：我該先補哪些技能？",
                label_visibility="collapsed",
            )
            action_cols = st.columns(2, gap="small")
            with action_cols[0]:
                if st.button(
                    "送出問題",
                    key="assistant-launcher-submit-question",
                    type="primary",
                    use_container_width=True,
                ):
                    question = assistant_launcher_question.strip()
                    if not question:
                        st.warning("請先輸入問題。")
                    else:
                        st.session_state.assistant_question_draft = question
                        st.session_state.assistant_question_input = question
                        st.session_state.assistant_launcher_submit_pending = True
                        st.session_state.assistant_launcher_open = False
                        set_main_tab("assistant")
                        st.rerun()
            with action_cols[1]:
                if st.button(
                    "打開 AI 助理",
                    key="assistant-launcher-open-page",
                    type="secondary",
                    use_container_width=True,
                ):
                    st.session_state.assistant_launcher_open = False
                    set_main_tab("assistant")
                    st.rerun()

            faq_questions = [
                "可以優先學習的技能有哪些？",
                "目前市場對這類職缺最重視什麼條件？",
            ]
            for index, question in enumerate(faq_questions, start=1):
                faq_cols = st.columns([6.2, 0.8], gap="small")
                faq_cols[0].markdown(
                    f"<div class='assistant-launcher-faq-item'>{question}</div>",
                    unsafe_allow_html=True,
                )
                if faq_cols[1].button(
                    "›",
                    key=f"assistant-launcher-faq-{index}",
                    type="secondary",
                    use_container_width=True,
                ):
                    st.session_state.assistant_question_draft = question
                    st.session_state.assistant_question_input = question
                    st.session_state.assistant_launcher_submit_pending = True
                    st.session_state.assistant_launcher_open = False
                    set_main_tab("assistant")
                    st.rerun()
