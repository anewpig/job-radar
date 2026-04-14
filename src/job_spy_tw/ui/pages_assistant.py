"""提供 AI 助理頁面的渲染函式。"""

from __future__ import annotations

import streamlit as st

from ..models import ResumeProfile
from .assistant_actions import (
    generate_assistant_report,
    submit_assistant_question,
)
from .common import render_section_header
from .page_context import PageContext
from .pages_assistant_sections import (
    _render_assistant_cleanup_actions,
    _render_assistant_context_chips,
    _render_assistant_disabled_state,
    _render_assistant_outputs,
    _render_assistant_profile_section,
    _render_assistant_quick_ask_section,
)
from .resources import get_rag_assistant


def render_assistant_page(ctx: PageContext) -> None:
    """渲染 AI 助理頁與個人化提問流程。"""
    render_section_header(
        "AI 助理",
        "",
        "Assistant",
    )
    if not ctx.settings.openai_api_key:
        _render_assistant_disabled_state()
        return

    assistant = get_rag_assistant(
        api_key=ctx.settings.openai_api_key,
        answer_model=ctx.settings.assistant_model,
        general_chat_model=ctx.settings.assistant_general_chat_model,
        prompt_variant=ctx.settings.assistant_prompt_variant,
        latency_profile=ctx.settings.assistant_latency_profile,
        embedding_model=ctx.settings.embedding_model,
        base_url=ctx.settings.openai_base_url,
        cache_dir=str(ctx.settings.cache_dir),
        persistent_index_sync_interval_seconds=ctx.settings.assistant_ann_sync_interval_seconds,
        persistent_index_enabled=ctx.settings.assistant_persistent_index_enabled,
        persistent_index_sources=ctx.settings.assistant_persistent_index_sources,
        persistent_index_max_snapshots=ctx.settings.assistant_persistent_index_max_snapshots,
        persistent_index_max_history_rows=ctx.settings.assistant_persistent_index_max_history_rows,
        external_search_enabled=ctx.settings.assistant_external_search_enabled,
        external_search_provider=ctx.settings.assistant_external_search_provider,
        external_search_max_results=ctx.settings.assistant_external_search_max_results,
        external_search_timeout_seconds=ctx.settings.assistant_external_search_timeout_seconds,
        external_search_cache_ttl_seconds=ctx.settings.assistant_external_search_cache_ttl_seconds,
        salary_prediction_enabled=ctx.settings.salary_prediction_enabled,
        salary_prediction_model_path=str(
            ctx.settings.salary_prediction_model_path or ""
        ),
    )
    resume_context_profile: ResumeProfile | None = st.session_state.resume_profile
    manual_context_profile: ResumeProfile | None = st.session_state.assistant_profile
    assistant_profile: ResumeProfile | None = (
        resume_context_profile or manual_context_profile
    )
    _render_assistant_context_chips(assistant_profile)

    left_col, right_col = st.columns([1.02, 1.25], gap="large")
    with left_col:
        _render_assistant_profile_section(
            ctx,
            resume_context_profile=resume_context_profile,
            manual_context_profile=manual_context_profile,
        )

    with right_col:
        quick_ask_state = _render_assistant_quick_ask_section()

    if quick_ask_state.submit_question:
        if not quick_ask_state.question:
            st.warning("請先輸入問題。")
        else:
            submit_assistant_question(
                ctx=ctx,
                assistant=assistant,
                assistant_profile=assistant_profile,
                question=quick_ask_state.question,
            )

    if quick_ask_state.generate_report:
        generate_assistant_report(
            ctx=ctx,
            assistant=assistant,
            assistant_profile=assistant_profile,
        )

    _render_assistant_cleanup_actions()
    _render_assistant_outputs(
        ctx,
        assistant=assistant,
        assistant_profile=assistant_profile,
    )
