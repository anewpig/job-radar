#!/usr/bin/env python3
"""在 Colab 上執行 Job Radar 的 SFT -> DPO post-training 與 artifact 發布流程。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_PATH = Path(__file__).resolve()
EVAL_ROOT = SCRIPT_PATH.parents[1]
if str(EVAL_ROOT) not in sys.path:
    sys.path.insert(0, str(EVAL_ROOT))

from job_radar_eval.post_training_colab import (
    PostTrainingRepoIds,
    build_default_repo_ids,
    infer_trackio_space_id,
    run_post_training_pipeline,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="在 Colab 上執行 Job Radar SFT -> DPO post-training")
    parser.add_argument(
        "--base-model",
        type=str,
        default="Qwen/Qwen3-4B-Instruct-2507",
        help="base model id，預設使用 Qwen/Qwen3-4B-Instruct-2507",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=EVAL_ROOT / "results",
        help="post-training dataset artifacts 所在的 results 目錄",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=EVAL_ROOT / "outputs" / "post_training",
        help="訓練輸出目錄（adapter / merged model / summary）",
    )
    parser.add_argument("--hf-owner", type=str, default="", help="Hugging Face 使用者或組織名稱")
    parser.add_argument("--artifact-repo", type=str, default="", help="dataset / manifest artifact repo id")
    parser.add_argument("--sft-adapter-repo", type=str, default="", help="SFT adapter model repo id")
    parser.add_argument("--sft-model-repo", type=str, default="", help="merged SFT model repo id")
    parser.add_argument("--dpo-adapter-repo", type=str, default="", help="DPO adapter model repo id")
    parser.add_argument("--dpo-model-repo", type=str, default="", help="merged DPO model repo id")
    parser.add_argument("--trackio-project", type=str, default="job-radar-posttrain", help="Trackio project 名稱")
    parser.add_argument("--trackio-space-id", type=str, default="", help="Trackio space id，例如 username/trackio")
    parser.add_argument(
        "--stages",
        type=str,
        default="sft,dpo",
        help="要執行的 stages，逗號分隔：sft,dpo",
    )
    parser.add_argument("--sft-summary", type=Path, default=None, help="指定 posttrain_sft_dataset summary.json")
    parser.add_argument("--dpo-summary", type=Path, default=None, help="指定 posttrain_dpo_pairs summary.json")
    parser.add_argument(
        "--sft-model-source",
        type=str,
        default="",
        help="若只跑 dpo，可指定 merged SFT model repo 或本地路徑",
    )
    parser.add_argument("--no-4bit", action="store_true", help="停用 QLoRA 4-bit 載入，改用 bf16")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    parser.add_argument("--eval-steps", type=int, default=25, help="eval interval steps")
    parser.add_argument("--save-steps", type=int, default=25, help="save interval steps")
    parser.add_argument("--logging-steps", type=int, default=5, help="logging interval steps")
    parser.add_argument("--lora-r", type=int, default=32, help="LoRA rank")
    parser.add_argument("--lora-alpha", type=int, default=64, help="LoRA alpha")
    parser.add_argument("--lora-dropout", type=float, default=0.05, help="LoRA dropout")
    parser.add_argument(
        "--target-modules",
        type=str,
        default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj",
        help="LoRA target modules，逗號分隔",
    )
    parser.add_argument("--sft-learning-rate", type=float, default=2e-4, help="SFT LoRA learning rate")
    parser.add_argument("--sft-num-train-epochs", type=float, default=2.0, help="SFT epochs")
    parser.add_argument("--sft-per-device-train-batch-size", type=int, default=2, help="SFT batch size")
    parser.add_argument("--sft-gradient-accumulation-steps", type=int, default=8, help="SFT grad accumulation")
    parser.add_argument("--sft-max-length", type=int, default=2048, help="SFT max_length")
    parser.add_argument("--dpo-learning-rate", type=float, default=5e-6, help="DPO LoRA learning rate")
    parser.add_argument("--dpo-num-train-epochs", type=float, default=1.0, help="DPO epochs")
    parser.add_argument("--dpo-per-device-train-batch-size", type=int, default=2, help="DPO batch size")
    parser.add_argument("--dpo-gradient-accumulation-steps", type=int, default=8, help="DPO grad accumulation")
    parser.add_argument("--dpo-max-length", type=int, default=2048, help="DPO max_length")
    parser.add_argument("--dpo-max-prompt-length", type=int, default=1024, help="DPO max_prompt_length")
    parser.add_argument("--dpo-beta", type=float, default=0.1, help="DPO beta")
    return parser.parse_args()


def _infer_owner(explicit_owner: str) -> str:
    if explicit_owner.strip():
        return explicit_owner.strip()
    from huggingface_hub import HfApi

    whoami = HfApi().whoami()
    return str(whoami.get("name") or whoami.get("fullname") or "").strip()


def _build_repo_ids(args: argparse.Namespace, owner: str) -> PostTrainingRepoIds:
    defaults = build_default_repo_ids(owner, args.base_model)
    return PostTrainingRepoIds(
        artifact_repo=args.artifact_repo.strip() or defaults.artifact_repo,
        sft_adapter_repo=args.sft_adapter_repo.strip() or defaults.sft_adapter_repo,
        sft_model_repo=args.sft_model_repo.strip() or defaults.sft_model_repo,
        dpo_adapter_repo=args.dpo_adapter_repo.strip() or defaults.dpo_adapter_repo,
        dpo_model_repo=args.dpo_model_repo.strip() or defaults.dpo_model_repo,
    )


def main() -> None:
    args = parse_args()
    owner = _infer_owner(args.hf_owner)
    if not owner:
        raise RuntimeError("無法推斷 Hugging Face owner，請手動傳 --hf-owner。")
    repo_ids = _build_repo_ids(args, owner)
    stages = tuple(item.strip() for item in args.stages.split(",") if item.strip())
    target_modules = [item.strip() for item in args.target_modules.split(",") if item.strip()]

    summary = run_post_training_pipeline(
        results_dir=args.results_dir.resolve(),
        output_root=args.output_root.resolve(),
        base_model=args.base_model,
        owner=owner,
        sft_summary_path=args.sft_summary.resolve() if args.sft_summary else None,
        dpo_summary_path=args.dpo_summary.resolve() if args.dpo_summary else None,
        repo_ids=repo_ids,
        trackio_project=args.trackio_project,
        trackio_space_id=infer_trackio_space_id(owner, args.trackio_space_id.strip() or None),
        stages=stages,
        load_in_4bit=not args.no_4bit,
        seed=args.seed,
        sft_learning_rate=args.sft_learning_rate,
        sft_num_train_epochs=args.sft_num_train_epochs,
        sft_per_device_train_batch_size=args.sft_per_device_train_batch_size,
        sft_gradient_accumulation_steps=args.sft_gradient_accumulation_steps,
        sft_max_length=args.sft_max_length,
        dpo_learning_rate=args.dpo_learning_rate,
        dpo_num_train_epochs=args.dpo_num_train_epochs,
        dpo_per_device_train_batch_size=args.dpo_per_device_train_batch_size,
        dpo_gradient_accumulation_steps=args.dpo_gradient_accumulation_steps,
        dpo_max_length=args.dpo_max_length,
        dpo_max_prompt_length=args.dpo_max_prompt_length,
        dpo_beta=args.dpo_beta,
        eval_steps=args.eval_steps,
        save_steps=args.save_steps,
        logging_steps=args.logging_steps,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=target_modules,
        sft_model_source=args.sft_model_source.strip() or None,
    )

    print("[done] post-training pipeline complete")
    print(f"[done] summary: {summary['pipeline_summary_path']}")
    print("[done] repos:")
    for key, value in summary["repo_ids"].items():
        print(f"  - {key}: {value}")
    print("[done] page env:")
    print(json.dumps(summary["page_env"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
