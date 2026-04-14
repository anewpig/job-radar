"""提供職缺卡片相關 renderer。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..detail_parsing import split_structured_items
from ..models import JobListing
from ..product_store import ProductStore
from ..salary_prediction import format_salary_estimate_label, should_display_salary_estimate
from ..utils import normalize_text
from .common import _escape, build_html_list
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


def _build_salary_chip_label(
    row: dict[str, object],
    job: JobListing | None,
) -> str:
    raw_salary = str(row.get("salary") or "").strip()
    if raw_salary:
        return f"薪資 {raw_salary}"
    if job is not None and should_display_salary_estimate(job.salary_estimate):
        return format_salary_estimate_label(job.salary_estimate or None)
    return "薪資 未提供"


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
        st.markdown(
            """
<div class="overview-empty-state">
  目前沒有符合條件的職缺，試著放寬技能或來源篩選。
</div>
            """,
            unsafe_allow_html=True,
        )
        return

    for index, row in enumerate(frame.to_dict(orient="records")):
        job = jobs_by_url.get(str(row.get("url") or ""))
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
        relevance_label = f"{row['relevance_score']}"
        salary_label = _build_salary_chip_label(row, job)
        posted_label = f"更新 {row['posted_at'] or '未提供'}"
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
        preview_empty_text = (
            ""
            if details_pending
            else "這筆職缺目前尚未拆出明確的工作內容條目。"
        )
        work_items_markup = build_html_list(
            work_content_items,
            empty_text=preview_empty_text,
            limit=3,
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
                    ("overview-job-card-score", "分數標籤。"),
                    ("overview-chip--warm", "薪資 tag。"),
                    ("job-card-block-title", "內容區塊的小標。"),
                ],
                compact=True,
                show_popover=True,
                popover_key=f"overview-job-card-shell-{index}",
            )
            st.markdown(
                f"""
<div class="overview-job-card">
  <div class="overview-job-card-header">
    <div class="overview-job-card-header-main">
      <div class="job-card-title">{_escape(row["title"])}</div>
      <div class="job-card-company">{_escape(row["company"])}</div>
    </div>
    <div class="overview-job-card-score">
      <span>分數</span>
      <strong>{_escape(relevance_label)}</strong>
    </div>
  </div>
  <div class="chip-row overview-job-card-meta">{meta_chips}</div>
  <div class="job-card-block overview-job-card-preview">
    <div class="job-card-block-title">工作內容摘要</div>
    <ul class="job-card-list">{work_items_markup}</ul>
  </div>
</div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("查看技能與條件", expanded=False):
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
            action_cols = st.columns([3.2, 1], gap="small")
            action_cols[0].empty()
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
