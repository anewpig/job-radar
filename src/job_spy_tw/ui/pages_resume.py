"""提供履歷匹配頁面的渲染函式。"""

from __future__ import annotations

import streamlit as st

from ..models import ResumeJobMatch, ResumeProfile
from .common import render_section_header
from .page_context import PageContext
from .pages_resume_actions import _analyze_resume_submission
from .pages_resume_sections import (
    _render_resume_empty_state,
    _render_resume_form,
    _render_resume_results,
)


def render_resume_page(ctx: PageContext) -> None:
    """渲染履歷上傳、摘要擷取與匹配結果頁。"""
    render_section_header(
        "履歷匹配",
        "上傳履歷後，系統會整理重點技能、偏好工作內容，並用雙分數幫你看哪些職缺更適合投遞。",
        "Resume Match",
    )
    if ctx.crawl_phase == "finalizing":
        st.info("已取得初步職缺列表，正在補完整分析。等原文解析完成後再做履歷匹配會更準確。")
        return
    if ctx.current_user_is_guest:
        st.caption("目前是訪客模式。分析結果會留在這次使用期間；登入後可把履歷摘要保存到自己的帳號。")
    form_state = _render_resume_form(ctx)

    if form_state.analyze_resume:
        _analyze_resume_submission(
            ctx,
            uploaded_resume=form_state.uploaded_resume,
            pasted_resume_text=form_state.pasted_resume_text,
            use_llm=form_state.use_llm,
            collect_resume_profile=form_state.collect_resume_profile,
        )

    resume_profile: ResumeProfile | None = st.session_state.resume_profile
    resume_matches: list[ResumeJobMatch] = st.session_state.resume_matches

    if resume_profile is None:
        _render_resume_empty_state()
        return

    _render_resume_results(
        resume_profile=resume_profile,
        resume_matches=resume_matches,
    )
