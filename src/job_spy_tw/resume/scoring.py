"""Resume-analysis helpers for scoring."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from typing import Any, Iterable

from ..models import ResumeJobMatch
from ..utils import normalize_text
from .text import _sanitize_extracted_text


ROLE_WEIGHT = 15.0
SKILL_SEMANTIC_WEIGHT = 30.0
TASK_SEMANTIC_WEIGHT = 25.0
KEYWORD_WEIGHT = 10.0
EXACT_SKILL_WEIGHT = 12.0
EXACT_TASK_WEIGHT = 8.0
EXACT_TITLE_WEIGHT = 6.0
MARKET_FIT_TOTAL = ROLE_WEIGHT + SKILL_SEMANTIC_WEIGHT + TASK_SEMANTIC_WEIGHT + KEYWORD_WEIGHT
SEMANTIC_TOTAL = SKILL_SEMANTIC_WEIGHT + TASK_SEMANTIC_WEIGHT + KEYWORD_WEIGHT


def summarize_match_gaps(
    matches: list[ResumeJobMatch],
    *,
    top_n: int = 10,
    limit: int = 6,
) -> dict[str, list[tuple[str, int]]]:
    top_matches = matches[:top_n]
    matched_skill_counter: Counter[str] = Counter()
    matched_task_counter: Counter[str] = Counter()
    missing_skill_counter: Counter[str] = Counter()
    missing_task_counter: Counter[str] = Counter()

    for match in top_matches:
        matched_skill_counter.update(match.matched_skills)
        matched_task_counter.update(match.matched_tasks)
        missing_skill_counter.update(match.missing_skills)
        missing_task_counter.update(match.missing_tasks)

    return {
        "strength_skills": matched_skill_counter.most_common(limit),
        "strength_tasks": matched_task_counter.most_common(limit),
        "gap_skills": missing_skill_counter.most_common(limit),
        "gap_tasks": missing_task_counter.most_common(limit),
    }


def _build_fit_summary(
    *,
    title_reason: str,
    matched_skills: list[str],
    matched_tasks: list[str],
    missing_skills: list[str],
    missing_tasks: list[str],
) -> str:
    segments: list[str] = []
    if title_reason:
        segments.append(f"職稱判斷：{title_reason}")
    if matched_skills:
        segments.append(f"已命中技能 {', '.join(matched_skills[:3])}")
    if matched_tasks:
        segments.append(f"已命中工作內容 {', '.join(matched_tasks[:2])}")
    if missing_skills:
        segments.append(f"建議補強 {', '.join(missing_skills[:3])}")
    elif missing_tasks:
        segments.append(f"可再補強 {', '.join(missing_tasks[:2])}")
    return "；".join(segments[:4])


def _stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _prepare_embedding_text(text: str, max_chars: int = 2800) -> str:
    prepared = normalize_text(_sanitize_extracted_text(text))
    return prepared[:max_chars]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(l * r for l, r in zip(left, right))
    left_norm = math.sqrt(sum(l * l for l in left))
    right_norm = math.sqrt(sum(r * r for r in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(0.0, min(1.0, numerator / (left_norm * right_norm)))


def _dice_coefficient(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    overlap = len(left_set & right_set)
    return (2 * overlap) / (len(left_set) + len(right_set))


def _saturating_hit_ratio(hit_count: int, saturation: int) -> float:
    if hit_count <= 0 or saturation <= 0:
        return 0.0
    return min(1.0, hit_count / saturation)


def _normalize_score(score: float, max_score: float) -> float:
    if max_score <= 0:
        return 0.0
    return max(0.0, min(100.0, (score / max_score) * 100.0))


def _stabilize_title_similarity(raw_similarity: float, fallback_similarity: float) -> float:
    raw = max(0.0, min(1.0, raw_similarity))
    fallback = max(0.0, min(1.0, fallback_similarity))
    if fallback >= 1.0:
        return 1.0
    if fallback > 0:
        return max(fallback, min(raw, fallback + 0.18))
    return min(raw, 0.2)


def _title_exact_match_bonus(target_roles: Iterable[str], job_title: str) -> float:
    normalized_title = normalize_text(job_title).lower()
    if not normalized_title:
        return 0.0
    for index, role in enumerate(target_roles):
        normalized_role = normalize_text(role).lower()
        if not normalized_role:
            continue
        if normalized_role == normalized_title:
            decay = max(0.4, 1.0 - (index * 0.2))
            return round(EXACT_TITLE_WEIGHT * decay, 2)
    return 0.0
