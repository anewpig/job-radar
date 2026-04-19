from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATASET_THRESHOLDS = {
    "assistant_questions": {"minimum": 80, "label": "Assistant 題集數"},
    "resume_extraction_labels": {"minimum": 20, "label": "履歷擷取標註數"},
    "resume_match_labels": {"minimum": 20, "label": "履歷匹配標註數"},
}

ASSISTANT_MODE_COVERAGE = {
    "market_summary": {"minimum_cases": 1, "label": "Assistant market_summary 覆蓋"},
    "personalized_guidance": {"minimum_cases": 1, "label": "Assistant personalized_guidance 覆蓋"},
    "job_comparison": {"minimum_cases": 1, "label": "Assistant job_comparison 覆蓋"},
}

QUALITY_THRESHOLDS = {
    "assistant_citation_keyword_recall_mean": {"minimum": 0.95, "label": "Assistant citation keyword recall"},
    "assistant_evidence_sufficiency_rate": {"minimum": 0.95, "label": "Assistant evidence sufficiency"},
    "retrieval_expected_type_recall_mean": {"minimum": 0.95, "label": "Retrieval expected-type recall"},
    "resume_top3_url_hit_rate": {"minimum": 0.95, "label": "Resume top3 URL hit rate"},
    "resume_matched_skill_recall_mean": {"minimum": 0.95, "label": "Resume matched skill recall"},
    "resume_label_top1_best_label_hit_rate": {"minimum": 0.95, "label": "Resume label Top1 best-label hit"},
    "resume_label_pairwise_order_accuracy_mean": {"minimum": 0.95, "label": "Resume label pairwise order accuracy"},
    "resume_label_ndcg_at_3_mean": {"minimum": 0.85, "label": "Resume label nDCG@3"},
}

HUMAN_REVIEW_THRESHOLDS = {
    "reviewer_count": {"minimum": 2, "label": "Human review reviewer count"},
    "case_count": {"minimum": 8, "label": "Human review case count"},
    "grounding_score_mean": {"minimum": 4.0, "label": "Human review grounding mean"},
    "overall_score_mean": {"minimum": 4.0, "label": "Human review overall mean"},
    "pairwise_verdict_agreement_rate": {"minimum": 0.7, "label": "Human review verdict agreement"},
}

