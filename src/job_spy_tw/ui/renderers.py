"""提供各頁共用的卡片與回應渲染函式。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..detail_parsing import split_structured_items
from ..models import JobListing, ResumeProfile
from ..product_store import ProductStore
from ..resume_analysis import describe_resume_source, mask_personal_items, mask_personal_text
from ..utils import normalize_text
from .common import (
    _escape,
    _escape_multiline,
    build_chip_row,
    build_html_list,
)
from .dev_annotations import render_dev_card_annotation


def _build_work_preview_items(row: dict[str, object]) -> list[str]:
    """優先使用拆好的工作內容條目，必要時從 detail text 即時回推。"""
    structured_items = [
        str(item).strip()
        for item in (row.get("work_content_items") or [])
        if str(item).strip()
    ]
    if structured_items:
        return structured_items

    source = str(row.get("source") or "").strip()
    raw_work_text = ""
    detail_sections = row.get("detail_sections")
    if isinstance(detail_sections, dict):
        raw_work_text = str(detail_sections.get("work_content") or "").strip()
    description_text = str(row.get("description") or "").strip()

    candidate_texts = [raw_work_text]
    if description_text and description_text != raw_work_text:
        candidate_texts.append(description_text)

    for candidate_text in candidate_texts:
        if not candidate_text:
            continue
        fallback_items = split_structured_items(candidate_text, keep_unspecified=True)
        if fallback_items:
            if (
                candidate_text == raw_work_text
                and len(fallback_items) == 1
                and len(fallback_items[0]) >= 180
                and description_text
                and description_text != raw_work_text
            ):
                continue
            return fallback_items

    normalized = normalize_text(raw_work_text or description_text)
    return [normalized] if normalized else []


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
    details_pending: bool = False,
) -> None:
    """渲染分頁後的職缺卡片，包含收藏操作與補分析中的狀態。"""
    if frame.empty:
        st.info("目前沒有符合條件的職缺。")
        return

    for index, row in enumerate(frame.to_dict(orient="records")):
        work_content_items = _build_work_preview_items(row)
        required_skill_items = row.get("required_skill_items") or []
        requirement_items = row.get("requirement_items") or []
        other_requirements = [
            item for item in requirement_items if item not in set(required_skill_items)
        ]
        meta_parts: list[str] = [
            f'<span class="ui-chip ui-chip--soft">{_escape(row["source"])}</span>',
            f'<span class="ui-chip ui-chip--soft">{_escape(row["location"] or "地點未提供")}</span>',
        ]
        matched_role = str(row.get("matched_role") or "").strip()
        if matched_role:
            meta_parts.append(
                f'<span class="ui-chip ui-chip--accent">{_escape(matched_role)}</span>'
            )
        relevance_label = f"分數 {row['relevance_score']}"
        salary_label = f"薪資 {row['salary'] or '未提供'}"
        posted_label = f"更新 {row['posted_at'] or '未提供'}"
        meta_parts.append(
            f'<span class="ui-chip overview-chip--priority">{_escape(relevance_label)}</span>'
        )
        meta_parts.append(
            f'<span class="ui-chip overview-chip--warm">{_escape(salary_label)}</span>'
        )
        meta_parts.append(
            f'<span class="ui-chip ui-chip--soft">{_escape(posted_label)}</span>'
        )
        if row.get("url"):
            meta_parts.append(
                f'<a class="ui-chip overview-chip--link job-card-link-chip" '
                f'href="{_escape(row["url"])}" target="_blank" rel="noopener noreferrer">'
                "查看職缺原文</a>"
            )
        meta_chips = "".join(meta_parts)
        preview_limit = 4
        preview_empty_text = (
            ""
            if details_pending
            else "這筆職缺目前尚未拆出明確的工作內容條目。"
        )
        work_items_markup = build_html_list(
            work_content_items,
            empty_text=preview_empty_text,
            limit=preview_limit,
        )
        preview_note = (
            f"另有 {len(work_content_items) - preview_limit} 條完整工作內容，可展開查看詳情。"
            if len(work_content_items) > preview_limit
            else (
                ""
                if details_pending and not work_content_items
                else "展開後可查看必備技能與其他要求。"
            )
        )
        preview_note_markup = (
            f'<div class="overview-job-card-note">{_escape(preview_note)}</div>'
            if preview_note
            else ""
        )
        required_empty_text = (
            ""
            if details_pending
            else "這筆職缺目前尚未拆出明確的必備技能條目。"
        )
        required_items_markup = build_html_list(
            required_skill_items,
            empty_text=required_empty_text,
            limit=8,
        )
        other_empty_text = "" if details_pending else "目前沒有額外條件條目。"
        other_items_markup = build_html_list(
            other_requirements,
            empty_text=other_empty_text,
            limit=6,
        )
        with st.container(border=True, key=f"overview-job-card-shell-{index}"):
            render_dev_card_annotation(
                "職缺列表卡片",
                element_id=f"overview-job-card-shell-{index}",
                description="職缺總覽中的單張職缺卡，含標題、公司、meta tag、內容預覽與收藏按鈕。",
                layers=[
                    "overview-job-card-header",
                    "overview-job-card-meta",
                    "overview-job-card-preview",
                    "favorite button",
                ],
                text_nodes=[
                    ("job-card-title", "職缺名稱大標。"),
                    ("job-card-company", "公司名稱。"),
                    ("ui-chip ui-chip--soft", "來源 / 地點 / 更新時間 tag。"),
                    ("ui-chip ui-chip--accent", "匹配角色 tag。"),
                    ("overview-chip--priority", "分數 tag。"),
                    ("overview-chip--warm", "薪資 tag。"),
                    ("job-card-block-title", "內容區塊的小標。"),
                    ("overview-job-card-note", "內容預覽下方的小提醒。"),
                    ("overview-job-card-footer-note", "收藏前提示小字。"),
                ],
                compact=True,
                show_popover=True,
                popover_key=f"overview-job-card-shell-{index}",
            )
            st.markdown(
                f"""
