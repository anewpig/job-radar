# Colab Post-Training Workflow

這份流程是給 `Qwen/Qwen3-4B-Instruct-2507` 的第一版 `SFT -> DPO` post-training。

目標：
- 從已經生成好的 `posttrain_sft_dataset_*` / `posttrain_dpo_pairs_*` artifacts 讀資料
- 在 Colab A100 跑 `SFT adapter -> merged SFT -> DPO adapter -> merged DPO`
- 自動把 datasets / manifests / training summaries 推到 Hugging Face Hub
- 同時把 Trackio-compatible metrics snapshot 一起推上去，讓 dashboard 可以直接接

## 1. Colab 環境

建議使用：
- Runtime: Python 3.11+
- GPU: A100

在 Colab 第一格執行：

```python
!git clone https://github.com/<your-org-or-user>/<your-repo>.git
%cd <your-repo>
%pip install -U pip
%pip install "datasets>=2.18.0" "trl>=0.12.0" "peft>=0.7.0" "transformers>=4.36.0" "accelerate>=0.24.0" "bitsandbytes>=0.43.0" "huggingface_hub>=0.24.0" "trackio"
```

接著登入 Hugging Face：

```python
from huggingface_hub import notebook_login
notebook_login()
```

## 2. 先確認本地已有 dataset artifacts

你應該至少要有：

- `job-radar-eval/results/posttrain_sft_dataset_*/summary.json`
- `job-radar-eval/results/posttrain_sft_dataset_*/sft_rows.jsonl`
- `job-radar-eval/results/posttrain_dpo_pairs_*/summary.json`
- `job-radar-eval/results/posttrain_dpo_pairs_*/dpo_pairs.jsonl`

如果你沒有指定 `--sft-summary` / `--dpo-summary`，腳本會直接吃最新一份。

## 3. 直接跑完整 pipeline

最小指令：

```bash
python job-radar-eval/scripts/run_post_training_colab.py \
  --hf-owner <your-hf-username>
```

這會自動：
- 建立 / 使用以下 repos
  - `job-radar-...-posttrain-artifacts`
  - `job-radar-...-posttrain-sft-adapter`
  - `job-radar-...-posttrain-sft`
  - `job-radar-...-posttrain-dpo-adapter`
  - `job-radar-...-posttrain-dpo`
- 上傳 versioned + latest dataset artifacts
- 跑 SFT
- push SFT adapter
- merge 並 push SFT model
- 跑 DPO
- push DPO adapter
- merge 並 push DPO model
- 上傳 stage summary 與 Trackio metrics snapshot

## 4. 建議參數

對 Colab A100 的第一版保守設定：

```bash
python job-radar-eval/scripts/run_post_training_colab.py \
  --hf-owner <your-hf-username> \
  --trackio-project job-radar-posttrain \
  --sft-num-train-epochs 2 \
  --sft-learning-rate 2e-4 \
  --sft-per-device-train-batch-size 2 \
  --sft-gradient-accumulation-steps 8 \
  --dpo-num-train-epochs 1 \
  --dpo-learning-rate 5e-6 \
  --dpo-per-device-train-batch-size 2 \
  --dpo-gradient-accumulation-steps 8 \
  --dpo-beta 0.1 \
  --eval-steps 25 \
  --save-steps 25 \
  --logging-steps 5
```

預設會開 `4-bit` 載入。若你想直接用 bf16，可加：

```bash
--no-4bit
```

## 5. 只跑 DPO

如果你已經有 merged SFT model，可以只跑 DPO：

```bash
python job-radar-eval/scripts/run_post_training_colab.py \
  --hf-owner <your-hf-username> \
  --stages dpo \
  --sft-model-source <your-merged-sft-model-repo>
```

## 6. Artifact 佈局

artifact repo 會上傳到：

