"""提供搜尋表單與 AI 助理上下文準備相關的輔助邏輯。"""

from __future__ import annotations

import streamlit as st

from ..models import AssistantResponse, ResumeProfile, TargetRole
from ..search_keyword_recommender import normalize_search_role_rows

SEARCH_ROW_FIELDS = ("enabled", "priority", "role", "keywords")
PERSONALIZED_QUESTION_HINTS = (
    "我",
    "我的",
    "適合",
    "補足",
    "優先學習",
    "該學",
    "缺什麼",
    "缺哪些",
    "履歷",
    "求職建議",
    "我還需",
    "我還要",
)


def build_role_targets(edited_rows: list[dict]) -> list[TargetRole]:
    """把可編輯搜尋列轉成排序後的目標職缺模型。"""
    roles: list[TargetRole] = []
    for row in edited_rows:
        enabled = bool(row.get("enabled", True))
        role_name = str(row.get("role", "")).strip()
        if not enabled or not role_name or role_name.lower() in {"none", "non", "null"}:
            continue
        keywords = [
            keyword.strip()
            for keyword in str(row["keywords"]).split(",")
            if keyword.strip()
        ]
        roles.append(
            TargetRole(
                name=role_name,
                priority=int(row["priority"]),
                keywords=keywords,
            )
        )
    roles.sort(key=lambda role: role.priority)
    return roles


def _suggest_saved_search_name(rows: list[dict], custom_queries_text: str) -> str:
    """依目前搜尋輸入推導可讀性較高的搜尋名稱。"""
    role_names = [
        str(row.get("role", "")).strip()
        for row in rows
        if bool(row.get("enabled", True)) and str(row.get("role", "")).strip()
    ]
    if role_names:
        return " / ".join(role_names[:2])
    extra_lines = [line.strip() for line in custom_queries_text.splitlines() if line.strip()]
    if extra_lines:
        return extra_lines[0][:20]
    return "我的搜尋"


def _default_search_row() -> dict[str, object]:
    """回傳新搜尋列預設使用的 UI 狀態。"""
    return {
        "enabled": True,
        "priority": 1,
        "role": "",
        "keywords": "",
    }


def _next_search_priority(rows: list[dict]) -> int:
    """回傳新增搜尋列時要使用的下一個舊版 priority 值。"""
    priorities: list[int] = []
    for row in rows:
        try:
            priorities.append(int(row.get("priority", 0) or 0))
        except (TypeError, ValueError):
            continue
    return max(priorities, default=0) + 1


def _search_row_has_content(row: dict) -> bool:
    """判斷某列是否含有可視為搜尋草稿的內容。"""
    return bool(str(row.get("role", "")).strip() or str(row.get("keywords", "")).strip())


def split_search_rows_for_ui(
    rows: list[dict],
    *,
    draft_index: int | None = None,
) -> tuple[list[dict], dict[str, object]]:
    """把搜尋列拆成「已加入 rows」與「目前編輯中的 draft row」。

    draft_index 有效時，該列會被視為目前正在編輯的草稿，即使它已經有內容。
    """
    normalized_rows = normalize_search_role_rows(rows)
    resolved_draft_index = (
        draft_index
        if isinstance(draft_index, int) and 0 <= draft_index < len(normalized_rows)
        else None
    )
    if resolved_draft_index is None and normalized_rows and not _search_row_has_content(normalized_rows[-1]):
        resolved_draft_index = len(normalized_rows) - 1

    committed_rows: list[dict] = []
    for index, row in enumerate(normalized_rows):
        if index == resolved_draft_index:
            continue
        if str(row.get("role", "")).strip():
            committed_rows.append(row)

    if resolved_draft_index is not None:
        draft_row = dict(normalized_rows[resolved_draft_index])
    else:
        draft_row = _default_search_row()
        draft_row["priority"] = _next_search_priority(committed_rows)

    return committed_rows, draft_row


def get_committed_search_rows(
    rows: list[dict],
    *,
    draft_index: int | None = None,
) -> list[dict]:
    """取得真正已加入搜尋條件的 rows，不包含目前尚未提交的 draft。"""
    committed_rows, _draft_row = split_search_rows_for_ui(rows, draft_index=draft_index)
    return committed_rows


