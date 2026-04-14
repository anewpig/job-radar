"""提供 AI 助理頁面的 section render helper。"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

import streamlit as st

from ..assistant.question_presets import DEFAULT_ASSISTANT_QUESTIONS
from ..models import ResumeProfile
from ..resume_analysis import mask_personal_items, mask_personal_text
from .assistant_actions import (
    clear_assistant_agent_state,
    clear_assistant_history,
    clear_assistant_report,
    clear_manual_assistant_profile,
    confirm_assistant_agent_action,
    execute_assistant_agent_task,
    reject_assistant_agent_action,
    save_manual_assistant_profile,
)
from .common import build_chip_row
from .dev_annotations import render_dev_card_annotation
from .page_context import PageContext
from .renderers import (
    render_assistant_response,
    render_assistant_suggestion_buttons,
)
from .renderers_assistant_agent import render_agent_task_card
from .session import assistant_question_batches, set_main_tab

SUGGESTED_ASSISTANT_QUESTIONS = DEFAULT_ASSISTANT_QUESTIONS
EXPERIENCE_LEVEL_OPTIONS = ["", "新鮮人 / 轉職中", "1-3 年", "3-5 年", "5 年以上"]


@dataclass(slots=True)
class AssistantQuickAskState:
    question: str
    submit_question: bool
    generate_report: bool


def _render_assistant_disabled_state() -> None:
    render_dev_card_annotation(
        "AI 助理未啟用提示卡",
        element_id="assistant-disabled-card",
        description="尚未設定 API key 時的提示卡。",
        text_nodes=[
            ("info-card-title", "提示卡標題。"),
            ("summary-card-text", "提示卡說明文字。"),
        ],
        compact=True,
        show_popover=True,
        popover_key="assistant-disabled-card",
    )
    st.markdown(
        """
<div class="summary-card">
  <div class="info-card-title">AI 助理尚未啟用</div>
  <div class="summary-card-text">設定好 OpenAI API key 後，這裡就能根據目前的職缺快照回答技能缺口、工作內容、薪資區間，也能幫你產生簡短求職報告。</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.info("請先設定 `OPENAI_API_KEY`，才能使用 OpenAI + RAG 客服與簡報。")


def _render_assistant_context_chips(
    assistant_profile: ResumeProfile | None,
) -> None:
    assistant_chips: list[str] = []
    if assistant_profile is not None:
        assistant_chips.extend(mask_personal_items(assistant_profile.target_roles[:3]))
        assistant_chips.extend(mask_personal_items(assistant_profile.core_skills[:3]))
    else:
        assistant_chips.append("目前以市場資料為主")
    st.markdown(
        f"<div class='chip-row' style='margin:0.2rem 0 0.85rem;'>{build_chip_row(assistant_chips, tone='soft', limit=6)}</div>",
        unsafe_allow_html=True,
    )


