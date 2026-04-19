"""提供 AI 助理頁與履歷頁共用的互動 helper。"""

from __future__ import annotations

from time import perf_counter

import streamlit as st

from ..application.assistant_agent import AssistantAgentApplication
from ..error_taxonomy import ERROR_KIND_LLM, error_metadata
from ..models import ResumeProfile
from ..observability import new_trace_id, trace_context
from .assistant_agent_runtime import (
    AgentRuntimeContext,
    build_agent_planning_context,
    execute_agent_plan,
    resolve_pending_confirmation,
)
from .page_context import PageContext
from .search import (
    build_context_request_response,
    build_manual_assistant_profile,
    format_openai_error,
    needs_personal_context,
)
from .session import set_main_tab


def record_ai_monitoring_event(
    *,
    ctx: PageContext,
    event_type: str,
    status: str = "success",
    latency_ms: float = 0.0,
    model_name: str = "",
    metadata: dict[str, object] | None = None,
) -> None:
    try:
        ctx.product_store.record_ai_monitoring_event(
            user_id=ctx.current_user_id,
            event_type=event_type,
            status=status,
            latency_ms=latency_ms,
            model_name=model_name,
            query_signature=ctx.current_signature,
            metadata=metadata or {},
        )
    except Exception:
        pass


def usage_metadata(usage: dict[str, object] | None) -> dict[str, int]:
    payload = usage or {}
    return {
        "usage_requests": int(payload.get("requests", 0) or 0),
        "usage_input_tokens": int(payload.get("input_tokens", 0) or 0),
        "usage_output_tokens": int(payload.get("output_tokens", 0) or 0),
        "usage_total_tokens": int(payload.get("total_tokens", 0) or 0),
        "usage_cached_input_tokens": int(payload.get("cached_input_tokens", 0) or 0),
    }


def request_metrics_metadata(metrics: dict[str, object] | None) -> dict[str, object]:
    payload = metrics or {}
    if not payload:
        return {}
    allowed_keys = (
        "answer_mode",
        "selected_model",
        "used_market_retrieval",
        "chunk_cache_hit",
        "top_k",
        "prompt_version",
        "retrieval_policy_version",
        "chunking_policy_version",
        "persistent_index_version",
        "persistent_index_enabled",
        "persistent_index_runtime_sync",
        "persistent_index_source_sync",
        "persistent_ann_candidates",
        "merged_chunk_count",
        "question_intents",
        "candidate_chunk_count",
        "retrieval_scored_chunk_count",
        "retrieved_chunk_count",
        "embedding_memory_hits",
        "embedding_disk_hits",
        "embedding_remote_texts",
        "embedding_remote_batches",
        "salary_prediction_used",
        "salary_prediction_confidence",
        "salary_prediction_model_version",
        "salary_prediction_fallback_reason",
        "salary_prediction_evidence_count",
    )
    return {
        key: payload[key]
        for key in allowed_keys
        if key in payload and payload[key] not in ("", None, [], {})
    }


def monitored_model_name(default_model: str, metrics: dict[str, object] | None) -> str:
    selected = str((metrics or {}).get("selected_model") or "").strip()
    return selected or default_model


def clear_assistant_agent_state() -> None:
    st.session_state.assistant_agent_mode = "assistant"
    st.session_state.assistant_agent_task = None
    st.session_state.assistant_agent_pending_confirmation = None
    st.session_state.assistant_agent_last_result = None
    set_main_tab("assistant")
    st.rerun()


