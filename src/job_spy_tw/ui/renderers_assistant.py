"""提供 AI 回答與快捷問題相關 renderer。"""

from __future__ import annotations

import streamlit as st

from .common import _escape, _escape_multiline
from .dev_annotations import render_dev_card_annotation


def render_assistant_response(title: str, response) -> None:
    """渲染帶標題、引用與檢索說明的 AI 回答卡片。"""
    if response is None:
        return
    render_dev_card_annotation(
        f"{title}卡",
        element_id=f"assistant-response-{title}",
        description="AI 助理輸出的回答 / 報告卡，內含段落標籤與引用。",
        layers=[
            "assistant-response-body",
            "citations",
            "retrieval notes",
        ],
        text_nodes=[
            ("info-card-title", "回答卡標題。"),
            ("summary-card-text", "回答內容本體。"),
        ],
        compact=True,
        show_popover=True,
        popover_key=f"assistant-response-{title}-{id(response)}",
    )
    st.markdown(
        f"""
<div class="summary-card">
  <div class="info-card-title">{_escape(title)}</div>
  <div class="summary-card-text">
    {_render_assistant_response_body(response)}
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    if response.citations:
        reference_links = [
            f"[{index}]({citation.url})"
            for index, citation in enumerate(response.citations, start=1)
            if citation.url
        ]
        if reference_links:
            st.markdown(" ".join(reference_links))
    if response.retrieval_notes:
        for note in response.retrieval_notes:
            st.caption(note)


def _render_assistant_response_body(response) -> str:
    body = str(getattr(response, "answer", "") or "").strip()
    if not body:
        body = str(getattr(response, "summary", "") or "").strip()
    return _escape_multiline(body or "目前沒有產生回答。")


def render_assistant_suggestion_buttons(questions: list[str]) -> str | None:
    """渲染快捷提問按鈕格，並回傳被點擊的問題。"""
    st.markdown(
        """
<style>
#assistant-suggestion-anchor + div [data-testid="stButton"] > button {
    width: 100%;
    min-height: 5.4rem;
    height: 5.4rem;
    padding: 0.95rem 1rem;
    border-radius: 18px;
    border: 1px solid rgba(15, 23, 42, 0.10);
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    box-shadow: 0 10px 22px rgba(15, 23, 42, 0.06);
    white-space: normal;
    line-height: 1.4;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}

#assistant-suggestion-anchor + div [data-testid="stButton"] > button:hover {
    border-color: rgba(14, 116, 144, 0.30);
    background: linear-gradient(180deg, #f0fdf4 0%, #ecfeff 100%);
}

#assistant-suggestion-anchor + div [data-testid="stButton"] {
    width: 100%;
}

@media (max-width: 960px) {
    #assistant-suggestion-anchor + div [data-testid="stButton"] > button {
        min-height: 4.8rem;
        height: 4.8rem;
    }
}
</style>
<div id="assistant-suggestion-anchor"></div>
        """,
        unsafe_allow_html=True,
    )
    rows = [questions[index : index + 2] for index in range(0, len(questions), 2)]
    for row_index, row_questions in enumerate(rows):
        suggestion_cols = st.columns(2, gap="small")
        for col_index, question in enumerate(row_questions):
            stable_key = f"assistant-suggest-{row_index}-{col_index}-{question}"
            if suggestion_cols[col_index].button(
                question,
                key=stable_key,
                use_container_width=True,
            ):
                return question
        if len(row_questions) == 1:
            suggestion_cols[1].empty()
    return None
