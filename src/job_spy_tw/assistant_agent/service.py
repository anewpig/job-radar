"""Planning and routing helpers for the job-search workflow agent."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from uuid import uuid4

from .models import AgentIntent, AgentStep, AgentTaskPlan

ACTION_HINTS = (
    "幫我",
    "替我",
    "請幫我",
    "請替我",
    "我要你",
    "幫忙",
    "幫",
)
CAREER_HINTS = (
    "求職",
    "職缺",
    "工作",
    "履歷",
    "面試",
    "投遞",
    "轉職",
    "職涯",
    "薪資",
    "市場",
    "通知",
    "saved search",
    "搜尋條件",
    "職位",
    "職稱",
)
SEARCH_HINTS = ("找", "搜尋", "查", "刷新", "更新快照", "重新抓", "重新搜尋")
SUMMARY_HINTS = ("摘要", "總結", "整理", "市場重點", "市場摘要", "重點")
REPORT_HINTS = ("報告", "求職報告", "產生報告", "生成報告")
SAVED_SEARCH_HINTS = ("saved search", "儲存搜尋", "保存搜尋", "建立搜尋", "存成搜尋", "存起來")
NOTIFICATION_HINTS = ("通知", "提醒", "email", "line", "信箱", "站內")
PROFILE_HINTS = ("基本資料", "個人背景", "求職背景", "目標職缺", "希望地點", "目前技能", "年資")
OPEN_TAB_HINTS = ("切到", "切去", "打開", "開啟", "帶我去")
GENERAL_CHAT_HINTS = ("笑話", "情書", "祝福", "晚安", "早安", "翻譯", "閒聊")

ROLE_PATTERN = re.compile(
    r"([\u4e00-\u9fffA-Za-z0-9+/．. -]{1,24}"
    r"(?:工程師|經理|分析師|設計師|顧問|專員|架構師|科學家|研究員|PM|pm|產品經理|專案經理|developer|manager))",
    re.IGNORECASE,
)
NUMBER_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")

TAB_HINTS = {
    "overview": ("職缺總覽", "總覽", "overview"),
    "assistant": ("ai 助理", "助手", "客服", "assistant"),
    "resume": ("履歷匹配", "履歷", "resume"),
    "tasks": ("工作內容", "技能", "tasks"),
    "tracking": ("追蹤中心", "追蹤", "saved search"),
    "board": ("投遞看板", "看板", "board"),
    "notifications": ("通知", "提醒", "notifications"),
    "export": ("下載資料", "匯出", "export"),
}
STEP_SPECS = {
    "inspect_snapshot": ("檢查目前市場快照", "先確認目前快照與查詢條件是否足夠。"),
    "start_or_refresh_search": ("啟動或刷新職缺查詢", "依任務條件建立查詢並更新目前市場結果。"),
    "generate_job_report": ("產生求職報告", "整理市場快照與個人背景後產生報告。"),
    "switch_main_tab": ("切到指定工作台", "打開使用者指定的工作台頁面。"),
    "open_relevant_surface": ("打開對應工作台", "把畫面切到最適合查看結果的工作台。"),
    "summarize_market_snapshot": ("整理市場摘要", "把目前市場快照整理成可讀摘要。"),
    "save_assistant_profile": ("更新 AI 助理個人背景", "整理並寫入 AI 助理的手動背景資料。"),
    "create_or_update_saved_search": ("建立或更新 Saved Search", "把目前搜尋條件保存成可追蹤的搜尋。"),
    "update_notification_preferences": ("更新通知條件", "依你的需求更新提醒通道與門檻。"),
}
WRITE_TOOLS = {
    "save_assistant_profile",
    "create_or_update_saved_search",
    "update_notification_preferences",
}


@dataclass(slots=True)
class AgentPlanningContext:
    current_search_rows: list[dict[str, object]]
    custom_queries_text: str
    crawl_preset_label: str
    active_saved_search_name: str = ""
    has_snapshot: bool = False
    has_profile: bool = False
    remembered_target_roles: list[str] = field(default_factory=list)
    remembered_search_roles: list[str] = field(default_factory=list)
    remembered_locations: list[str] = field(default_factory=list)
    remembered_skills: list[str] = field(default_factory=list)
    remembered_experience_level: str = ""
    recent_task_summaries: list[str] = field(default_factory=list)


def _normalize_question(question: str) -> str:
    return str(question or "").strip()


def _contains_any(text: str, hints: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(hint.lower() in lowered for hint in hints)


def _clean_memory_phrase(text: str) -> str:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^(加上|加入|改成|改為|換成|設成|變成|更新成)\s*", "", cleaned)
    return cleaned.strip("，,。；; ")


def _extract_roles(
    question: str,
    current_search_rows: list[dict[str, object]],
    remembered_roles: list[str],
) -> list[str]:
    matches = [match.group(1).strip("，,。；; ") for match in ROLE_PATTERN.finditer(question)]
    if matches:
        return _unique_preserve(matches)
    current_roles = [
        str(row.get("role", "")).strip()
        for row in current_search_rows
        if bool(row.get("enabled", True)) and str(row.get("role", "")).strip()
    ]
    if current_roles:
        return _unique_preserve(current_roles[:2])
    return _unique_preserve([_clean_memory_phrase(role) for role in remembered_roles if _clean_memory_phrase(role)][:2])


def _extract_tab(question: str) -> str:
    lowered = question.lower()
    for tab_id, labels in TAB_HINTS.items():
        if any(label.lower() in lowered for label in labels):
            return tab_id
    return ""


def _extract_profile_fields(
    question: str,
    current_search_rows: list[dict[str, object]],
    *,
    remembered_roles: list[str],
    remembered_locations: list[str],
    remembered_skills: list[str],
    remembered_experience_level: str,
) -> dict[str, object]:
    roles = _extract_roles(question, current_search_rows, remembered_roles)
    experience = ""
    if "新鮮人" in question or "轉職" in question:
        experience = "新鮮人 / 轉職中"
    elif "1-3" in question or "1 到 3" in question:
        experience = "1-3 年"
    elif "3-5" in question or "3 到 5" in question:
        experience = "3-5 年"
    elif "5 年以上" in question or "五年以上" in question:
        experience = "5 年以上"
    locations = _extract_list_after_hint(question, ("地點", "地區", "希望工作地點", "希望在")) or list(remembered_locations)
    skills = _extract_list_after_hint(question, ("技能", "會", "熟悉", "目前技能")) or list(remembered_skills)
    return {
        "target_roles": roles,
        "experience_level": experience or remembered_experience_level,
        "locations": locations,
        "skills": skills,
    }


def _extract_list_after_hint(question: str, hints: tuple[str, ...]) -> list[str]:
    normalized = question.replace("，", ",").replace("、", ",").replace("；", ",")
    for hint in hints:
        match = re.search(rf"{re.escape(hint)}[:：]?\s*([^。；;\n]+)", normalized, re.IGNORECASE)
        if match:
            return _split_items(match.group(1))
    return []


def _extract_notification_changes(question: str) -> dict[str, object]:
    lowered = question.lower()
    changes: dict[str, object] = {}
    if "email" in lowered or "信箱" in question:
        changes["email_enabled"] = not any(token in question for token in ("關掉", "停用", "不要", "取消"))
    if "line" in lowered:
        changes["line_enabled"] = not any(token in question for token in ("關掉", "停用", "不要", "取消"))
    if "站內" in question or "網站" in question:
        changes["site_enabled"] = not any(token in question for token in ("關掉", "停用", "不要", "取消"))

    if any(hint in question for hint in ("分數", "最低相關", "最低分", "門檻")):
        number_match = NUMBER_PATTERN.search(question)
        if number_match:
            changes["min_relevance_score"] = float(number_match.group(1))
    if any(hint in question for hint in ("最多", "上限", "每次", "每則")):
        number_match = NUMBER_PATTERN.search(question)
        if number_match:
            changes["max_jobs_per_alert"] = int(float(number_match.group(1)))
    return changes


def _extract_saved_search_name(question: str, roles: list[str], active_name: str) -> str:
    if "命名" in question or "名稱" in question or "叫做" in question:
        match = re.search(r"(?:命名|名稱|叫做)[:：]?\s*([^。；;\n]+)", question)
        if match:
            return match.group(1).strip()
    if active_name:
        return active_name
    if roles:
        return " / ".join(roles[:2])
    return "我的搜尋"


def _split_items(text: str) -> list[str]:
    raw_items = re.split(r"[,/\n]+", text)
    return _unique_preserve(
        [
            _clean_memory_phrase(item)
            for item in raw_items
            if _clean_memory_phrase(item)
        ]
    )


def _unique_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def _is_domain_request(question: str) -> bool:
    return _contains_any(question, CAREER_HINTS) or bool(ROLE_PATTERN.search(question))


class JobSearchWorkflowAgent:
    """Deterministic planner for job-search workflow actions."""

    def route_request(
        self,
        *,
        question: str,
        planning_context: AgentPlanningContext,
    ) -> AgentIntent:
        normalized = _normalize_question(question)
        if not normalized:
            return AgentIntent(reason="empty question")
        if _contains_any(normalized, GENERAL_CHAT_HINTS) and not _is_domain_request(normalized):
            return AgentIntent(reason="general chat")

        remembered_roles = _unique_preserve(
            list(planning_context.remembered_search_roles)
            + list(planning_context.remembered_target_roles)
        )
        has_memory_context = bool(
            remembered_roles
            or planning_context.remembered_locations
            or planning_context.remembered_skills
            or planning_context.recent_task_summaries
        )
        followup_hints = (
            "剛剛",
            "剛才",
            "上次",
            "沿用",
            "這組",
            "再看一次",
            "再找一次",
            "同一組",
        )

        workflow_signal = (
            _contains_any(normalized, ACTION_HINTS)
            or _contains_any(normalized, SEARCH_HINTS)
            or _contains_any(normalized, REPORT_HINTS)
            or _contains_any(normalized, SAVED_SEARCH_HINTS)
            or _contains_any(normalized, NOTIFICATION_HINTS)
            or _contains_any(normalized, PROFILE_HINTS)
            or _contains_any(normalized, OPEN_TAB_HINTS)
        )
        domain_request = _is_domain_request(normalized) or (
            has_memory_context and _contains_any(normalized, followup_hints)
        )
        if not workflow_signal or not domain_request:
            return AgentIntent(reason="assistant fallback")

        roles = _extract_roles(
            normalized,
            planning_context.current_search_rows,
            remembered_roles,
        )
        requested_tab = _contains_any(normalized, OPEN_TAB_HINTS)
        tab_id = _extract_tab(normalized) if requested_tab else ""
        profile_fields = _extract_profile_fields(
            normalized,
            planning_context.current_search_rows,
            remembered_roles=remembered_roles,
            remembered_locations=planning_context.remembered_locations,
            remembered_skills=planning_context.remembered_skills,
            remembered_experience_level=planning_context.remembered_experience_level,
        )
        notification_changes = _extract_notification_changes(normalized)

        actions: list[str] = []
        if _contains_any(normalized, SEARCH_HINTS) and roles:
            actions.extend(["inspect_snapshot", "start_or_refresh_search"])
        if _contains_any(normalized, SUMMARY_HINTS):
            if "inspect_snapshot" not in actions:
                actions.append("inspect_snapshot")
            actions.append("summarize_market_snapshot")
        if _contains_any(normalized, REPORT_HINTS):
            actions.append("generate_job_report")
        if _contains_any(normalized, SAVED_SEARCH_HINTS):
            if "start_or_refresh_search" not in actions and roles:
                actions.extend(["inspect_snapshot", "start_or_refresh_search"])
            actions.append("create_or_update_saved_search")
        if _contains_any(normalized, NOTIFICATION_HINTS):
            actions.append("update_notification_preferences")
        if _contains_any(normalized, PROFILE_HINTS) and (
            profile_fields["target_roles"]
            or profile_fields["locations"]
            or profile_fields["skills"]
            or profile_fields["experience_level"]
        ):
            actions.append("save_assistant_profile")
            if profile_fields["target_roles"]:
                if "inspect_snapshot" not in actions:
                    actions.append("inspect_snapshot")
                if "start_or_refresh_search" not in actions:
                    actions.append("start_or_refresh_search")
        if tab_id:
            actions.append("switch_main_tab")

        actions = _unique_preserve(actions)
        if not actions:
            return AgentIntent(reason="no supported workflow action")

        if "switch_main_tab" not in actions:
            if "update_notification_preferences" in actions:
                actions.append("open_relevant_surface")
            elif "create_or_update_saved_search" in actions:
                actions.append("open_relevant_surface")
            elif "start_or_refresh_search" in actions:
                actions.append("open_relevant_surface")
            elif "generate_job_report" in actions:
                actions.append("open_relevant_surface")

        kind = self._resolve_intent_kind(actions)
        return AgentIntent(
            route="agent",
            kind=kind,
            user_goal=normalized,
            actions=actions,
            requires_write=any(action in WRITE_TOOLS for action in actions),
            extracted={
                "roles": roles,
                "target_tab": tab_id,
                "profile_fields": profile_fields,
                "notification_changes": notification_changes,
                "saved_search_name": _extract_saved_search_name(
                    normalized,
                    roles,
                    planning_context.active_saved_search_name,
                ),
                "memory_context_used": has_memory_context and not bool(planning_context.current_search_rows),
                "recent_task_summaries": list(planning_context.recent_task_summaries[:3]),
            },
            reason="matched workflow action",
        )

    def build_task_plan(
        self,
        *,
        question: str,
        intent: AgentIntent,
    ) -> AgentTaskPlan:
        steps: list[AgentStep] = []
        for index, action in enumerate(intent.actions, start=1):
            title, description = STEP_SPECS.get(action, (action, action))
            payload = self._build_step_payload(intent=intent, action=action)
            steps.append(
                AgentStep(
                    step_id=f"step-{index}",
                    title=title,
                    tool_name=action,
                    description=description,
                    payload=payload,
                )
            )

        summary = self._build_task_summary(steps)
        return AgentTaskPlan(
            task_id=f"agent-task-{uuid4().hex}",
            question=question,
            trace_id=f"agent-{uuid4().hex[:10]}",
            intent=intent,
            title=self._resolve_task_title(intent),
            summary=summary,
            steps=steps,
            result_tab=self._default_result_tab(intent),
        )

    def _resolve_intent_kind(self, actions: list[str]) -> str:
        if "update_notification_preferences" in actions:
            return "notification_workflow"
        if "save_assistant_profile" in actions and "start_or_refresh_search" in actions:
            return "profile_update_and_search"
        if "save_assistant_profile" in actions:
            return "profile_update"
        if "create_or_update_saved_search" in actions and "start_or_refresh_search" in actions:
            return "search_and_save"
        if "create_or_update_saved_search" in actions:
            return "saved_search_management"
        if "generate_job_report" in actions:
            return "job_report"
        if "start_or_refresh_search" in actions:
            return "job_search"
        if "switch_main_tab" in actions:
            return "surface_navigation"
        if "summarize_market_snapshot" in actions:
            return "market_summary"
        return "workflow_agent"

    def _resolve_task_title(self, intent: AgentIntent) -> str:
        title_map = {
            "job_search": "職缺搜尋任務",
            "job_report": "求職報告任務",
            "search_and_save": "搜尋並保存任務",
            "saved_search_management": "Saved Search 任務",
            "notification_workflow": "通知設定任務",
            "profile_update_and_search": "背景更新與搜尋刷新任務",
            "profile_update": "個人背景更新任務",
            "surface_navigation": "工作台導覽任務",
            "market_summary": "市場摘要任務",
        }
        return title_map.get(intent.kind, "求職工作流任務")

    def _build_task_summary(self, steps: list[AgentStep]) -> str:
        if not steps:
            return "目前沒有可執行的步驟。"
        titles = [step.title for step in steps]
        if len(titles) == 1:
            return f"我會先替你{titles[0]}。"
        if len(titles) == 2:
            return f"我會先替你{titles[0]}，再{titles[1]}。"
        return f"我會先替你{titles[0]}，接著{titles[1]}，最後{titles[-1]}。"

    def _default_result_tab(self, intent: AgentIntent) -> str:
        if intent.extracted.get("target_tab"):
            return str(intent.extracted["target_tab"])
        if intent.kind == "notification_workflow":
            return "notifications"
        if intent.kind == "profile_update_and_search":
            return "overview"
        if intent.kind in {"saved_search_management", "search_and_save"}:
            return "tracking"
        if intent.kind in {"job_search", "market_summary"}:
            return "overview"
        return "assistant"

    def _build_step_payload(self, *, intent: AgentIntent, action: str) -> dict[str, object]:
        extracted = intent.extracted
        if action == "start_or_refresh_search":
            return {
                "roles": list(extracted.get("roles", [])),
                "crawl_preset_label": "快速",
            }
        if action == "switch_main_tab":
            return {"tab_id": str(extracted.get("target_tab", ""))}
        if action == "open_relevant_surface":
            return {"tab_id": self._default_result_tab(intent)}
        if action == "save_assistant_profile":
            return dict(extracted.get("profile_fields", {}))
        if action == "create_or_update_saved_search":
            return {
                "roles": list(extracted.get("roles", [])),
                "name": str(extracted.get("saved_search_name", "") or "我的搜尋"),
            }
        if action == "update_notification_preferences":
            return dict(extracted.get("notification_changes", {}))
        return {}
