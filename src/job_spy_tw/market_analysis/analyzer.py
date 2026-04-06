"""Market-analysis helpers for analyzer."""

from __future__ import annotations

import math
import re
from collections import defaultdict

from ..models import ItemInsight, JobListing, SkillInsight, TargetRole
from ..utils import normalize_text
from .taxonomies import ROLE_KEYWORD_PATTERNS, SKILL_TAXONOMY, TASK_TAXONOMY


class JobAnalyzer:
    def __init__(self, role_targets: list[TargetRole]) -> None:
        self.role_targets = role_targets
        self._compiled_skills = self._compile_pattern_map(SKILL_TAXONOMY)
        self._compiled_tasks = self._compile_pattern_map(TASK_TAXONOMY)

    def score_jobs(self, jobs: list[JobListing]) -> list[JobListing]:
        for job in jobs:
            role, score = self._match_role(job)
            job.matched_role = role.name
            job.relevance_score = round(score, 2)
            skill_source = job.requirement_text() or job.combined_text()
            job.extracted_skills = self.extract_skills(skill_source)
            if not job.extracted_skills and skill_source != job.combined_text():
                job.extracted_skills = self.extract_skills(job.combined_text())
        jobs.sort(key=lambda item: item.relevance_score, reverse=True)
        return jobs

    def summarize_skills(self, jobs: list[JobListing]) -> list[SkillInsight]:
        aggregate: dict[str, dict[str, object]] = defaultdict(
            lambda: {
                "category": "",
                "score": 0.0,
                "occurrences": 0,
                "sources": set(),
                "sample_jobs": [],
            }
        )

        role_weight_map = {role.name: role.weight for role in self.role_targets}

        for job in jobs:
            role_weight = role_weight_map.get(job.matched_role, 0.4)
            title_lower = f" {job.title.lower()} "
            requirement_text = f" {normalize_text(job.requirement_text()).lower()} "
            body_lower = f" {job.combined_text().lower()} "
            for category, skill_map in self._compiled_skills.items():
                for skill, patterns in skill_map.items():
                    requirement_hits = sum(
                        len(pattern.findall(requirement_text)) for pattern in patterns
                    )
                    body_hits = sum(len(pattern.findall(body_lower)) for pattern in patterns)
                    weighted_hits = (requirement_hits * 2.4) + max(
                        0.0, body_hits - requirement_hits
                    ) * 0.6
                    if weighted_hits == 0:
                        continue
                    in_title = any(pattern.search(title_lower) for pattern in patterns)
                    score = weighted_hits * role_weight * (1.7 if in_title else 1.0)
                    slot = aggregate[skill]
                    slot["category"] = category
                    slot["score"] = float(slot["score"]) + score
                    slot["occurrences"] = int(slot["occurrences"]) + 1
                    slot["sources"].add(job.source)
                    if len(slot["sample_jobs"]) < 3:
                        slot["sample_jobs"].append(f"{job.title} @ {job.company}")

        insights: list[SkillInsight] = []
        max_score = max((float(data["score"]) for data in aggregate.values()), default=1.0)
        for skill, data in aggregate.items():
            normalized = float(data["score"]) / max_score
            insights.append(
                SkillInsight(
                    skill=skill,
                    category=str(data["category"]),
                    score=round(float(data["score"]), 2),
                    importance=self._importance_label(normalized),
                    occurrences=int(data["occurrences"]),
                    sources=sorted(data["sources"]),
                    sample_jobs=list(data["sample_jobs"]),
                )
            )
        insights.sort(key=lambda item: item.score, reverse=True)
        return insights

    def summarize_tasks(self, jobs: list[JobListing]) -> list[ItemInsight]:
        aggregate: dict[str, dict[str, object]] = defaultdict(
            lambda: {
                "score": 0.0,
                "occurrences": 0,
                "sources": set(),
                "sample_jobs": [],
            }
        )
        role_weight_map = {role.name: role.weight for role in self.role_targets}

        for job in jobs:
            role_weight = role_weight_map.get(job.matched_role, 0.4)
            matched_tasks: dict[str, int] = {}
            for item in job.work_content_items:
                lowered = f" {normalize_text(item).lower()} "
                found = False
                for task, patterns in self._compiled_tasks.items():
                    if any(pattern.search(lowered) for pattern in patterns):
                        matched_tasks[task] = matched_tasks.get(task, 0) + 1
                        found = True
                if not found and len(item) <= 36:
                    matched_tasks[item] = matched_tasks.get(item, 0) + 1

            for task, hits in matched_tasks.items():
                slot = aggregate[task]
                slot["score"] = float(slot["score"]) + (hits * role_weight)
                slot["occurrences"] = int(slot["occurrences"]) + 1
                slot["sources"].add(job.source)
                if len(slot["sample_jobs"]) < 3:
                    slot["sample_jobs"].append(f"{job.title} @ {job.company}")

        max_score = max((float(data["score"]) for data in aggregate.values()), default=1.0)
        insights: list[ItemInsight] = []
        for task, data in aggregate.items():
            normalized = float(data["score"]) / max_score
            insights.append(
                ItemInsight(
                    item=task,
                    score=round(float(data["score"]), 2),
                    importance=self._importance_label(normalized),
                    occurrences=int(data["occurrences"]),
                    sources=sorted(data["sources"]),
                    sample_jobs=list(data["sample_jobs"]),
                )
            )
        insights.sort(key=lambda item: item.score, reverse=True)
        return insights

    def extract_skills(self, text: str) -> list[str]:
        lowered = f" {normalize_text(text).lower()} "
        found: list[str] = []
        for skill_map in self._compiled_skills.values():
            for skill, patterns in skill_map.items():
                if any(pattern.search(lowered) for pattern in patterns):
                    found.append(skill)
        return sorted(found)

    def _match_role(self, job: JobListing) -> tuple[TargetRole, float]:
        text = normalize_text(job.combined_text()).lower()
        title = job.title.lower()
        best_role = self.role_targets[0]
        best_score = -math.inf

        for role in self.role_targets:
            score = role.weight * 4
            role_terms = self._role_terms(role)
            if self._contains_phrase(title, role.name):
                score += 92
            elif self._contains_phrase(text, role.name):
                score += 60

            for keyword in role_terms:
                if keyword == role.name:
                    continue
                if self._contains_phrase(title, keyword):
                    score += 78
                elif self._contains_phrase(text, keyword):
                    score += 22

            if score > best_score:
                best_score = score
                best_role = role

        return best_role, min(best_score, 100.0)

    def _role_terms(self, role: TargetRole) -> list[str]:
        aliases = [role.name]
        aliases.extend(
            keyword for keyword in role.keywords if self._looks_like_role_alias(keyword)
        )
        return list(dict.fromkeys(keyword.strip() for keyword in aliases if keyword.strip()))

    def _looks_like_role_alias(self, keyword: str) -> bool:
        lowered = normalize_text(keyword).lower()
        if not lowered:
            return False
        if lowered in {"pm", "po", "fae", "qa", "ui", "ux", "hr", "rd"}:
            return True
        return any(pattern in lowered for pattern in ROLE_KEYWORD_PATTERNS)

    def _contains_phrase(self, haystack: str, needle: str) -> bool:
        normalized_haystack = normalize_text(haystack).lower()
        normalized_needle = normalize_text(needle).lower()
        if not normalized_haystack or not normalized_needle:
            return False
        if re.fullmatch(r"[a-z0-9+/# .-]+", normalized_needle):
            escaped = re.escape(normalized_needle).replace(r"\ ", r"\s+")
            return bool(
                re.search(rf"(?<!\w){escaped}(?!\w)", normalized_haystack, re.IGNORECASE)
            )
        return normalized_needle in normalized_haystack

    def _compile_pattern_map(
        self,
        taxonomy: dict[str, dict[str, tuple[str, ...]]] | dict[str, tuple[str, ...]],
    ) -> dict[str, dict[str, tuple[re.Pattern[str], ...]]] | dict[str, tuple[re.Pattern[str], ...]]:
        compiled = {}
        for category, skill_map in taxonomy.items():
            if isinstance(skill_map, dict):
                compiled[category] = {}
                for skill, aliases in skill_map.items():
                    compiled[category][skill] = self._compile_aliases(aliases)
            else:
                compiled[category] = self._compile_aliases(skill_map)
        return compiled

    def _compile_aliases(self, aliases: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
        patterns: list[re.Pattern[str]] = []
        for alias in aliases:
            cleaned = alias.strip()
            if re.fullmatch(r"[a-zA-Z0-9+/# .-]+", cleaned):
                escaped = re.escape(cleaned)
                escaped = escaped.replace(r"\ ", r"\s+")
                pattern = re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)
            else:
                pattern = re.compile(re.escape(cleaned), re.IGNORECASE)
            patterns.append(pattern)
        return tuple(patterns)

    def _importance_label(self, normalized_score: float) -> str:
        if normalized_score >= 0.75:
            return "高"
        if normalized_score >= 0.45:
            return "中高"
        if normalized_score >= 0.2:
            return "中"
        return "低"
