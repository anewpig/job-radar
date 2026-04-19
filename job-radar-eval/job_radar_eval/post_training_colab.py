"""Colab-oriented SFT -> DPO training workflow for post-training artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
import json
from pathlib import Path
import tempfile
from typing import Any, Iterable


POSTTRAIN_SYSTEM_PROMPT = (
    "你是 Job Radar AI 助理。請依 answer_mode 產出結構化 JSON，欄位固定為 "
    "summary、key_points、limitations、next_step。"
)


@dataclass(slots=True)
class PostTrainingRepoIds:
    artifact_repo: str
    sft_adapter_repo: str
    sft_model_repo: str
    dpo_adapter_repo: str
    dpo_model_repo: str


@dataclass(slots=True)
class TrainingInputBundle:
    sft_summary_path: Path
    sft_rows_path: Path
    sft_dataset_version: str
    dpo_summary_path: Path
    dpo_rows_path: Path
    dpo_dataset_version: str


def _slugify(text: str) -> str:
    parts = []
    for char in str(text or "").lower():
        if char.isalnum():
            parts.append(char)
        else:
            parts.append("-")
    return "-".join(filter(None, "".join(parts).split("-")))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def resolve_latest_summary(results_dir: Path, prefix: str) -> Path:
    matches = sorted(results_dir.glob(f"{prefix}_*/summary.json"))
    if not matches:
        raise FileNotFoundError(f"找不到 {prefix}_*/summary.json")
    return matches[-1].resolve()


def resolve_training_inputs(
    *,
    results_dir: Path,
    sft_summary_path: Path | None = None,
    dpo_summary_path: Path | None = None,
) -> TrainingInputBundle:
    sft_summary_path = (sft_summary_path or resolve_latest_summary(results_dir, "posttrain_sft_dataset")).resolve()
    dpo_summary_path = (dpo_summary_path or resolve_latest_summary(results_dir, "posttrain_dpo_pairs")).resolve()
    sft_rows_path = sft_summary_path.parent / "sft_rows.jsonl"
    dpo_rows_path = dpo_summary_path.parent / "dpo_pairs.jsonl"
    if not sft_rows_path.exists():
        raise FileNotFoundError(f"找不到 SFT rows: {sft_rows_path}")
    if not dpo_rows_path.exists():
        raise FileNotFoundError(f"找不到 DPO rows: {dpo_rows_path}")
    sft_summary = _load_json(sft_summary_path)
    dpo_summary = _load_json(dpo_summary_path)
    return TrainingInputBundle(
        sft_summary_path=sft_summary_path,
        sft_rows_path=sft_rows_path.resolve(),
        sft_dataset_version=str(sft_summary.get("dataset_version", "")).strip(),
        dpo_summary_path=dpo_summary_path,
        dpo_rows_path=dpo_rows_path.resolve(),
        dpo_dataset_version=str(dpo_summary.get("dataset_version", "")).strip(),
    )


def build_default_repo_ids(owner: str, base_model: str) -> PostTrainingRepoIds:
    model_slug = _slugify(base_model.split("/")[-1]).replace("-instruct-2507", "").replace("-instruct", "")
    prefix = f"{owner}/job-radar-{model_slug}-posttrain"
    return PostTrainingRepoIds(
        artifact_repo=f"{prefix}-artifacts",
        sft_adapter_repo=f"{prefix}-sft-adapter",
        sft_model_repo=f"{prefix}-sft",
        dpo_adapter_repo=f"{prefix}-dpo-adapter",
        dpo_model_repo=f"{prefix}-dpo",
    )


def infer_trackio_space_id(owner: str, explicit_space_id: str | None = None) -> str:
    if explicit_space_id:
        return explicit_space_id
    return f"{owner}/trackio"


def build_stage_run_name(stage: str, dataset_version: str, *, suffix: str | None = None) -> str:
    timestamp = suffix or datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{stage}-{dataset_version}-{timestamp}"


def build_page_env_suggestions(
    repo_ids: PostTrainingRepoIds,
    *,
    base_model: str = "",
    trackio_project: str = "",
    latest_sft_run_id: str = "",
    latest_dpo_run_id: str = "",
) -> dict[str, str]:
    artifact_base = f"https://huggingface.co/datasets/{repo_ids.artifact_repo}/resolve/main"
    return {
        "JOB_RADAR_POSTTRAIN_SFT_MANIFEST_URL": f"{artifact_base}/datasets/sft/latest/summary.json",
        "JOB_RADAR_POSTTRAIN_DPO_MANIFEST_URL": f"{artifact_base}/datasets/dpo/latest/summary.json",
        "JOB_RADAR_POSTTRAIN_EVAL_MANIFEST_URL": f"{artifact_base}/eval/latest/summary.json",
        "JOB_RADAR_POSTTRAIN_REVIEW_MANIFEST_URL": f"{artifact_base}/review/latest/summary.json",
        "JOB_RADAR_POSTTRAIN_TRACKIO_SFT_URL": f"{artifact_base}/training/sft/latest/trackio_metrics.json",
        "JOB_RADAR_POSTTRAIN_TRACKIO_DPO_URL": f"{artifact_base}/training/dpo/latest/trackio_metrics.json",
        "JOB_RADAR_POSTTRAIN_BASE_MODEL": base_model,
        "JOB_RADAR_POSTTRAIN_SFT_ADAPTER_REPO": repo_ids.sft_adapter_repo,
        "JOB_RADAR_POSTTRAIN_SFT_MODEL_REPO": repo_ids.sft_model_repo,
        "JOB_RADAR_POSTTRAIN_DPO_ADAPTER_REPO": repo_ids.dpo_adapter_repo,
        "JOB_RADAR_POSTTRAIN_DPO_MODEL_REPO": repo_ids.dpo_model_repo,
        "JOB_RADAR_POSTTRAIN_DATASET_REPO": repo_ids.artifact_repo,
        "JOB_RADAR_POSTTRAIN_ARTIFACT_REPO": repo_ids.artifact_repo,
        "JOB_RADAR_POSTTRAIN_TRACKIO_PROJECT": trackio_project,
        "JOB_RADAR_POSTTRAIN_TRACKIO_SFT_RUN_ID": latest_sft_run_id,
        "JOB_RADAR_POSTTRAIN_TRACKIO_DPO_RUN_ID": latest_dpo_run_id,
    }


def normalize_sft_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        messages = row.get("messages")
        if not isinstance(messages, list) or not messages:
            continue
        normalized.append(
            {
                "id": row.get("id", ""),
                "question": row.get("question", ""),
                "answer_mode": row.get("answer_mode", ""),
                "messages": messages,
                "split": row.get("split", "train"),
                "quality_tag": row.get("quality_tag", ""),
                "review_status": row.get("review_status", ""),
                "source_artifact": row.get("source_artifact", ""),
                "source_run": row.get("source_run", ""),
                "citation_count": row.get("citation_count", 0),
                "citation_keyword_recall": row.get("citation_keyword_recall", 0.0),
                "evidence_sufficient": row.get("evidence_sufficient", False),
                "quality_score": row.get("quality_score", 0.0),
            }
        )
    return normalized


def _normalize_prompt_messages(prompt: Any) -> list[dict[str, str]]:
    if isinstance(prompt, list):
        return [
            {"role": str(item.get("role", "user")), "content": str(item.get("content", "")).strip()}
            for item in prompt
            if isinstance(item, dict) and str(item.get("content", "")).strip()
        ]
    if isinstance(prompt, dict):
        prompt_text = json.dumps(prompt, ensure_ascii=False)
    else:
        prompt_text = str(prompt or "").strip()
    if not prompt_text:
        return []
    try:
        parsed = json.loads(prompt_text)
    except json.JSONDecodeError:
        parsed = None
    user_content = prompt_text
    if isinstance(parsed, dict):
        user_content = json.dumps(
            {
                "answer_mode": parsed.get("answer_mode", ""),
                "question": parsed.get("question", ""),
            },
            ensure_ascii=False,
        )
    return [
        {"role": "system", "content": POSTTRAIN_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def normalize_dpo_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        prompt_messages = _normalize_prompt_messages(row.get("prompt"))
        chosen = str(row.get("chosen", "")).strip()
        rejected = str(row.get("rejected", "")).strip()
        if not prompt_messages or not chosen or not rejected:
            continue
        normalized.append(
            {
                "id": row.get("id", ""),
                "question": row.get("question", ""),
                "answer_mode": row.get("answer_mode", ""),
                "prompt": prompt_messages,
                "chosen": [{"role": "assistant", "content": chosen}],
                "rejected": [{"role": "assistant", "content": rejected}],
                "pair_rule": row.get("pair_rule", ""),
                "split": row.get("split", "train"),
                "chosen_source": row.get("chosen_source", ""),
                "rejected_source": row.get("rejected_source", ""),
                "chosen_artifact": row.get("chosen_artifact", ""),
                "rejected_artifact": row.get("rejected_artifact", ""),
                "score_gap": row.get("score_gap", 0.0),
                "similarity": row.get("similarity", 0.0),
            }
        )
    return normalized


def split_rows(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("split", "")).strip() == "train":
            train_rows.append(dict(row))
        else:
            eval_rows.append(dict(row))
    return train_rows, eval_rows


def ensure_hf_repos(repo_ids: PostTrainingRepoIds) -> dict[str, str]:
    from huggingface_hub import HfApi

    api = HfApi()
    created: dict[str, str] = {}
    for repo_id, repo_type in (
        (repo_ids.artifact_repo, "dataset"),
        (repo_ids.sft_adapter_repo, "model"),
        (repo_ids.sft_model_repo, "model"),
        (repo_ids.dpo_adapter_repo, "model"),
        (repo_ids.dpo_model_repo, "model"),
    ):
        api.create_repo(repo_id=repo_id, repo_type=repo_type, exist_ok=True, private=False)
        created[repo_id] = repo_type
    return created


def _upload_file(api, *, repo_id: str, repo_type: str, local_path: Path, remote_path: str, commit_message: str) -> None:
    api.upload_file(
        path_or_fileobj=str(local_path.resolve()),
        path_in_repo=remote_path,
        repo_id=repo_id,
        repo_type=repo_type,
        commit_message=commit_message,
    )


def publish_dataset_artifacts(
    *,
    repo_ids: PostTrainingRepoIds,
    inputs: TrainingInputBundle,
) -> dict[str, Any]:
    from huggingface_hub import HfApi

    api = HfApi()
    uploads: list[dict[str, str]] = []
    plans = [
        ("sft", inputs.sft_dataset_version, inputs.sft_summary_path, inputs.sft_rows_path),
        ("dpo", inputs.dpo_dataset_version, inputs.dpo_summary_path, inputs.dpo_rows_path),
    ]
    for stage, dataset_version, summary_path, rows_path in plans:
        base_dir = summary_path.parent
        for local_path, name in (
            (summary_path, "summary.json"),
            (base_dir / "manifest.json", "manifest.json"),
            (base_dir / "report.md", "report.md"),
            (rows_path, rows_path.name),
            (base_dir / rows_path.with_suffix(".csv").name, rows_path.with_suffix(".csv").name),
        ):
            if not local_path.exists():
                continue
            for remote_path in (
                f"datasets/{stage}/{dataset_version}/{name}",
                f"datasets/{stage}/latest/{name}",
            ):
                _upload_file(
                    api,
                    repo_id=repo_ids.artifact_repo,
                    repo_type="dataset",
                    local_path=local_path,
                    remote_path=remote_path,
                    commit_message=f"Upload {stage} {name}",
                )
                uploads.append({"local_path": str(local_path.resolve()), "remote_path": remote_path})
    return {"artifact_repo": repo_ids.artifact_repo, "uploads": uploads}


def _coerce_json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return {str(key): _coerce_json_safe(item) for key, item in asdict(value).items()}
    if isinstance(value, Path):
        return str(value.resolve())
    if isinstance(value, dict):
        return {str(key): _coerce_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_coerce_json_safe(item) for item in value]
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(_coerce_json_safe(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def _extract_numeric_metrics(payload: dict[str, Any]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for key, value in payload.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            metrics[key] = float(value)
    return metrics


def _build_local_datasets(rows: list[dict[str, Any]]):
    from datasets import Dataset

    train_rows, eval_rows = split_rows(rows)
    train_dataset = Dataset.from_list(train_rows)
    eval_dataset = Dataset.from_list(eval_rows) if eval_rows else None
    return train_dataset, eval_dataset, len(train_rows), len(eval_rows)


def _load_tokenizer(model_name_or_path: str):
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)
    if tokenizer.pad_token is None and tokenizer.eos_token is not None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    return tokenizer


def _load_causal_lm(
    model_name_or_path: str,
    *,
    load_in_4bit: bool,
):
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig

    if load_in_4bit:
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.bfloat16,
        )
        from peft import prepare_model_for_kbit_training

        return prepare_model_for_kbit_training(model)
    return AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )


def _build_lora_config(
    *,
    r: int,
    alpha: int,
    dropout: float,
    target_modules: list[str],
):
    from peft import LoraConfig

    return LoraConfig(
        r=r,
        lora_alpha=alpha,
        lora_dropout=dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=target_modules,
    )


def _trackio_module(
    *,
    project: str,
    run_name: str,
    space_id: str | None,
    config: dict[str, Any],
    group: str | None,
):
    import trackio

    init_kwargs = {
        "project": project,
        "config": config,
        "name": run_name,
    }
    if space_id:
        init_kwargs["space_id"] = space_id
    if group:
        init_kwargs["group"] = group
    trackio.init(**init_kwargs)
    return trackio


def _build_trackio_callback(stage: str):
    import time
    import torch
    from transformers import TrainerCallback

    class TrackioRuntimeCallback(TrainerCallback):
        def __init__(self) -> None:
            self.started_at = time.time()
            self.rows: list[dict[str, Any]] = []

        def on_train_begin(self, args, state, control, **kwargs):
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()

        def on_log(self, args, state, control, logs=None, **kwargs):
            import trackio

            payload = _extract_numeric_metrics(logs or {})
            payload["global_step"] = float(state.global_step)
            if state.epoch is not None:
                payload["epoch"] = float(state.epoch)
            payload["elapsed_time"] = float(time.time() - self.started_at)
            if torch.cuda.is_available():
                payload["max_gpu_memory"] = float(torch.cuda.max_memory_allocated() / (1024**3))
            if payload:
                trackio.log(payload)
                timestamp = datetime.now().isoformat(timespec="seconds")
                for metric_name, value in payload.items():
                    self.rows.append(
                        {
                            "stage": stage,
                            "metric_name": metric_name,
                            "step": float(state.global_step),
                            "value": float(value),
                            "timestamp": timestamp,
                        }
                    )

        def on_train_end(self, args, state, control, **kwargs):
            import trackio

            final_payload = {
                "elapsed_time": float(time.time() - self.started_at),
            }
            if torch.cuda.is_available():
                final_payload["max_gpu_memory"] = float(torch.cuda.max_memory_allocated() / (1024**3))
            trackio.log(final_payload)

    return TrackioRuntimeCallback()


def _merge_adapter_to_model(
    *,
    base_model: str,
    adapter_source: str,
    merged_repo_id: str,
    output_dir: Path,
) -> dict[str, Any]:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM

    tokenizer = _load_tokenizer(adapter_source)
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(base, adapter_source)
    merged = model.merge_and_unload()
    merged.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    merged.push_to_hub(merged_repo_id)
    tokenizer.push_to_hub(merged_repo_id)
    return {
        "base_model": base_model,
        "adapter_source": adapter_source,
        "merged_repo_id": merged_repo_id,
        "local_output_dir": str(output_dir.resolve()),
    }


def _stage_output_dir(output_root: Path, stage: str, run_name: str) -> Path:
    path = output_root / stage / run_name
    path.mkdir(parents=True, exist_ok=True)
    return path


def train_sft_stage(
    *,
    base_model: str,
    sft_rows_path: Path,
    dataset_version: str,
    repo_ids: PostTrainingRepoIds,
    trackio_project: str,
    trackio_space_id: str | None,
    output_root: Path,
    run_name: str,
    load_in_4bit: bool,
    seed: int,
    learning_rate: float,
    num_train_epochs: float,
    per_device_train_batch_size: int,
    gradient_accumulation_steps: int,
    max_length: int,
    eval_steps: int,
    save_steps: int,
    logging_steps: int,
    lora_r: int,
    lora_alpha: int,
    lora_dropout: float,
    target_modules: list[str],
) -> dict[str, Any]:
    from trl import SFTConfig, SFTTrainer

    rows = normalize_sft_rows(load_jsonl(sft_rows_path))
    train_dataset, eval_dataset, train_count, eval_count = _build_local_datasets(rows)
    stage_output_dir = _stage_output_dir(output_root, "sft", run_name)
    local_adapter_dir = stage_output_dir / "adapter"
    local_merged_dir = stage_output_dir / "merged"
    tokenizer = _load_tokenizer(base_model)
    model = _load_causal_lm(base_model, load_in_4bit=load_in_4bit)
    trackio = _trackio_module(
        project=trackio_project,
        run_name=run_name,
        space_id=trackio_space_id,
        config={
            "stage": "sft",
            "dataset_version": dataset_version,
            "base_model": base_model,
            "hub_model_id": repo_ids.sft_adapter_repo,
            "artifact_repo": repo_ids.artifact_repo,
        },
        group="post-training",
    )
    callback = _build_trackio_callback("sft")
    trainer = SFTTrainer(
        model=model,
        args=SFTConfig(
            output_dir=str(local_adapter_dir),
            push_to_hub=True,
            hub_model_id=repo_ids.sft_adapter_repo,
            hub_strategy="end",
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_ratio=0.1,
            lr_scheduler_type="cosine",
            logging_steps=logging_steps,
            save_strategy="steps",
            save_steps=save_steps,
            save_total_limit=2,
            eval_strategy="steps" if eval_dataset is not None else "no",
            eval_steps=eval_steps,
            load_best_model_at_end=eval_dataset is not None,
            metric_for_best_model="eval_loss" if eval_dataset is not None else None,
            greater_is_better=False if eval_dataset is not None else None,
            max_length=max_length,
            bf16=True,
            gradient_checkpointing=True,
            report_to="trackio",
            run_name=run_name,
            seed=seed,
            assistant_only_loss=True,
        ),
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        peft_config=_build_lora_config(
            r=lora_r,
            alpha=lora_alpha,
            dropout=lora_dropout,
            target_modules=target_modules,
        ),
        processing_class=tokenizer,
        callbacks=[callback],
    )
    train_result = trainer.train()
    trainer.push_to_hub(commit_message=f"Upload SFT adapter for {run_name}")
    tokenizer.push_to_hub(repo_ids.sft_adapter_repo)
    merged_summary = _merge_adapter_to_model(
        base_model=base_model,
        adapter_source=str(local_adapter_dir.resolve()),
        merged_repo_id=repo_ids.sft_model_repo,
        output_dir=local_merged_dir,
    )
    stage_summary = {
        "stage": "sft",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset_version": dataset_version,
        "base_model": base_model,
        "adapter_repo": repo_ids.sft_adapter_repo,
        "merged_model_repo": repo_ids.sft_model_repo,
        "artifact_repo": repo_ids.artifact_repo,
        "trackio_project": trackio_project,
        "trackio_space_id": trackio_space_id or "",
        "run_name": run_name,
        "train_rows": train_count,
        "eval_rows": eval_count,
        "best_checkpoint": trainer.state.best_model_checkpoint or "",
        "training_metrics": _extract_numeric_metrics(train_result.metrics),
        "trackio_metric_rows": callback.rows,
        "local_adapter_dir": str(local_adapter_dir.resolve()),
        "local_merged_dir": str(local_merged_dir.resolve()),
        "merge": merged_summary,
    }
    _write_json(stage_output_dir / "summary.json", stage_summary)
    _write_json(stage_output_dir / "trackio_metrics.json", {"rows": callback.rows, "updated_at": stage_summary["generated_at"]})
    trackio.finish()
    return stage_summary


def train_dpo_stage(
    *,
    model_source: str,
    dpo_rows_path: Path,
    dataset_version: str,
    repo_ids: PostTrainingRepoIds,
    trackio_project: str,
    trackio_space_id: str | None,
    output_root: Path,
    run_name: str,
    load_in_4bit: bool,
    seed: int,
    learning_rate: float,
    num_train_epochs: float,
    per_device_train_batch_size: int,
    gradient_accumulation_steps: int,
    max_length: int,
    max_prompt_length: int,
    beta: float,
    eval_steps: int,
    save_steps: int,
    logging_steps: int,
    lora_r: int,
    lora_alpha: int,
    lora_dropout: float,
    target_modules: list[str],
) -> dict[str, Any]:
    from trl import DPOConfig, DPOTrainer

    rows = normalize_dpo_rows(load_jsonl(dpo_rows_path))
    train_dataset, eval_dataset, train_count, eval_count = _build_local_datasets(rows)
    stage_output_dir = _stage_output_dir(output_root, "dpo", run_name)
    local_adapter_dir = stage_output_dir / "adapter"
    local_merged_dir = stage_output_dir / "merged"
    tokenizer = _load_tokenizer(model_source)
    model = _load_causal_lm(model_source, load_in_4bit=load_in_4bit)
    trackio = _trackio_module(
        project=trackio_project,
        run_name=run_name,
        space_id=trackio_space_id,
        config={
            "stage": "dpo",
            "dataset_version": dataset_version,
            "base_model": model_source,
            "hub_model_id": repo_ids.dpo_adapter_repo,
            "artifact_repo": repo_ids.artifact_repo,
        },
        group="post-training",
    )
    callback = _build_trackio_callback("dpo")
    trainer = DPOTrainer(
        model=model,
        args=DPOConfig(
            output_dir=str(local_adapter_dir),
            push_to_hub=True,
            hub_model_id=repo_ids.dpo_adapter_repo,
            hub_strategy="end",
            beta=beta,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_ratio=0.1,
            lr_scheduler_type="cosine",
            logging_steps=logging_steps,
            save_strategy="steps",
            save_steps=save_steps,
            save_total_limit=2,
            eval_strategy="steps" if eval_dataset is not None else "no",
            eval_steps=eval_steps,
            load_best_model_at_end=eval_dataset is not None,
            metric_for_best_model="eval_loss" if eval_dataset is not None else None,
            greater_is_better=False if eval_dataset is not None else None,
            max_length=max_length,
            max_prompt_length=max_prompt_length,
            bf16=True,
            gradient_checkpointing=True,
            report_to="trackio",
            run_name=run_name,
            seed=seed,
        ),
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        peft_config=_build_lora_config(
            r=lora_r,
            alpha=lora_alpha,
            dropout=lora_dropout,
            target_modules=target_modules,
        ),
        processing_class=tokenizer,
        callbacks=[callback],
    )
    train_result = trainer.train()
    trainer.push_to_hub(commit_message=f"Upload DPO adapter for {run_name}")
    tokenizer.push_to_hub(repo_ids.dpo_adapter_repo)
    merged_summary = _merge_adapter_to_model(
        base_model=model_source,
        adapter_source=str(local_adapter_dir.resolve()),
        merged_repo_id=repo_ids.dpo_model_repo,
        output_dir=local_merged_dir,
    )
    stage_summary = {
        "stage": "dpo",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset_version": dataset_version,
        "base_model": model_source,
        "adapter_repo": repo_ids.dpo_adapter_repo,
        "merged_model_repo": repo_ids.dpo_model_repo,
        "artifact_repo": repo_ids.artifact_repo,
        "trackio_project": trackio_project,
        "trackio_space_id": trackio_space_id or "",
        "run_name": run_name,
        "train_rows": train_count,
        "eval_rows": eval_count,
        "best_checkpoint": trainer.state.best_model_checkpoint or "",
        "training_metrics": _extract_numeric_metrics(train_result.metrics),
        "trackio_metric_rows": callback.rows,
        "local_adapter_dir": str(local_adapter_dir.resolve()),
        "local_merged_dir": str(local_merged_dir.resolve()),
        "merge": merged_summary,
    }
    _write_json(stage_output_dir / "summary.json", stage_summary)
    _write_json(stage_output_dir / "trackio_metrics.json", {"rows": callback.rows, "updated_at": stage_summary["generated_at"]})
    trackio.finish()
    return stage_summary


def publish_training_summary(
    *,
    repo_ids: PostTrainingRepoIds,
    stage: str,
    summary: dict[str, Any],
) -> dict[str, str]:
    from huggingface_hub import HfApi

    api = HfApi()
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        handle.write(json.dumps(_coerce_json_safe(summary), ensure_ascii=False, indent=2))
        temp_path = Path(handle.name)
    trackio_snapshot = {
        "rows": list(summary.get("trackio_metric_rows", [])),
        "updated_at": str(summary.get("generated_at", "")),
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        handle.write(json.dumps(_coerce_json_safe(trackio_snapshot), ensure_ascii=False, indent=2))
        trackio_path = Path(handle.name)
    try:
        version = str(summary.get("dataset_version", "unknown"))
        uploads = {}
        for remote_path in (
            f"training/{stage}/{version}/summary.json",
            f"training/{stage}/latest/summary.json",
        ):
            _upload_file(
                api,
                repo_id=repo_ids.artifact_repo,
                repo_type="dataset",
                local_path=temp_path,
                remote_path=remote_path,
                commit_message=f"Upload {stage} training summary",
            )
            uploads[remote_path] = f"https://huggingface.co/datasets/{repo_ids.artifact_repo}/resolve/main/{remote_path}"
        for remote_path in (
            f"training/{stage}/{version}/trackio_metrics.json",
            f"training/{stage}/latest/trackio_metrics.json",
        ):
            _upload_file(
                api,
                repo_id=repo_ids.artifact_repo,
                repo_type="dataset",
                local_path=trackio_path,
                remote_path=remote_path,
                commit_message=f"Upload {stage} trackio metrics snapshot",
            )
            uploads[remote_path] = f"https://huggingface.co/datasets/{repo_ids.artifact_repo}/resolve/main/{remote_path}"
        return uploads
    finally:
        temp_path.unlink(missing_ok=True)
        trackio_path.unlink(missing_ok=True)


def run_post_training_pipeline(
    *,
    results_dir: Path,
    output_root: Path,
    base_model: str,
    owner: str,
    sft_summary_path: Path | None,
    dpo_summary_path: Path | None,
    repo_ids: PostTrainingRepoIds | None,
    trackio_project: str,
    trackio_space_id: str | None,
    stages: tuple[str, ...],
    load_in_4bit: bool,
    seed: int,
    sft_learning_rate: float,
    sft_num_train_epochs: float,
    sft_per_device_train_batch_size: int,
    sft_gradient_accumulation_steps: int,
    sft_max_length: int,
    dpo_learning_rate: float,
    dpo_num_train_epochs: float,
    dpo_per_device_train_batch_size: int,
    dpo_gradient_accumulation_steps: int,
    dpo_max_length: int,
    dpo_max_prompt_length: int,
    dpo_beta: float,
    eval_steps: int,
    save_steps: int,
    logging_steps: int,
    lora_r: int,
    lora_alpha: int,
    lora_dropout: float,
    target_modules: list[str],
    sft_model_source: str | None = None,
) -> dict[str, Any]:
    inputs = resolve_training_inputs(
        results_dir=results_dir,
        sft_summary_path=sft_summary_path,
        dpo_summary_path=dpo_summary_path,
    )
    repo_ids = repo_ids or build_default_repo_ids(owner, base_model)
    ensure_hf_repos(repo_ids)
    dataset_uploads = publish_dataset_artifacts(repo_ids=repo_ids, inputs=inputs)

    summary: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "base_model": base_model,
        "repo_ids": _coerce_json_safe(repo_ids),
        "dataset_inputs": _coerce_json_safe(inputs),
        "dataset_uploads": dataset_uploads,
        "trackio_project": trackio_project,
        "trackio_space_id": trackio_space_id or "",
        "stages": list(stages),
        "page_env": build_page_env_suggestions(
            repo_ids,
            base_model=base_model,
            trackio_project=trackio_project,
        ),
    }

    if "sft" in stages:
        sft_run_name = build_stage_run_name("sft", inputs.sft_dataset_version)
        sft_summary = train_sft_stage(
            base_model=base_model,
            sft_rows_path=inputs.sft_rows_path,
            dataset_version=inputs.sft_dataset_version,
            repo_ids=repo_ids,
            trackio_project=trackio_project,
            trackio_space_id=trackio_space_id,
            output_root=output_root,
            run_name=sft_run_name,
            load_in_4bit=load_in_4bit,
            seed=seed,
            learning_rate=sft_learning_rate,
            num_train_epochs=sft_num_train_epochs,
            per_device_train_batch_size=sft_per_device_train_batch_size,
            gradient_accumulation_steps=sft_gradient_accumulation_steps,
            max_length=sft_max_length,
            eval_steps=eval_steps,
            save_steps=save_steps,
            logging_steps=logging_steps,
            lora_r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            target_modules=target_modules,
        )
        summary["sft"] = sft_summary
        summary["sft_summary_urls"] = publish_training_summary(repo_ids=repo_ids, stage="sft", summary=sft_summary)
        sft_model_source = sft_summary["local_merged_dir"]

    if "dpo" in stages:
        if not sft_model_source:
            raise ValueError("DPO 需要 merged SFT model，請先執行 SFT 或提供 sft_model_source。")
        dpo_run_name = build_stage_run_name("dpo", inputs.dpo_dataset_version)
        dpo_summary = train_dpo_stage(
            model_source=sft_model_source,
            dpo_rows_path=inputs.dpo_rows_path,
            dataset_version=inputs.dpo_dataset_version,
            repo_ids=repo_ids,
            trackio_project=trackio_project,
            trackio_space_id=trackio_space_id,
            output_root=output_root,
            run_name=dpo_run_name,
            load_in_4bit=load_in_4bit,
            seed=seed,
            learning_rate=dpo_learning_rate,
            num_train_epochs=dpo_num_train_epochs,
            per_device_train_batch_size=dpo_per_device_train_batch_size,
            gradient_accumulation_steps=dpo_gradient_accumulation_steps,
            max_length=dpo_max_length,
            max_prompt_length=dpo_max_prompt_length,
            beta=dpo_beta,
            eval_steps=eval_steps,
            save_steps=save_steps,
            logging_steps=logging_steps,
            lora_r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            target_modules=target_modules,
        )
        summary["dpo"] = dpo_summary
        summary["dpo_summary_urls"] = publish_training_summary(repo_ids=repo_ids, stage="dpo", summary=dpo_summary)

    summary["page_env"] = build_page_env_suggestions(
        repo_ids,
        base_model=base_model,
        trackio_project=trackio_project,
        latest_sft_run_id=str(summary.get("sft", {}).get("run_name", "")),
        latest_dpo_run_id=str(summary.get("dpo", {}).get("run_name", "")),
    )
    output_root.mkdir(parents=True, exist_ok=True)
    pipeline_summary_path = output_root / "post_training_pipeline_summary.json"
    _write_json(pipeline_summary_path, summary)
    summary["pipeline_summary_path"] = str(pipeline_summary_path.resolve())
    return summary
