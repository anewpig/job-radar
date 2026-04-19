"""使用 resume_match_labels 執行履歷排序標註評估。"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
import math
from pathlib import Path

from .fixtures import build_market_snapshot_fixture, load_resume_cases, load_resume_match_labels
from .metrics import average, p95
from .resume_eval import InstrumentedResumeAnalysisService


LABEL_GAINS = {
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
    "reject": 0.0,
}
RELEVANT_LABELS = {"high", "medium"}


@dataclass(slots=True)
class ResumeLabelCaseResult:
    resume_id: str
    iterations: int
    label_count: int
    relevant_label_count: int
    build_profile_ms_mean: float
    match_jobs_ms_mean: float
    total_ms_mean: float
    total_ms_p95: float
    top1_best_label_hit_rate: float
    top3_relevant_recall_mean: float
    top3_reject_free_rate: float
    pairwise_order_accuracy_mean: float
    ndcg_at_3_mean: float
    latest_top_job_url: str
    latest_top1_label: str


def _gain(label: str) -> float:
    return LABEL_GAINS.get(label, 0.0)


def _dcg(gains: list[float]) -> float:
    total = 0.0
    for index, gain in enumerate(gains):
        total += gain / math.log2(index + 2)
    return total


def _ndcg_at_k(predicted_urls: list[str], labels_by_url: dict[str, dict], k: int = 3) -> float:
    predicted_gains = [_gain(labels_by_url.get(url, {}).get("fit_label", "reject")) for url in predicted_urls[:k]]
    ideal_gains = sorted((_gain(item["fit_label"]) for item in labels_by_url.values()), reverse=True)[:k]
    ideal = _dcg(ideal_gains)
    if ideal <= 0:
        return 1.0
    return _dcg(predicted_gains) / ideal


def _pairwise_order_accuracy(labels: list[dict], rank_by_url: dict[str, int], default_rank: int) -> float:
    decisions: list[float] = []
    for index, left in enumerate(labels):
        for right in labels[index + 1:]:
            left_gain = _gain(left["fit_label"])
            right_gain = _gain(right["fit_label"])
            if left_gain == right_gain:
                continue
            if left_gain > right_gain:
                higher, lower = left, right
            else:
                higher, lower = right, left
            higher_rank = rank_by_url.get(higher["job_id"], default_rank)
            lower_rank = rank_by_url.get(lower["job_id"], default_rank)
            decisions.append(1.0 if higher_rank < lower_rank else 0.0)
    return average(decisions) if decisions else 1.0


def evaluate_resume_labels(
    config,
    iterations: int,
    cache_dir: Path | None = None,
    *,
    case_limit: int | None = None,
    openai_api_key: str = "",
    openai_base_url: str = "",
    llm_model: str = "gpt-4.1-mini",
    title_model: str = "gpt-4.1-mini",
    embedding_model: str = "text-embedding-3-large",
    use_fake_client: bool = True,
    use_llm: bool = False,
) -> dict:
    snapshot = build_market_snapshot_fixture()
    jobs = snapshot.jobs
    resume_cases = {case["id"]: case for case in load_resume_cases(config)}
    labels_by_resume: dict[str, list[dict]] = defaultdict(list)
    for label in load_resume_match_labels(config):
        if label["resume_id"] in resume_cases:
            labels_by_resume[label["resume_id"]].append(label)

    ordered_resume_ids = sorted(labels_by_resume.keys())
    if case_limit is not None:
        ordered_resume_ids = ordered_resume_ids[:case_limit]

    service = InstrumentedResumeAnalysisService(
        cache_dir=cache_dir or (config.results_dir / ".cache" / "resume_labels"),
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        llm_model=llm_model,
        title_model=title_model,
        embedding_model=embedding_model,
        use_fake_client=use_fake_client,
        use_llm=use_llm,
    )

    case_rows: list[dict] = []
    summaries: list[ResumeLabelCaseResult] = []

    for resume_id in ordered_resume_ids:
        case = resume_cases[resume_id]
        labels = labels_by_resume[resume_id]
        labels_by_url = {item["job_id"]: item for item in labels}
        best_gain = max(_gain(item["fit_label"]) for item in labels)
        relevant_urls = {item["job_id"] for item in labels if item["fit_label"] in RELEVANT_LABELS}
        reject_urls = {item["job_id"] for item in labels if item["fit_label"] == "reject"}

        build_values: list[float] = []
        match_values: list[float] = []
        total_values: list[float] = []
        top1_best_hits: list[float] = []
        top3_relevant_recalls: list[float] = []
        top3_reject_frees: list[float] = []
        pairwise_accuracies: list[float] = []
        ndcg_values: list[float] = []
        latest_top_job_url = ""
        latest_top1_label = "unlabeled"

        for iteration in range(iterations):
            result = service.run_case(case["resume_text"], jobs)
            matches = result["matches"]
            ranked_urls = [match.job_url for match in matches]
            rank_by_url = {url: index + 1 for index, url in enumerate(ranked_urls)}
            default_rank = len(ranked_urls) + 1
            top_match = matches[0] if matches else None
            latest_top_job_url = top_match.job_url if top_match else ""
            latest_top1_label = labels_by_url.get(latest_top_job_url, {}).get("fit_label", "unlabeled")
            top1_best_hits.append(1.0 if _gain(latest_top1_label) == best_gain else 0.0)

            top3_urls = ranked_urls[:3]
            if relevant_urls:
                relevant_hits = sum(1 for url in top3_urls if url in relevant_urls)
                top3_relevant_recalls.append(relevant_hits / len(relevant_urls))
            else:
                top3_relevant_recalls.append(1.0)
            top3_reject_frees.append(1.0 if not any(url in reject_urls for url in top3_urls) else 0.0)
            pairwise_accuracies.append(_pairwise_order_accuracy(labels, rank_by_url, default_rank))
            ndcg_values.append(_ndcg_at_k(ranked_urls, labels_by_url, k=3))

            timings = result["timings"]
            build_values.append(timings["build_profile_ms"])
            match_values.append(timings["match_jobs_ms"])
            total_values.append(timings["total_ms"])
            case_rows.append(
                {
                    "resume_id": resume_id,
                    "iteration": iteration + 1,
                    "label_count": len(labels),
                    "top1_job_url": latest_top_job_url,
                    "top1_label": latest_top1_label,
                    "top1_best_label_hit": _gain(latest_top1_label) == best_gain,
                    "top3_relevant_recall": round(top3_relevant_recalls[-1], 4),
                    "top3_reject_free": bool(top3_reject_frees[-1]),
                    "pairwise_order_accuracy": round(pairwise_accuracies[-1], 4),
                    "ndcg_at_3": round(ndcg_values[-1], 4),
                    "build_profile_ms": round(timings["build_profile_ms"], 3),
                    "match_jobs_ms": round(timings["match_jobs_ms"], 3),
                    "total_ms": round(timings["total_ms"], 3),
                }
            )

        summaries.append(
            ResumeLabelCaseResult(
                resume_id=resume_id,
                iterations=iterations,
                label_count=len(labels),
                relevant_label_count=len(relevant_urls),
                build_profile_ms_mean=round(average(build_values), 3),
                match_jobs_ms_mean=round(average(match_values), 3),
                total_ms_mean=round(average(total_values), 3),
                total_ms_p95=round(p95(total_values), 3),
                top1_best_label_hit_rate=round(average(top1_best_hits), 4),
                top3_relevant_recall_mean=round(average(top3_relevant_recalls), 4),
                top3_reject_free_rate=round(average(top3_reject_frees), 4),
                pairwise_order_accuracy_mean=round(average(pairwise_accuracies), 4),
                ndcg_at_3_mean=round(average(ndcg_values), 4),
                latest_top_job_url=latest_top_job_url,
                latest_top1_label=latest_top1_label,
            )
        )

    return {
        "rows": case_rows,
        "summary": [asdict(item) for item in summaries],
        "aggregate": {
            "case_count": len(summaries),
            "label_count": sum(item.label_count for item in summaries),
            "build_profile_ms_mean": round(average([item.build_profile_ms_mean for item in summaries]), 3),
            "match_jobs_ms_mean": round(average([item.match_jobs_ms_mean for item in summaries]), 3),
            "total_ms_mean": round(average([item.total_ms_mean for item in summaries]), 3),
            "total_ms_p95": round(p95([item.total_ms_p95 for item in summaries]), 3),
            "top1_best_label_hit_rate": round(average([item.top1_best_label_hit_rate for item in summaries]), 4),
            "top3_relevant_recall_mean": round(average([item.top3_relevant_recall_mean for item in summaries]), 4),
            "top3_reject_free_rate": round(average([item.top3_reject_free_rate for item in summaries]), 4),
            "pairwise_order_accuracy_mean": round(average([item.pairwise_order_accuracy_mean for item in summaries]), 4),
            "ndcg_at_3_mean": round(average([item.ndcg_at_3_mean for item in summaries]), 4),
        },
    }
