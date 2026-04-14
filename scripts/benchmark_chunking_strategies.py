from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from job_spy_tw.assistant.chunking_eval import (
    build_anchored_compact_market_hybrid_chunks,
    LocalHashEmbeddingClient,
    build_all_eval_cases,
    build_anchored_hybrid_chunks,
    build_anchored_itemized_chunks,
    build_anchored_windowed_chunks,
    build_default_eval_cases,
    build_realistic_eval_cases,
    build_hybrid_chunks,
    build_itemized_chunks,
    evaluate_chunking_strategy,
)
from job_spy_tw.assistant.chunks import build_chunks
from job_spy_tw.assistant.retrieval import EmbeddingRetriever
from job_spy_tw.prompt_versions import (
    CHUNKING_POLICY_VERSION,
    RETRIEVAL_POLICY_VERSION,
    answer_prompt_version,
    normalize_prompt_variant,
)
from job_spy_tw.storage import load_snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark current vs alternative RAG chunking strategies.")
    parser.add_argument(
        "--snapshot",
        default=str(ROOT / "data" / "jobs_latest.json"),
        help="Path to MarketSnapshot JSON.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Top-k retrieved chunks to evaluate.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--show-failures",
        type=int,
        default=4,
        help="How many miss cases to print per strategy in text mode.",
    )
    parser.add_argument(
        "--case-set",
        choices=("default", "realistic", "all"),
        default="default",
        help="Which evaluation question set to use.",
    )
    parser.add_argument(
        "--gate-strategy",
        default="current_structured",
        help="Strategy used for regression gate comparisons.",
    )
    parser.add_argument(
        "--baseline-file",
        default="",
        help="Optional baseline JSON to compare against.",
    )
    parser.add_argument(
        "--write-baseline",
        default="",
        help="Optional path to write a baseline JSON for the gate strategy.",
    )
    parser.add_argument(
        "--min-hit-at-1",
        type=float,
        default=0.0,
        help="Hard floor for gate strategy hit@1.",
    )
    parser.add_argument(
        "--min-mrr",
        type=float,
        default=0.0,
        help="Hard floor for gate strategy MRR.",
    )
    parser.add_argument(
        "--prompt-variant",
        default="control",
        help="Prompt variant metadata to store with the baseline.",
    )
    parser.add_argument(
        "--gate-only",
        action="store_true",
        help="Only evaluate the gate strategy instead of all chunking strategies.",
    )
    return parser.parse_args()


def _summary_payload(summary, *, case_set: str, top_k: int, prompt_variant: str) -> dict[str, object]:
    return {
        "strategy": summary.strategy_name,
        "case_set": case_set,
        "top_k": int(top_k),
        "chunks": summary.chunks_count,
        "case_count": summary.case_count,
        "hit_at_1": round(summary.hit_at_1, 6),
        "hit_at_3": round(summary.hit_at_3, 6),
        "hit_at_5": round(summary.hit_at_5, 6),
        "mrr": round(summary.mrr, 6),
        "source_hit_rate": round(summary.source_hit_rate, 6),
        "target_hit_rate": round(summary.target_hit_rate, 6),
        "prompt_variant": normalize_prompt_variant(prompt_variant),
        "prompt_version": answer_prompt_version(prompt_variant),
        "retrieval_policy_version": RETRIEVAL_POLICY_VERSION,
        "chunking_policy_version": CHUNKING_POLICY_VERSION,
    }