ASSISTANT_MODE_QUALITY_THRESHOLDS = {
    "market_summary": {
        "citation_keyword_recall_mean": {"minimum": 0.95, "label": "Market summary citation keyword recall"},
        "evidence_sufficiency_rate": {"minimum": 0.95, "label": "Market summary evidence sufficiency"},
    },
    "personalized_guidance": {
        "citation_keyword_recall_mean": {"minimum": 0.95, "label": "Personalized guidance citation keyword recall"},
        "evidence_sufficiency_rate": {"minimum": 0.95, "label": "Personalized guidance evidence sufficiency"},
    },
    "job_comparison": {
        "citation_keyword_recall_mean": {"minimum": 0.95, "label": "Job comparison citation keyword recall"},
        "evidence_sufficiency_rate": {"minimum": 0.95, "label": "Job comparison evidence sufficiency"},
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_json(path: Path) -> int:
    payload = _load_json(path)
    if isinstance(payload, list):
        return len(payload)
    raise TypeError(f"Expected list JSON at {path}")


def _count_jsonl(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def dataset_counts(fixtures_root: Path) -> dict[str, int]:
    return {
        "assistant_questions": _count_json(fixtures_root / "assistant_questions.json"),
        "resume_extraction_labels": _count_jsonl(fixtures_root / "resume_extraction_labels.jsonl"),
        "resume_match_labels": _count_jsonl(fixtures_root / "resume_match_labels.jsonl"),
    }


def build_training_readiness(
    *,
    ai_checks_summary_path: Path | None = None,
    assistant_summary_path: Path,
    retrieval_summary_path: Path,
    resume_summary_path: Path,
    resume_label_summary_path: Path,
    human_review_summary_path: Path | None = None,
    fixtures_root: Path,
) -> dict[str, Any]:
    ai_checks_summary = _load_json(ai_checks_summary_path) if ai_checks_summary_path else None
    assistant_summary = _load_json(assistant_summary_path)
    retrieval_summary = _load_json(retrieval_summary_path)
    resume_summary = _load_json(resume_summary_path)
    resume_label_summary = _load_json(resume_label_summary_path)
    human_review_summary = _load_json(human_review_summary_path) if human_review_summary_path else None

    snapshot_gate = (
        ai_checks_summary["real_snapshot"]["snapshot_health_gate"]
        if ai_checks_summary
        else assistant_summary["real_snapshot"]["snapshot_health_gate"]
    )
    assistant = assistant_summary["real_snapshot"]["assistant"]["aggregate"]
    assistant_modes = assistant_summary["real_snapshot"]["assistant"].get("mode_breakdown", {})
    retrieval = retrieval_summary["real_snapshot"]["retrieval"]["aggregate"]
    resume = resume_summary["real_snapshot"]["resume"]["aggregate"]
    resume_label = resume_label_summary["resume_label"]["aggregate"]

    counts = dataset_counts(fixtures_root)
    dataset_checks: list[dict[str, Any]] = []
    dataset_blocked = False
    for key, rule in DATASET_THRESHOLDS.items():
        actual = counts[key]
        passed = actual >= rule["minimum"]
        dataset_checks.append(
            {
                "key": key,
                "label": rule["label"],
                "actual": actual,
                "minimum": rule["minimum"],
                "passed": passed,
            }
        )
        if not passed:
            dataset_blocked = True

    assistant_mode_coverage_checks: list[dict[str, Any]] = []
    assistant_mode_coverage_blocked = False
    for mode, rule in ASSISTANT_MODE_COVERAGE.items():
        mode_bucket = assistant_modes.get(mode, {})
        actual = int(mode_bucket.get("case_count", 0) or 0)
        passed = actual >= rule["minimum_cases"]
        assistant_mode_coverage_checks.append(
            {
                "key": mode,
                "label": rule["label"],
                "actual": actual,
                "minimum": rule["minimum_cases"],
                "passed": passed,
            }
        )
        if not passed:
            assistant_mode_coverage_blocked = True

    metrics = {
        "assistant_citation_keyword_recall_mean": assistant.get("citation_keyword_recall_mean", 0.0),
        "assistant_evidence_sufficiency_rate": assistant.get("evidence_sufficiency_rate", 0.0),
        "retrieval_expected_type_recall_mean": retrieval.get("expected_type_recall_mean", 0.0),
        "resume_top3_url_hit_rate": resume.get("top3_url_hit_rate", 0.0),
        "resume_matched_skill_recall_mean": resume.get("matched_skill_recall_mean", 0.0),
        "resume_label_top1_best_label_hit_rate": resume_label.get("top1_best_label_hit_rate", 0.0),
        "resume_label_pairwise_order_accuracy_mean": resume_label.get("pairwise_order_accuracy_mean", 0.0),
        "resume_label_ndcg_at_3_mean": resume_label.get("ndcg_at_3_mean", 0.0),
    }

    quality_checks: list[dict[str, Any]] = []
    failed_quality: list[str] = []
    for key, rule in QUALITY_THRESHOLDS.items():
        actual = float(metrics[key])
        passed = actual >= rule["minimum"]
        quality_checks.append(
            {
                "key": key,
                "label": rule["label"],
                "actual": round(actual, 4),
                "minimum": rule["minimum"],
                "passed": passed,
            }
        )
        if not passed:
            failed_quality.append(rule["label"])

    assistant_mode_quality_checks: list[dict[str, Any]] = []
    failed_mode_quality: list[str] = []
    for mode, metric_rules in ASSISTANT_MODE_QUALITY_THRESHOLDS.items():
        mode_bucket = assistant_modes.get(mode, {})
        for metric_key, rule in metric_rules.items():
            actual = float(mode_bucket.get(metric_key, 0.0) or 0.0)
            passed = actual >= rule["minimum"]
            assistant_mode_quality_checks.append(
                {
                    "key": f"{mode}_{metric_key}",
                    "label": rule["label"],
                    "actual": round(actual, 4),
                    "minimum": rule["minimum"],
                    "passed": passed,
                    "mode": mode,
                }
            )
            if not passed:
                failed_mode_quality.append(rule["label"])

    assistant_mode_gate = {
        "status": "PASS" if not assistant_mode_coverage_blocked and not failed_mode_quality else "FAIL",
        "coverage_checks": assistant_mode_coverage_checks,
        "quality_checks": assistant_mode_quality_checks,
        "failed_labels": failed_mode_quality,
    }

    human_review_gate: dict[str, Any]
    failed_human_review: list[str] = []
    if human_review_summary is None or human_review_summary.get("mode") != "formal_human_review":
        human_review_gate = {
            "status": "PENDING",
            "checks": [],
            "failed_labels": [],
            "summary_path": str(human_review_summary_path) if human_review_summary_path else None,
        }
    else:
        human_review = human_review_summary.get("aggregate", {})
        human_review_checks: list[dict[str, Any]] = []
        for key, rule in HUMAN_REVIEW_THRESHOLDS.items():
            actual = float(human_review.get(key, 0.0) or 0.0)
            passed = actual >= rule["minimum"]
            human_review_checks.append(
                {
                    "key": key,
                    "label": rule["label"],
                    "actual": round(actual, 4),
                    "minimum": rule["minimum"],
                    "passed": passed,
                }
            )
            if not passed:
                failed_human_review.append(rule["label"])
        human_review_gate = {
            "status": "PASS" if not failed_human_review else "FAIL",
            "checks": human_review_checks,
            "failed_labels": failed_human_review,
            "summary_path": str(human_review_summary_path),
        }

    if snapshot_gate["status"] != "READY" or dataset_blocked or assistant_mode_coverage_blocked:
        status = "BLOCKED"
        verdict = "評估覆蓋不足，現在不應進行 fine-tuning。先補資料、補齊 answer mode 覆蓋，或先讓 snapshot gate 變成 READY。"
    elif not failed_quality and not failed_mode_quality and not failed_human_review:
        status = "DEFER"
        verdict = "品質面已達標，現在沒有足夠證據支持 fine-tuning。應先優化 latency、監控與產品整合。"
    else:
        status = "READY"
        verdict = "資料與評估覆蓋已足夠，且仍存在穩定品質缺口，可以開始小範圍 fine-tuning 試驗。"

    return {
        "status": status,
        "verdict": verdict,
        "assistant_summary_path": str(assistant_summary_path),
        "ai_checks_summary_path": str(ai_checks_summary_path) if ai_checks_summary_path else None,
        "retrieval_summary_path": str(retrieval_summary_path),
        "resume_summary_path": str(resume_summary_path),
        "resume_label_summary_path": str(resume_label_summary_path),
        "human_review_summary_path": str(human_review_summary_path) if human_review_summary_path else None,
        "snapshot_health_gate": snapshot_gate,
        "dataset_checks": dataset_checks,
        "quality_checks": quality_checks,
        "assistant_mode_gate": assistant_mode_gate,
        "human_review_gate": human_review_gate,
        "assistant_mode_observations": assistant_modes,
        "failed_quality_labels": failed_quality + failed_mode_quality + failed_human_review,
        "latency_observations": {
            "assistant_total_ms_mean": round(float(assistant.get("total_ms_mean", 0.0)), 3),
            "resume_total_ms_mean": round(float(resume.get("total_ms_mean", 0.0)), 3),
            "resume_build_profile_ms_mean": round(float(resume.get("build_profile_ms_mean", 0.0)), 3),
            "resume_match_jobs_ms_mean": round(float(resume.get("match_jobs_ms_mean", 0.0)), 3),
        },
        "resume_label_observations": {
            "top1_best_label_hit_rate": round(float(resume_label.get("top1_best_label_hit_rate", 0.0)), 4),
            "top3_relevant_recall_mean": round(float(resume_label.get("top3_relevant_recall_mean", 0.0)), 4),
            "pairwise_order_accuracy_mean": round(float(resume_label.get("pairwise_order_accuracy_mean", 0.0)), 4),
            "ndcg_at_3_mean": round(float(resume_label.get("ndcg_at_3_mean", 0.0)), 4),
        },
    }


def _format_checks(items: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for item in items:
        label = item["label"]
        actual = item["actual"]
        minimum = item["minimum"]
        verdict = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {label}：`{actual}` / 門檻 `>= {minimum}` {verdict}")
    return "\n".join(lines)


def build_training_readiness_report(summary: dict[str, Any]) -> str:
    gate = summary["snapshot_health_gate"]
    mode_gate = summary["assistant_mode_gate"]
    human_review_gate = summary["human_review_gate"]
    latency = summary["latency_observations"]
    return f"""# Job Radar Training Readiness

## 結論
- Gate 狀態：`{summary['status']}`
- Assistant mode gate：`{mode_gate['status']}`
- Human review gate：`{human_review_gate['status']}`
- 判斷：{summary['verdict']}

## Snapshot Health Gate
- 狀態：`{gate['status']}`
- 判斷：{gate['verdict']}
{_format_checks(gate['checks'])}

## Dataset Coverage
{_format_checks(summary['dataset_checks'])}

## Quality Checks
{_format_checks(summary['quality_checks'])}

## Assistant Mode Coverage
{_format_checks(mode_gate['coverage_checks'])}

## Assistant Mode Quality
{_format_checks(mode_gate['quality_checks'])}

## Human Review Gate
{_format_checks(human_review_gate['checks']) if human_review_gate['checks'] else '- 尚未提供正式 human review summary。'}

## Latency Observations
- Assistant total mean：`{latency['assistant_total_ms_mean']} ms`
- Resume total mean：`{latency['resume_total_ms_mean']} ms`
- Resume build_profile mean：`{latency['resume_build_profile_ms_mean']} ms`
- Resume match_jobs mean：`{latency['resume_match_jobs_ms_mean']} ms`

## Resume Label Observations
- Top1 best-label hit：`{summary['resume_label_observations']['top1_best_label_hit_rate']}`
- Top3 relevant recall：`{summary['resume_label_observations']['top3_relevant_recall_mean']}`
- Pairwise order accuracy：`{summary['resume_label_observations']['pairwise_order_accuracy_mean']}`
- nDCG@3：`{summary['resume_label_observations']['ndcg_at_3_mean']}`

## Source Summaries
- AI checks summary：`{summary['ai_checks_summary_path']}`
- Assistant summary：`{summary['assistant_summary_path']}`
- Retrieval summary：`{summary['retrieval_summary_path']}`
- Resume summary：`{summary['resume_summary_path']}`
- Resume label summary：`{summary['resume_label_summary_path']}`
- Human review summary：`{summary['human_review_summary_path']}`
"""
