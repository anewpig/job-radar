#!/usr/bin/env python3
"""載入 Base / SFT / DPO 模型做本地 assistant benchmark，並產生 comparison manifest。"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import platform
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
EVAL_ROOT = SCRIPT_PATH.parents[1]
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from job_radar_eval.assistant_eval import evaluate_assistant
from job_radar_eval.config import build_config, build_model_config, ensure_project_importable
from job_radar_eval.experiment_artifacts import build_experiment_manifest, write_case_exports, write_experiment_manifest
from job_radar_eval.local_responses_client import LocalTransformersClient
from job_radar_eval.post_training import EVAL_RUN_PREFIX, build_eval_comparison_manifest
from job_radar_eval.reporting import build_run_dir, write_csv, write_json


def _print_progress(stage_name: str, payload: dict) -> None:
    event = str(payload.get("event", ""))
    if event == "stage_started":
        print(
            f"[{stage_name}] start: total_cases={payload.get('total_cases', 0)} "
            f"iterations={payload.get('iterations', 0)} model={payload.get('answer_model', '')}",
            flush=True,
        )
        return
    if event == "case_started":
        question = str(payload.get("question", "")).strip().replace("\n", " ")
        if len(question) > 60:
            question = question[:57] + "..."
        print(
            f"[{stage_name}] case {payload.get('case_index', 0)}/{payload.get('total_cases', 0)} "
            f"{payload.get('answer_mode', '')} | {question}",
            flush=True,
        )
        return
    if event == "case_finished":
        print(
            f"[{stage_name}] done {payload.get('case_index', 0)}/{payload.get('total_cases', 0)} "
            f"f1={payload.get('keyword_f1_mean', 0.0):.4f} total_ms={payload.get('total_ms_mean', 0.0):.1f}",
            flush=True,
        )
        return
    if event == "stage_finished":
        aggregate = payload.get("aggregate", {})
        print(
            f"[{stage_name}] finished: case_count={aggregate.get('case_count', 0)} "
            f"keyword_f1={aggregate.get('keyword_f1_mean', 0.0):.4f} total_ms={aggregate.get('total_ms_mean', 0.0):.1f}",
            flush=True,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="跑 post-training Base / SFT / DPO assistant benchmark")
    parser.add_argument("--base-model-source", type=str, default="Qwen/Qwen3-4B-Instruct-2507", help="Base model repo 或本地路徑")
    parser.add_argument("--sft-model-source", type=str, required=True, help="Merged SFT model repo 或本地路徑")
    parser.add_argument("--dpo-model-source", type=str, required=True, help="Merged DPO model repo 或本地路徑")
    parser.add_argument("--dataset-version", type=str, required=True, help="對應 post-training dataset version")
    parser.add_argument("--iterations", type=int, default=1, help="每個 case 重跑次數")
    parser.add_argument("--case-limit", type=int, default=None, help="限制 fixture case 數")
    parser.add_argument("--embedding-model", type=str, default="", help="embedding model，預設讀主專案設定")
    parser.add_argument("--embedding-api-key", type=str, default="", help="embedding API key，預設讀主專案設定")
    parser.add_argument("--embedding-base-url", type=str, default="", help="embedding base url，預設讀主專案設定")
    parser.add_argument("--artifact-repo", type=str, default="", help="若提供，會把 comparison manifest 上傳到此 dataset repo")
    parser.add_argument("--trust-remote-code", action="store_true", help="載入本地 / HF 模型時啟用 trust_remote_code")
    parser.add_argument("--max-input-tokens", type=int, default=4096, help="local generation client prompt truncation")
    return parser.parse_args()


def _build_report(summary: dict) -> str:
    overall = summary.get("assistant_metrics_overall", {})
    deltas = summary.get("stage_deltas", {})
    return f"""# Post-Training Evaluation Comparison

- Generated at: `{summary.get('generated_at', '')}`
- Dataset version: `{summary.get('dataset_version', '')}`
- Base model: `{summary.get('base_model', '')}`
- SFT model: `{summary.get('sft_model', '')}`
- DPO model: `{summary.get('dpo_model', '')}`
- Case count: `{summary.get('sample_size', 0)}`

