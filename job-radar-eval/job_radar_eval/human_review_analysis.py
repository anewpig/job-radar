"""人工評分結果彙整。"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

from .metrics import average


SCORE_COLUMNS = [
    "correctness_score",
    "grounding_score",
    "usefulness_score",
    "clarity_score",
    "overall_score",
]


@dataclass(slots=True)
class HumanReviewCaseSummary:
    case_id: str
    review_count: int
    reviewer_count: int
    correctness_score_mean: float
    grounding_score_mean: float
    usefulness_score_mean: float
    clarity_score_mean: float
    overall_score_mean: float
    verdict_majority: str
    verdict_agreement_rate: float
    overall_score_range: float
    notes_count: int


@dataclass(slots=True)
class HumanReviewReviewerSummary:
    reviewer_id: str
    review_count: int
    overlap_review_count: int
    correctness_score_mean: float
    grounding_score_mean: float
    usefulness_score_mean: float
    clarity_score_mean: float
    overall_score_mean: float
    accept_like_rate: float
    reject_rate: float


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _normalize_verdict(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _is_reviewed(row: dict[str, Any]) -> bool:
    if str(row.get("reviewer_id", "")).strip():
        return True
    if _normalize_verdict(row.get("verdict", "")):
        return True
    return any(_to_float(row.get(column)) is not None for column in SCORE_COLUMNS)


def load_review_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                normalized = dict(row)
                normalized["_source_path"] = str(path.resolve())
                rows.append(normalized)
    return rows


def _safe_round(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 4)


def _cohens_kappa(labels_a: list[str], labels_b: list[str]) -> float | None:
    if len(labels_a) != len(labels_b) or not labels_a:
        return None
    observed = average(
        [1.0 if left == right else 0.0 for left, right in zip(labels_a, labels_b, strict=True)]
    )
    categories = sorted(set(labels_a) | set(labels_b))
    if not categories:
        return None
    dist_a = {category: labels_a.count(category) / len(labels_a) for category in categories}
    dist_b = {category: labels_b.count(category) / len(labels_b) for category in categories}
    expected = sum(dist_a[category] * dist_b[category] for category in categories)
    if expected >= 0.999999:
        return 1.0
    return (observed - expected) / (1.0 - expected)


def build_human_review_tables(summary: dict[str, Any]) -> str:
    aggregate = summary["aggregate"]
    reviewer_rows = summary.get("reviewer_rows", [])
    case_rows = summary.get("case_rows", [])

    reviewer_table_lines = [
        "| Reviewer | Reviews | Overlap Reviews | Overall Mean | Accept-like Rate | Reject Rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in reviewer_rows:
        reviewer_table_lines.append(
            "| {reviewer_id} | {review_count} | {overlap_review_count} | {overall_score_mean} | {accept_like_rate} | {reject_rate} |".format(
                **row
            )
        )
    if len(reviewer_table_lines) == 2:
        reviewer_table_lines.append("| - | 0 | 0 | 0 | 0 | 0 |")

    case_preview_lines = [
        "| Case ID | Reviews | Majority Verdict | Agreement Rate | Overall Mean | Score Range |",
        "| --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for row in case_rows[:10]:
        case_preview_lines.append(
            "| {case_id} | {review_count} | {verdict_majority} | {verdict_agreement_rate} | {overall_score_mean} | {overall_score_range} |".format(
                **row
            )
        )
    if len(case_preview_lines) == 2:
        case_preview_lines.append("| - | 0 | - | 0 | 0 | 0 |")

    kappa_display = aggregate.get("cohens_kappa_verdict")
    if kappa_display is None:
        kappa_text = "N/A"
    else:
        kappa_text = str(kappa_display)

    return f"""# Human Review Thesis Tables

## Aggregate Table

| Metric | Value |
| --- | ---: |
| Reviewed Rows | {aggregate['reviewed_row_count']} |
| Reviewer Count | {aggregate['reviewer_count']} |
| Case Count | {aggregate['case_count']} |
| Overlap Case Count | {aggregate['overlap_case_count']} |
| Correctness Mean | {aggregate['correctness_score_mean']} |
| Grounding Mean | {aggregate['grounding_score_mean']} |
| Usefulness Mean | {aggregate['usefulness_score_mean']} |
| Clarity Mean | {aggregate['clarity_score_mean']} |
| Overall Mean | {aggregate['overall_score_mean']} |
| Mean Verdict Agreement Rate | {aggregate['mean_verdict_agreement_rate']} |
| Pairwise Verdict Agreement Rate | {aggregate['pairwise_verdict_agreement_rate']} |
| Pairwise Overall Score MAE | {aggregate['pairwise_overall_score_mae']} |
| Cohen's Kappa (Verdict) | {kappa_text} |
| Mean Overall Score Range | {aggregate['mean_overall_score_range']} |

