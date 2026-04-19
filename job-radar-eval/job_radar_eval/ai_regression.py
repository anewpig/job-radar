from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import EvalConfig
from .latency_regression import (
    build_latency_regression,
    build_latency_regression_report,
)
from .training_readiness import (
    ASSISTANT_MODE_COVERAGE,
    build_training_readiness,
    build_training_readiness_report,
)
from .reporting import _render_mode_breakdown_markdown, write_json


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_result_summaries(results_dir: Path, prefix: str):
    for run_dir in sorted(results_dir.glob(f"{prefix}_*"), reverse=True):
        summary_path = run_dir / "summary.json"
        if summary_path.exists():
            yield summary_path


def _has_component(summary: dict[str, Any], component: str) -> bool:
    aggregate = summary.get("real_snapshot", {}).get(component, {}).get("aggregate", {})
    return bool(aggregate)


def _assistant_modes_complete(summary: dict[str, Any]) -> bool:
    mode_breakdown = summary.get("real_snapshot", {}).get("assistant", {}).get("mode_breakdown", {})
    if not mode_breakdown:
        return False
    for mode, rule in ASSISTANT_MODE_COVERAGE.items():
        case_count = int(mode_breakdown.get(mode, {}).get("case_count", 0) or 0)
        if case_count < int(rule["minimum_cases"]):
            return False
    return True


def _latest_real_model_summary(results_dir: Path, component: str) -> Path:
    fallback: Path | None = None
    for summary_path in _iter_result_summaries(results_dir, "real_model_eval"):
        try:
            summary = _load_json(summary_path)
        except Exception:
            continue
        if not _has_component(summary, component):
            continue
        if fallback is None:
            fallback = summary_path
        if component == "assistant":
            if _assistant_modes_complete(summary):
                return summary_path
            continue
        return summary_path
    if fallback is not None:
        return fallback
    raise FileNotFoundError(f"No real_model_eval summary found for component={component}")


def _latest_prefixed_summary(results_dir: Path, prefix: str) -> Path:
    for summary_path in _iter_result_summaries(results_dir, prefix):
        return summary_path
    raise FileNotFoundError(f"No summary found for prefix={prefix}")


def _latest_resume_label_summary(results_dir: Path) -> Path:
    fallback: Path | None = None
    for summary_path in _iter_result_summaries(results_dir, "resume_label_eval"):
        if fallback is None:
            fallback = summary_path
        try:
            summary = _load_json(summary_path)
        except Exception:
            continue
        aggregate = summary.get("resume_label", {}).get("aggregate", {})
        case_count = int(aggregate.get("case_count", 0) or 0)
        label_count = int(aggregate.get("label_count", 0) or 0)
        if case_count >= 10 and label_count >= 20:
            return summary_path
    if fallback:
        return fallback
    raise FileNotFoundError("No summary found for prefix=resume_label_eval")


def _latest_human_review_summary(results_dir: Path) -> Path | None:
    fallback: Path | None = None
    for summary_path in _iter_result_summaries(results_dir, "formal_human_review"):
        if fallback is None:
            fallback = summary_path
        try:
            summary = _load_json(summary_path)
        except Exception:
            continue
        aggregate = summary.get("aggregate", {})
        if summary.get("mode") != "formal_human_review":
            continue
        reviewer_count = int(aggregate.get("reviewer_count", 0) or 0)
        case_count = int(aggregate.get("case_count", 0) or 0)
        if reviewer_count >= 2 and case_count >= 8:
            return summary_path
    if fallback is not None:
        return fallback
    return None


def resolve_regression_sources(
    *,
    config: EvalConfig,
    ai_checks_summary_path: Path | None = None,
    assistant_summary_path: Path | None = None,
    retrieval_summary_path: Path | None = None,
    resume_summary_path: Path | None = None,
    resume_label_summary_path: Path | None = None,
    resume_warm_summary_path: Path | None = None,
    human_review_summary_path: Path | None = None,
) -> dict[str, Path]:
    results_dir = config.results_dir
    resolved_human_review = human_review_summary_path.resolve() if human_review_summary_path else _latest_human_review_summary(results_dir)
    return {
        "ai_checks_summary": ai_checks_summary_path.resolve() if ai_checks_summary_path else _latest_prefixed_summary(results_dir, "ai_checks"),
        "assistant_summary": assistant_summary_path.resolve() if assistant_summary_path else _latest_real_model_summary(results_dir, "assistant"),
        "retrieval_summary": retrieval_summary_path.resolve() if retrieval_summary_path else _latest_real_model_summary(results_dir, "retrieval"),
        "resume_summary": resume_summary_path.resolve() if resume_summary_path else _latest_real_model_summary(results_dir, "resume"),
        "resume_label_summary": resume_label_summary_path.resolve() if resume_label_summary_path else _latest_resume_label_summary(results_dir),
        "resume_warm_summary": resume_warm_summary_path.resolve() if resume_warm_summary_path else _latest_prefixed_summary(results_dir, "resume_warm_probe"),
        "human_review_summary": resolved_human_review,
    }