def _render_assistant_profile_section(
    ctx: PageContext,
    *,
    resume_context_profile: ResumeProfile | None,
    manual_context_profile: ResumeProfile | None,
) -> None:
    manual_target_roles_text = "、".join(manual_context_profile.target_roles) if manual_context_profile else ""
    manual_locations_text = "、".join(manual_context_profile.domain_keywords) if manual_context_profile else ""
    manual_skills_text = "、".join(manual_context_profile.core_skills) if manual_context_profile else ""
    manual_experience_level = ""
    if manual_context_profile is not None:
        matched = re.search(r"年資：([^；]+)", str(manual_context_profile.summary or ""))
        if matched:
            manual_experience_level = matched.group(1).strip()
    experience_index = (
        EXPERIENCE_LEVEL_OPTIONS.index(manual_experience_level)
        if manual_experience_level in EXPERIENCE_LEVEL_OPTIONS
        else 0
    )

    with st.container(border=True, key="assistant-profile-card-shell"):
        render_dev_card_annotation(
            "AI 助理個人化背景卡",
            element_id="assistant-profile-card-shell",
            description="AI 助理左側的背景資料卡，顯示履歷或手動輸入的個人化資訊。",
            layers=[
                "resume summary",
                "assistant_profile_form",
                "assistant-clear-profile",
            ],
            text_nodes=[
                ("個人化背景", "卡片標題。"),
                ("st.caption", "背景狀態說明小字。"),
                ("assistant_profile_form", "基本資料表單。"),
            ],
            show_popover=True,
            popover_key="assistant-profile-card-shell",
        )
        st.markdown("**個人化背景**")
        if resume_context_profile is not None:
            st.caption("目前已載入履歷，AI 助理會優先依照履歷內容回答；你也可以在下方補充條件。")
            st.markdown(
                mask_personal_text(resume_context_profile.summary or "已載入履歷摘要。")
            )

        if manual_context_profile is not None:
            if resume_context_profile is not None:
                st.caption("目前也有手動補充的求職條件，AI 助理會一起參考。")
            else:
                st.caption("目前已載入求職基本資料。你也可以重新填寫或清除。")
            st.markdown(
                mask_personal_text(
                    manual_context_profile.summary or "已載入求職基本資料。"
                )
            )
            clear_profile_cols = st.columns([1.3, 1], gap="medium")
            if clear_profile_cols[1].button(
                "清除基本資料",
                key="assistant-clear-profile",
                use_container_width=True,
            ):
                clear_manual_assistant_profile()

        with st.expander(
            "補充或更新求職基本資料" if resume_context_profile is not None else "填寫或更新求職基本資料",
            expanded=resume_context_profile is None and manual_context_profile is None,
        ):
            with st.form("assistant_profile_form"):
                target_roles_text = st.text_area(
                    "目標職缺",
                    placeholder="例如：AI應用工程師、AI工程師",
                    height=100,
                    value=manual_target_roles_text,
                )
                experience_level = st.selectbox(
                    "年資",
                    EXPERIENCE_LEVEL_OPTIONS,
                    index=experience_index,
                )
                locations_text = st.text_area(
                    "希望工作地點",
                    placeholder="例如：台北市、新竹市、遠端",
                    height=80,
                    value=manual_locations_text,
                )
                skills_text = st.text_area(
                    "目前技能",
                    placeholder="例如：Python、LLM、RAG、Docker",
                    height=100,
                    value=manual_skills_text,
                )
                if resume_context_profile is not None:
                    st.caption("備註：送出後會保存你補充的條件；AI 助理會以履歷為主，再加上這些補充資訊回答。")
                else:
                    st.caption("備註：送出後會保存你填寫的基本資料與系統整理後的摘要。")
                save_profile = st.form_submit_button(
                    "儲存基本資料",
                    use_container_width=True,
                )
            if save_profile:
                save_manual_assistant_profile(
                    ctx=ctx,
                    target_roles_text=target_roles_text,
                    experience_level=experience_level,
                    locations_text=locations_text,
                    skills_text=skills_text,
                )


