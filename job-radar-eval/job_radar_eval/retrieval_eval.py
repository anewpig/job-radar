"""retrieval.py baseline 評估。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

from .fake_clients import FakeOpenAIClient
from .fixtures import build_retrieval_chunks_fixture, load_retrieval_cases
from .metrics import average, p95


@dataclass(slots=True)
class RetrievalCaseResult:
    """單一 retrieval 測題的聚合結果。"""

    case_id: str
    question: str
    iterations: int
    cold_ms_mean: float
    warm_ms_mean: float
    cold_ms_p95: float
    warm_ms_p95: float
    speedup_ratio_mean: float
    top1_hit_rate: float
    recall_at_k_mean: float
    mrr_mean: float
    latest_top_chunk_id: str


def _recall_at_k(expected_chunk_ids: list[str], retrieved_chunk_ids: list[str]) -> float:
    """計算 retrieval 的 recall@k。"""
    if not expected_chunk_ids:
        return 1.0
    expected = set(expected_chunk_ids)
    actual = set(retrieved_chunk_ids)
    return len(expected & actual) / len(expected)


def _mrr(expected_chunk_ids: list[str], retrieved_chunk_ids: list[str]) -> float:
    """計算第一個命中相關 chunk 的 reciprocal rank。"""
    expected = set(expected_chunk_ids)
    for index, chunk_id in enumerate(retrieved_chunk_ids, start=1):
        if chunk_id in expected:
            return 1.0 / index
    return 0.0


def _build_retrieval_client(*, api_key: str, base_url: str, use_fake_client: bool):
    if use_fake_client:
        return FakeOpenAIClient()
    from openai import OpenAI

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAI(**client_kwargs)


def evaluate_retrieval(
    config,
    iterations: int,
    cache_dir: Path | None = None,
    *,
    case_limit: int | None = None,
    embedding_model: str = "fake-embedding",
    api_key: str = "fake",
    base_url: str = "",
    use_fake_client: bool = True,
) -> dict:
    """執行 retrieval baseline，量測命中率與冷熱快取延遲。"""
    from job_spy_tw.assistant.retrieval import EmbeddingRetriever

    cases = load_retrieval_cases(config)
    if case_limit is not None:
        cases = cases[:case_limit]
    chunks = build_retrieval_chunks_fixture()
    case_rows = []
    summaries: list[RetrievalCaseResult] = []

    for case in cases:
        cold_values = []
        warm_values = []
        speedup_values = []
        top1_hits = []
        recall_values = []
        mrr_values = []
        latest_top_chunk_id = ""

        for iteration in range(iterations):
            iteration_cache_dir = (
                (cache_dir or (config.results_dir / ".cache" / "retrieval"))
                / case["id"]
                / f"iter_{iteration + 1}"
            )
            retriever = EmbeddingRetriever(
                client=_build_retrieval_client(
                    api_key=api_key,
                    base_url=base_url,
                    use_fake_client=use_fake_client,
                ),
                embedding_model=embedding_model,
                cache_dir=iteration_cache_dir,
            )

            started = perf_counter()
            cold_result = retriever.retrieve(
                question=case["question"],
                chunks=chunks,
                top_k=int(case["top_k"]),
            )
            cold_ms = (perf_counter() - started) * 1000

            started = perf_counter()
            warm_result = retriever.retrieve(
                question=case["question"],
                chunks=chunks,
                top_k=int(case["top_k"]),
            )
            warm_ms = (perf_counter() - started) * 1000

            retrieved_ids = [chunk.chunk_id for chunk in warm_result]
            latest_top_chunk_id = retrieved_ids[0] if retrieved_ids else ""
            top1_hit = latest_top_chunk_id == case["expected_top_chunk_id"]
            recall = _recall_at_k(case["expected_relevant_chunk_ids"], retrieved_ids)
            mrr = _mrr(case["expected_relevant_chunk_ids"], retrieved_ids)
            speedup_ratio = (cold_ms / warm_ms) if warm_ms > 0 else 0.0

            cold_values.append(cold_ms)
            warm_values.append(warm_ms)
            speedup_values.append(speedup_ratio)
            top1_hits.append(1.0 if top1_hit else 0.0)
            recall_values.append(recall)
            mrr_values.append(mrr)
            case_rows.append(
                {
                    "case_id": case["id"],
                    "iteration": iteration + 1,
                    "question": case["question"],
                    "cold_ms": round(cold_ms, 3),
                    "warm_ms": round(warm_ms, 3),
                    "speedup_ratio": round(speedup_ratio, 4),
                    "top1_chunk_id": latest_top_chunk_id,
                    "top1_hit": top1_hit,
                    "recall_at_k": round(recall, 4),
                    "mrr": round(mrr, 4),
                }
            )

        summaries.append(
            RetrievalCaseResult(
                case_id=case["id"],
                question=case["question"],
                iterations=iterations,
                cold_ms_mean=round(average(cold_values), 3),
                warm_ms_mean=round(average(warm_values), 3),
                cold_ms_p95=round(p95(cold_values), 3),
                warm_ms_p95=round(p95(warm_values), 3),
                speedup_ratio_mean=round(average(speedup_values), 4),
                top1_hit_rate=round(average(top1_hits), 4),
                recall_at_k_mean=round(average(recall_values), 4),
                mrr_mean=round(average(mrr_values), 4),
                latest_top_chunk_id=latest_top_chunk_id,
            )
        )

    return {
        "rows": case_rows,
        "summary": [asdict(item) for item in summaries],
        "aggregate": {
            "cold_ms_mean": round(average([item.cold_ms_mean for item in summaries]), 3),
            "warm_ms_mean": round(average([item.warm_ms_mean for item in summaries]), 3),
            "cold_ms_p95": round(p95([item.cold_ms_p95 for item in summaries]), 3),
            "warm_ms_p95": round(p95([item.warm_ms_p95 for item in summaries]), 3),
            "speedup_ratio_mean": round(average([item.speedup_ratio_mean for item in summaries]), 4),
            "top1_hit_rate": round(average([item.top1_hit_rate for item in summaries]), 4),
            "recall_at_k_mean": round(average([item.recall_at_k_mean for item in summaries]), 4),
            "mrr_mean": round(average([item.mrr_mean for item in summaries]), 4),
        },
    }