def build_ai_regression_bundle(
    *,
    config: EvalConfig,
    sources: dict[str, Path],
    fixtures_root: Path | None = None,
) -> dict[str, Any]:
    fixtures_root = fixtures_root.resolve() if fixtures_root else config.fixtures_dir
    ai_checks_summary = _load_json(sources["ai_checks_summary"])
    latency_summary = build_latency_regression(
        assistant_summary_path=sources["assistant_summary"],
        retrieval_summary_path=sources["retrieval_summary"],
        resume_summary_path=sources["resume_summary"],
        resume_warm_summary_path=sources["resume_warm_summary"],
    )
    training_summary = build_training_readiness(
        ai_checks_summary_path=sources["ai_checks_summary"],
        assistant_summary_path=sources["assistant_summary"],
        retrieval_summary_path=sources["retrieval_summary"],
        resume_summary_path=sources["resume_summary"],
        resume_label_summary_path=sources["resume_label_summary"],
        human_review_summary_path=sources.get("human_review_summary"),
        fixtures_root=fixtures_root,
    )
    assistant_summary = _load_json(sources["assistant_summary"])
    assistant_mode_breakdown = assistant_summary.get("real_snapshot", {}).get("assistant", {}).get("mode_breakdown", {})
    return {
        "mode": "ai_regression",
        "project_root": str(config.project_root),
        "fixtures_root": str(fixtures_root),
        "source_paths": {key: str(path) for key, path in sources.items()},
        "ai_checks": {
            "summary_path": str(sources["ai_checks_summary"]),
            "snapshot_health_gate": ai_checks_summary.get("real_snapshot", {}).get("snapshot_health_gate", {}),
        },
        "assistant_real_model": {
            "summary_path": str(sources["assistant_summary"]),
            "mode_breakdown": assistant_mode_breakdown,
            "mode_gate_status": training_summary["assistant_mode_gate"]["status"],
        },
        "human_review": {
            "summary_path": str(sources["human_review_summary"]) if sources.get("human_review_summary") else None,
            "gate_status": training_summary["human_review_gate"]["status"],
        },
        "latency_regression": latency_summary,
        "training_readiness": training_summary,
    }


def build_ai_regression_report(summary: dict[str, Any]) -> str:
    ai_checks_gate = summary["ai_checks"].get("snapshot_health_gate", {})
    assistant_real_model = summary["assistant_real_model"]
    human_review = summary["human_review"]
    latency = summary["latency_regression"]
    training = summary["training_readiness"]
    source_lines = chr(10).join(
        f"- {key}: `{value}`" for key, value in summary["source_paths"].items()
    )
    snapshot_gate_status = ai_checks_gate.get("status", "UNKNOWN")
    snapshot_gate_verdict = ai_checks_gate.get("verdict", "")
    return f"""# Job Radar AI Regression Bundle

## 結論
- Snapshot health gate: `{snapshot_gate_status}`
- Assistant mode gate: `{assistant_real_model['mode_gate_status']}`
- Human review gate: `{human_review['gate_status']}`
- Latency regression: `{latency['status']}`
- Training readiness: `{training['status']}`

## Snapshot Health
- 判斷：{snapshot_gate_verdict}

## Assistant Real-Model Modes
{_render_mode_breakdown_markdown('Assistant real-model mode breakdown', assistant_real_model.get('mode_breakdown'))}

## Latency Regression
- 判斷：{latency['verdict']}

## Training Readiness
- 判斷：{training['verdict']}

## Embedded Reports

### Latency Regression
{build_latency_regression_report(latency)}

### Training Readiness
{build_training_readiness_report(training)}

## Source Summaries
{source_lines}
"""


def write_ai_regression_bundle(*, run_dir: Path, summary: dict[str, Any]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "summary.json", summary)
    (run_dir / "report.md").write_text(build_ai_regression_report(summary), encoding="utf-8")
