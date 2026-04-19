"""人工評分檔驗證。"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .human_review import ASSISTANT_BLIND_FIELDS


REVIEWER_EDITABLE_FIELDS = {
    "reviewer_id",
    "correctness_score",
    "grounding_score",
    "usefulness_score",
    "clarity_score",
    "overall_score",
    "verdict",
    "notes",
}
ALLOWED_VERDICTS = {"accept", "minor_issue", "major_issue", "reject"}
SCORE_FIELDS = [
    "correctness_score",
    "grounding_score",
    "usefulness_score",
    "clarity_score",
    "overall_score",
]


@dataclass(slots=True)
class HumanReviewValidationIssue:
    severity: str
    code: str
    row_index: int | None
    message: str


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _parse_score(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return int(round(float(text)))
    except ValueError:
        return None


def _normalize_verdict(value: Any) -> str:
    text = str(value or "").strip().lower().replace(" ", "_")
    return text


def validate_human_review_csv(
    path: Path,
    *,
    require_completed: bool = False,
) -> dict[str, Any]:
    fieldnames, rows = _load_csv(path)
    issues: list[HumanReviewValidationIssue] = []

    missing_columns = [column for column in ASSISTANT_BLIND_FIELDS if column not in fieldnames]
    extra_columns = [column for column in fieldnames if column not in ASSISTANT_BLIND_FIELDS]
    if missing_columns:
        issues.append(
            HumanReviewValidationIssue(
                severity="error",
                code="missing_columns",
                row_index=None,
                message=f"缺少欄位：{', '.join(missing_columns)}",
            )
        )

    review_ids: set[str] = set()
    reviewer_ids: set[str] = set()
    duplicate_review_ids: list[str] = []

    for index, row in enumerate(rows, start=1):
        review_id = str(row.get("review_id", "")).strip()
        if not review_id:
            issues.append(
                HumanReviewValidationIssue(
                    severity="error",
                    code="missing_review_id",
                    row_index=index,
                    message="review_id 不可為空。",
                )
            )
        elif review_id in review_ids:
            duplicate_review_ids.append(review_id)
        else:
            review_ids.add(review_id)

        reviewer_id = str(row.get("reviewer_id", "")).strip()
        if reviewer_id:
            reviewer_ids.add(reviewer_id)

        if require_completed and not reviewer_id:
            issues.append(
                HumanReviewValidationIssue(
                    severity="error",
                    code="missing_reviewer_id",
                    row_index=index,
                    message="正式 reviewer submission 必須填 reviewer_id。",
                )
            )

        for field in SCORE_FIELDS:
            score = _parse_score(row.get(field))
            if require_completed and score is None:
                issues.append(
                    HumanReviewValidationIssue(
                        severity="error",
                        code="missing_score",
                        row_index=index,
                        message=f"{field} 未填。",
                    )
                )
                continue
            if score is not None and not 1 <= score <= 5:
                issues.append(
                    HumanReviewValidationIssue(
                        severity="error",
                        code="invalid_score_range",
                        row_index=index,
                        message=f"{field} 必須介於 1 到 5。",
                    )
                )

        verdict = _normalize_verdict(row.get("verdict", ""))
        if require_completed and verdict not in ALLOWED_VERDICTS:
            issues.append(
                HumanReviewValidationIssue(
                    severity="error",
                    code="invalid_verdict",
                    row_index=index,
                    message=f"verdict 必須是 {', '.join(sorted(ALLOWED_VERDICTS))} 之一。",
                )
            )

    if duplicate_review_ids:
        issues.append(
            HumanReviewValidationIssue(
                severity="error",
                code="duplicate_review_id",
                row_index=None,
                message=f"review_id 重複：{', '.join(sorted(set(duplicate_review_ids)))}",
            )
        )

    if require_completed and len(reviewer_ids) > 1:
        issues.append(
            HumanReviewValidationIssue(
                severity="error",
                code="multiple_reviewer_ids",
                row_index=None,
                message=f"單一 reviewer submission 只能有一個 reviewer_id，實際收到：{', '.join(sorted(reviewer_ids))}",
            )
        )

    structure_ok = not any(issue.severity == "error" for issue in issues if issue.code in {"missing_columns", "missing_review_id", "duplicate_review_id"})
    content_ok = not any(issue.severity == "error" for issue in issues if issue.code not in {"missing_columns", "missing_review_id", "duplicate_review_id"})
    status = "PASS" if not issues else ("FAIL" if any(issue.severity == "error" for issue in issues) else "WARN")

    return {
        "path": str(path.resolve()),
        "require_completed": require_completed,
        "row_count": len(rows),
        "field_count": len(fieldnames),
        "missing_columns": missing_columns,
        "extra_columns": extra_columns,
        "reviewer_ids": sorted(reviewer_ids),
        "structure_ok": structure_ok,
        "content_ok": content_ok,
        "status": status,
        "issues": [asdict(issue) for issue in issues],
    }
