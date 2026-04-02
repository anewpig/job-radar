from __future__ import annotations

import re
from typing import Any, Iterable

from ..analysis import JobAnalyzer
from ..models import ResumeProfile, TargetRole
from ..utils import normalize_text, unique_preserving_order
from .schemas import LLMResumeProfile, OpenAI
from .text import (
    DOMAIN_TAXONOMY,
    STOPWORDS,
    TOKEN_PATTERN,
    _clean_resume_lines,
    _contains_personal_info,
    _is_safe_domain_keyword,
    _looks_garbled,
    _sanitize_domain_keywords,
    _sanitize_extracted_text,
    _sanitize_match_keywords,
)


class RuleBasedResumeExtractor:
    def __init__(self, role_targets: list[TargetRole]) -> None:
        self.role_targets = role_targets
        self.job_analyzer = JobAnalyzer(role_targets)
        self.compiled_tasks = self.job_analyzer._compiled_tasks
        self.skill_categories = self._build_skill_category_map()
        self.domain_patterns = self._compile_alias_map(DOMAIN_TAXONOMY)

    def extract(self, text: str, source_name: str = "") -> ResumeProfile:
        prepared_text = _sanitize_extracted_text(text)
        normalized_text = normalize_text(prepared_text)
        detected_roles = self._extract_roles(normalized_text)
        extracted_skills = self.job_analyzer.extract_skills(normalized_text)
        core_skills, tool_skills = self._split_skills(extracted_skills)
        preferred_tasks = self._extract_tasks(normalized_text)
        domain_keywords = self._extract_domain_keywords(prepared_text)
        prompt_keywords = unique_preserving_order(
            core_skills + tool_skills + domain_keywords + preferred_tasks + detected_roles
        )[:18]
        summary = self._build_summary(
            prepared_text, detected_roles, core_skills, preferred_tasks
        )
        prompts = self._generate_prompts(
            detected_roles=detected_roles,
            core_skills=core_skills,
            tool_skills=tool_skills,
            preferred_tasks=preferred_tasks,
            domain_keywords=domain_keywords,
        )
        notes: list[str] = []
        if not detected_roles:
            notes.append("履歷中沒有明確職稱，已用技能與經驗內容推估適合職缺。")
        if not extracted_skills:
            notes.append("沒有辨識到明確技能關鍵字，建議在履歷補上工具與技術名稱。")
        return ResumeProfile(
            source_name=source_name,
            raw_text=prepared_text,
            summary=summary,
            target_roles=detected_roles,
            core_skills=core_skills,
            tool_skills=tool_skills,
            domain_keywords=domain_keywords,
            preferred_tasks=preferred_tasks,
            generated_prompts=prompts,
            match_keywords=prompt_keywords,
            extraction_method="rule_based",
            notes=unique_preserving_order(notes),
        )

    def _extract_roles(self, text: str) -> list[str]:
        lowered = text.lower()
        scored_roles: list[tuple[int, str]] = []
        for role in self.role_targets:
            score = 0
            role_lower = role.name.lower()
            if role_lower in lowered:
                score += 4
            for keyword in role.keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in lowered:
                    score += 2
            if score > 0:
                scored_roles.append((score, role.name))

        if not scored_roles:
            inferred: list[str] = []
            extracted_skills = set(self.job_analyzer.extract_skills(text))
            if {"LLM", "RAG", "Prompt Engineering", "AI Agent"} & extracted_skills:
                inferred.extend(["AI應用工程師", "AI工程師"])
            if {"Product Management", "Project Management", "Roadmap"} & extracted_skills:
                inferred.append("PM")
            if {"Technical Support", "Customer Communication", "Requirement Analysis"} & extracted_skills:
                inferred.append("應用工程師")
            if not inferred and {"Python", "JavaScript", "TypeScript", "Java"} & extracted_skills:
                inferred.append("軟體工程師")
            return unique_preserving_order(inferred or [self.role_targets[0].name])[:3]

        scored_roles.sort(key=lambda item: (-item[0], item[1]))
        return [role for _, role in scored_roles[:4]]

    def _split_skills(self, skills: list[str]) -> tuple[list[str], list[str]]:
        core_skills: list[str] = []
        tool_skills: list[str] = []
        for skill in skills:
            category = self.skill_categories.get(skill, "")
            if category in {"Programming", "Framework / Tooling", "Cloud / DevOps"}:
                tool_skills.append(skill)
            else:
                core_skills.append(skill)
        if not core_skills:
            core_skills = skills[:6]
        if not tool_skills:
            tool_skills = [skill for skill in skills if skill not in core_skills][:6]
        return core_skills[:8], tool_skills[:8]

    def _extract_tasks(self, text: str) -> list[str]:
        lowered = f" {normalize_text(text).lower()} "
        matched: list[str] = []
        for task, patterns in self.compiled_tasks.items():
            if any(pattern.search(lowered) for pattern in patterns):
                matched.append(task)
        return matched[:8]

    def _extract_domain_keywords(self, text: str) -> list[str]:
        filtered_text = "\n".join(
            line for line in _clean_resume_lines(text) if not _contains_personal_info(line)
        )
        lowered = f" {normalize_text(filtered_text).lower()} "
        matched: list[str] = []
        for keyword, patterns in self.domain_patterns.items():
            if any(pattern.search(lowered) for pattern in patterns):
                matched.append(keyword)

        if not matched:
            fallback_tokens: list[str] = []
            for token in TOKEN_PATTERN.findall(filtered_text):
                candidate = normalize_text(token)
                if not _is_safe_domain_keyword(candidate):
                    continue
                fallback_tokens.append(candidate)
            matched.extend(fallback_tokens[:6])

        return _sanitize_domain_keywords(matched)[:10]

    def _build_summary(
        self,
        text: str,
        detected_roles: list[str],
        core_skills: list[str],
        preferred_tasks: list[str],
    ) -> str:
        role_terms = {role.lower() for role in detected_roles}
        skill_terms = {skill.lower() for skill in core_skills}
        task_terms = {task.lower() for task in preferred_tasks}

        scored_lines: list[tuple[int, int, str]] = []
        for index, line in enumerate(_clean_resume_lines(text)):
            if _contains_personal_info(line) or _looks_garbled(line):
                continue

            lowered = line.lower()
            score = 0
            score += sum(3 for term in role_terms if term and term in lowered)
            score += sum(2 for term in skill_terms if term and term in lowered)
            score += sum(2 for term in task_terms if term and term in lowered)
            if score == 0 and len(line) < 12:
                continue
            scored_lines.append((score, -index, line))

        if scored_lines:
            scored_lines.sort(reverse=True)
            selected = [line for _, _, line in scored_lines[:2]]
            return "；".join(unique_preserving_order(selected))[:220]

        parts = []
        if detected_roles:
            parts.append(f"目標角色偏向 {' / '.join(detected_roles[:3])}")
        if core_skills:
            parts.append(f"核心技能包含 {'、'.join(core_skills[:4])}")
        if preferred_tasks:
            parts.append(f"偏好工作內容為 {'、'.join(preferred_tasks[:3])}")
        return "；".join(parts)

    def _generate_prompts(
        self,
        detected_roles: list[str],
        core_skills: list[str],
        tool_skills: list[str],
        preferred_tasks: list[str],
        domain_keywords: list[str],
    ) -> list[str]:
        roles_text = " / ".join(detected_roles[:3]) or "目標職缺"
        core_text = "、".join(core_skills[:4]) or "相關技能"
        tool_text = "、".join(tool_skills[:4]) or "技術工具"
        task_text = "、".join(preferred_tasks[:3]) or "相關工作內容"
        domain_text = "、".join(domain_keywords[:3]) or "相關產業"
        return unique_preserving_order(
            [
                f"{roles_text}，擅長 {core_text}",
                f"{roles_text}，熟悉 {tool_text}，偏好 {task_text}",
                f"{roles_text}，希望切入 {domain_text} 類型職缺",
            ]
        )

    def _build_skill_category_map(self) -> dict[str, str]:
        category_map: dict[str, str] = {}
        for category, skill_map in self.job_analyzer._compiled_skills.items():
            for skill in skill_map:
                category_map[skill] = category
        return category_map

    def _compile_alias_map(
        self, mapping: dict[str, tuple[str, ...]]
    ) -> dict[str, tuple[re.Pattern[str], ...]]:
        compiled: dict[str, tuple[re.Pattern[str], ...]] = {}
        for label, aliases in mapping.items():
            patterns: list[re.Pattern[str]] = []
            for alias in aliases:
                cleaned = alias.strip()
                if re.fullmatch(r"[a-zA-Z0-9+/# .-]+", cleaned):
                    escaped = re.escape(cleaned).replace(r"\ ", r"\s+")
                    pattern = re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)
                else:
                    pattern = re.compile(re.escape(cleaned), re.IGNORECASE)
                patterns.append(pattern)
            compiled[label] = tuple(patterns)
        return compiled