def _render_assistant_quick_ask_section() -> AssistantQuickAskState:
    with st.container(border=True, key="assistant-quick-ask-card-shell"):
        render_dev_card_annotation(
            "AI 助理快速提問卡",
            element_id="assistant-quick-ask-card-shell",
            description="AI 助理右側的快捷問題、輸入區與求職報告入口。",
            layers=[
                "assistant suggestion buttons",
                "assistant_form",
                "assistant-next-question-batch",
            ],
            text_nodes=[
                ("快速提問", "卡片標題。"),
                ("assistant question buttons", "快捷問題按鈕文字。"),
                ("詢問客服", "文字輸入區標籤。"),
                ("送出問題 / 產生求職報告", "底部主操作按鈕。"),
            ],
            show_popover=True,
            popover_key="assistant-quick-ask-card-shell",
        )
        question_batches = assistant_question_batches(
            SUGGESTED_ASSISTANT_QUESTIONS,
            batch_size=4,
        )
        batch_count = max(1, len(question_batches))
        current_batch_index = int(st.session_state.assistant_suggestion_page) % batch_count
        suggestion_header_cols = st.columns([1.6, 1], gap="medium")
        suggestion_header_cols[0].markdown("**快速提問**")
        if suggestion_header_cols[1].button(
            "換一批問題",
            key="assistant-next-question-batch",
            use_container_width=True,
        ):
            current_batch_index = (current_batch_index + 1) % batch_count
            st.session_state.assistant_suggestion_page = current_batch_index
            set_main_tab("assistant")
        selected_question = render_assistant_suggestion_buttons(
            question_batches[current_batch_index]
        )
        if selected_question:
            st.session_state.assistant_question_draft = selected_question
            st.session_state.assistant_question_input = selected_question

        with st.form("assistant_form"):
            assistant_question = st.text_area(
                "詢問客服",
                key="assistant_question_input",
                height=120,
                placeholder="例如：可以優先學習的技能有哪些？",
            )
            col_left, col_right = st.columns(2)
            ask_assistant = col_left.form_submit_button(
                "送出問題",
                use_container_width=True,
            )
            generate_report = col_right.form_submit_button(
                "產生求職報告",
                use_container_width=True,
            )

    pending_launcher_submit = bool(
        st.session_state.pop("assistant_launcher_submit_pending", False)
    )
    question = (
        assistant_question.strip()
        if ask_assistant
        else str(st.session_state.get("assistant_question_input", "")).strip()
    )
    return AssistantQuickAskState(
        question=question,
        submit_question=bool(ask_assistant or pending_launcher_submit),
        generate_report=bool(generate_report),
    )


def _render_assistant_cleanup_actions() -> None:
    has_agent_state = any(
        (
            st.session_state.get("assistant_agent_task") is not None,
            st.session_state.get("assistant_agent_pending_confirmation") is not None,
            st.session_state.get("assistant_agent_last_result") is not None,
        )
    )
    action_cols = st.columns([1.2, 1.05, 1.05, 1.25], gap="medium")
    clear_history = action_cols[1].button(
        "清除問答紀錄",
        key="assistant-clear-history",
        use_container_width=True,
        disabled=not st.session_state.assistant_history,
    )
    clear_report = action_cols[2].button(
        "清除求職報告",
        key="assistant-clear-report",
        use_container_width=True,
        disabled=st.session_state.assistant_report is None,
    )
    clear_agent = action_cols[3].button(
        "清除 Agent 任務",
        key="assistant-clear-agent-task",
        use_container_width=True,
        disabled=not has_agent_state,
    )
    if clear_history:
        clear_assistant_history()
    if clear_report:
        clear_assistant_report()
    if clear_agent:
        clear_assistant_agent_state()


def _render_assistant_outputs(
    ctx: PageContext,
    *,
    assistant,
    assistant_profile: ResumeProfile | None,
) -> None:
    agent_action = render_agent_task_card(
        task=st.session_state.get("assistant_agent_task"),
        result=st.session_state.get("assistant_agent_last_result"),
        pending_confirmation=st.session_state.get("assistant_agent_pending_confirmation"),
    )
    if agent_action == "confirm":
        confirm_assistant_agent_action(
            ctx=ctx,
            assistant=assistant,
            assistant_profile=assistant_profile,
        )
    elif agent_action == "execute":
        execute_assistant_agent_task(
            ctx=ctx,
            assistant=assistant,
            assistant_profile=assistant_profile,
        )
    elif agent_action == "reject":
        reject_assistant_agent_action(
            ctx=ctx,
            assistant=assistant,
            assistant_profile=assistant_profile,
        )

    if st.session_state.assistant_report is not None:
        render_assistant_response("求職報告", st.session_state.assistant_report)
        _render_assistant_feedback(
            ctx=ctx,
            answer=st.session_state.assistant_report,
            context_key="report",
        )

    if st.session_state.assistant_history:
        st.markdown("**問答紀錄**")
        for index, answer in enumerate(st.session_state.assistant_history, start=1):
            with st.container(border=True):
                render_dev_card_annotation(
                    "AI 問答紀錄卡",
                    element_id=f"assistant-history-card-{index}",
                    description="AI 助理問答紀錄中的單筆問題卡。",
                    layers=["question heading", "answer card"],
                    text_nodes=[
                        (f"Q{index}", "問題序號與問題標題。"),
                    ],
                    compact=True,
                    show_popover=True,
                    popover_key=f"assistant-history-card-{index}",
                )
                st.markdown(f"**Q{index}. {answer.question}**")
                render_assistant_response("回答", answer)
                _render_assistant_feedback(
                    ctx=ctx,
                    answer=answer,
                    context_key=f"history-{index}",
                )