## Overall

- Base keyword F1: `{overall.get('base', {}).get('keyword_f1_mean', 0.0)}`
- SFT keyword F1: `{overall.get('sft', {}).get('keyword_f1_mean', 0.0)}`
- DPO keyword F1: `{overall.get('dpo', {}).get('keyword_f1_mean', 0.0)}`
- DPO evidence sufficiency: `{overall.get('dpo', {}).get('evidence_sufficiency_rate', 0.0)}`
- DPO structured output rate: `{overall.get('dpo', {}).get('structured_output_rate', 0.0)}`

## Deltas

- Base -> SFT keyword F1 delta: `{deltas.get('sft_vs_base', {}).get('keyword_f1_mean', 0.0)}`
- SFT -> DPO keyword F1 delta: `{deltas.get('dpo_vs_sft', {}).get('keyword_f1_mean', 0.0)}`
- Base -> DPO keyword F1 delta: `{deltas.get('dpo_vs_base', {}).get('keyword_f1_mean', 0.0)}`
- Base -> DPO latency delta: `{deltas.get('dpo_vs_base', {}).get('total_ms_mean', 0.0)}`
"""


def _stage_eval(
    *,
    config,
    stage_name: str,
    model_source: str,
    embedding_model: str,
    embedding_api_key: str,
    embedding_base_url: str,
    iterations: int,
    case_limit: int | None,
    trust_remote_code: bool,
    max_input_tokens: int,
) -> dict:
    return evaluate_assistant(
        config,
        iterations=iterations,
        case_limit=case_limit,
        answer_model=model_source,
        embedding_model=embedding_model,
        api_key="local-transformers",
        base_url="",
        use_fake_client=False,
        client=LocalTransformersClient(
            model_source,
            max_input_tokens=max_input_tokens,
            trust_remote_code=trust_remote_code,
        ),
        embedding_api_key=embedding_api_key,
        embedding_base_url=embedding_base_url,
        progress_callback=lambda payload: _print_progress(stage_name, payload),
    )


def _upload_eval_artifacts(*, artifact_repo: str, dataset_version: str, files: dict[str, Path]) -> dict[str, str]:
    from huggingface_hub import HfApi

    api = HfApi()
    uploads: dict[str, str] = {}
    for name, local_path in files.items():
        for remote_path in (
            f"eval/{dataset_version}/{name}",
            f"eval/latest/{name}",
        ):
            api.upload_file(
                path_or_fileobj=str(local_path.resolve()),
                path_in_repo=remote_path,
                repo_id=artifact_repo,
                repo_type="dataset",
                commit_message=f"Upload post-training eval {name}",
            )
            uploads[remote_path] = f"https://huggingface.co/datasets/{artifact_repo}/resolve/main/{remote_path}"
    return uploads


def main() -> None:
    args = parse_args()
    config = build_config()
    ensure_project_importable(config.project_root)
    model_config = build_model_config(config.project_root)
    embedding_model = args.embedding_model.strip() or model_config.embedding_model
    embedding_api_key = args.embedding_api_key.strip() or model_config.openai_api_key
    embedding_base_url = args.embedding_base_url.strip() or model_config.openai_base_url

    run_dir = build_run_dir(config.results_dir, prefix=EVAL_RUN_PREFIX)
    base_results = _stage_eval(
        config=config,
        stage_name="base",
        model_source=args.base_model_source,
        embedding_model=embedding_model,
        embedding_api_key=embedding_api_key,
        embedding_base_url=embedding_base_url,
        iterations=args.iterations,
        case_limit=args.case_limit,
        trust_remote_code=args.trust_remote_code,
        max_input_tokens=args.max_input_tokens,
    )
    sft_results = _stage_eval(
        config=config,
        stage_name="sft",
        model_source=args.sft_model_source,
        embedding_model=embedding_model,
        embedding_api_key=embedding_api_key,
        embedding_base_url=embedding_base_url,
        iterations=args.iterations,
        case_limit=args.case_limit,
        trust_remote_code=args.trust_remote_code,
        max_input_tokens=args.max_input_tokens,
    )
    dpo_results = _stage_eval(
        config=config,
        stage_name="dpo",
        model_source=args.dpo_model_source,
        embedding_model=embedding_model,
        embedding_api_key=embedding_api_key,
        embedding_base_url=embedding_base_url,
        iterations=args.iterations,
        case_limit=args.case_limit,
        trust_remote_code=args.trust_remote_code,
        max_input_tokens=args.max_input_tokens,
    )

    comparison_manifest = build_eval_comparison_manifest(
        base_summary=base_results,
        sft_summary=sft_results,
        dpo_summary=dpo_results,
        base_model=args.base_model_source,
        sft_model=args.sft_model_source,
        dpo_model=args.dpo_model_source,
        dataset_version=args.dataset_version,
    )
    comparison_manifest.update(
        {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "mode": "post_training_local_eval",
            "project_root": str(config.project_root),
            "python_version": sys.version,
            "platform": platform.platform(),
            "embedding_model": embedding_model,
        }
    )

    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"
    case_rows_path = run_dir / "assistant_case_rows.csv"
    base_path = run_dir / "base_assistant_summary.json"
    sft_path = run_dir / "sft_assistant_summary.json"
    dpo_path = run_dir / "dpo_assistant_summary.json"
    write_json(summary_path, comparison_manifest)
    report_path.write_text(_build_report(comparison_manifest), encoding="utf-8")
    write_csv(case_rows_path, comparison_manifest.get("assistant_case_rows", []))
    write_json(base_path, base_results)
    write_json(sft_path, sft_results)
    write_json(dpo_path, dpo_results)

    case_exports = write_case_exports(
        run_dir=run_dir,
        case_sections={
            "assistant_eval_comparison": comparison_manifest.get("assistant_case_rows", []),
        },
    )
    manifest = build_experiment_manifest(
        config=config,
        run_name=EVAL_RUN_PREFIX,
        run_dir=run_dir,
        summary_path=summary_path,
        report_path=report_path,
        cli_args=vars(args),
        source_paths={
            "base_model_source": args.base_model_source,
            "sft_model_source": args.sft_model_source,
            "dpo_model_source": args.dpo_model_source,
        },
        model_config={
            "embedding_model": embedding_model,
        },
        case_exports=case_exports,
        extra_artifacts=[
            {"name": "base_assistant_summary", "path": str(base_path.resolve())},
            {"name": "sft_assistant_summary", "path": str(sft_path.resolve())},
            {"name": "dpo_assistant_summary", "path": str(dpo_path.resolve())},
            {"name": "assistant_case_rows_csv", "path": str(case_rows_path.resolve())},
        ],
    )
    experiment_manifest_path = run_dir / "manifest.json"
    write_experiment_manifest(experiment_manifest_path, manifest)

    upload_urls = {}
    if args.artifact_repo.strip():
        upload_urls = _upload_eval_artifacts(
            artifact_repo=args.artifact_repo.strip(),
            dataset_version=args.dataset_version,
            files={
                "summary.json": summary_path,
                "report.md": report_path,
                "manifest.json": experiment_manifest_path,
                case_rows_path.name: case_rows_path,
                "base_assistant_summary.json": base_path,
                "sft_assistant_summary.json": sft_path,
                "dpo_assistant_summary.json": dpo_path,
                "assistant_eval_comparison_cases.csv": run_dir / "assistant_eval_comparison_cases.csv",
                "assistant_eval_comparison_cases.jsonl": run_dir / "assistant_eval_comparison_cases.jsonl",
            },
        )

    print(f"[done] results saved to: {run_dir}")
    print(f"[done] summary: {summary_path}")
    print(f"[done] report:  {report_path}")
    print(f"[done] base:    {base_path}")
    print(f"[done] sft:     {sft_path}")
    print(f"[done] dpo:     {dpo_path}")
    if upload_urls:
        print("[done] uploaded:")
        print(json.dumps(upload_urls, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