class OpenAIResumeExtractor:
    def __init__(
        self,
        role_targets: list[TargetRole],
        api_key: str,
        model: str,
        base_url: str = "",
        client: Any | None = None,
    ) -> None:
        if OpenAI is None or LLMResumeProfile is None:
            raise RuntimeError("OpenAI 或 Pydantic 套件不可用，無法啟用 LLM 履歷分析。")
        if client is None and not api_key:
            raise RuntimeError("沒有提供 OPENAI_API_KEY。")

        self.role_targets = role_targets
        if client is not None:
            self.client = client
        else:
            client_kwargs = {"api_key": api_key}
            if base_url:
                client_kwargs["base_url"] = base_url
            self.client = OpenAI(**client_kwargs)
        self.model = model

    def extract(
        self,
        text: str,
        source_name: str,
        fallback_profile: ResumeProfile,
    ) -> ResumeProfile:
        role_hint = "\n".join(
            f"- {role.priority}. {role.name}: {', '.join(role.keywords)}"
            for role in self.role_targets
        )
        response = self.client.responses.parse(
            model=self.model,
            temperature=0.1,
            max_output_tokens=900,
            input=(
                "請閱讀這份履歷，整理成結構化求職摘要，用於台灣職缺比對。\n"
                "請優先判斷候選人最適合的職缺方向、核心技能、工具技能、偏好工作內容與匹配關鍵字。\n"
                "generated_prompts 請輸出 3 句短 prompt，可直接拿去做職缺搜尋或比對。\n"
                "target_roles 請盡量對齊下列目標職缺名稱：\n"
                f"{role_hint}\n\n"
                "以下是規則分析的初步結果，可當作參考但不要逐字照抄：\n"
                f"summary: {fallback_profile.summary}\n"
                f"target_roles: {', '.join(fallback_profile.target_roles)}\n"
                f"core_skills: {', '.join(fallback_profile.core_skills)}\n"
                f"tool_skills: {', '.join(fallback_profile.tool_skills)}\n"
                f"preferred_tasks: {', '.join(fallback_profile.preferred_tasks)}\n"
                f"domain_keywords: {', '.join(fallback_profile.domain_keywords)}\n\n"
                "履歷原文如下：\n"
                f"{text[:12000]}"
            ),
            text_format=LLMResumeProfile,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("LLM 沒有回傳可解析的結構化結果。")

        target_roles = self._normalize_roles(parsed.target_roles, fallback_profile.target_roles)
        core_skills = unique_preserving_order(
            [item.strip() for item in parsed.core_skills if item.strip()]
            + fallback_profile.core_skills
        )[:8]
        tool_skills = unique_preserving_order(
            [item.strip() for item in parsed.tool_skills if item.strip()]
            + fallback_profile.tool_skills
        )[:8]
        domain_keywords = _sanitize_domain_keywords(
            [item.strip() for item in parsed.domain_keywords if item.strip()]
            + fallback_profile.domain_keywords
        )[:10]
        preferred_tasks = unique_preserving_order(
            [item.strip() for item in parsed.preferred_tasks if item.strip()]
            + fallback_profile.preferred_tasks
        )[:8]
        generated_prompts = unique_preserving_order(
            [item.strip() for item in parsed.generated_prompts if item.strip()]
            + fallback_profile.generated_prompts
        )[:4]
        match_keywords = _sanitize_match_keywords(
            [item.strip() for item in parsed.match_keywords if item.strip()]
            + core_skills
            + tool_skills
            + domain_keywords
            + preferred_tasks
            + target_roles
        )[:18]

        return ResumeProfile(
            source_name=source_name,
            raw_text=text,
            summary=parsed.summary.strip() or fallback_profile.summary,
            target_roles=target_roles,
            core_skills=core_skills,
            tool_skills=tool_skills,
            domain_keywords=domain_keywords,
            preferred_tasks=preferred_tasks,
            generated_prompts=generated_prompts,
            match_keywords=match_keywords,
            extraction_method="llm",
            llm_model=self.model,
            notes=unique_preserving_order(fallback_profile.notes + ["已使用 LLM 擷取履歷重點。"]),
        )

    def _normalize_roles(self, roles: Iterable[str], fallback_roles: list[str]) -> list[str]:
        normalized: list[str] = []
        for role_text in roles:
            cleaned = normalize_text(role_text)
            if not cleaned:
                continue
            lowered = cleaned.lower()
            matched_role = ""
            for role in self.role_targets:
                if role.name.lower() in lowered or lowered in role.name.lower():
                    matched_role = role.name
                    break
                if any(
                    keyword.lower() in lowered or lowered in keyword.lower()
                    for keyword in role.keywords
                ):
                    matched_role = role.name
                    break
            normalized.append(matched_role or cleaned)
        return unique_preserving_order(normalized + fallback_roles)[:4]