def _write_baseline(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _check_regression(
    *,
    baseline_path: Path,
    payload: dict[str, object],
    min_hit_at_1: float,
    min_mrr: float,
) -> list[str]:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    issues: list[str] = []
    for field_name in ("strategy", "case_set", "top_k"):
        if str(baseline.get(field_name, "")) != str(payload.get(field_name, "")):
            issues.append(
                f"baseline {field_name} mismatch: expected {baseline.get(field_name)} got {payload.get(field_name)}"
            )
    if float(payload.get("hit_at_1", 0.0) or 0.0) < float(baseline.get("hit_at_1", 0.0) or 0.0):
        issues.append(
            f"hit@1 regressed: baseline={baseline.get('hit_at_1')} current={payload.get('hit_at_1')}"
        )
    if float(payload.get("mrr", 0.0) or 0.0) < float(baseline.get("mrr", 0.0) or 0.0):
        issues.append(f"mrr regressed: baseline={baseline.get('mrr')} current={payload.get('mrr')}")
    if float(payload.get("hit_at_1", 0.0) or 0.0) < float(min_hit_at_1):
        issues.append(
            f"hit@1 below floor: floor={min_hit_at_1:.4f} current={float(payload.get('hit_at_1', 0.0) or 0.0):.4f}"
        )
    if float(payload.get("mrr", 0.0) or 0.0) < float(min_mrr):
        issues.append(
            f"mrr below floor: floor={min_mrr:.4f} current={float(payload.get('mrr', 0.0) or 0.0):.4f}"
        )
    return issues


def main() -> int:
    args = parse_args()
    snapshot_path = Path(args.snapshot)
    snapshot = load_snapshot(snapshot_path)
    if snapshot is None:
        raise SystemExit(f"Cannot load snapshot from: {snapshot_path}")

    case_builder = {
        "default": build_default_eval_cases,
        "realistic": build_realistic_eval_cases,
        "all": build_all_eval_cases,
    }[args.case_set]
    cases = case_builder(snapshot)
    retriever = EmbeddingRetriever(
        client=LocalHashEmbeddingClient(),
        embedding_model="local-hash-96",
        cache_dir=None,
    )

    strategy_builders = {
        "current_structured": build_chunks,
        "granular_itemized": build_itemized_chunks,
        "anchored_itemized": build_anchored_itemized_chunks,
        "anchored_windowed": build_anchored_windowed_chunks,
        "hybrid_layered": build_hybrid_chunks,
        "anchored_hybrid": build_anchored_hybrid_chunks,
        "anchored_compact_market": build_anchored_compact_market_hybrid_chunks,
    }
    selected_strategy_names = (
        [args.gate_strategy]
        if args.gate_only
        else list(strategy_builders.keys())
    )
    summaries = [
        evaluate_chunking_strategy(
            strategy_name=strategy_name,
            chunk_builder=strategy_builders[strategy_name],
            snapshot=snapshot,
            resume_profile=None,
            cases=cases,
            retriever=retriever,
            top_k=args.top_k,
        )
        for strategy_name in selected_strategy_names
    ]
    gate_summary = next(
        (summary for summary in summaries if summary.strategy_name == args.gate_strategy),
        None,
    )
    if gate_summary is None:
        raise SystemExit(f"Unknown gate strategy: {args.gate_strategy}")
    gate_payload = _summary_payload(
        gate_summary,
        case_set=args.case_set,
        top_k=args.top_k,
        prompt_variant=args.prompt_variant,
    )
    if args.write_baseline:
        _write_baseline(Path(args.write_baseline), gate_payload)

    regression_issues: list[str] = []
    if args.baseline_file:
        regression_issues = _check_regression(
            baseline_path=Path(args.baseline_file),
            payload=gate_payload,
            min_hit_at_1=args.min_hit_at_1,
            min_mrr=args.min_mrr,
        )
    else:
        if float(gate_payload["hit_at_1"]) < float(args.min_hit_at_1):
            regression_issues.append(
                f"hit@1 below floor: floor={args.min_hit_at_1:.4f} current={float(gate_payload['hit_at_1']):.4f}"
            )
        if float(gate_payload["mrr"]) < float(args.min_mrr):
            regression_issues.append(
                f"mrr below floor: floor={args.min_mrr:.4f} current={float(gate_payload['mrr']):.4f}"
            )

    if args.format == "json":
        print(
            json.dumps(
                {
                    "snapshot": str(snapshot_path),
                    "case_set": args.case_set,
                    "cases": len(cases),
                    "gate": {
                        "strategy": args.gate_strategy,
                        "baseline_file": args.baseline_file or None,
                        "issues": regression_issues,
                        "current": gate_payload,
                    },
                    "strategies": [
                        {
                            "strategy": summary.strategy_name,
                            "chunks": summary.chunks_count,
                            "hit_at_1": round(summary.hit_at_1, 4),
                            "hit_at_3": round(summary.hit_at_3, 4),
                            "hit_at_5": round(summary.hit_at_5, 4),
                            "mrr": round(summary.mrr, 4),
                            "source_hit_rate": round(summary.source_hit_rate, 4),
                            "target_hit_rate": round(summary.target_hit_rate, 4),
                        }
                        for summary in summaries
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1 if regression_issues else 0

    print(f"snapshot: {snapshot_path}")
    print(f"jobs: {len(snapshot.jobs)} | eval cases: {len(cases)} | top_k: {args.top_k} | case_set: {args.case_set}")
    print("")
    print(
        f"{'strategy':<20} {'chunks':>7} {'hit@1':>8} {'hit@3':>8} {'hit@5':>8} {'mrr':>8} {'source':>8} {'target':>8}"
    )
    print("-" * 82)
    for summary in summaries:
        print(
            f"{summary.strategy_name:<20} "
            f"{summary.chunks_count:>7} "
            f"{summary.hit_at_1:>8.2%} "
            f"{summary.hit_at_3:>8.2%} "
            f"{summary.hit_at_5:>8.2%} "
            f"{summary.mrr:>8.3f} "
            f"{summary.source_hit_rate:>8.2%} "
            f"{summary.target_hit_rate:>8.2%}"
        )

    for summary in summaries:
        misses = [case for case in summary.cases if not case.hit_at_5][: args.show_failures]
        if not misses:
            continue
        print("")
        print(f"[{summary.strategy_name}] miss samples")
        for miss in misses:
            labels = [f"{chunk.source_type}:{chunk.label}" for chunk in miss.retrieved[: args.top_k]]
            print(f"- {miss.case.question}")
            print(f"  expected={miss.case.expected_source_types} target={miss.case.target_terms}")
            print(f"  got={labels}")
    print("")
    print(f"[regression gate] strategy={args.gate_strategy}")
    print(
        f"current hit@1={float(gate_payload['hit_at_1']):.4f} "
        f"mrr={float(gate_payload['mrr']):.4f} "
        f"prompt={gate_payload['prompt_version']} "
        f"retrieval={gate_payload['retrieval_policy_version']} "
        f"chunking={gate_payload['chunking_policy_version']}"
    )
    if args.baseline_file:
        print(f"baseline={args.baseline_file}")
    if regression_issues:
        print("gate result: FAIL")
        for issue in regression_issues:
            print(f"- {issue}")
        return 1
    print("gate result: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