## Reviewer Table
{chr(10).join(reviewer_table_lines)}

## Case Preview Table
{chr(10).join(case_preview_lines)}
"""


def _latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def build_human_review_latex_tables(summary: dict[str, Any]) -> str:
    aggregate = summary["aggregate"]
    reviewer_rows = summary.get("reviewer_rows", [])
    case_rows = summary.get("case_rows", [])

    aggregate_rows = [
        ("Reviewed Rows", aggregate["reviewed_row_count"]),
        ("Reviewer Count", aggregate["reviewer_count"]),
        ("Case Count", aggregate["case_count"]),
        ("Overlap Case Count", aggregate["overlap_case_count"]),
        ("Correctness Mean", aggregate["correctness_score_mean"]),
        ("Grounding Mean", aggregate["grounding_score_mean"]),
        ("Usefulness Mean", aggregate["usefulness_score_mean"]),
        ("Clarity Mean", aggregate["clarity_score_mean"]),
        ("Overall Mean", aggregate["overall_score_mean"]),
        ("Mean Verdict Agreement Rate", aggregate["mean_verdict_agreement_rate"]),
        ("Pairwise Verdict Agreement Rate", aggregate["pairwise_verdict_agreement_rate"]),
        ("Pairwise Overall Score MAE", aggregate["pairwise_overall_score_mae"]),
        ("Cohen's Kappa (Verdict)", aggregate["cohens_kappa_verdict"] if aggregate["cohens_kappa_verdict"] is not None else "N/A"),
        ("Mean Overall Score Range", aggregate["mean_overall_score_range"]),
    ]

    aggregate_table = "\n".join(
        f"{_latex_escape(metric)} & {_latex_escape(value)} \\\\"
        for metric, value in aggregate_rows
    )

    reviewer_table = "\n".join(
        f"{_latex_escape(row['reviewer_id'])} & {row['review_count']} & {row['overlap_review_count']} & {row['overall_score_mean']} & {row['accept_like_rate']} & {row['reject_rate']} \\\\"
        for row in reviewer_rows
    ) or "N/A & 0 & 0 & 0 & 0 & 0 \\\\"

    case_table = "\n".join(
        f"{_latex_escape(row['case_id'])} & {row['review_count']} & {_latex_escape(row['verdict_majority'])} & {row['verdict_agreement_rate']} & {row['overall_score_mean']} & {row['overall_score_range']} \\\\"
        for row in case_rows[:10]
    ) or "N/A & 0 & N/A & 0 & 0 & 0 \\\\"

    return rf"""\begin{{table}}[htbp]
\centering
\caption{{Human review aggregate metrics}}
\begin{{tabular}}{{lr}}
\hline
Metric & Value \\
\hline
{aggregate_table}
\hline
\end{{tabular}}
\end{{table}}

\begin{{table}}[htbp]
\centering
\caption{{Reviewer-level summary}}
\begin{{tabular}}{{lrrrrr}}
\hline
Reviewer & Reviews & Overlap & Overall Mean & Accept-like Rate & Reject Rate \\
\hline
{reviewer_table}
\hline
\end{{tabular}}
\end{{table}}

