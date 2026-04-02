from __future__ import annotations

import streamlit as st
import pandas as pd

from ..models import JobListing, ResumeProfile
from ..product_store import ProductStore
from ..resume_analysis import describe_resume_source, mask_personal_items, mask_personal_text
from .common import (
    _escape,
    _escape_multiline,
    build_chip_row,
    build_html_list,
)


def render_job_cards(
    frame: pd.DataFrame,
    *,
    jobs_by_url: dict[str, JobListing],
    product_store: ProductStore,
    favorite_urls: set[str],
    current_user_id: int | None,
    favorites_enabled: bool,
    active_saved_search_id: int | None,
    active_saved_search_name: str,
) -> None:
    if frame.empty:
        st.info("目前沒有符合條件的職缺。")
        return

    for index, row in enumerate(frame.to_dict(orient="records")):
        work_content_items = row.get("work_content_items") or []
        required_skill_items = row.get("required_skill_items") or []
        requirement_items = row.get("requirement_items") or []
        other_requirements = [
            item for item in requirement_items if item not in set(required_skill_items)
        ]
        meta_chips = build_chip_row(
            [
                row["source"],
                row["location"] or "地點未提供",
                row["title"] or row["matched_role"] or "職缺名稱未提供",
                f"分數 {row['relevance_score']}",
                f"薪資 {row['salary'] or '未提供'}",
                f"更新 {row['posted_at'] or '未提供'}",
            ],
            tone="soft",
            limit=6,
        )
        work_items_markup = build_html_list(
            work_content_items,
            empty_text="這筆職缺目前尚未拆出明確的工作內容條目。",
            limit=8,
        )
        required_items_markup = build_html_list(
            required_skill_items,
            empty_text="這筆職缺目前尚未拆出明確的必備技能條目。",
            limit=8,
        )
        other_items_markup = build_html_list(
            other_requirements,
            empty_text="目前沒有額外條件條目。",
            limit=6,
        )
        st.markdown(
            f"""
<div class="surface-card">
  <div class="job-card-title">{_escape(row["title"])}</div>
  <div class="job-card-company">{_escape(row["company"])}</div>
  <div class="chip-row" style="margin-top:0.8rem;">{meta_chips}</div>
  <div class="job-card-block" style="margin-top:0.85rem;">
    <div class="job-card-block-title">工作內容條目</div>
    <ul class="job-card-list">{work_items_markup}</ul>
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("查看必備技能 / 條件", expanded=False):
            st.markdown(
                f"""
<div class="job-card-block" style="margin-top:0.1rem;">
  <div class="job-card-block-title">必備技能 / 條件條目</div>
  <ul class="job-card-list">{required_items_markup}</ul>
</div>
                """,
                unsafe_allow_html=True,
            )
        with st.expander("查看其他要求", expanded=False):
            st.markdown(
                f"""
<div class="job-card-block" style="margin-top:0.1rem;">
  <div class="job-card-block-title">其他要求條目</div>
  <ul class="job-card-list">{other_items_markup}</ul>
</div>
                """,
                unsafe_allow_html=True,
            )
        action_cols = st.columns([1.1, 1])
        action_cols[0].markdown(f"[查看職缺原文]({row['url']})")
        is_favorite = row["url"] in favorite_urls
        favorite_label = (
            "取消收藏"
            if is_favorite
            else "收藏職缺"
            if favorites_enabled
            else "登入後可收藏"
        )
        if action_cols[1].button(
            favorite_label,
            key=f"favorite-job-{index}",
            use_container_width=True,
            disabled=not favorites_enabled,
            help="" if favorites_enabled else "登入後才能保存自己的收藏職缺與投遞流程。",
        ):
            job = jobs_by_url.get(row["url"])
            if job is not None:
                now_favorite = product_store.toggle_favorite(
                    job,
                    user_id=int(current_user_id or product_store.guest_user_id),
                    saved_search_id=active_saved_search_id,
                    saved_search_name=active_saved_search_name,
                )
                if now_favorite:
                    st.session_state.favorite_feedback = f"已收藏：{job.title}"
                else:
                    st.session_state.favorite_feedback = f"已取消收藏：{job.title}"
                st.rerun()


def render_resume_profile(profile: ResumeProfile) -> None:
    metrics = st.columns(4)
    metrics[0].metric("目標角色", len(profile.target_roles))
    metrics[1].metric("核心技能", len(profile.core_skills))
    metrics[2].metric("工具技能", len(profile.tool_skills))
    metrics[3].metric("偏好工作內容", len(profile.preferred_tasks))

    summary_caption = "LLM 擷取" if profile.extraction_method == "llm" else "規則分析"
    if profile.llm_model:
        summary_caption = f"{summary_caption} ｜ {profile.llm_model}"

    if profile.source_name:
        st.caption(f"履歷來源：{describe_resume_source(profile.source_name)}")
    st.caption(summary_caption)
    st.markdown(
        f"""
<div class="summary-card">
  <div class="info-card-title">履歷摘要</div>
  <div class="summary-card-text">{_escape_multiline(mask_personal_text(profile.summary) or "目前沒有摘要。")}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    left.markdown(
        f"""
<div class="info-card">
  <div class="info-card-title">目標職缺</div>
  <div class="chip-row" style="margin-top:0.75rem;">{build_chip_row(mask_personal_items(profile.target_roles), empty_text="未辨識", tone="accent", limit=10)}</div>
  <div class="info-card-title" style="margin-top:1rem;">核心技能</div>
  <div class="chip-row" style="margin-top:0.75rem;">{build_chip_row(mask_personal_items(profile.core_skills), empty_text="未辨識", tone="soft", limit=12)}</div>
  <div class="info-card-title" style="margin-top:1rem;">偏好工作內容</div>
  <div class="chip-row" style="margin-top:0.75rem;">{build_chip_row(mask_personal_items(profile.preferred_tasks), empty_text="未辨識", tone="warm", limit=12)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    right.markdown(
        f"""
<div class="info-card">
  <div class="info-card-title">工具技能</div>
  <div class="chip-row" style="margin-top:0.75rem;">{build_chip_row(mask_personal_items(profile.tool_skills), empty_text="未辨識", tone="soft", limit=12)}</div>
  <div class="info-card-title" style="margin-top:1rem;">領域關鍵字</div>
  <div class="chip-row" style="margin-top:0.75rem;">{build_chip_row(mask_personal_items(profile.domain_keywords), empty_text="未辨識", tone="accent", limit=12)}</div>
  <div class="info-card-title" style="margin-top:1rem;">匹配關鍵字</div>
  <div class="chip-row" style="margin-top:0.75rem;">{build_chip_row(mask_personal_items(profile.match_keywords), empty_text="未辨識", tone="warm", limit=12)}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    if profile.generated_prompts:
        with st.expander("查看系統產生的匹配 Prompt"):
            for prompt in mask_personal_items(profile.generated_prompts):
                st.code(prompt)

    if profile.notes:
        for note in mask_personal_items(profile.notes):
            st.info(note)


def render_assistant_response(title: str, response) -> None:
    if response is None:
        return
    st.markdown(
        f"""
<div class="summary-card">
  <div class="info-card-title">{_escape(title)}</div>
  <div class="summary-card-text">{_escape_multiline(response.answer or "目前沒有產生回答。")}</div>
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


def render_assistant_suggestion_buttons(questions: list[str]) -> str | None:
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
