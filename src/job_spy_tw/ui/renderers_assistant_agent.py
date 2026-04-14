"""Render helpers for assistant agent task cards."""

from __future__ import annotations

import streamlit as st

from ..assistant_agent.models import (
    AgentExecutionResult,
    AgentPendingConfirmation,
    AgentStep,
    AgentTaskPlan,
)
from .session import set_main_tab

STATUS_LABELS = {
    "planned": "已規劃",
    "running": "執行中",
    "waiting_confirmation": "等待確認",
    "completed": "已完成",
    "failed": "失敗",
    "blocked": "阻擋",
    "cancelled": "已取消",
    "success": "已完成",
    "skipped": "已略過",
}

STEP_ICONS = {
    "planned": "•",
    "success": "✓",
    "waiting_confirmation": "!",
    "blocked": "△",
    "failed": "✕",
    "cancelled": "○",
    "skipped": "–",
}

TAB_LABELS = {
    "overview": "職缺總覽",
    "assistant": "AI 助理",
    "resume": "履歷匹配",
    "tasks": "工作內容",
    "tracking": "追蹤中心",
    "board": "投遞看板",
    "notifications": "通知",
    "export": "下載資料",
}


def _step_status_text(step: AgentStep) -> str:
    icon = STEP_ICONS.get(step.status, "•")
    label = STATUS_LABELS.get(step.status, step.status)
    return f"{icon} {step.title}｜{label}"


def render_agent_task_card(
    *,
    task: AgentTaskPlan | None,
    result: AgentExecutionResult | None,
    pending_confirmation: AgentPendingConfirmation | None,
) -> str:
    """Render the latest agent task card and return UI action."""
    if task is None and result is None:
        return ""

    current_title = task.title if task is not None else result.title
    current_question = task.question if task is not None else result.question
    current_status = (
        pending_confirmation is not None
        and "waiting_confirmation"
        or (result.status if result is not None else task.status)
    )
    current_steps = result.steps if result is not None and result.steps else (task.steps if task is not None else [])
    is_plan_only = task is not None and result is None and pending_confirmation is None

    with st.container(border=True, key="assistant-agent-task-card"):
        st.markdown("**求職工作流 Agent**")
        st.caption(f"{STATUS_LABELS.get(current_status, current_status)}｜{current_title}")
        if current_question:
            st.markdown(f"**任務目標**：{current_question}")
        if task is not None and task.summary:
            st.write(task.summary)
        if task is not None and bool(task.intent.extracted.get("memory_context_used")):
            recent_summaries = list(task.intent.extracted.get("recent_task_summaries", []) or [])
            if recent_summaries:
                st.caption(f"已沿用最近記憶：{recent_summaries[0]}")
            else:
                st.caption("這次計畫有沿用你最近確認過的求職記憶。")
        if is_plan_only:
            st.info("目前是規劃階段，系統尚未執行任何動作。確認計畫後，再開始執行。")

        if current_steps:
            st.markdown("**計畫步驟**")
            for step in current_steps:
                st.markdown(_step_status_text(step))
                if step.summary:
                    st.caption(step.summary)

        action = ""
        if is_plan_only and st.button(
            "開始執行計畫",
            key=f"assistant-agent-execute-{task.task_id}",
            use_container_width=True,
            type="primary",
        ):
            action = "execute"

        if result is not None:
            st.markdown("**執行結果**")
            st.write(result.summary)
            if result.answer_text:
                st.markdown(result.answer_text)
            if result.key_points:
                for point in result.key_points:
                    st.markdown(f"- {point}")
            if result.next_step:
                st.info(f"下一步：{result.next_step}")

        if pending_confirmation is not None:
            st.markdown("**待確認寫入**")
            st.warning(pending_confirmation.message)
            if pending_confirmation.before_summary:
                st.caption(f"目前設定：{pending_confirmation.before_summary}")
            if pending_confirmation.after_summary:
                st.caption(f"寫入後：{pending_confirmation.after_summary}")
            confirm_cols = st.columns(2, gap="small")
            if confirm_cols[0].button(
                "確認執行",
                key=f"assistant-agent-confirm-{pending_confirmation.step_id}",
                use_container_width=True,
                type="primary",
            ):
                action = "confirm"
            if confirm_cols[1].button(
                "取消這次寫入",
                key=f"assistant-agent-reject-{pending_confirmation.step_id}",
                use_container_width=True,
            ):
                action = "reject"

        target_tab = ""
        if result is not None and result.result_tab:
            target_tab = result.result_tab
        elif task is not None and task.result_tab:
            target_tab = task.result_tab
        if target_tab:
            label = TAB_LABELS.get(target_tab, target_tab)
            if st.button(
                f"前往 {label}",
                key=f"assistant-agent-open-tab-{target_tab}",
                use_container_width=True,
            ):
                set_main_tab(target_tab)
                st.rerun()

    return action