\begin{{table}}[htbp]
\centering
\caption{{Case-level preview of human review results}}
\begin{{tabular}}{{lrrrrr}}
\hline
Case ID & Reviews & Majority Verdict & Agreement Rate & Overall Mean & Score Range \\
\hline
{case_table}
\hline
\end{{tabular}}
\end{{table}}
"""


def summarize_human_reviews(rows: list[dict[str, Any]]) -> dict[str, Any]:
    reviewed_rows = [row for row in rows if _is_reviewed(row)]
    score_values: dict[str, list[float]] = {column: [] for column in SCORE_COLUMNS}
    verdict_counter: Counter[str] = Counter()
    reviewer_ids: set[str] = set()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in reviewed_rows:
        case_id = str(row.get("case_id", "")).strip() or "unknown_case"
        grouped[case_id].append(row)
        reviewer_id = str(row.get("reviewer_id", "")).strip()
        if reviewer_id:
            reviewer_ids.add(reviewer_id)
        verdict = _normalize_verdict(row.get("verdict", ""))
        if verdict:
            verdict_counter[verdict] += 1
        for column in SCORE_COLUMNS:
            value = _to_float(row.get(column))
            if value is not None:
                score_values[column].append(value)

    case_rows: list[dict[str, Any]] = []
    reviewer_grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    overlap_case_count = 0
    agreement_rates: list[float] = []
    score_ranges: list[float] = []
    pairwise_verdict_hits: list[float] = []
    pairwise_overall_diffs: list[float] = []
    two_reviewer_overlap_cases: list[tuple[str, str]] = []
    for case_id, case_group in sorted(grouped.items()):
        for item in case_group:
            reviewer_id = str(item.get("reviewer_id", "")).strip()
            if reviewer_id:
                reviewer_grouped[reviewer_id].append(item)
        if len(case_group) >= 2:
            overlap_case_count += 1
        verdicts = [
            _normalize_verdict(item.get("verdict", ""))
            for item in case_group
            if _normalize_verdict(item.get("verdict", ""))
        ]
        verdict_majority = Counter(verdicts).most_common(1)[0][0] if verdicts else ""
        verdict_agreement_rate = (
            round(Counter(verdicts).most_common(1)[0][1] / len(verdicts), 4)
            if verdicts
            else 0.0
        )
        if verdicts:
            agreement_rates.append(verdict_agreement_rate)
        overall_scores = [_to_float(item.get("overall_score")) for item in case_group]
        normalized_overall = [value for value in overall_scores if value is not None]
        overall_range = round(max(normalized_overall) - min(normalized_overall), 4) if normalized_overall else 0.0
        if normalized_overall:
            score_ranges.append(overall_range)

        for left, right in combinations(case_group, 2):
            left_verdict = _normalize_verdict(left.get("verdict", ""))
            right_verdict = _normalize_verdict(right.get("verdict", ""))
            if left_verdict and right_verdict:
                pairwise_verdict_hits.append(1.0 if left_verdict == right_verdict else 0.0)
                left_reviewer = str(left.get("reviewer_id", "")).strip()
                right_reviewer = str(right.get("reviewer_id", "")).strip()
                if left_reviewer and right_reviewer:
                    two_reviewer_overlap_cases.append((left_verdict, right_verdict))
            left_overall = _to_float(left.get("overall_score"))
            right_overall = _to_float(right.get("overall_score"))
            if left_overall is not None and right_overall is not None:
                pairwise_overall_diffs.append(abs(left_overall - right_overall))

        summary = HumanReviewCaseSummary(
            case_id=case_id,
            review_count=len(case_group),
            reviewer_count=len({str(item.get("reviewer_id", "")).strip() for item in case_group if str(item.get("reviewer_id", "")).strip()}),
            correctness_score_mean=round(average([value for value in (_to_float(item.get("correctness_score")) for item in case_group) if value is not None]), 4),
            grounding_score_mean=round(average([value for value in (_to_float(item.get("grounding_score")) for item in case_group) if value is not None]), 4),
            usefulness_score_mean=round(average([value for value in (_to_float(item.get("usefulness_score")) for item in case_group) if value is not None]), 4),
            clarity_score_mean=round(average([value for value in (_to_float(item.get("clarity_score")) for item in case_group) if value is not None]), 4),
            overall_score_mean=round(average([value for value in normalized_overall if value is not None]), 4),
            verdict_majority=verdict_majority,
            verdict_agreement_rate=verdict_agreement_rate,
            overall_score_range=overall_range,
            notes_count=sum(1 for item in case_group if str(item.get("notes", "")).strip()),
        )
        case_rows.append(asdict(summary))

    reviewer_rows: list[dict[str, Any]] = []
    overlap_case_ids = {
        row["case_id"]
        for row in case_rows
        if row["review_count"] >= 2
    }
    for reviewer_id, reviewer_group in sorted(reviewer_grouped.items()):
        verdicts = [
            _normalize_verdict(item.get("verdict", ""))
            for item in reviewer_group
            if _normalize_verdict(item.get("verdict", ""))
        ]
        accept_like = sum(1 for verdict in verdicts if verdict in {"accept", "minor_issue"})
        reject_count = sum(1 for verdict in verdicts if verdict == "reject")
        reviewer_rows.append(
            asdict(
                HumanReviewReviewerSummary(
                    reviewer_id=reviewer_id,
                    review_count=len(reviewer_group),
                    overlap_review_count=sum(
                        1
                        for item in reviewer_group
                        if str(item.get("case_id", "")).strip() in overlap_case_ids
                    ),
                    correctness_score_mean=round(average([value for value in (_to_float(item.get("correctness_score")) for item in reviewer_group) if value is not None]), 4),
                    grounding_score_mean=round(average([value for value in (_to_float(item.get("grounding_score")) for item in reviewer_group) if value is not None]), 4),
                    usefulness_score_mean=round(average([value for value in (_to_float(item.get("usefulness_score")) for item in reviewer_group) if value is not None]), 4),
                    clarity_score_mean=round(average([value for value in (_to_float(item.get("clarity_score")) for item in reviewer_group) if value is not None]), 4),
                    overall_score_mean=round(average([value for value in (_to_float(item.get("overall_score")) for item in reviewer_group) if value is not None]), 4),
                    accept_like_rate=round(accept_like / len(verdicts), 4) if verdicts else 0.0,
                    reject_rate=round(reject_count / len(verdicts), 4) if verdicts else 0.0,
                )
            )
        )

    cohens_kappa_verdict = None
    if len(reviewer_ids) == 2 and two_reviewer_overlap_cases:
        labels_a = [left for left, _ in two_reviewer_overlap_cases]
        labels_b = [right for _, right in two_reviewer_overlap_cases]
        cohens_kappa_verdict = _safe_round(_cohens_kappa(labels_a, labels_b))

    aggregate = {
        "row_count": len(rows),
        "reviewed_row_count": len(reviewed_rows),
        "reviewer_count": len(reviewer_ids),
        "case_count": len(case_rows),
        "overlap_case_count": overlap_case_count,
        "correctness_score_mean": round(average(score_values["correctness_score"]), 4),
        "grounding_score_mean": round(average(score_values["grounding_score"]), 4),
        "usefulness_score_mean": round(average(score_values["usefulness_score"]), 4),
        "clarity_score_mean": round(average(score_values["clarity_score"]), 4),
        "overall_score_mean": round(average(score_values["overall_score"]), 4),
        "verdict_distribution": dict(verdict_counter),
        "mean_verdict_agreement_rate": round(average(agreement_rates), 4),
        "mean_overall_score_range": round(average(score_ranges), 4),
        "pairwise_overlap_count": len(pairwise_verdict_hits),
        "pairwise_verdict_agreement_rate": round(average(pairwise_verdict_hits), 4),
        "pairwise_overall_score_mae": round(average(pairwise_overall_diffs), 4),
        "cohens_kappa_verdict": cohens_kappa_verdict,
    }
    return {
        "review_rows": reviewed_rows,
        "case_rows": case_rows,
        "reviewer_rows": reviewer_rows,
        "aggregate": aggregate,
    }


def build_human_review_report(summary: dict[str, Any]) -> str:
    aggregate = summary["aggregate"]
    verdict_lines = "\n".join(
        f"- `{key}`: {value}"
        for key, value in sorted(aggregate.get("verdict_distribution", {}).items())
    ) or "- 無 verdict"
    return f"""# Human Review Report

## 摘要
- reviewed rows: `{aggregate['reviewed_row_count']}`
- reviewers: `{aggregate['reviewer_count']}`
- cases: `{aggregate['case_count']}`
- overlap cases: `{aggregate['overlap_case_count']}`

## 平均分數
- correctness: `{aggregate['correctness_score_mean']}`
- grounding: `{aggregate['grounding_score_mean']}`
- usefulness: `{aggregate['usefulness_score_mean']}`
- clarity: `{aggregate['clarity_score_mean']}`
- overall: `{aggregate['overall_score_mean']}`

## 一致性
- mean verdict agreement rate: `{aggregate['mean_verdict_agreement_rate']}`
- pairwise verdict agreement rate: `{aggregate['pairwise_verdict_agreement_rate']}`
- pairwise overall score MAE: `{aggregate['pairwise_overall_score_mae']}`
- Cohen's kappa (verdict): `{aggregate['cohens_kappa_verdict']}`
- mean overall score range: `{aggregate['mean_overall_score_range']}`

## Verdict Distribution
{verdict_lines}
"""