def execute_assistant_agent_task(
    *,
    ctx: PageContext,
    assistant,
    assistant_profile: ResumeProfile | None,
) -> None:
    task_plan = st.session_state.get("assistant_agent_task")
    if task_plan is None:
        st.info("目前沒有可執行的 agent 計畫。")
        return
    if st.session_state.get("assistant_agent_pending_confirmation") is not None:
        st.warning("目前有待確認的寫入動作，請先確認或取消。")
        return

    st.session_state.assistant_agent_mode = "agent_executing"
    execution_result = execute_agent_plan(
        runtime_context=AgentRuntimeContext(
            page_context=ctx,
            assistant=assistant,
            assistant_profile=assistant_profile,
        ),
        task_plan=task_plan,
    )
    st.session_state.assistant_agent_task = task_plan
    st.session_state.assistant_agent_pending_confirmation = execution_result.pending_confirmation
    st.session_state.assistant_agent_last_result = execution_result
    if execution_result.status == "waiting_confirmation":
        st.session_state.assistant_agent_mode = "agent_waiting_confirmation"
    else:
        st.session_state.assistant_agent_mode = "agent_completed"
    st.rerun()


def _submit_rag_assistant_question(
    *,
    ctx: PageContext,
    assistant,
    assistant_profile: ResumeProfile | None,
    question: str,
) -> None:
    st.session_state.assistant_question_draft = question
    st.session_state.assistant_agent_mode = "assistant"
    conversation_context = list(st.session_state.assistant_history[:3])
    answer_mode = assistant.classify_answer_mode(
        question=question,
        resume_profile=assistant_profile,
        conversation_context=conversation_context,
    )
    base_metadata: dict[str, object] = {
        "question_length": len(question),
        "has_resume_profile": assistant_profile is not None,
        "snapshot_jobs": len(ctx.snapshot.jobs),
        "role_targets": len(ctx.snapshot.role_targets),
        "history_turns_used": len(conversation_context),
        "answer_mode": answer_mode,
    }
    if assistant_profile is None and needs_personal_context(question):
        trace_id = new_trace_id("assistant")
        history = st.session_state.assistant_history
        history.insert(0, build_context_request_response(question))
        st.session_state.assistant_history = history[:6]
        record_ai_monitoring_event(
            ctx=ctx,
            event_type="assistant.answer_question",
            status="blocked_missing_profile",
            model_name=ctx.settings.assistant_model,
            metadata={**base_metadata, "trace_id": trace_id},
        )
        return

    started_at = perf_counter()
    trace_id = new_trace_id("assistant")
    answer_status = st.status("正在整理回答...", expanded=True)
    try:
        with trace_context(trace_id):
            answer_status.write("1. 檢索相關職缺、技能與市場資料")
            answer_status.write("2. 生成回答與整理引用來源")
            answer = assistant.answer_question(
                question=question,
                snapshot=ctx.snapshot,
                resume_profile=assistant_profile,
                conversation_context=conversation_context,
            )
        history = st.session_state.assistant_history
        history.insert(0, answer)
        st.session_state.assistant_history = history[:6]
        answer_status.update(
            label="回答完成",
            state="complete",
            expanded=False,
        )
        request_metrics = getattr(assistant, "last_request_metrics", None)
        record_ai_monitoring_event(
            ctx=ctx,
            event_type="assistant.answer_question",
            status="success",
            latency_ms=round((perf_counter() - started_at) * 1000, 3),
            model_name=monitored_model_name(ctx.settings.assistant_model, request_metrics),
            metadata={
                **base_metadata,
                "trace_id": trace_id,
                "used_chunks": int(answer.used_chunks),
                "citations_count": len(answer.citations),
                "key_points_count": len(answer.key_points),
                **request_metrics_metadata(request_metrics),
                **usage_metadata(getattr(assistant, "last_usage", None)),
            },
        )
    except Exception as exc:  # noqa: BLE001
        try:
            answer_status.update(
                label="回答失敗",
                state="error",
                expanded=True,
            )
        except Exception:
            pass
        record_ai_monitoring_event(
            ctx=ctx,
            event_type="assistant.answer_question",
            status="error",
            latency_ms=round((perf_counter() - started_at) * 1000, 3),
            model_name=ctx.settings.assistant_model,
            metadata={
                **base_metadata,
                "trace_id": trace_id,
                **error_metadata(
                    exc,
                    default_kind=ERROR_KIND_LLM,
                    metadata={"operation": "assistant.answer_question"},
                ),
                **request_metrics_metadata(getattr(assistant, "last_request_metrics", None)),
                **usage_metadata(getattr(assistant, "last_usage", None)),
            },
        )
        st.error(format_openai_error(exc))