def _search_widget_key(index: int, field: str) -> str:
    """建立搜尋列 widget 對應的穩定 session key。"""
    return f"search_row_{index}_{field}"


def _prime_search_row_widget_state(rows: list[dict], *, force: bool = False) -> None:
    """依持久化搜尋列資料初始化 Streamlit widget 狀態。"""
    for index, row in enumerate(rows):
        for field in SEARCH_ROW_FIELDS:
            key = _search_widget_key(index, field)
            if force or key not in st.session_state:
                fallback = _default_search_row()[field]
                st.session_state[key] = row.get(field, fallback)


def _read_search_row_widgets(row_count: int) -> list[dict]:
    """把目前搜尋列 widget 狀態讀回並整理成標準列資料。"""
    rows: list[dict] = []
    for index in range(row_count):
        rows.append(
            {
                "enabled": True,
                "priority": int(
                    st.session_state.get(_search_widget_key(index, "priority"), index + 1)
                    or (index + 1)
                ),
                "role": str(st.session_state.get(_search_widget_key(index, "role"), "")).strip(),
                "keywords": str(st.session_state.get(_search_widget_key(index, "keywords"), "")).strip(),
            }
        )
    return rows


def split_user_text(text: str) -> list[str]:
    """把逗號或換行分隔的使用者輸入切成乾淨字詞。"""
    return [
        item.strip()
        for raw in text.replace("，", "\n").splitlines()
        if (item := raw.strip())
    ]


def build_manual_assistant_profile(
    target_roles_text: str,
    experience_level: str,
    locations_text: str,
    skills_text: str,
) -> ResumeProfile:
    """依手動輸入資料建立簡化版 AI 助理個人背景。"""
    target_roles = split_user_text(target_roles_text)
    locations = split_user_text(locations_text)
    skills = split_user_text(skills_text)
    summary_parts = []
    if target_roles:
        summary_parts.append(f"目標職缺：{'、'.join(target_roles[:4])}")
    if experience_level:
        summary_parts.append(f"年資：{experience_level}")
    if locations:
        summary_parts.append(f"希望地點：{'、'.join(locations[:4])}")
    if skills:
        summary_parts.append(f"目前技能：{'、'.join(skills[:6])}")
    return ResumeProfile(
        source_name="assistant_intake",
        summary="；".join(summary_parts),
        target_roles=target_roles,
        core_skills=skills[:8],
        domain_keywords=locations[:6],
        preferred_tasks=[],
        match_keywords=(target_roles + skills + locations)[:18],
        extraction_method="manual_profile",
        notes=["AI 助理目前使用你填寫的求職基本資料進行個人化回答。"],
    )


def needs_personal_context(question: str) -> bool:
    """判斷某個問題是否需要使用者個人背景才能回答。"""
    lowered = question.lower()
    return any(hint.lower() in lowered for hint in PERSONALIZED_QUESTION_HINTS)


def build_context_request_response(question: str) -> AssistantResponse:
    """在缺少個人背景時，回傳提示補充資訊的預設回答。"""
    return AssistantResponse(
        question=question,
        answer=(
            "這題屬於個人化求職建議，我目前沒有你的履歷或求職基本資料，"
            "不會先假設你要應徵哪一種職缺。請先到「履歷匹配」上傳履歷，"
            "或在上方填寫求職基本資料後再問我。"
        ),
        retrieval_notes=[
            "建議先提供：目標職缺、年資、地點偏好、目前技能。",
        ],
    )


def format_openai_error(exc: Exception) -> str:
    """把常見 OpenAI 例外轉成較容易理解的使用者提示。"""
    message = str(exc)
    lowered = message.lower()
    if "invalid_api_key" in lowered or "incorrect api key provided" in lowered:
        return (
            "OpenAI API key 無效或已失效。請到 OpenAI Platform 重新建立一把新的 API key，"
            "更新 `OPENAI_API_KEY` 後再重啟 Streamlit。"
        )
    if "401" in lowered and "authentication" in lowered:
        return "OpenAI 驗證失敗，請確認 `OPENAI_API_KEY` 是否正確、是否已被撤銷。"
    if "rate limit" in lowered or "429" in lowered:
        return "OpenAI 請求次數已達上限，請稍後再試，或檢查帳戶配額。"
    return f"OpenAI 請求失敗：{message}"