def _render_assistant_feedback(*, ctx: PageContext, answer, context_key: str) -> None:
    question = str(getattr(answer, "question", "") or "")
    answer_text = str(getattr(answer, "answer", "") or "")
    answer_mode = str(getattr(answer, "answer_mode", "") or "")
    base_signature = f"{question}|{answer_text}|{answer_mode}|{getattr(answer, 'model', '')}"
    target_id = hashlib.sha1(base_signature.encode("utf-8")).hexdigest()
    feedback_key = f"assistant-feedback-{context_key}-{target_id}"

    rating_label_key = f"{feedback_key}-rating"
    tags_key = f"{feedback_key}-tags"
    comment_key = f"{feedback_key}-comment"

    rating_choices = ["未評分", "有幫助", "沒幫助"]
    rating_map = {"未評分": 0, "有幫助": 1, "沒幫助": -1}
    stored_rating_label = st.session_state.get(rating_label_key, "未評分")

    with st.form(key=f"{feedback_key}-form"):
        st.markdown("這個回答有幫助嗎？")
        rating_label = st.radio(
            " ",
            rating_choices,
            index=rating_choices.index(stored_rating_label)
            if stored_rating_label in rating_choices
            else 0,
            horizontal=True,
        )
        rating_value = rating_map.get(rating_label, 0)
        tags: list[str] = []
        if rating_value == 1:
            tags = st.multiselect(
                "哪些地方有幫助？",
                ["清楚", "可執行", "新資訊", "符合需求", "引用完整"],
                default=st.session_state.get(tags_key, []),
            )
        elif rating_value == -1:
            tags = st.multiselect(
                "哪裡需要改進？",
                ["不精準", "太籠統", "不相關", "太長", "缺少引用", "不夠可執行"],
                default=st.session_state.get(tags_key, []),
            )
        comment = st.text_area(
            "想補充的意見（選填）",
            value=st.session_state.get(comment_key, ""),
            height=90,
        )
        submitted = st.form_submit_button("送出回饋", use_container_width=True)

    if not submitted:
        return

    st.session_state[rating_label_key] = rating_label
    st.session_state[tags_key] = tags
    st.session_state[comment_key] = comment

    if rating_value == 0:
        st.info("請先選擇有幫助或沒幫助。")
        return

    ctx.product_store.record_feedback_event(
        user_id=ctx.current_user_id,
        target_type="assistant_answer",
        target_id=target_id,
        rating=rating_value,
        tags=tags,
        comment=comment,
        metadata={
            "answer_mode": answer_mode,
            "model": str(getattr(answer, "model", "") or ""),
            "used_chunks": int(getattr(answer, "used_chunks", 0) or 0),
            "citations_count": len(getattr(answer, "citations", []) or []),
            "query_signature": ctx.current_signature,
            "snapshot_generated_at": getattr(ctx.snapshot, "generated_at", ""),
        },
    )
    st.success("已收到回饋，謝謝！")