- `datasets/sft/<dataset_version>/summary.json`
- `datasets/sft/<dataset_version>/sft_rows.jsonl`
- `datasets/sft/latest/summary.json`
- `datasets/sft/latest/sft_rows.jsonl`
- `datasets/dpo/<dataset_version>/summary.json`
- `datasets/dpo/<dataset_version>/dpo_pairs.jsonl`
- `datasets/dpo/latest/summary.json`
- `datasets/dpo/latest/dpo_pairs.jsonl`
- `training/sft/<dataset_version>/summary.json`
- `training/sft/latest/summary.json`
- `training/sft/latest/trackio_metrics.json`
- `training/dpo/<dataset_version>/summary.json`
- `training/dpo/latest/summary.json`
- `training/dpo/latest/trackio_metrics.json`

## 7. 給 dashboard 的 env

腳本跑完會直接印出一組 `page env`。  
你也可以固定用這些路徑：

```bash
JOB_RADAR_POSTTRAIN_SFT_MANIFEST_URL=https://huggingface.co/datasets/<artifact-repo>/resolve/main/datasets/sft/latest/summary.json
JOB_RADAR_POSTTRAIN_DPO_MANIFEST_URL=https://huggingface.co/datasets/<artifact-repo>/resolve/main/datasets/dpo/latest/summary.json
JOB_RADAR_POSTTRAIN_EVAL_MANIFEST_URL=https://huggingface.co/datasets/<artifact-repo>/resolve/main/eval/latest/summary.json
JOB_RADAR_POSTTRAIN_REVIEW_MANIFEST_URL=https://huggingface.co/datasets/<artifact-repo>/resolve/main/review/latest/summary.json
JOB_RADAR_POSTTRAIN_TRACKIO_SFT_URL=https://huggingface.co/datasets/<artifact-repo>/resolve/main/training/sft/latest/trackio_metrics.json
JOB_RADAR_POSTTRAIN_TRACKIO_DPO_URL=https://huggingface.co/datasets/<artifact-repo>/resolve/main/training/dpo/latest/trackio_metrics.json
```

## 8. 訓練完成後跑 Evaluation Comparison

當 `SFT` 與 `DPO` merged model 都已經存在後，接著跑：

```bash
python job-radar-eval/scripts/run_post_training_local_eval.py \
  --sft-model-source <your-sft-model-repo-or-local-dir> \
  --dpo-model-source <your-dpo-model-repo-or-local-dir> \
  --dataset-version <your-dpo-dataset-version> \
  --embedding-api-key $OPENAI_API_KEY \
  --artifact-repo <artifact-repo>
```

如果 base model 也想改成 Hub 上的固定版本，可以額外指定：

```bash
--base-model-source Qwen/Qwen3-4B-Instruct-2507
```

這支腳本會：
- 依序跑 `Base / SFT / DPO` assistant benchmark
- 產生 `summary.json`、`report.md`、`manifest.json`
- 輸出 `assistant_case_rows.csv`
- 輸出 `assistant_eval_comparison_cases.csv/jsonl`
- 輸出三份 stage summary
- 如果提供 `--artifact-repo`，就同步上傳到
  - `eval/<dataset_version>/...`
  - `eval/latest/...`

## 9. 再產生 Review Manifest

如果你已經有人評結果，可以再接：

```bash
python job-radar-eval/scripts/build_post_training_review_manifest.py \
  --review-summary <formal-human-review-summary.json> \
  --comparison-summary <posttrain-eval-summary.json> \
  --dpo-summary <posttrain-dpo-summary.json> \
  --artifact-repo <artifact-repo>
```

這支腳本會產生 review / failure analysis summary，並在指定 artifact repo 時同步上傳到：
- `review/<dataset_version>/...`
- `review/latest/...`

## 10. 現階段沒做的事

這份第一版 workflow 還沒自動做：
- Colab training 結束後自動串接 evaluation script
- Colab training 結束後自動串接 review manifest script

也就是說，現在 `training -> eval -> review` 三段都能跑，但還是分開執行，沒有做成單一一鍵 pipeline。
