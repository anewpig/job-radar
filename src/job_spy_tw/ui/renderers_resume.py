"""提供履歷摘要相關 renderer。"""

from __future__ import annotations

import streamlit as st

from ..models import ResumeProfile
from ..resume_analysis import describe_resume_source, mask_personal_items, mask_personal_text
from .common import _escape_multiline, build_chip_row
from .dev_annotations import render_dev_card_annotation


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
