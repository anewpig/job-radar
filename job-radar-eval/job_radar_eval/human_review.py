"""人工評分 packet 生成。"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import EvalConfig
from .experiment_artifacts import write_jsonl
from .reporting import build_run_dir, write_csv, write_json


ASSISTANT_RESEARCH_FIELDS = [
    "review_id",
    "source_path",
    "source_run",
    "case_id",
    "question",
    "answer",
    "summary",
    "key_points",
    "limitations",
    "next_step",
    "citation_count",
    "top_citation_type",
    "citation_labels",
    "citation_snippets",
    "auto_total_ms",
    "auto_citation_keyword_recall",
    "auto_evidence_sufficient",
    "auto_issue_priority",
    "reviewer_id",
    "correctness_score",
    "grounding_score",
    "usefulness_score",
    "clarity_score",
    "overall_score",
    "verdict",
    "notes",
]

ASSISTANT_BLIND_FIELDS = [
    "review_id",
    "case_id",
    "question",
    "answer",
    "summary",
    "key_points",
    "limitations",
    "next_step",
    "citation_count",
    "citation_labels",
    "citation_snippets",
    "reviewer_id",
    "correctness_score",
    "grounding_score",
    "usefulness_score",
    "clarity_score",
    "overall_score",
    "verdict",
    "notes",
]


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def _iter_real_model_assistant_case_files(results_dir: Path):
    for run_dir in sorted(results_dir.glob("real_model_eval_*"), reverse=True):
        for candidate in [
            run_dir / "real_snapshot" / "assistant_cases.jsonl",
            run_dir / "real_snapshot" / "assistant_cases.csv",
            run_dir / "fixture" / "assistant_cases.jsonl",
            run_dir / "fixture" / "assistant_cases.csv",
        ]:
            if candidate.exists():
                yield candidate


def resolve_latest_assistant_cases(config: EvalConfig) -> Path:
    for path in _iter_real_model_assistant_case_files(config.results_dir):
        if not path.exists() or path.stat().st_size == 0:
            continue
        try:
            rows = _load_rows(path)
        except Exception:
            continue
        if rows:
            return path
    raise FileNotFoundError("找不到可用的 assistant case export。")


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _issue_priority(row: dict[str, Any]) -> int:
    score = 0
    if not _to_bool(row.get("citation_ok", True)):
        score += 3
    if not _to_bool(row.get("evidence_sufficient", True)):
        score += 2
    if _to_float(row.get("citation_keyword_recall", 1.0), 1.0) < 1.0:
        score += 2
    if not _to_bool(row.get("structured_output", True)):
        score += 2
    total_ms = _to_float(row.get("total_ms", 0.0), 0.0)
    if total_ms >= 6000:
        score += 1
    return score


def build_assistant_review_rows(
    *,
    source_path: Path,
    rows: list[dict[str, Any]],
    limit: int | None = None,
    case_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    normalized_case_ids = {
        str(case_id).strip()
        for case_id in (case_ids or [])
        if str(case_id).strip()
    }
    for row in rows:
        case_id = str(row.get("case_id", "")).strip() or "unknown_case"
        if normalized_case_ids and case_id not in normalized_case_ids:
            continue
        current = deduped.get(case_id)
        row_priority = _issue_priority(row)
        if current is None:
            deduped[case_id] = dict(row)
            continue
        current_priority = _issue_priority(current)
        current_iteration = int(current.get("iteration", 0) or 0)
        row_iteration = int(row.get("iteration", 0) or 0)
        if (row_priority, row_iteration) > (current_priority, current_iteration):
            deduped[case_id] = dict(row)

    selected = sorted(
        deduped.values(),
        key=lambda item: (
            -_issue_priority(item),
            item.get("case_id", ""),
        ),
    )
    if limit is not None:
        selected = selected[:limit]

    review_rows: list[dict[str, Any]] = []
    source_run = source_path.parent.name
    for index, row in enumerate(selected, start=1):
        answer = str(row.get("answer", "") or "").strip()
        summary = str(row.get("summary", "") or "").strip()
        review_rows.append(
            {
                "review_id": f"assistant-{index:03d}",
                "source_path": str(source_path.resolve()),
                "source_run": source_run,
                "case_id": row.get("case_id", ""),
                "question": row.get("question", ""),
                "answer": answer or summary,
                "summary": summary,
                "key_points": row.get("key_points", ""),
                "limitations": row.get("limitations", ""),
                "next_step": row.get("next_step", ""),
                "citation_count": row.get("citation_count", ""),
                "top_citation_type": row.get("top_citation_type", ""),
                "citation_labels": row.get("citation_labels", ""),
                "citation_snippets": row.get("citation_snippets", ""),
                "auto_total_ms": row.get("total_ms", ""),
                "auto_citation_keyword_recall": row.get("citation_keyword_recall", ""),
                "auto_evidence_sufficient": row.get("evidence_sufficient", ""),
                "auto_issue_priority": _issue_priority(row),
                "reviewer_id": "",
                "correctness_score": "",
                "grounding_score": "",
                "usefulness_score": "",
                "clarity_score": "",
                "overall_score": "",
                "verdict": "",
                "notes": "",
            }
        )
    return review_rows


def write_assistant_review_packet(
    *,
    config: EvalConfig,
    source_path: Path,
    rows: list[dict[str, Any]],
    limit: int | None = None,
    case_ids: list[str] | None = None,
    run_dir: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    review_rows = build_assistant_review_rows(
        source_path=source_path,
        rows=rows,
        limit=limit,
        case_ids=case_ids,
    )
    run_dir = run_dir or build_run_dir(config.results_dir, prefix="human_review_packet")
    run_dir.mkdir(parents=True, exist_ok=True)

    blind_csv_rows = [{field: row.get(field, "") for field in ASSISTANT_BLIND_FIELDS} for row in review_rows]
    research_csv_rows = [{field: row.get(field, "") for field in ASSISTANT_RESEARCH_FIELDS} for row in review_rows]
    blind_csv_path = run_dir / "assistant_review_packet_blind.csv"
    blind_jsonl_path = run_dir / "assistant_review_packet_blind.jsonl"
    research_csv_path = run_dir / "assistant_review_packet_research.csv"
    research_jsonl_path = run_dir / "assistant_review_packet_research.jsonl"
    summary_path = run_dir / "summary.json"

    write_csv(blind_csv_path, blind_csv_rows)
    write_jsonl(blind_jsonl_path, blind_csv_rows)
    write_csv(research_csv_path, research_csv_rows)
    write_jsonl(research_jsonl_path, research_csv_rows)
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "human_review_packet",
        "review_type": "assistant",
        "source_path": str(source_path.resolve()),
        "packet_size": len(review_rows),
        "case_ids": [str(case_id).strip() for case_id in (case_ids or []) if str(case_id).strip()],
        "blind_csv_path": str(blind_csv_path.resolve()),
        "blind_jsonl_path": str(blind_jsonl_path.resolve()),
        "research_csv_path": str(research_csv_path.resolve()),
        "research_jsonl_path": str(research_jsonl_path.resolve()),
    }
    write_json(summary_path, summary)
    return run_dir, summary


def resolve_latest_human_review_packet(config: EvalConfig) -> Path:
    for run_dir in sorted(config.results_dir.glob("human_review_packet_*"), reverse=True):
        summary_path = run_dir / "summary.json"
        if summary_path.exists():
            return summary_path
    raise FileNotFoundError("找不到可用的 human review packet summary。")


def write_formal_reviewer_bundle(
    *,
    config: EvalConfig,
    packet_summary_path: Path,
    reviewer_ids: list[str],
    run_dir: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    packet_summary = json.loads(packet_summary_path.read_text(encoding="utf-8"))
    blind_csv_path = Path(packet_summary["blind_csv_path"]).resolve()
    blind_jsonl_path = Path(packet_summary["blind_jsonl_path"]).resolve()
    rubric_path = (config.fixtures_dir.parent / "docs" / "human_review_rubric.md").resolve()
    workflow_path = (config.fixtures_dir.parent / "docs" / "formal_human_review_workflow.md").resolve()
    invitation_path = (config.fixtures_dir.parent / "docs" / "reviewer_invitation_template.md").resolve()
    blind_rows = _load_rows(blind_csv_path)

    run_dir = run_dir or build_run_dir(config.results_dir, prefix="formal_reviewer_bundle")
    run_dir.mkdir(parents=True, exist_ok=True)

    reviewer_files: list[dict[str, Any]] = []
    for reviewer_id in reviewer_ids:
        reviewer_rows: list[dict[str, Any]] = []
        for row in blind_rows:
            reviewer_row = dict(row)
            reviewer_row["reviewer_id"] = reviewer_id
            reviewer_rows.append(reviewer_row)
        reviewer_csv_path = run_dir / f"assistant_review_{reviewer_id}.csv"
        reviewer_jsonl_path = run_dir / f"assistant_review_{reviewer_id}.jsonl"
        write_csv(reviewer_csv_path, reviewer_rows)
        write_jsonl(reviewer_jsonl_path, reviewer_rows)
        reviewer_files.append(
            {
                "reviewer_id": reviewer_id,
                "csv_path": str(reviewer_csv_path.resolve()),
                "jsonl_path": str(reviewer_jsonl_path.resolve()),
            }
        )

    rubric_copy_path = run_dir / "human_review_rubric.md"
    workflow_copy_path = run_dir / "formal_human_review_workflow.md"
    invitation_copy_path = run_dir / "reviewer_invitation_template.md"
    rubric_copy_path.write_text(rubric_path.read_text(encoding="utf-8"), encoding="utf-8")
    workflow_copy_path.write_text(workflow_path.read_text(encoding="utf-8"), encoding="utf-8")
    invitation_copy_path.write_text(invitation_path.read_text(encoding="utf-8"), encoding="utf-8")

    readme_path = run_dir / "README.md"
    reviewer_line = ", ".join(f"`{item}`" for item in reviewer_ids)
    file_lines = "\n".join(
        f"- `{Path(item['csv_path']).name}`" for item in reviewer_files
    )
    readme_path.write_text(
        "\n".join(
            [
                "# Formal Reviewer Bundle",
                "",
                "這份 bundle 可直接發給 reviewer。",
                "",
                f"Reviewer IDs：{reviewer_line}",
                "",
                "## 內容",
                file_lines,
                "- `human_review_rubric.md`",
                "- `formal_human_review_workflow.md`",
                "- `reviewer_invitation_template.md`",
                "",
                "## 使用方式",
                "1. 每位 reviewer 只拿自己的 CSV。",
                "2. 評分規則看 `human_review_rubric.md`。",
                "3. 發送文字可直接參考 `reviewer_invitation_template.md`。",
                "4. 回收後用 `run_formal_human_review.py` 做正式彙整。",
                "",
            ]
        ),
        encoding="utf-8",
    )

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "formal_reviewer_bundle",
        "packet_summary_path": str(packet_summary_path.resolve()),
        "packet_size": len(blind_rows),
        "reviewer_ids": reviewer_ids,
        "reviewer_files": reviewer_files,
        "rubric_path": str(rubric_copy_path.resolve()),
        "workflow_path": str(workflow_copy_path.resolve()),
        "invitation_template_path": str(invitation_copy_path.resolve()),
        "readme_path": str(readme_path.resolve()),
    }
    write_json(run_dir / "summary.json", summary)
    return run_dir, summary