<div class="overview-job-card">
  <div class="overview-job-card-header">
    <div>
      <div class="job-card-title">{_escape(row["title"])}</div>
      <div class="job-card-company">{_escape(row["company"])}</div>
    </div>
  </div>
  <div class="chip-row overview-job-card-meta">{meta_chips}</div>
  <div class="job-card-block overview-job-card-preview">
    <div class="job-card-block-title">工作內容預覽</div>
    <ul class="job-card-list">{work_items_markup}</ul>
    {preview_note_markup}
  </div>
</div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("查看職缺詳情", expanded=False):
                detail_cols = st.columns(2, gap="medium")
                detail_cols[0].markdown(
                    f"""
<div class="job-card-block overview-job-card-detail">
  <div class="job-card-block-title">必備技能 / 條件</div>
  <ul class="job-card-list">{required_items_markup}</ul>
</div>
                    """,
                    unsafe_allow_html=True,
                )
                detail_cols[1].markdown(
                    f"""
<div class="job-card-block overview-job-card-detail">
  <div class="job-card-block-title">其他要求</div>
  <ul class="job-card-list">{other_items_markup}</ul>
</div>
                    """,
                    unsafe_allow_html=True,
                )
            action_cols = st.columns([1.8, 1], gap="small")
            action_cols[0].markdown(
                """
<div class="overview-job-card-footer-note">
  收藏前可先展開查看完整技能條件與其他要求。
</div>
                """,
                unsafe_allow_html=True,
            )
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
    """渲染履歷頁會使用的標準化履歷摘要卡。"""
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
    render_dev_card_annotation(
        "履歷摘要卡",
        element_id="resume-summary-card",
        description="履歷分析後的摘要卡，顯示摘要段落與基本統計。",
        layers=[
            "summary-card",
            "metrics row",
        ],
        text_nodes=[
            ("info-card-title", "摘要卡標題。"),
            ("summary-card-text", "履歷摘要文字。"),
            ("st.caption", "來源與分析方式的小字。"),
        ],
        compact=True,
        show_popover=True,
        popover_key="resume-summary-card",
    )
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
    with left:
        render_dev_card_annotation(
            "履歷重點資訊卡",
            element_id="resume-profile-left-info-card",
            description="左側資訊卡，顯示目標職缺、核心技能與偏好工作內容。",
            layers=["target roles", "core skills", "preferred tasks"],
            text_nodes=[
                ("info-card-title", "區塊標題文字。"),
                ("ui-chip ui-chip--accent", "目標職缺 tag。"),
                ("ui-chip ui-chip--soft", "核心技能 tag。"),
                ("ui-chip ui-chip--warm", "偏好工作內容 tag。"),
            ],
            compact=True,
            show_popover=True,
            popover_key="resume-profile-left-info-card",
        )
    with right:
        render_dev_card_annotation(
            "履歷延伸資訊卡",
            element_id="resume-profile-right-info-card",
            description="右側資訊卡，顯示工具技能、領域關鍵字與匹配關鍵字。",
            layers=["tool skills", "domain keywords", "match keywords"],
            text_nodes=[
                ("info-card-title", "區塊標題文字。"),
                ("ui-chip ui-chip--soft", "工具技能 tag。"),
                ("ui-chip ui-chip--accent", "領域關鍵字 tag。"),
                ("ui-chip ui-chip--warm", "匹配關鍵字 tag。"),
            ],
            compact=True,
            show_popover=True,
            popover_key="resume-profile-right-info-card",
        )
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
    """渲染帶標題、引用與檢索說明的 AI 回答卡片。"""
    if response is None:
        return
    render_dev_card_annotation(
        f"{title}卡",
        element_id=f"assistant-response-{title}",
        description="AI 助理輸出的回答 / 報告卡，內含段落標籤與引用。",
        layers=[
            "assistant-response-section",
            "citations",
            "retrieval notes",
        ],
        text_nodes=[
            ("info-card-title", "回答卡標題。"),
            ("assistant-response-label", "結論 / 重點 / 限制 / 下一步的小標。"),
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
    if getattr(response, "summary", ""):
        parts = [
            f'<div class="assistant-response-section"><div class="assistant-response-label">結論</div><div>{_escape_multiline(response.summary)}</div></div>'
        ]
        if getattr(response, "key_points", None):
            bullets = "".join(
                f"<li>{_escape(point)}</li>" for point in response.key_points if str(point).strip()
            )
            if bullets:
                parts.append(
                    f'<div class="assistant-response-section"><div class="assistant-response-label">重點</div><ul class="assistant-response-list">{bullets}</ul></div>'
                )
        if getattr(response, "limitations", None):
            bullets = "".join(
                f"<li>{_escape(point)}</li>" for point in response.limitations if str(point).strip()
            )
            if bullets:
                parts.append(
                    f'<div class="assistant-response-section"><div class="assistant-response-label">限制</div><ul class="assistant-response-list">{bullets}</ul></div>'
                )
        if getattr(response, "next_step", ""):
            parts.append(
                f'<div class="assistant-response-section"><div class="assistant-response-label">下一步</div><div>{_escape_multiline(response.next_step)}</div></div>'
            )
        return "".join(parts)
    return _escape_multiline(response.answer or "目前沒有產生回答。")


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
