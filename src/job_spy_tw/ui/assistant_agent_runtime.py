"""Runtime helpers for the assistant job-search workflow agent."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, Any

import streamlit as st

from ..application.assistant_agent import AssistantAgentPlanningContext
from ..application.crawl import CrawlApplication, CrawlStartRequest
from ..application.query import BuildRoleTargetsRequest, QueryApplication
from ..assistant_agent.models import (
    AgentExecutionResult,
    AgentPendingConfirmation,
    AgentStep,
    AgentTaskPlan,
    AgentToolCall,
)
from ..crawl_tuning import get_crawl_preset, apply_crawl_preset
from ..models import NotificationPreference, ResumeProfile
from ..observability import trace_context
from ..search_keyword_recommender import normalize_search_role_rows
from .crawl_runtime_state import apply_pending_crawl_state, build_crawl_queries, clear_pending_crawl_state
from .search import (
    build_context_request_response,
    build_manual_assistant_profile,
    get_committed_search_rows,
)

if TYPE_CHECKING:
    from .page_context import PageContext


@dataclass(slots=True)
class AgentRuntimeContext:
    page_context: "PageContext"
    assistant: object
    assistant_profile: ResumeProfile | None


@dataclass(slots=True)
class ToolExecutionOutcome:
    tool_call: AgentToolCall
    step: AgentStep
    pending_confirmation: AgentPendingConfirmation | None = None
    answer_text: str = ""
    key_points: list[str] | None = None
    next_step: str = ""
    result_tab: str = ""


def _set_main_tab(tab_id: str) -> None:
    st.session_state.main_tab_selection = tab_id
    st.session_state.pending_main_tab_selection = tab_id


def build_agent_planning_context(
    *,
    ctx: "PageContext",
    assistant_profile: ResumeProfile | None,
) -> AssistantAgentPlanningContext:
    active_saved_search_name = ""
    if ctx.active_saved_search is not None:
        active_saved_search_name = str(ctx.active_saved_search.name or "")
    elif ctx.current_search_name:
        active_saved_search_name = str(ctx.current_search_name)

    remembered_target_roles: list[str] = []
    remembered_search_roles: list[str] = []
    remembered_locations: list[str] = []
    remembered_skills: list[str] = []
    remembered_experience_level = ""
    recent_task_summaries: list[str] = []
    if not ctx.current_user_is_guest:
        profile_memory = ctx.product_store.get_agent_memory(
            user_id=ctx.current_user_id,
            memory_type="profile_fact",
            key="assistant_profile",
        )
        search_memory = ctx.product_store.get_agent_memory(
            user_id=ctx.current_user_id,
            memory_type="workflow_fact",
            key="last_search",
        )
        task_memories = ctx.product_store.list_agent_memories(
            user_id=ctx.current_user_id,
            memory_type="task_outcome",
            limit=3,
        )
        if profile_memory is not None:
            remembered_target_roles = [
                str(role).strip()
                for role in profile_memory.value.get("target_roles", [])
                if str(role).strip()
            ]
            remembered_locations = [
                str(item).strip()
                for item in profile_memory.value.get("locations", [])
                if str(item).strip()
            ]
            remembered_skills = [
                str(item).strip()
                for item in profile_memory.value.get("skills", [])
                if str(item).strip()
            ]
            remembered_experience_level = str(
                profile_memory.value.get("experience_level", "") or ""
            ).strip()
        if search_memory is not None:
            remembered_search_roles = [
                str(role).strip()
                for role in search_memory.value.get("roles", [])
                if str(role).strip()
            ]
        recent_task_summaries = [
            str(memory.summary or "").strip()
            for memory in task_memories
            if str(memory.summary or "").strip()
        ]

    return AssistantAgentPlanningContext(
        current_search_rows=get_committed_search_rows(
            list(st.session_state.get("search_role_rows", [])),
            draft_index=st.session_state.get("search_role_draft_index"),
        ),
        custom_queries_text=str(st.session_state.get("custom_queries_text", "") or ""),
        crawl_preset_label=str(st.session_state.get("crawl_preset_label", "快速") or "快速"),
        active_saved_search_name=active_saved_search_name,
        has_snapshot=bool(ctx.snapshot.jobs),
        has_profile=assistant_profile is not None,
        remembered_target_roles=remembered_target_roles,
        remembered_search_roles=remembered_search_roles,
        remembered_locations=remembered_locations,
        remembered_skills=remembered_skills,
        remembered_experience_level=remembered_experience_level,
        recent_task_summaries=recent_task_summaries,
    )


def _unique_items(items: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = str(item or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        normalized.append(cleaned)
    return normalized


def _remember(
    ctx: "PageContext",
    *,
    memory_type: str,
    key: str,
    value: dict[str, Any],
    summary: str,
    source: str,
    confidence: float = 1.0,
) -> None:
    if ctx.current_user_is_guest:
        return
    try:
        ctx.product_store.upsert_agent_memory(
            user_id=ctx.current_user_id,
            memory_type=memory_type,
            key=key,
            value=value,
            summary=summary,
            source=source,
            confidence=confidence,
        )
    except Exception:
        pass


def _remember_task_outcome(
    ctx: "PageContext",
    *,
    task_plan: AgentTaskPlan,
    status: str,
    summary: str,
    result_tab: str,
) -> None:
    _remember(
        ctx,
        memory_type="task_outcome",
        key=f"latest_{task_plan.intent.kind}",
        value={
            "intent_kind": task_plan.intent.kind,
            "question": task_plan.question,
            "status": status,
            "result_tab": result_tab,
            "step_count": len(task_plan.steps),
            "trace_id": task_plan.trace_id,
        },
        summary=summary,
        source="assistant_agent_task",
        confidence=0.85,
    )


def _load_profile_memory(ctx: "PageContext") -> dict[str, Any]:
    if ctx.current_user_is_guest:
        return {}
    memory = ctx.product_store.get_agent_memory(
        user_id=ctx.current_user_id,
        memory_type="profile_fact",
        key="assistant_profile",
    )
    return dict(memory.value) if memory is not None else {}


def _merge_profile_payload(
    *,
    runtime_context: AgentRuntimeContext,
    payload: dict[str, Any],
) -> dict[str, Any]:
    current_profile = runtime_context.assistant_profile or st.session_state.get("assistant_profile")
    stored_memory = _load_profile_memory(runtime_context.page_context)
    merged_target_roles = _unique_items(
        list(payload.get("target_roles", []))
        or list(getattr(current_profile, "target_roles", []) or [])
        or list(stored_memory.get("target_roles", []))
    )
    merged_locations = _unique_items(
        list(payload.get("locations", []))
        or list(getattr(current_profile, "domain_keywords", []) or [])
        or list(stored_memory.get("locations", []))
    )
    incoming_skills = _unique_items(list(payload.get("skills", [])))
    existing_skills = _unique_items(
        list(getattr(current_profile, "core_skills", []) or [])
        or list(stored_memory.get("skills", []))
    )
    merged_skills = _unique_items(existing_skills + incoming_skills) if incoming_skills else existing_skills
    experience_level = str(payload.get("experience_level", "") or "").strip() or str(
        stored_memory.get("experience_level", "") or ""
    ).strip()
    return {
        "target_roles": merged_target_roles,
        "locations": merged_locations,
        "skills": merged_skills,
        "experience_level": experience_level,
    }


def execute_agent_plan(
    *,
    runtime_context: AgentRuntimeContext,
    task_plan: AgentTaskPlan,
    previous_tool_calls: list[AgentToolCall] | None = None,
) -> AgentExecutionResult:
    """Run a task plan until completion or the next confirmation gate."""
    tool_calls = list(previous_tool_calls or [])
    answer_text = ""
    key_points: list[str] = []
    next_step = ""
    result_tab = task_plan.result_tab

    task_plan.status = "running"
    with trace_context(task_plan.trace_id):
        for step in task_plan.steps:
            if step.status not in {"planned", "waiting_confirmation"}:
                continue
            if step.tool_name in {"save_assistant_profile", "create_or_update_saved_search", "update_notification_preferences"}:
                outcome = _prepare_write_tool(
                    runtime_context=runtime_context,
                    task_plan=task_plan,
                    step=step,
                )
            else:
                outcome = _execute_tool(
                    runtime_context=runtime_context,
                    task_plan=task_plan,
                    step=step,
                )

            tool_calls.append(outcome.tool_call)
            _record_tool_monitoring(
                runtime_context=runtime_context,
                task_plan=task_plan,
                tool_call=outcome.tool_call,
            )

            if outcome.answer_text:
                answer_text = outcome.answer_text
            if outcome.key_points:
                key_points = list(outcome.key_points)
            if outcome.next_step:
                next_step = outcome.next_step
            if outcome.result_tab:
                result_tab = outcome.result_tab

            if outcome.pending_confirmation is not None:
                task_plan.status = "waiting_confirmation"
                return AgentExecutionResult(
                    task_id=task_plan.task_id,
                    question=task_plan.question,
                    trace_id=task_plan.trace_id,
                    intent_kind=task_plan.intent.kind,
                    status="waiting_confirmation",
                    title=task_plan.title,
                    summary=outcome.pending_confirmation.message,
                    key_points=key_points,
                    answer_text=answer_text,
                    next_step="確認後才會真的寫入系統狀態。",
                    result_tab=result_tab,
                    steps=task_plan.steps,
                    tool_calls=tool_calls,
                    pending_confirmation=outcome.pending_confirmation,
                )
            if outcome.tool_call.status == "failed":
                task_plan.status = "failed"
                _remember_task_outcome(
                    runtime_context.page_context,
                    task_plan=task_plan,
                    status="failed",
                    summary=outcome.tool_call.user_message or outcome.tool_call.summary,
                    result_tab=result_tab,
                )
                return AgentExecutionResult(
                    task_id=task_plan.task_id,
                    question=task_plan.question,
                    trace_id=task_plan.trace_id,
                    intent_kind=task_plan.intent.kind,
                    status="failed",
                    title=task_plan.title,
                    summary=outcome.tool_call.user_message or outcome.tool_call.summary,
                    key_points=key_points,
                    answer_text=answer_text,
                    next_step=next_step or "你可以修正條件後再試一次。",
                    result_tab=result_tab,
                    steps=task_plan.steps,
                    tool_calls=tool_calls,
                )
            if outcome.tool_call.status == "blocked":
                task_plan.status = "blocked"
                _remember_task_outcome(
                    runtime_context.page_context,
                    task_plan=task_plan,
                    status="blocked",
                    summary=outcome.tool_call.user_message or outcome.tool_call.summary,
                    result_tab=result_tab,
                )
                return AgentExecutionResult(
                    task_id=task_plan.task_id,
                    question=task_plan.question,
                    trace_id=task_plan.trace_id,
                    intent_kind=task_plan.intent.kind,
                    status="blocked",
                    title=task_plan.title,
                    summary=outcome.tool_call.user_message or outcome.tool_call.summary,
                    key_points=key_points,
                    answer_text=answer_text,
                    next_step=next_step,
                    result_tab=result_tab,
                    steps=task_plan.steps,
                    tool_calls=tool_calls,
                )

    task_plan.status = "completed"
    completion_summary = _build_completion_summary(task_plan=task_plan, answer_text=answer_text)
    _remember_task_outcome(
        runtime_context.page_context,
        task_plan=task_plan,
        status="completed",
        summary=completion_summary,
        result_tab=result_tab,
    )
    return AgentExecutionResult(
        task_id=task_plan.task_id,
        question=task_plan.question,
        trace_id=task_plan.trace_id,
        intent_kind=task_plan.intent.kind,
        status="completed",
        title=task_plan.title,
        summary=completion_summary,
        key_points=key_points,
        answer_text=answer_text,
        next_step=next_step or _default_next_step(result_tab),
        result_tab=result_tab,
        steps=task_plan.steps,
        tool_calls=tool_calls,
    )


def resolve_pending_confirmation(
    *,
    runtime_context: AgentRuntimeContext,
    task_plan: AgentTaskPlan,
    pending_confirmation: AgentPendingConfirmation,
    previous_result: AgentExecutionResult | None,
    approved: bool,
) -> AgentExecutionResult:
    """Resolve a previously prepared write action and continue the workflow."""
    step = next(
        (candidate for candidate in task_plan.steps if candidate.step_id == pending_confirmation.step_id),
        None,
    )
    if step is None:
        task_plan.status = "failed"
        return AgentExecutionResult(
            task_id=task_plan.task_id,
            question=task_plan.question,
            trace_id=task_plan.trace_id,
            intent_kind=task_plan.intent.kind,
            status="failed",
            title=task_plan.title,
            summary="找不到待確認的步驟，請重新發起任務。",
            steps=task_plan.steps,
            tool_calls=list(previous_result.tool_calls if previous_result else []),
        )

    prior_tool_calls = list(previous_result.tool_calls if previous_result else [])
    if not approved:
        step.status = "cancelled"
        step.summary = "你已取消這次寫入。"
        cancelled_call = AgentToolCall(
            step_id=step.step_id,
            tool_name=step.tool_name,
            status="cancelled",
            summary="你已取消這次寫入。",
            user_message="這次寫入已取消，前面已完成的讀取結果仍保留。",
            metadata={
                "agent_intent": task_plan.intent.kind,
                "confirmation_status": "rejected",
            },
        )
        prior_tool_calls.append(cancelled_call)
        _record_tool_monitoring(
            runtime_context=runtime_context,
            task_plan=task_plan,
            tool_call=cancelled_call,
        )
        runtime_context.page_context.product_store.record_audit_event(
            event_type="assistant.agent.confirmation_rejected",
            status="cancelled",
            target_type=pending_confirmation.target_type,
            target_id=pending_confirmation.target_id,
            details={
                "tool_name": pending_confirmation.tool_name,
                "after_summary": pending_confirmation.after_summary,
            },
            user_id=runtime_context.page_context.current_user_id,
            actor_role=runtime_context.page_context.current_user_role,
            trace_id=task_plan.trace_id,
        )
        task_plan.status = "completed" if any(call.status == "success" for call in prior_tool_calls) else "cancelled"
        _remember_task_outcome(
            runtime_context.page_context,
            task_plan=task_plan,
            status=str(task_plan.status),
            summary="你已取消這次寫入，前面整理好的結果仍保留。",
            result_tab=previous_result.result_tab if previous_result else task_plan.result_tab,
        )
        return AgentExecutionResult(
            task_id=task_plan.task_id,
            question=task_plan.question,
            trace_id=task_plan.trace_id,
            intent_kind=task_plan.intent.kind,
            status=task_plan.status,
            title=task_plan.title,
            summary="你已取消這次寫入，前面整理好的結果仍保留。",
            answer_text=previous_result.answer_text if previous_result else "",
            key_points=list(previous_result.key_points if previous_result else []),
            next_step=previous_result.next_step if previous_result else "",
            result_tab=previous_result.result_tab if previous_result else task_plan.result_tab,
            steps=task_plan.steps,
            tool_calls=prior_tool_calls,
        )

    with trace_context(task_plan.trace_id):
        outcome = _execute_tool(
            runtime_context=runtime_context,
            task_plan=task_plan,
            step=step,
            force_payload=pending_confirmation.payload,
        )
    prior_tool_calls.append(outcome.tool_call)
    _record_tool_monitoring(
        runtime_context=runtime_context,
        task_plan=task_plan,
        tool_call=outcome.tool_call,
    )
    if outcome.tool_call.status == "success":
        runtime_context.page_context.product_store.record_audit_event(
            event_type=f"assistant.agent.{pending_confirmation.tool_name}.confirmed",
            status="success",
            target_type=pending_confirmation.target_type,
            target_id=pending_confirmation.target_id,
            details={
                "before_summary": pending_confirmation.before_summary,
                "after_summary": pending_confirmation.after_summary,
            },
            user_id=runtime_context.page_context.current_user_id,
            actor_role=runtime_context.page_context.current_user_role,
            trace_id=task_plan.trace_id,
        )

    return execute_agent_plan(
        runtime_context=runtime_context,
        task_plan=task_plan,
        previous_tool_calls=prior_tool_calls,
    )


def _prepare_write_tool(
    *,
    runtime_context: AgentRuntimeContext,
    task_plan: AgentTaskPlan,
    step: AgentStep,
) -> ToolExecutionOutcome:
    ctx = runtime_context.page_context
    payload = dict(step.payload)
    if ctx.current_user_is_guest:
        step.status = "blocked"
        step.summary = "訪客模式下不能替你寫入設定。"
        return ToolExecutionOutcome(
            tool_call=AgentToolCall(
                step_id=step.step_id,
                tool_name=step.tool_name,
                status="blocked",
                summary=step.summary,
                user_message="目前是訪客模式，agent 不會替你做持久化寫入。請先登入後再試。",
                metadata={
                    "agent_intent": task_plan.intent.kind,
                    "confirmation_status": "blocked_guest",
                },
            ),
            step=step,
        )

    before_summary = ""
    after_summary = ""
    message = ""
    target_type = step.tool_name
    target_id = ""

    if step.tool_name == "save_assistant_profile":
        profile_payload = _merge_profile_payload(
            runtime_context=runtime_context,
            payload=payload,
        )
        if not (
            profile_payload.get("target_roles")
            or profile_payload.get("locations")
            or profile_payload.get("skills")
            or profile_payload.get("experience_level")
        ):
            step.status = "blocked"
            step.summary = "缺少可更新的背景資料。"
            return ToolExecutionOutcome(
                tool_call=AgentToolCall(
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    status="blocked",
                    summary=step.summary,
                    user_message="我目前沒辦法從這句話整理出可寫入的個人背景。請至少提供目標職缺、技能、地點或年資。",
                    metadata={"agent_intent": task_plan.intent.kind},
                ),
                step=step,
            )
        current_profile = runtime_context.assistant_profile or st.session_state.get("assistant_profile")
        if current_profile is not None and getattr(current_profile, "summary", ""):
            before_summary = str(current_profile.summary)
        else:
            before_summary = str(_load_profile_memory(ctx).get("summary", "") or "")
        after_summary = "；".join(
            part
            for part in [
                f"目標職缺：{'、'.join(payload.get('target_roles', [])[:3])}" if payload.get("target_roles") else "",
                f"年資：{payload.get('experience_level')}" if payload.get("experience_level") else "",
                f"希望地點：{'、'.join(payload.get('locations', [])[:3])}" if payload.get("locations") else "",
                f"目前技能：{'、'.join(payload.get('skills', [])[:5])}" if payload.get("skills") else "",
            ]
            if part
        )
        payload = profile_payload
        message = f"我準備替你更新 AI 助理個人背景：{after_summary or '新的基本資料'}。"
        target_id = str(ctx.current_user_id)
    elif step.tool_name == "create_or_update_saved_search":
        rows = _resolve_search_rows(payload=payload)
        if not rows:
            step.status = "blocked"
            step.summary = "目前沒有可保存的搜尋條件。"
            return ToolExecutionOutcome(
                tool_call=AgentToolCall(
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    status="blocked",
                    summary=step.summary,
                    user_message="我現在沒有足夠的搜尋條件可存成 saved search。請先指定職缺角色，或先讓我替你跑一次搜尋。",
                    metadata={"agent_intent": task_plan.intent.kind},
                ),
                step=step,
            )
        name = str(payload.get("name", "") or "我的搜尋")
        existing = ctx.product_store.find_saved_search_by_signature(
            rows,
            st.session_state.custom_queries_text,
            st.session_state.crawl_preset_label,
            user_id=ctx.current_user_id,
        )
        before_summary = existing.name if existing is not None else "目前沒有相同條件的 saved search"
        after_summary = f"{name}（{ ' / '.join([row['role'] for row in rows if row.get('role')][:2]) }）"
        message = f"我準備替你{('更新' if existing is not None else '建立')} saved search：{after_summary}。"
        target_id = str(existing.id) if existing is not None else name
    elif step.tool_name == "update_notification_preferences":
        changes = payload
        if not changes:
            step.status = "blocked"
            step.summary = "缺少可更新的通知條件。"
            return ToolExecutionOutcome(
                tool_call=AgentToolCall(
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    status="blocked",
                    summary=step.summary,
                    user_message="我還沒讀到你要怎麼改通知條件。請直接說明要開哪些通道、門檻分數或每次通知上限。",
                    metadata={"agent_intent": task_plan.intent.kind},
                ),
                step=step,
            )
        current = ctx.notification_preferences
        before_summary = _notification_summary(current)
        proposed = NotificationPreference(
            site_enabled=bool(changes.get("site_enabled", current.site_enabled)),
            email_enabled=bool(changes.get("email_enabled", current.email_enabled)),
            line_enabled=bool(changes.get("line_enabled", current.line_enabled)),
            email_recipients=str(changes.get("email_recipients", current.email_recipients)),
            line_target=str(changes.get("line_target", current.line_target)),
            line_bind_code=current.line_bind_code,
            line_bind_requested_at=current.line_bind_requested_at,
            line_bind_expires_at=current.line_bind_expires_at,
            line_bound_at=current.line_bound_at,
            min_relevance_score=float(changes.get("min_relevance_score", current.min_relevance_score)),
            max_jobs_per_alert=int(changes.get("max_jobs_per_alert", current.max_jobs_per_alert)),
            frequency=current.frequency,
        )
        after_summary = _notification_summary(proposed)
        message = f"我準備替你更新通知條件：{after_summary}。"
        target_id = str(ctx.current_user_id)

    step.status = "waiting_confirmation"
    step.summary = message
    pending = AgentPendingConfirmation(
        confirmation_id=f"agent-confirm-{st.session_state.get('_app_render_nonce', '')}-{step.step_id}",
        task_id=task_plan.task_id,
        step_id=step.step_id,
        tool_name=step.tool_name,
        message=message,
        target_type=target_type,
        target_id=target_id,
        before_summary=before_summary,
        after_summary=after_summary,
        payload=payload,
        trace_id=task_plan.trace_id,
    )
    return ToolExecutionOutcome(
        tool_call=AgentToolCall(
            step_id=step.step_id,
            tool_name=step.tool_name,
            status="needs_confirmation",
            summary=message,
            user_message=message,
            metadata={
                "agent_intent": task_plan.intent.kind,
                "confirmation_status": "required",
                "target_type": target_type,
            },
        ),
        step=step,
        pending_confirmation=pending,
    )


def _execute_tool(
    *,
    runtime_context: AgentRuntimeContext,
    task_plan: AgentTaskPlan,
    step: AgentStep,
    force_payload: dict[str, Any] | None = None,
) -> ToolExecutionOutcome:
    started_at = perf_counter()
    tool_name = step.tool_name
    payload = dict(force_payload or step.payload or {})
    try:
        if tool_name == "inspect_snapshot":
            outcome = _tool_inspect_snapshot(runtime_context=runtime_context, step=step)
        elif tool_name == "start_or_refresh_search":
            outcome = _tool_start_or_refresh_search(
                runtime_context=runtime_context,
                step=step,
                payload=payload,
            )
        elif tool_name == "generate_job_report":
            outcome = _tool_generate_job_report(runtime_context=runtime_context, step=step)
        elif tool_name == "summarize_market_snapshot":
            outcome = _tool_summarize_market_snapshot(runtime_context=runtime_context, task_plan=task_plan, step=step)
        elif tool_name == "switch_main_tab":
            outcome = _tool_switch_main_tab(step=step, payload=payload)
        elif tool_name == "open_relevant_surface":
            outcome = _tool_open_relevant_surface(step=step, payload=payload)
        elif tool_name == "save_assistant_profile":
            outcome = _tool_save_assistant_profile(runtime_context=runtime_context, step=step, payload=payload)
        elif tool_name == "create_or_update_saved_search":
            outcome = _tool_create_or_update_saved_search(runtime_context=runtime_context, step=step, payload=payload)
        elif tool_name == "update_notification_preferences":
            outcome = _tool_update_notification_preferences(runtime_context=runtime_context, step=step, payload=payload)
        else:
            step.status = "failed"
            step.summary = f"未知工具：{tool_name}"
            outcome = ToolExecutionOutcome(
                tool_call=AgentToolCall(
                    step_id=step.step_id,
                    tool_name=tool_name,
                    status="failed",
                    summary=step.summary,
                    user_message=step.summary,
                    metadata={"tool_error": "unknown_tool"},
                ),
                step=step,
            )
    except Exception as exc:  # noqa: BLE001
        step.status = "failed"
        step.summary = f"{tool_name} 執行失敗：{exc}"
        outcome = ToolExecutionOutcome(
            tool_call=AgentToolCall(
                step_id=step.step_id,
                tool_name=tool_name,
                status="failed",
                summary=step.summary,
                user_message=f"這一步執行失敗：{exc}",
                metadata={
                    "agent_intent": task_plan.intent.kind,
                    "tool_error": exc.__class__.__name__,
                },
            ),
            step=step,
        )
    outcome.tool_call.duration_ms = round((perf_counter() - started_at) * 1000, 3)
    return outcome


def _tool_inspect_snapshot(*, runtime_context: AgentRuntimeContext, step: AgentStep) -> ToolExecutionOutcome:
    snapshot = st.session_state.get("snapshot")
    if snapshot is None:
        step.status = "success"
        step.summary = "目前還沒有市場快照，我會依任務需要建立新的查詢。"
        return ToolExecutionOutcome(
            tool_call=AgentToolCall(
                step_id=step.step_id,
                tool_name=step.tool_name,
                status="success",
                summary=step.summary,
                user_message=step.summary,
                metadata={"has_snapshot": False},
            ),
            step=step,
        )
    step.status = "success"
    step.summary = f"目前快照共有 {len(snapshot.jobs)} 筆職缺，最近更新時間是 {snapshot.generated_at or '未提供'}。"
    return ToolExecutionOutcome(
        tool_call=AgentToolCall(
            step_id=step.step_id,
            tool_name=step.tool_name,
            status="success",
            summary=step.summary,
            user_message=step.summary,
            metadata={
                "has_snapshot": True,
                "snapshot_jobs": len(snapshot.jobs),
                "snapshot_generated_at": snapshot.generated_at,
            },
        ),
        step=step,
    )


def _tool_start_or_refresh_search(
    *,
    runtime_context: AgentRuntimeContext,
    step: AgentStep,
    payload: dict[str, Any],
) -> ToolExecutionOutcome:
    ctx = runtime_context.page_context
    roles = [str(role).strip() for role in payload.get("roles", []) if str(role).strip()]
    if not roles:
        step.status = "blocked"
        step.summary = "缺少目標職缺，無法替你啟動搜尋。"
        return ToolExecutionOutcome(
            tool_call=AgentToolCall(
                step_id=step.step_id,
                tool_name=step.tool_name,
                status="blocked",
                summary=step.summary,
                user_message="請直接告訴我要找哪一類職缺，例如「AI 工程師」或「前端工程師」。",
                metadata={"missing": "roles"},
            ),
            step=step,
        )

    rows = normalize_search_role_rows(
        [
            {
                "enabled": True,
                "priority": index + 1,
                "role": role,
                "keywords": "",
            }
            for index, role in enumerate(roles)
        ]
    )
    _update_search_session(rows=rows, crawl_preset_label=str(payload.get("crawl_preset_label", "快速") or "快速"))
    role_targets = QueryApplication().build_role_targets(
        BuildRoleTargetsRequest(rows=rows)
    )
    crawl_preset = get_crawl_preset(st.session_state.crawl_preset_label)
    runtime_settings = apply_crawl_preset(ctx.settings, crawl_preset)
    queries = build_crawl_queries(
        role_targets=role_targets,
        crawl_preset=crawl_preset,
        custom_queries=st.session_state.custom_queries_text,
    )
    signature = ctx.product_store.build_signature(
        rows,
        st.session_state.custom_queries_text,
        st.session_state.crawl_preset_label,
    )
    start_result = CrawlApplication().start(
        CrawlStartRequest(
            settings=runtime_settings,
            role_targets=role_targets,
            queries=queries,
            query_signature=signature,
            force_refresh=False,
            crawl_preset_label=st.session_state.crawl_preset_label,
            worker_id=str(st.session_state.crawl_worker_id),
            execution_mode=ctx.settings.crawl_execution_mode,
            rows=rows,
            custom_queries_text=st.session_state.custom_queries_text,
            user_id=None if ctx.current_user_is_guest else ctx.current_user_id,
            active_saved_search_id=None,
        )
    )
    st.session_state.crawl_query_signature = signature
    if start_result.snapshot is not None:
        st.session_state.snapshot = start_result.snapshot
        st.session_state.last_crawl_signature = signature

    if start_result.status == "invalid":
        step.status = "blocked"
        step.summary = start_result.warning_message or "搜尋條件不足。"
        return ToolExecutionOutcome(
            tool_call=AgentToolCall(
                step_id=step.step_id,
                tool_name=step.tool_name,
                status="blocked",
                summary=step.summary,
                user_message=step.summary,
                metadata={"roles": roles, "query_signature": signature},
            ),
            step=step,
        )
    if start_result.status == "awaiting_snapshot":
        if start_result.pending_state is not None:
            apply_pending_crawl_state(
                phase="awaiting_snapshot",
                pending_state=start_result.pending_state,
            )
        step.status = "success"
        step.summary = "已有其他 worker 正在刷新同一組條件，我會等待最新快照。"
    elif start_result.pending_state is not None:
        apply_pending_crawl_state(
            phase="finalizing",
            pending_state=start_result.pending_state,
        )
        step.status = "success"
        step.summary = "已建立初步職缺列表，背景補分析會繼續完成剩餘內容。"
    else:
        clear_pending_crawl_state()
        step.status = "success"
        if start_result.status == "used_fresh_cache":
            step.summary = "已直接使用最新快照，不需要重新抓取。"
        else:
            step.summary = f"已替你整理 {len(st.session_state.snapshot.jobs) if st.session_state.snapshot is not None else 0} 筆目前職缺。"
    _remember(
        ctx,
        memory_type="workflow_fact",
        key="last_search",
        value={
            "roles": roles,
            "query_signature": signature,
            "crawl_preset_label": st.session_state.crawl_preset_label,
            "job_count": len(st.session_state.snapshot.jobs) if st.session_state.get("snapshot") is not None else 0,
            "crawl_status": start_result.status,
        },
        summary=f"最近搜尋：{' / '.join(roles[:2])}",
        source="assistant_agent_search",
    )
    return ToolExecutionOutcome(
        tool_call=AgentToolCall(
            step_id=step.step_id,
            tool_name=step.tool_name,
            status="success",
            summary=step.summary,
            user_message=step.summary,
            metadata={
                "roles": roles,
                "query_signature": signature,
                "crawl_status": start_result.status,
                "queries": queries,
            },
        ),
        step=step,
        result_tab="overview",
        next_step="你可以打開職缺總覽查看這次搜尋結果。",
    )


def _tool_generate_job_report(
    *,
    runtime_context: AgentRuntimeContext,
    step: AgentStep,
) -> ToolExecutionOutcome:
    if runtime_context.assistant_profile is None:
        response = build_context_request_response("請產生求職報告")
        step.status = "blocked"
        step.summary = response.answer
        return ToolExecutionOutcome(
            tool_call=AgentToolCall(
                step_id=step.step_id,
                tool_name=step.tool_name,
                status="blocked",
                summary="缺少個人背景，無法直接產生求職報告。",
                user_message=response.answer,
                metadata={"missing": "assistant_profile"},
            ),
            step=step,
            answer_text=response.answer,
            next_step="請先提供履歷或填寫求職基本資料。",
        )

    response = runtime_context.assistant.generate_report(
        snapshot=runtime_context.page_context.snapshot,
        resume_profile=runtime_context.assistant_profile,
    )
    st.session_state.assistant_report = response
    step.status = "success"
    step.summary = "已替你產生新的求職報告。"
    return ToolExecutionOutcome(
        tool_call=AgentToolCall(
            step_id=step.step_id,
            tool_name=step.tool_name,
            status="success",
            summary=step.summary,
            user_message=step.summary,
            metadata={
                "answer_mode": getattr(response, "answer_mode", ""),
                "used_chunks": int(getattr(response, "used_chunks", 0)),
                "selected_model": str((runtime_context.assistant.last_request_metrics or {}).get("selected_model") or ""),
            },
        ),
        step=step,
        answer_text=response.answer,
        key_points=list(response.key_points),
        next_step=response.next_step,
        result_tab="assistant",
    )


def _tool_summarize_market_snapshot(
    *,
    runtime_context: AgentRuntimeContext,
    task_plan: AgentTaskPlan,
    step: AgentStep,
) -> ToolExecutionOutcome:
    snapshot = st.session_state.get("snapshot")
    if snapshot is None:
        step.status = "blocked"
        step.summary = "目前沒有可整理的市場快照。"
        return ToolExecutionOutcome(
            tool_call=AgentToolCall(
                step_id=step.step_id,
                tool_name=step.tool_name,
                status="blocked",
                summary=step.summary,
                user_message="目前沒有可整理的市場快照。請先指定職缺，讓我替你跑一次搜尋。",
                metadata={"has_snapshot": False},
            ),
            step=step,
        )

    response = runtime_context.assistant.answer_question(
        question=task_plan.question,
        snapshot=snapshot,
        resume_profile=runtime_context.assistant_profile,
        conversation_context=[],
    )
    step.status = "success"
    step.summary = "已整理目前市場摘要。"
    return ToolExecutionOutcome(
        tool_call=AgentToolCall(
            step_id=step.step_id,
            tool_name=step.tool_name,
            status="success",
            summary=step.summary,
            user_message=step.summary,
            metadata={
                "answer_mode": getattr(response, "answer_mode", ""),
                "used_chunks": int(getattr(response, "used_chunks", 0)),
                "selected_model": str((runtime_context.assistant.last_request_metrics or {}).get("selected_model") or ""),
            },
        ),
        step=step,
        answer_text=response.answer,
        key_points=list(response.key_points),
        next_step=response.next_step,
        result_tab="overview",
    )


def _tool_switch_main_tab(*, step: AgentStep, payload: dict[str, Any]) -> ToolExecutionOutcome:
    tab_id = str(payload.get("tab_id", "") or "").strip()
    if not tab_id:
        step.status = "blocked"
        step.summary = "沒有可切換的頁面。"
        return ToolExecutionOutcome(
            tool_call=AgentToolCall(
                step_id=step.step_id,
                tool_name=step.tool_name,
                status="blocked",
                summary=step.summary,
                user_message="我沒有讀到要切去哪個工作台。",
            ),
            step=step,
        )
    _set_main_tab(tab_id)
    step.status = "success"
    step.summary = f"我已替你準備切到 {tab_id} 工作台。"
    return ToolExecutionOutcome(
        tool_call=AgentToolCall(
            step_id=step.step_id,
            tool_name=step.tool_name,
            status="success",
            summary=step.summary,
            user_message=step.summary,
            metadata={"tab_id": tab_id},
        ),
        step=step,
        result_tab=tab_id,
        next_step=f"按下下方按鈕即可打開 {tab_id} 工作台。",
    )


def _tool_open_relevant_surface(*, step: AgentStep, payload: dict[str, Any]) -> ToolExecutionOutcome:
    tab_id = str(payload.get("tab_id", "") or "assistant")
    step.status = "success"
    step.summary = f"我已替你整理好結果，建議下一步打開 {tab_id} 工作台。"
    return ToolExecutionOutcome(
        tool_call=AgentToolCall(
            step_id=step.step_id,
            tool_name=step.tool_name,
            status="success",
            summary=step.summary,
            user_message=step.summary,
            metadata={"tab_id": tab_id},
        ),
        step=step,
        result_tab=tab_id,
    )


def _tool_save_assistant_profile(
    *,
    runtime_context: AgentRuntimeContext,
    step: AgentStep,
    payload: dict[str, Any],
) -> ToolExecutionOutcome:
    ctx = runtime_context.page_context
    merged_payload = _merge_profile_payload(
        runtime_context=runtime_context,
        payload=payload,
    )
    updated_profile = build_manual_assistant_profile(
        target_roles_text="、".join(merged_payload.get("target_roles", [])),
        experience_level=str(merged_payload.get("experience_level", "") or ""),
        locations_text="、".join(merged_payload.get("locations", [])),
        skills_text="、".join(merged_payload.get("skills", [])),
    )
    st.session_state.assistant_profile = updated_profile
    ctx.user_data_store.save_profile(
        profile=updated_profile,
        source_type="assistant_agent_profile",
    )
    _remember(
        ctx,
        memory_type="profile_fact",
        key="assistant_profile",
        value={
            "target_roles": list(updated_profile.target_roles),
            "skills": list(updated_profile.core_skills),
            "locations": list(merged_payload.get("locations", [])),
            "experience_level": str(merged_payload.get("experience_level", "") or ""),
            "summary": updated_profile.summary,
        },
        summary=updated_profile.summary or "已更新 AI 助理背景",
        source="assistant_agent_profile",
    )
    step.status = "success"
    step.summary = "已更新 AI 助理的個人背景。"
    return ToolExecutionOutcome(
        tool_call=AgentToolCall(
            step_id=step.step_id,
            tool_name=step.tool_name,
            status="success",
            summary=step.summary,
            user_message=step.summary,
            metadata={
                "profile_roles": updated_profile.target_roles,
                "profile_skills": updated_profile.core_skills,
            },
        ),
        step=step,
        result_tab="assistant",
        next_step="你現在可以直接追問個人化建議。",
    )


def _tool_create_or_update_saved_search(
    *,
    runtime_context: AgentRuntimeContext,
    step: AgentStep,
    payload: dict[str, Any],
) -> ToolExecutionOutcome:
    ctx = runtime_context.page_context
    rows = _resolve_search_rows(payload=payload)
    if not rows:
        step.status = "blocked"
        step.summary = "目前沒有可保存的搜尋條件。"
        return ToolExecutionOutcome(
            tool_call=AgentToolCall(
                step_id=step.step_id,
                tool_name=step.tool_name,
                status="blocked",
                summary=step.summary,
                user_message=step.summary,
            ),
            step=step,
        )

    name = str(payload.get("name", "") or "我的搜尋")
    signature = ctx.product_store.build_signature(
        rows,
        st.session_state.custom_queries_text,
        st.session_state.crawl_preset_label,
    )
    existing = ctx.product_store.find_saved_search_by_signature(
        rows,
        st.session_state.custom_queries_text,
        st.session_state.crawl_preset_label,
        user_id=ctx.current_user_id,
    )
    search_id = existing.id if existing is not None else None
    snapshot = st.session_state.snapshot if st.session_state.get("last_crawl_signature") == signature else None
    saved_search_id = ctx.product_store.save_search(
        user_id=ctx.current_user_id,
        name=name,
        rows=rows,
        custom_queries_text=st.session_state.custom_queries_text,
        crawl_preset_label=st.session_state.crawl_preset_label,
        snapshot=snapshot,
        search_id=search_id,
    )
    st.session_state.active_saved_search_id = saved_search_id
    _remember(
        ctx,
        memory_type="workflow_fact",
        key="last_saved_search",
        value={
            "search_id": saved_search_id,
            "name": name,
            "roles": [str(row.get("role", "")).strip() for row in rows if str(row.get("role", "")).strip()],
            "query_signature": signature,
        },
        summary=f"最近存成的搜尋：{name}",
        source="assistant_agent_saved_search",
    )
    step.status = "success"
    step.summary = f"已替你{('更新' if search_id else '建立')} saved search：{name}。"
    return ToolExecutionOutcome(
        tool_call=AgentToolCall(
            step_id=step.step_id,
            tool_name=step.tool_name,
            status="success",
            summary=step.summary,
            user_message=step.summary,
            metadata={
                "search_id": saved_search_id,
                "query_signature": signature,
                "search_name": name,
            },
        ),
        step=step,
        result_tab="tracking",
        next_step="你可以前往追蹤中心查看這組 saved search。",
    )


def _tool_update_notification_preferences(
    *,
    runtime_context: AgentRuntimeContext,
    step: AgentStep,
    payload: dict[str, Any],
) -> ToolExecutionOutcome:
    ctx = runtime_context.page_context
    current = ctx.product_store.get_notification_preferences(user_id=ctx.current_user_id)
    updated = NotificationPreference(
        site_enabled=bool(payload.get("site_enabled", current.site_enabled)),
        email_enabled=bool(payload.get("email_enabled", current.email_enabled)),
        line_enabled=bool(payload.get("line_enabled", current.line_enabled)),
        email_recipients=str(payload.get("email_recipients", current.email_recipients)),
        line_target=str(payload.get("line_target", current.line_target)),
        line_bind_code=current.line_bind_code,
        line_bind_requested_at=current.line_bind_requested_at,
        line_bind_expires_at=current.line_bind_expires_at,
        line_bound_at=current.line_bound_at,
        min_relevance_score=float(payload.get("min_relevance_score", current.min_relevance_score)),
        max_jobs_per_alert=int(payload.get("max_jobs_per_alert", current.max_jobs_per_alert)),
        frequency=current.frequency,
    )
    ctx.product_store.save_notification_preferences(updated, user_id=ctx.current_user_id)
    st.session_state.notify_site_enabled = updated.site_enabled
    st.session_state.notify_email_enabled = updated.email_enabled
    st.session_state.notify_line_enabled = updated.line_enabled
    st.session_state.notify_email_recipients = updated.email_recipients
    st.session_state.notify_line_target = updated.line_target
    st.session_state.notify_min_score = int(updated.min_relevance_score)
    st.session_state.notify_max_jobs = int(updated.max_jobs_per_alert)
    _remember(
        ctx,
        memory_type="user_preference",
        key="notification_preferences",
        value={
            "site_enabled": updated.site_enabled,
            "email_enabled": updated.email_enabled,
            "line_enabled": updated.line_enabled,
            "email_recipients": updated.email_recipients,
            "line_target": updated.line_target,
            "min_relevance_score": updated.min_relevance_score,
            "max_jobs_per_alert": updated.max_jobs_per_alert,
        },
        summary=_notification_summary(updated),
        source="assistant_agent_notification_preferences",
    )
    step.status = "success"
    step.summary = "已更新通知條件。"
    return ToolExecutionOutcome(
        tool_call=AgentToolCall(
            step_id=step.step_id,
            tool_name=step.tool_name,
            status="success",
            summary=step.summary,
            user_message=_notification_summary(updated),
            metadata={
                "site_enabled": updated.site_enabled,
                "email_enabled": updated.email_enabled,
                "line_enabled": updated.line_enabled,
                "min_relevance_score": updated.min_relevance_score,
                "max_jobs_per_alert": updated.max_jobs_per_alert,
            },
        ),
        step=step,
        result_tab="notifications",
        next_step="你可以前往通知設定頁確認完整內容。",
    )


def _record_tool_monitoring(
    *,
    runtime_context: AgentRuntimeContext,
    task_plan: AgentTaskPlan,
    tool_call: AgentToolCall,
) -> None:
    runtime_context.page_context.product_store.record_ai_monitoring_event(
        user_id=runtime_context.page_context.current_user_id,
        event_type=f"assistant.agent.{tool_call.tool_name}",
        status=tool_call.status,
        latency_ms=tool_call.duration_ms,
        model_name=str(tool_call.metadata.get("selected_model") or runtime_context.page_context.settings.assistant_model),
        query_signature=runtime_context.page_context.current_signature,
        metadata={
            "agent_intent": task_plan.intent.kind,
            "plan_step_count": len(task_plan.steps),
            "tool_name": tool_call.tool_name,
            "tool_status": tool_call.status,
            "confirmation_status": tool_call.metadata.get("confirmation_status", ""),
            **tool_call.metadata,
        },
    )


def _build_completion_summary(*, task_plan: AgentTaskPlan, answer_text: str) -> str:
    if answer_text:
        return "我已完成這次求職工作流任務，並整理好結果。"
    if any(step.tool_name in {"save_assistant_profile", "create_or_update_saved_search", "update_notification_preferences"} for step in task_plan.steps):
        return "我已完成這次工作流設定更新。"
    return "我已完成這次求職工作流任務。"


def _default_next_step(result_tab: str) -> str:
    if not result_tab:
        return ""
    return f"如果要看詳細畫面，可以打開 {result_tab} 工作台。"


def _update_search_session(*, rows: list[dict[str, object]], crawl_preset_label: str) -> None:
    draft_row = {
        "enabled": True,
        "priority": len(rows) + 1,
        "role": "",
        "keywords": "",
    }
    updated_rows = normalize_search_role_rows(rows) + [draft_row]
    st.session_state.search_role_rows = updated_rows
    st.session_state.search_role_draft_index = len(updated_rows) - 1
    st.session_state.search_role_widget_refresh = updated_rows
    st.session_state.crawl_preset_label = crawl_preset_label
    st.session_state.custom_queries_text = ""
    st.session_state.active_saved_search_id = None


def _resolve_search_rows(*, payload: dict[str, Any]) -> list[dict[str, object]]:
    roles = [str(role).strip() for role in payload.get("roles", []) if str(role).strip()]
    if roles:
        return normalize_search_role_rows(
            [
                {
                    "enabled": True,
                    "priority": index + 1,
                    "role": role,
                    "keywords": "",
                }
                for index, role in enumerate(roles)
            ]
        )
    committed_rows = [
        row
        for row in normalize_search_role_rows(list(st.session_state.get("search_role_rows", [])))
        if str(row.get("role", "")).strip()
    ]
    return committed_rows


def _notification_summary(preferences: NotificationPreference) -> str:
    channels: list[str] = []
    if preferences.site_enabled:
        channels.append("站內")
    if preferences.email_enabled:
        channels.append("Email")
    if preferences.line_enabled:
        channels.append("LINE")
    return (
        f"通道：{' / '.join(channels) if channels else '全部關閉'}；"
        f"最低分數：{preferences.min_relevance_score:g}；"
        f"每次最多 {preferences.max_jobs_per_alert} 筆。"
    )