def submit_assistant_question(
    *,
    ctx: PageContext,
    assistant,
    assistant_profile: ResumeProfile | None,
    question: str,
) -> None:
    """根據輸入內容決定走既有 RAG 助理或求職工作流 agent。"""
    if st.session_state.get("assistant_agent_pending_confirmation") is not None:
        st.warning("目前有待確認的寫入動作，請先確認或取消，再發起下一個 agent 任務。")
        return
    planning_context = build_agent_planning_context(
        ctx=ctx,
        assistant_profile=assistant_profile,
    )
    agent_app = AssistantAgentApplication()
    intent = agent_app.route_request(
        question=question,
        planning_context=planning_context,
    )
    if intent.route != "agent":
        _submit_rag_assistant_question(
            ctx=ctx,
            assistant=assistant,
            assistant_profile=assistant_profile,
            question=question,
        )
        return

    task_plan = agent_app.build_task_plan(
        question=question,
        intent=intent,
    )
    st.session_state.assistant_agent_mode = "agent_planned"
    st.session_state.assistant_agent_task = task_plan
    st.session_state.assistant_agent_pending_confirmation = None
    st.session_state.assistant_agent_last_result = None


def confirm_assistant_agent_action(
    *,
    ctx: PageContext,
    assistant,
    assistant_profile: ResumeProfile | None,
) -> None:
    task_plan = st.session_state.get("assistant_agent_task")
    pending_confirmation = st.session_state.get("assistant_agent_pending_confirmation")
    previous_result = st.session_state.get("assistant_agent_last_result")
    if task_plan is None or pending_confirmation is None:
        st.info("目前沒有待確認的 agent 寫入動作。")
        return

    execution_result = resolve_pending_confirmation(
        runtime_context=AgentRuntimeContext(
            page_context=ctx,
            assistant=assistant,
            assistant_profile=assistant_profile,
        ),
        task_plan=task_plan,
        pending_confirmation=pending_confirmation,
        previous_result=previous_result,
        approved=True,
    )
    st.session_state.assistant_agent_task = task_plan
    st.session_state.assistant_agent_pending_confirmation = execution_result.pending_confirmation
    st.session_state.assistant_agent_last_result = execution_result
    if execution_result.status == "waiting_confirmation":
        st.session_state.assistant_agent_mode = "agent_waiting_confirmation"
    else:
        st.session_state.assistant_agent_mode = "agent_completed"
    st.rerun()


def reject_assistant_agent_action(
    *,
    ctx: PageContext,
    assistant,
    assistant_profile: ResumeProfile | None,
) -> None:
    task_plan = st.session_state.get("assistant_agent_task")
    pending_confirmation = st.session_state.get("assistant_agent_pending_confirmation")
    previous_result = st.session_state.get("assistant_agent_last_result")
    if task_plan is None or pending_confirmation is None:
        st.info("目前沒有待確認的 agent 寫入動作。")
        return

    execution_result = resolve_pending_confirmation(
        runtime_context=AgentRuntimeContext(
            page_context=ctx,
            assistant=assistant,
            assistant_profile=assistant_profile,
        ),
        task_plan=task_plan,
        pending_confirmation=pending_confirmation,
        previous_result=previous_result,
        approved=False,
    )
    st.session_state.assistant_agent_task = task_plan
    st.session_state.assistant_agent_pending_confirmation = execution_result.pending_confirmation
    st.session_state.assistant_agent_last_result = execution_result
    st.session_state.assistant_agent_mode = "agent_completed"
    st.rerun()


