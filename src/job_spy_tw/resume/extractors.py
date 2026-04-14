"""Resume-analysis helpers for extractors."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Iterable

from ..analysis import JobAnalyzer
from ..models import ResumeProfile, TargetRole
from ..openai_usage import extract_openai_usage, merge_openai_usage
from ..prompt_versions import RESUME_EXTRACTION_PROMPT_VERSION
from ..utils import ensure_directory, normalize_text, unique_preserving_order
from .scoring import _stable_hash
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

RESUME_PROFILE_MEMORY_CACHE_MAX = 128


class RuleBasedResumeExtractor:
    SPECIALIZED_ROLE_ALIASES: dict[str, tuple[str, ...]] = {
        "RAG AI Engineer": (
            "rag ai engineer",
            "rag engineer",
            "retrieval augmented generation",
            "向量資料庫",
            "知識庫系統",
            "檢索優化",
        ),
        "LLM Engineer": (
            "llm engineer",
            "prompt engineer",
            "prompt engineering",
            "ai agent",
            "agent workflow",
        ),
        "Embedded Linux Firmware Engineer": (
            "embedded linux firmware engineer",
            "embedded linux firmware",
            "bootloader",
            "driver development",
        ),
        "韌體工程師": (
            "韌體工程師",
            "firmware engineer",
            "bluetooth firmware",
            "embedded linux firmware",
            "rtos",
            "bring-up",
            "soc 韌體",
        ),
        "Product Manager": (
            "product manager",
            "產品經理",
            "prd",
            "roadmap",
        ),
    }
    SPECIALIZED_ROLE_PARENTS: dict[str, tuple[str, ...]] = {
        "RAG AI Engineer": ("AI應用工程師", "AI工程師"),
        "LLM Engineer": ("AI應用工程師", "AI工程師"),
        "Embedded Linux Firmware Engineer": ("韌體工程師", "軟體工程師"),
        "韌體工程師": ("軟體工程師",),
        "Product Manager": ("PM",),
    }

    def __init__(self, role_targets: list[TargetRole]) -> None:
        self.role_targets = role_targets
        self.job_analyzer = JobAnalyzer(role_targets)
        self.compiled_tasks = self.job_analyzer._compiled_tasks
        self.skill_categories = self._build_skill_category_map()
        self.domain_patterns = self._compile_alias_map(DOMAIN_TAXONOMY)
        self.specialized_role_patterns = self._compile_alias_map(self.SPECIALIZED_ROLE_ALIASES)

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
        specialized_roles = self._extract_specialized_roles(text)
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
            inferred.extend(specialized_roles)
            if {"LLM", "RAG", "Prompt Engineering", "AI Agent"} & extracted_skills:
                inferred.extend(["AI應用工程師", "AI工程師"])
            if {"Product Management", "Project Management", "Roadmap"} & extracted_skills:
                inferred.append("PM")
            if {"Technical Support", "Customer Communication", "Requirement Analysis"} & extracted_skills:
                inferred.append("應用工程師")
            if {"RTOS", "Bluetooth", "Embedded Linux", "C++"} & extracted_skills:
                inferred.extend(["韌體工程師", "軟體工程師"])
            if not inferred and {"Python", "JavaScript", "TypeScript", "Java"} & extracted_skills:
                inferred.append("軟體工程師")
            return unique_preserving_order(inferred or [self.role_targets[0].name])[:3]

        scored_roles.sort(key=lambda item: (-item[0], item[1]))
        ranked_roles = [role for _, role in scored_roles[:4]]
        return unique_preserving_order(
            specialized_roles
            + self._expand_parent_roles(specialized_roles)
            + ranked_roles
        )[:4]

    def _extract_specialized_roles(self, text: str) -> list[str]:
        lowered = f" {normalize_text(text).lower()} "
        matched: list[str] = []
        for role, patterns in self.specialized_role_patterns.items():
            if any(pattern.search(lowered) for pattern in patterns):
                matched.append(role)
        return unique_preserving_order(matched)

    def _expand_parent_roles(self, roles: Iterable[str]) -> list[str]:
        expanded: list[str] = []
        for role in roles:
            expanded.extend(self.SPECIALIZED_ROLE_PARENTS.get(role, ()))
        return unique_preserving_order(expanded)

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
        cache_dir: Path | None = None,
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
        self.cache_dir = ensure_directory(cache_dir) if cache_dir else None
        self.profile_cache_dir = (
            ensure_directory(self.cache_dir / "resume_profile_extracts")
            if self.cache_dir
            else None
        )
        self.last_usage = merge_openai_usage()
        self.last_metrics: dict[str, Any] = {}
        self._profile_memory_cache: dict[str, dict[str, Any]] = {}

    def extract(
        self,
        text: str,
        source_name: str,
        fallback_profile: ResumeProfile,
    ) -> ResumeProfile:
        self.last_usage = merge_openai_usage()
        self.last_metrics = {
            "prompt_version": RESUME_EXTRACTION_PROMPT_VERSION,
            "profile_cache_memory_hit": False,
            "profile_cache_disk_hit": False,
            "profile_cache_write": False,
            "resume_context_chars": 0,
        }
        condensed_resume_text = self._build_resume_context(text, fallback_profile)
        self.last_metrics["resume_context_chars"] = len(condensed_resume_text)
        role_hint = self._build_role_hint()
        fallback_brief = self._build_fallback_brief(fallback_profile)
        cache_key = _stable_hash(
            {
                "schema": "resume_profile_extract_v2",
                "model": self.model,
                "source_name": source_name,
                "role_hint": role_hint,
                "fallback_brief": fallback_brief,
                "resume_context": condensed_resume_text,
            }
        )
        cached = self._read_cache(cache_key)
        if cached is not None:
            self.last_metrics["profile_cache_memory_hit"] = bool(cached.get("_memory_hit"))
            self.last_metrics["profile_cache_disk_hit"] = not bool(cached.get("_memory_hit"))
            return self._build_profile_from_payload(
                payload=cached,
                source_name=source_name,
                raw_text=text,
                fallback_profile=fallback_profile,
            )
        response = self.client.responses.parse(
            model=self.model,
            temperature=0.1,
            max_output_tokens=240,
            input=(
                "請把這份履歷整理成台灣職缺比對用的結構化摘要。\n"
                "重點輸出：target_roles、core_skills、tool_skills、preferred_tasks、match_keywords。\n"
                "generated_prompts 只要 3 句短 prompt。\n"
                "target_roles 請優先對齊下列目標職缺名稱：\n"
                f"{role_hint}\n\n"
                "以下是規則分析初稿，可參考但不要逐字照抄：\n"
                f"{fallback_brief}\n\n"
                "以下是清理後的履歷重點片段，請優先根據這些內容抽取：\n"
                f"{condensed_resume_text}"
            ),
            text_format=LLMResumeProfile,
        )
        self.last_usage = merge_openai_usage(extract_openai_usage(response))
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("LLM 沒有回傳可解析的結構化結果。")

        payload = {
            "summary": parsed.summary,
            "target_roles": parsed.target_roles,
            "core_skills": parsed.core_skills,
            "tool_skills": parsed.tool_skills,
            "domain_keywords": parsed.domain_keywords,
            "preferred_tasks": parsed.preferred_tasks,
            "generated_prompts": parsed.generated_prompts,
            "match_keywords": parsed.match_keywords,
        }
        self._write_cache(cache_key, payload)
        self.last_metrics["profile_cache_write"] = True
        return self._build_profile_from_payload(
            payload=payload,
            source_name=source_name,
            raw_text=text,
            fallback_profile=fallback_profile,
        )

    def _build_profile_from_payload(
        self,
        *,
        payload: dict[str, Any],
        source_name: str,
        raw_text: str,
        fallback_profile: ResumeProfile,
    ) -> ResumeProfile:
        target_roles = self._normalize_roles(
            payload.get("target_roles", []),
            fallback_profile.target_roles,
        )
        core_skills = unique_preserving_order(
            [item.strip() for item in payload.get("core_skills", []) if item and item.strip()]
            + fallback_profile.core_skills
        )[:8]
        tool_skills = unique_preserving_order(
            [item.strip() for item in payload.get("tool_skills", []) if item and item.strip()]
            + fallback_profile.tool_skills
        )[:8]
        domain_keywords = _sanitize_domain_keywords(
            [item.strip() for item in payload.get("domain_keywords", []) if item and item.strip()]
            + fallback_profile.domain_keywords
        )[:10]
        preferred_tasks = unique_preserving_order(
            [item.strip() for item in payload.get("preferred_tasks", []) if item and item.strip()]
            + fallback_profile.preferred_tasks
        )[:8]
        generated_prompts = unique_preserving_order(
            [item.strip() for item in payload.get("generated_prompts", []) if item and item.strip()]
            + fallback_profile.generated_prompts
        )[:4]
        match_keywords = _sanitize_match_keywords(
            [item.strip() for item in payload.get("match_keywords", []) if item and item.strip()]
            + core_skills
            + tool_skills
            + domain_keywords
            + preferred_tasks
            + target_roles
        )[:18]

        return ResumeProfile(
            source_name=source_name,
            raw_text=raw_text,
            summary=(str(payload.get("summary", "")).strip() or fallback_profile.summary),
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

    def _build_role_hint(self) -> str:
        lines = []
        for role in self.role_targets[:4]:
            keyword_text = ", ".join(role.keywords[:3])
            lines.append(f"- {role.name}: {keyword_text}")
        return "\n".join(lines)

    def _build_fallback_brief(self, fallback_profile: ResumeProfile) -> str:
        return "\n".join(
            [
                f"summary: {fallback_profile.summary[:120]}",
                f"target_roles: {', '.join(fallback_profile.target_roles[:2])}",
                f"core_skills: {', '.join(fallback_profile.core_skills[:4])}",
                f"tool_skills: {', '.join(fallback_profile.tool_skills[:4])}",
                f"preferred_tasks: {', '.join(fallback_profile.preferred_tasks[:3])}",
                f"domain_keywords: {', '.join(fallback_profile.domain_keywords[:3])}",
            ]
        )

    def _build_resume_context(self, text: str, fallback_profile: ResumeProfile) -> str:
        cleaned_lines = _clean_resume_lines(text)
        if not cleaned_lines:
            return text[:1600]

        role_terms = {normalize_text(item).lower() for item in fallback_profile.target_roles if item}
        skill_terms = {
            normalize_text(item).lower()
            for item in (fallback_profile.core_skills + fallback_profile.tool_skills)
            if item
        }
        task_terms = {normalize_text(item).lower() for item in fallback_profile.preferred_tasks if item}
        keyword_terms = {
            normalize_text(item).lower()
            for item in (fallback_profile.domain_keywords + fallback_profile.match_keywords)
            if item
        }

        scored_lines: list[tuple[int, int, str]] = []
        for index, line in enumerate(cleaned_lines):
            if _contains_personal_info(line) or _looks_garbled(line):
                continue
            normalized_line = normalize_text(line)
            lowered = normalized_line.lower()
            if not lowered:
                continue

            score = 0
            score += sum(4 for term in role_terms if term and term in lowered)
            score += sum(3 for term in skill_terms if term and term in lowered)
            score += sum(2 for term in task_terms if term and term in lowered)
            score += sum(1 for term in keyword_terms if term and term in lowered)
            if any(token in lowered for token in ("經歷", "工作內容", "專案", "技能", "工具", "職稱")):
                score += 1
            if score == 0 and len(normalized_line) < 14:
                continue
            scored_lines.append((score, index, normalized_line))

        if not scored_lines:
            return text[:1600]

        scored_lines.sort(key=lambda item: (-item[0], item[1]))
        top_lines = scored_lines[:8]
        top_lines.sort(key=lambda item: item[1])
        selected = unique_preserving_order([line for _, _, line in top_lines])
        context = "\n".join(selected)
        return context[:1400]

    def _read_cache(self, cache_key: str) -> dict[str, Any] | None:
        memory_cached = self._profile_memory_cache.get(cache_key)
        if memory_cached is not None:
            payload = dict(memory_cached)
            payload["_memory_hit"] = True
            return payload
        if self.profile_cache_dir is None:
            return None
        path = self.profile_cache_dir / f"{cache_key}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        self._remember_profile_cache(cache_key, payload)
        payload["_memory_hit"] = False
        return payload

    def _write_cache(self, cache_key: str, payload: dict[str, Any]) -> None:
        self._remember_profile_cache(cache_key, payload)
        if self.profile_cache_dir is None:
            return
        path = self.profile_cache_dir / f"{cache_key}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def _remember_profile_cache(self, cache_key: str, payload: dict[str, Any]) -> None:
        self._profile_memory_cache[cache_key] = dict(payload)
        while len(self._profile_memory_cache) > RESUME_PROFILE_MEMORY_CACHE_MAX:
            oldest_key = next(iter(self._profile_memory_cache))
            self._profile_memory_cache.pop(oldest_key, None)

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
