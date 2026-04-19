"""Post-training dataset, comparison, and dashboard artifact builders."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from statistics import mean
from typing import Any, Iterable
from urllib.parse import urlparse

from .config import EvalConfig
from .metrics import average

STRUCTURED_FIELDS = ("summary", "key_points", "limitations", "next_step")
SFT_RUN_PREFIX = "posttrain_sft_dataset"
DPO_RUN_PREFIX = "posttrain_dpo_pairs"
EVAL_RUN_PREFIX = "posttrain_eval_comparison"
REVIEW_RUN_PREFIX = "posttrain_review_manifest"


@dataclass(slots=True)
class AssistantCandidate:
    """Normalized assistant answer candidate for SFT or DPO."""

    candidate_id: str
    question: str
    answer_mode: str
    answer_text: str
    messages: list[dict[str, str]]
    source_artifact: str
    source_run: str
    source_kind: str
    citation_count: int
    citation_keyword_recall: float
    evidence_sufficient: bool
    structured_output: bool
    top_citation_type_hit: bool
    human_overall: float
    human_grounding: float
    human_correctness: float
    human_usefulness: float
    human_clarity: float
    human_verdict: str
    human_notes: str
    is_human_review_gold: bool
    quality_score: float


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    return default


def _slugify(text: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return lowered.strip("-") or "unknown"


def _split_bucket(key: str) -> str:
    value = sum(ord(char) for char in key) % 10
    if value < 8:
        return "train"
    if value == 8:
        return "val"
    return "test"


def _strip_code_fence(text: str) -> str:
    stripped = str(text or "").strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _normalize_list_field(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    splitter = "|" if "|" in text else "\n"
    return [item.strip(" -") for item in text.split(splitter) if item.strip(" -")]


def _parse_structured_answer(answer_text: str) -> tuple[dict[str, Any] | None, str]:
    """Parse an assistant answer into the expected structure when possible."""
    cleaned = _strip_code_fence(answer_text)
    if not cleaned:
        return None, ""

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict):
        normalized = {
            "summary": str(parsed.get("summary", "")).strip(),
            "key_points": _normalize_list_field(parsed.get("key_points")),
            "limitations": _normalize_list_field(parsed.get("limitations")),
            "next_step": str(parsed.get("next_step", "")).strip(),
        }
        if normalized["summary"] and normalized["key_points"] and normalized["next_step"]:
            return normalized, json.dumps(normalized, ensure_ascii=False, indent=2)

    summary_match = re.search(r"(?:^|\n)(?:結論|summary)[:：]?\s*(.+)", cleaned, flags=re.IGNORECASE)
    key_points_match = re.search(
        r"(?:^|\n)(?:重點|key_points?)[:：]?\s*(.+?)(?:\n(?:限制|limitations?)[:：]|\Z)",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    limitations_match = re.search(
        r"(?:^|\n)(?:限制|limitations?)[:：]?\s*(.+?)(?:\n(?:下一步|next_step)[:：]|\Z)",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    next_step_match = re.search(
        r"(?:^|\n)(?:下一步|next_step)[:：]?\s*(.+)",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    normalized = {
        "summary": summary_match.group(1).strip() if summary_match else "",
        "key_points": _normalize_list_field(key_points_match.group(1) if key_points_match else ""),
        "limitations": _normalize_list_field(limitations_match.group(1) if limitations_match else ""),
        "next_step": next_step_match.group(1).strip() if next_step_match else "",
    }
    if normalized["summary"] and normalized["key_points"] and normalized["next_step"]:
        return normalized, json.dumps(normalized, ensure_ascii=False, indent=2)
    return None, cleaned


def _iter_real_model_summaries(results_dir: Path) -> Iterable[tuple[Path, str, dict[str, Any]]]:
    for summary_path in sorted(results_dir.glob("real_model_eval_*/summary.json")):
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if "baseline" in payload:
            yield summary_path, "baseline", payload["baseline"]
        if "real_snapshot" in payload:
            yield summary_path, "real_snapshot", payload["real_snapshot"]


def _extract_answer_mode_lookup(results_dir: Path) -> dict[str, str]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for _summary_path, _stage, payload in _iter_real_model_summaries(results_dir):
        for row in payload.get("assistant", {}).get("rows", []):
            question = str(row.get("question", "")).strip()
            answer_mode = str(row.get("answer_mode", "")).strip()
            if question and answer_mode:
                counts[question][answer_mode] += 1
    return {
        question: bucket.most_common(1)[0][0]
        for question, bucket in counts.items()
        if bucket
    }


def _quality_score(
    *,
    citation_keyword_recall: float,
    evidence_sufficient: bool,
    structured_output: bool,
    top_citation_type_hit: bool,
    citation_count: int,
    human_overall: float,
    human_grounding: float,
    human_correctness: float,
    human_usefulness: float,
    human_clarity: float,
    human_verdict: str,
    is_human_review_gold: bool,
) -> float:
    verdict_bonus = 2.5 if human_verdict.lower() == "accept" else -0.5 if human_verdict else 0.0
    gold_bonus = 3.0 if is_human_review_gold else 0.0
    human_score = (
        human_overall * 0.35
        + human_grounding * 0.3
        + human_correctness * 0.15
        + human_usefulness * 0.1
        + human_clarity * 0.1
    )
    auto_score = (
        citation_keyword_recall * 3.0
        + (2.0 if evidence_sufficient else 0.0)
        + (1.5 if structured_output else 0.0)
        + (1.0 if top_citation_type_hit else 0.0)
        + min(citation_count, 5) * 0.15
    )
    return round(human_score + auto_score + verdict_bonus + gold_bonus, 4)


def _normalize_candidate_id(
    *,
    question: str,
    answer_mode: str,
    source_artifact: str,
    answer_text: str,
) -> str:
    digest = hashlib.sha1(answer_text.encode("utf-8")).hexdigest()[:12]
    return "::".join(
        [
            _slugify(question)[:50],
            _slugify(answer_mode),
            _slugify(source_artifact.split("/")[-2] if "/" in source_artifact else source_artifact),
            digest,
        ]
    )


def _candidate_messages(question: str, answer_mode: str, answer_text: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是 Job Radar AI 助理。請依 answer_mode 產出結構化 JSON，欄位固定為 "
                "summary、key_points、limitations、next_step。"
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {"answer_mode": answer_mode, "question": question},
                ensure_ascii=False,
            ),
        },
        {"role": "assistant", "content": answer_text},
    ]


def _collect_sft_candidates(config: EvalConfig) -> tuple[list[AssistantCandidate], dict[str, int]]:
    """Build reusable SFT candidates from existing evaluation artifacts."""
    results_dir = config.results_dir
    answer_mode_lookup = _extract_answer_mode_lookup(results_dir)
    candidates: list[AssistantCandidate] = []
    dedupe_seen: set[tuple[str, str, str]] = set()
    duplicate_removed_count = 0

    for summary_path, stage_name, payload in _iter_real_model_summaries(results_dir):
        for row in payload.get("assistant", {}).get("rows", []):
            question = str(row.get("question", "")).strip()
            answer_mode = str(row.get("answer_mode", "")).strip()
            answer = str(row.get("answer") or row.get("latest_answer") or "").strip()
            if not question or not answer_mode or not answer:
                continue
            structured_payload, normalized_answer = _parse_structured_answer(answer)
            if structured_payload is None:
                continue
            citation_count = _safe_int(row.get("citation_count") or len(row.get("citations", [])))
            if citation_count < 1:
                continue
            dedupe_key = (question, answer_mode, normalized_answer)
            if dedupe_key in dedupe_seen:
                duplicate_removed_count += 1
                continue
            dedupe_seen.add(dedupe_key)
            citation_keyword_recall = _safe_float(
                row.get("citation_keyword_recall", row.get("keyword_recall", 0.0))
            )
            evidence_sufficient = _safe_bool(
                row.get("evidence_sufficient", row.get("citation_ok", False))
            )
            structured_output = _safe_bool(
                row.get("structured_output", structured_payload is not None),
                default=structured_payload is not None,
            )
            top_citation_type_hit = _safe_bool(
                row.get("top_citation_type_hit", row.get("citation_ok", False))
            )
            quality_score = _quality_score(
                citation_keyword_recall=citation_keyword_recall,
                evidence_sufficient=evidence_sufficient,
                structured_output=structured_output,
                top_citation_type_hit=top_citation_type_hit,
                citation_count=citation_count,
                human_overall=0.0,
                human_grounding=0.0,
                human_correctness=0.0,
                human_usefulness=0.0,
                human_clarity=0.0,
                human_verdict="",
                is_human_review_gold=False,
            )
            candidates.append(
                AssistantCandidate(
                    candidate_id=_normalize_candidate_id(
                        question=question,
                        answer_mode=answer_mode,
                        source_artifact=str(summary_path.resolve()),
                        answer_text=normalized_answer,
                    ),
                    question=question,
                    answer_mode=answer_mode,
                    answer_text=normalized_answer,
                    messages=_candidate_messages(question, answer_mode, normalized_answer),
                    source_artifact=str(summary_path.resolve()),
                    source_run=f"{summary_path.parent.name}:{stage_name}",
                    source_kind="real_model_eval",
                    citation_count=citation_count,
                    citation_keyword_recall=citation_keyword_recall,
                    evidence_sufficient=evidence_sufficient,
                    structured_output=structured_output,
                    top_citation_type_hit=top_citation_type_hit,
                    human_overall=0.0,
                    human_grounding=0.0,
                    human_correctness=0.0,
                    human_usefulness=0.0,
                    human_clarity=0.0,
                    human_verdict="",
                    human_notes="",
                    is_human_review_gold=False,
                    quality_score=quality_score,
                )
            )

    latest_review_summaries = sorted(results_dir.glob("formal_human_review_*/summary.json"), reverse=True)
    if latest_review_summaries:
        summary_path = latest_review_summaries[0]
        try:
            review_payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            review_payload = {}
        for review_row in review_payload.get("review_rows", []):
            question = str(review_row.get("question", "")).strip()
            if not question:
                continue
            answer_mode = answer_mode_lookup.get(question, "")
            if not answer_mode:
                continue
            structured_payload = {
                "summary": str(review_row.get("summary", "")).strip(),
                "key_points": _normalize_list_field(review_row.get("key_points")),
                "limitations": _normalize_list_field(review_row.get("limitations")),
                "next_step": str(review_row.get("next_step", "")).strip(),
            }
            if not structured_payload["summary"] or not structured_payload["key_points"]:
                continue
            normalized_answer = json.dumps(structured_payload, ensure_ascii=False, indent=2)
            dedupe_key = (question, answer_mode, normalized_answer)
            if dedupe_key in dedupe_seen:
                duplicate_removed_count += 1
                continue
            dedupe_seen.add(dedupe_key)
            human_overall = _safe_float(review_row.get("overall_score"))
            human_grounding = _safe_float(review_row.get("grounding_score"))
            human_correctness = _safe_float(review_row.get("correctness_score"))
            human_usefulness = _safe_float(review_row.get("usefulness_score"))
            human_clarity = _safe_float(review_row.get("clarity_score"))
            human_verdict = str(review_row.get("verdict", "")).strip()
            citation_count = _safe_int(review_row.get("citation_count"))
            is_human_review_gold = (
                human_verdict.lower() == "accept"
                and human_overall >= 4.5
                and human_grounding >= 4.5
            )
            quality_score = _quality_score(
                citation_keyword_recall=_safe_float(review_row.get("auto_citation_keyword_recall"), 1.0),
                evidence_sufficient=True,
                structured_output=True,
                top_citation_type_hit=True,
                citation_count=citation_count,
                human_overall=human_overall,
                human_grounding=human_grounding,
                human_correctness=human_correctness,
                human_usefulness=human_usefulness,
                human_clarity=human_clarity,
                human_verdict=human_verdict,
                is_human_review_gold=is_human_review_gold,
            )
            candidates.append(
                AssistantCandidate(
                    candidate_id=_normalize_candidate_id(
                        question=question,
                        answer_mode=answer_mode,
                        source_artifact=str(summary_path.resolve()),
                        answer_text=normalized_answer,
                    ),
                    question=question,
                    answer_mode=answer_mode,
                    answer_text=normalized_answer,
                    messages=_candidate_messages(question, answer_mode, normalized_answer),
                    source_artifact=str(summary_path.resolve()),
                    source_run=summary_path.parent.name,
                    source_kind="formal_human_review",
                    citation_count=citation_count,
                    citation_keyword_recall=_safe_float(review_row.get("auto_citation_keyword_recall"), 1.0),
                    evidence_sufficient=True,
                    structured_output=True,
                    top_citation_type_hit=True,
                    human_overall=human_overall,
                    human_grounding=human_grounding,
                    human_correctness=human_correctness,
                    human_usefulness=human_usefulness,
                    human_clarity=human_clarity,
                    human_verdict=human_verdict,
                    human_notes=str(review_row.get("notes", "")).strip(),
                    is_human_review_gold=is_human_review_gold,
                    quality_score=quality_score,
                )
            )

    ordered = sorted(
        candidates,
        key=lambda item: (
            item.answer_mode,
            -item.quality_score,
            item.question,
            item.candidate_id,
        ),
    )
    return ordered, {
        "duplicate_removed_count": duplicate_removed_count,
        "raw_candidate_count": len(ordered) + duplicate_removed_count,
    }


def build_sft_candidates(config: EvalConfig) -> list[AssistantCandidate]:
    """Build reusable SFT candidates from existing evaluation artifacts."""
    return _collect_sft_candidates(config)[0]


def build_sft_dataset_manifest(config: EvalConfig) -> dict[str, Any]:
    """Build the normalized SFT dataset rows and summary manifest."""
    all_candidates, candidate_stats = _collect_sft_candidates(config)
    filtered = [item for item in all_candidates if item.answer_mode in {"market_summary", "personalized_guidance", "job_comparison"}]
    mode_counts = Counter(item.answer_mode for item in filtered)
    smallest_bucket = min(mode_counts.values()) if mode_counts else 0
    mode_cap = smallest_bucket * 3 if smallest_bucket else 0
    kept: list[AssistantCandidate] = []
    dropped_for_balance = 0
    per_mode_counts: Counter[str] = Counter()
    for candidate in sorted(filtered, key=lambda item: (-item.quality_score, item.question, item.candidate_id)):
        if mode_cap and per_mode_counts[candidate.answer_mode] >= mode_cap:
            dropped_for_balance += 1
            continue
        kept.append(candidate)
        per_mode_counts[candidate.answer_mode] += 1

    rows = []
    split_counts: Counter[str] = Counter()
    citation_distribution: Counter[int] = Counter()
    for candidate in kept:
        split = _split_bucket(candidate.candidate_id)
        split_counts[split] += 1
        citation_distribution[candidate.citation_count] += 1
        rows.append(
            {
                "id": candidate.candidate_id,
                "question": candidate.question,
                "answer_mode": candidate.answer_mode,
                "messages": candidate.messages,
                "quality_tag": "gold" if candidate.is_human_review_gold else "silver",
                "review_status": candidate.human_verdict or "auto_only",
                "split": split,
                "source_run": candidate.source_run,
                "source_artifact": candidate.source_artifact,
                "citation_count": candidate.citation_count,
                "citation_keyword_recall": candidate.citation_keyword_recall,
                "evidence_sufficient": candidate.evidence_sufficient,
                "quality_score": candidate.quality_score,
            }
        )

    source_artifacts = sorted({item.source_artifact for item in kept})
    gold_count = sum(1 for item in kept if item.is_human_review_gold)
    return {
        "dataset_version": f"sft-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_rows": len(rows),
        "rows": rows,
        "split_counts": dict(split_counts),
        "mode_counts": dict(Counter(item.answer_mode for item in kept)),
        "gold_counts": {
            "human_review_gold_count": gold_count,
            "auto_only_count": len(rows) - gold_count,
        },
        "dedup_counts": {
            "raw_candidate_count": candidate_stats["raw_candidate_count"],
            "total_candidates": len(all_candidates),
            "dedup_removed_count": candidate_stats["duplicate_removed_count"],
            "mode_balance_dropped_count": dropped_for_balance,
        },
        "unique_questions": len({item.question for item in kept}),
        "source_artifact_count": len(source_artifacts),
        "source_artifacts": source_artifacts,
        "avg_answer_chars": round(average([float(len(item.answer_text)) for item in kept]), 2),
        "citation_count_distribution": {str(key): value for key, value in sorted(citation_distribution.items())},
    }


def _pair_rule(chosen: AssistantCandidate, rejected: AssistantCandidate) -> str:
    if chosen.is_human_review_gold and rejected.human_verdict.lower() == "minor_issue":
        return "gold_accept_vs_review_minor_issue"
    if chosen.is_human_review_gold and rejected.source_kind == "real_model_eval":
        return "gold_review_vs_auto_candidate"
    if rejected.human_verdict.lower() == "minor_issue":
        return "human_minor_issue_gap"
    if rejected.evidence_sufficient is False:
        return "evidence_gap"
    if rejected.citation_keyword_recall + 0.2 <= chosen.citation_keyword_recall:
        return "citation_recall_gap"
    return "quality_gap"


def _text_similarity(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"\w+|[\u4e00-\u9fff]+", left.lower()))
    right_tokens = set(re.findall(r"\w+|[\u4e00-\u9fff]+", right.lower()))
    if not left_tokens and not right_tokens:
        return 1.0
    union = left_tokens | right_tokens
    if not union:
        return 0.0
    return len(left_tokens & right_tokens) / len(union)


def build_dpo_pairs_manifest(config: EvalConfig) -> dict[str, Any]:
    """Build DPO preference pairs from normalized assistant candidates."""
    candidates = build_sft_candidates(config)
    grouped: dict[tuple[str, str], list[AssistantCandidate]] = defaultdict(list)
    for candidate in candidates:
        if candidate.answer_mode in {"market_summary", "personalized_guidance", "job_comparison"}:
            grouped[(candidate.question, candidate.answer_mode)].append(candidate)

    rows = []
    split_counts: Counter[str] = Counter()
    pair_rule_counts: Counter[str] = Counter()
    chosen_source_distribution: Counter[str] = Counter()
    rejected_source_distribution: Counter[str] = Counter()
    near_duplicate_rejected_count = 0
    score_gaps: list[float] = []
    pair_index = 0

    for (question, answer_mode), bucket in sorted(grouped.items()):
        ranked = sorted(bucket, key=lambda item: (-item.quality_score, item.candidate_id))
        if len(ranked) < 2:
            continue
        chosen = ranked[0]
        comparisons = 0
        for rejected in reversed(ranked[1:]):
            if comparisons >= 3:
                break
            score_gap = round(chosen.quality_score - rejected.quality_score, 4)
            if score_gap < 0.75:
                continue
            similarity = _text_similarity(chosen.answer_text, rejected.answer_text)
            if similarity >= 0.92:
                near_duplicate_rejected_count += 1
                continue
            pair_index += 1
            comparisons += 1
            pair_rule = _pair_rule(chosen, rejected)
            split = _split_bucket(f"{chosen.candidate_id}::{rejected.candidate_id}")
            split_counts[split] += 1
            pair_rule_counts[pair_rule] += 1
            chosen_source_distribution[chosen.source_kind] += 1
            rejected_source_distribution[rejected.source_kind] += 1
            score_gaps.append(score_gap)
            rows.append(
                {
                    "id": f"dpo-{pair_index:05d}",
                    "question": question,
                    "answer_mode": answer_mode,
                    "prompt": json.dumps(
                        {"answer_mode": answer_mode, "question": question},
                        ensure_ascii=False,
                    ),
                    "chosen": chosen.answer_text,
                    "rejected": rejected.answer_text,
                    "pair_rule": pair_rule,
                    "chosen_source": chosen.source_kind,
                    "rejected_source": rejected.source_kind,
                    "chosen_artifact": chosen.source_artifact,
                    "rejected_artifact": rejected.source_artifact,
                    "chosen_quality_score": chosen.quality_score,
                    "rejected_quality_score": rejected.quality_score,
                    "score_gap": score_gap,
                    "similarity": round(similarity, 4),
                    "split": split,
                }
            )

    return {
        "dataset_version": f"dpo-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_pairs": len(rows),
        "rows": rows,
        "split_counts": dict(split_counts),
        "pair_rule_counts": dict(pair_rule_counts),
        "unique_prompts": len({row["prompt"] for row in rows}),
        "chosen_source_distribution": dict(chosen_source_distribution),
        "rejected_source_distribution": dict(rejected_source_distribution),
        "score_gap_stats": {
            "avg_score_gap": round(average(score_gaps), 4),
            "max_score_gap": round(max(score_gaps), 4) if score_gaps else 0.0,
            "min_score_gap": round(min(score_gaps), 4) if score_gaps else 0.0,
        },
        "near_duplicate_rejected_count": near_duplicate_rejected_count,
        "source_artifacts": sorted(
            {
                row["chosen_artifact"]
                for row in rows
            }
            | {
                row["rejected_artifact"]
                for row in rows
            }
        ),
        "source_artifact_count": len(
            {
                row["chosen_artifact"]
                for row in rows
            }
            | {
                row["rejected_artifact"]
                for row in rows
            }
        ),
    }


def build_eval_comparison_manifest(
    *,
    base_summary: dict[str, Any],
    sft_summary: dict[str, Any],
    dpo_summary: dict[str, Any],
    base_model: str,
    sft_model: str,
    dpo_model: str,
    dataset_version: str,
) -> dict[str, Any]:
    """Build a stage comparison manifest from assistant evaluation summaries."""
    stage_summaries = {
        "base": base_summary.get("assistant", base_summary),
        "sft": sft_summary.get("assistant", sft_summary),
        "dpo": dpo_summary.get("assistant", dpo_summary),
    }

    metric_keys = [
        "keyword_precision_mean",
        "keyword_recall_mean",
        "keyword_f1_mean",
        "source_type_precision_mean",
        "source_type_recall_mean",
        "source_type_f1_mean",
        "citation_min_count_accuracy",
        "structured_output_rate",
        "top_citation_type_hit_rate",
        "citation_keyword_recall_mean",
        "evidence_sufficiency_rate",
        "total_ms_mean",
        "total_ms_p95",
        "case_count",
    ]

    assistant_metrics_overall: dict[str, dict[str, float]] = {}
    for stage, section in stage_summaries.items():
        aggregate = section.get("aggregate", {})
        assistant_metrics_overall[stage] = {
            key: _safe_float(aggregate.get(key), default=0.0)
            for key in metric_keys
        }

    by_mode: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    for stage, section in stage_summaries.items():
        for mode, metrics in section.get("mode_breakdown", {}).items():
            by_mode[mode][stage] = {
                key: _safe_float(metrics.get(key), default=0.0)
                for key in metric_keys
            }

    merged_case_rows: dict[tuple[str, str], dict[str, Any]] = {}
    for stage, section in stage_summaries.items():
        for row in section.get("rows", []):
            key = (str(row.get("case_id", "")), str(row.get("answer_mode", "")))
            record = merged_case_rows.setdefault(
                key,
                {
                    "case_id": key[0],
                    "answer_mode": key[1],
                    "question": row.get("question", ""),
                },
            )
            for field in [
                "answer",
                "keyword_precision",
                "keyword_recall",
                "keyword_f1",
                "source_type_precision",
                "source_type_recall",
                "source_type_f1",
                "citation_min_count_accuracy",
                "structured_output",
                "top_citation_type_hit",
                "citation_keyword_recall",
                "evidence_sufficient",
                "total_ms",
            ]:
                record[f"{stage}_{field}"] = row.get(field)

    def _delta(left: dict[str, float], right: dict[str, float]) -> dict[str, float]:
        return {
            key: round(right.get(key, 0.0) - left.get(key, 0.0), 4)
            for key in metric_keys
        }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "base_model": base_model,
        "sft_model": sft_model,
        "dpo_model": dpo_model,
        "dataset_version": dataset_version,
        "assistant_metrics_overall": assistant_metrics_overall,
        "assistant_metrics_by_mode": dict(by_mode),
        "assistant_case_rows": list(merged_case_rows.values()),
        "stage_deltas": {
            "sft_vs_base": _delta(assistant_metrics_overall["base"], assistant_metrics_overall["sft"]),
            "dpo_vs_sft": _delta(assistant_metrics_overall["sft"], assistant_metrics_overall["dpo"]),
            "dpo_vs_base": _delta(assistant_metrics_overall["base"], assistant_metrics_overall["dpo"]),
        },
        "sample_size": int(assistant_metrics_overall["dpo"].get("case_count", 0)),
    }


def build_review_manifest(
    *,
    review_summary: dict[str, Any],
    comparison_manifest: dict[str, Any],
    dpo_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Build combined human review and failure-analysis manifest."""
    review_rows = review_summary.get("review_rows", [])
    aggregate = review_summary.get("aggregate", {})
    comparison_rows = comparison_manifest.get("assistant_case_rows", [])
    failure_rows = sorted(
        comparison_rows,
        key=lambda row: _safe_float(row.get("dpo_keyword_f1"), default=999.0),
    )
    largest_regressions = sorted(
        comparison_rows,
        key=lambda row: _safe_float(row.get("dpo_keyword_f1"), 0.0) - _safe_float(row.get("base_keyword_f1"), 0.0),
    )
    dpo_by_mode = comparison_manifest.get("assistant_metrics_by_mode", {})
    mode_with_worst_delta = ""
    worst_delta = None
    for mode, stage_metrics in dpo_by_mode.items():
        delta = _safe_float(stage_metrics.get("dpo", {}).get("keyword_f1_mean"), 0.0) - _safe_float(
            stage_metrics.get("base", {}).get("keyword_f1_mean"),
            0.0,
        )
        if worst_delta is None or delta < worst_delta:
            worst_delta = delta
            mode_with_worst_delta = mode

    notes_counter = Counter()
    for row in review_rows:
        note = str(row.get("notes", "")).strip()
        if note:
            notes_counter[note] += 1

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset_version": dpo_manifest.get("dataset_version", comparison_manifest.get("dataset_version", "")),
        "aggregate": aggregate,
        "case_rows": review_summary.get("case_rows", []),
        "review_rows": review_rows,
        "failure_analysis": {
            "lowest_f1_cases": failure_rows[:5],
            "lowest_grounding_cases": sorted(
                review_rows,
                key=lambda row: _safe_float(row.get("grounding_score"), 999.0),
            )[:5],
            "lowest_evidence_cases": sorted(
                comparison_rows,
                key=lambda row: _safe_float(row.get("dpo_citation_keyword_recall"), default=999.0),
            )[:5],
            "largest_regression_cases": largest_regressions[:5],
            "mode_with_worst_delta": mode_with_worst_delta,
            "most_common_rejection_rules": Counter(row.get("pair_rule") for row in dpo_manifest.get("rows", [])).most_common(10),
            "most_common_human_review_notes": notes_counter.most_common(10),
        },
        "sample_size": int(aggregate.get("reviewed_row_count", len(review_rows)) or len(review_rows)),
    }


def resolve_resource_ref(ref: str) -> str:
    normalized = str(ref or "").strip()
    if not normalized:
        return normalized
    parsed = urlparse(normalized)
    if parsed.scheme in {"http", "https"}:
        return normalized
    return str(Path(normalized).expanduser().resolve())