def save_manual_assistant_profile(
    *,
    ctx: PageContext,
    target_roles_text: str,
    experience_level: str,
    locations_text: str,
    skills_text: str,
) -> None:
    updated_profile = build_manual_assistant_profile(
        target_roles_text=target_roles_text,
        experience_level=experience_level,
        locations_text=locations_text,
        skills_text=skills_text,
    )
    st.session_state.assistant_profile = updated_profile
    ctx.user_data_store.save_profile(
        profile=updated_profile,
        source_type="assistant_profile",
    )
    set_main_tab("assistant")
    st.session_state.favorite_feedback = "已儲存基本資料，AI 助理之後會用這份資料做個人化回答。"
    st.rerun()


def clear_manual_assistant_profile() -> None:
    st.session_state.assistant_profile = None
    set_main_tab("assistant")
    st.session_state.favorite_feedback = "已清除 AI 助理的求職基本資料。"
    st.rerun()


def clear_assistant_history() -> None:
    st.session_state.assistant_history = []
    set_main_tab("assistant")
    st.rerun()


def clear_assistant_report() -> None:
    st.session_state.assistant_report = None
    set_main_tab("assistant")
    st.rerun()


def generate_assistant_report(
    *,
    ctx: PageContext,
    assistant,
    assistant_profile: ResumeProfile | None,
) -> None:
    if assistant_profile is None:
        st.session_state.assistant_report = build_context_request_response(
            "請產生求職報告"
        )
        record_ai_monitoring_event(
            ctx=ctx,
            event_type="assistant.generate_report",
            status="blocked_missing_profile",
            model_name=ctx.settings.assistant_model,
            metadata={
                "answer_mode": "market_summary",
                "has_resume_profile": False,
                "snapshot_jobs": len(ctx.snapshot.jobs),
                "role_targets": len(ctx.snapshot.role_targets),
            },
        )
        return

    report_started_at = perf_counter()
    trace_id = new_trace_id("assistant-report")
    try:
        report_status = st.status("正在產生求職報告...", expanded=True)
        with trace_context(trace_id):
            report_status.write("1. 彙整市場快照與個人背景")
            report_status.write("2. 生成報告摘要與重點建議")
            st.session_state.assistant_report = assistant.generate_report(
                snapshot=ctx.snapshot,
                resume_profile=assistant_profile,
            )
        report_status.update(
            label="求職報告已產生",
            state="complete",
            expanded=False,
        )
        report = st.session_state.assistant_report
        request_metrics = getattr(assistant, "last_request_metrics", None)
        record_ai_monitoring_event(
            ctx=ctx,
            event_type="assistant.generate_report",
            status="success",
            latency_ms=round((perf_counter() - report_started_at) * 1000, 3),
            model_name=monitored_model_name(ctx.settings.assistant_model, request_metrics),
            metadata={
                "answer_mode": getattr(report, "answer_mode", "market_summary"),
                "has_resume_profile": True,
                "snapshot_jobs": len(ctx.snapshot.jobs),
                "role_targets": len(ctx.snapshot.role_targets),
                "trace_id": trace_id,
                "used_chunks": int(report.used_chunks),
                "citations_count": len(report.citations),
                **request_metrics_metadata(request_metrics),
                **usage_metadata(getattr(assistant, "last_usage", None)),
            },
        )
    except Exception as exc:  # noqa: BLE001
        try:
            report_status.update(
                label="求職報告產生失敗",
                state="error",
                expanded=True,
            )
        except Exception:
            pass
        record_ai_monitoring_event(
            ctx=ctx,
            event_type="assistant.generate_report",
            status="error",
            latency_ms=round((perf_counter() - report_started_at) * 1000, 3),
            model_name=ctx.settings.assistant_model,
            metadata={
                "answer_mode": "market_summary",
                "has_resume_profile": True,
                "snapshot_jobs": len(ctx.snapshot.jobs),
                "role_targets": len(ctx.snapshot.role_targets),
                "trace_id": trace_id,
                **error_metadata(
                    exc,
                    default_kind=ERROR_KIND_LLM,
                    metadata={"operation": "assistant.generate_report"},
                ),
                **request_metrics_metadata(getattr(assistant, "last_request_metrics", None)),
                **usage_metadata(getattr(assistant, "last_usage", None)),
            },
        )
        st.error(format_openai_error(exc))
