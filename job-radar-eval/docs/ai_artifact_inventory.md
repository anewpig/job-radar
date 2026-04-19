# AI Artifact Inventory

這份清單的目的不是列所有檔案，而是區分：

- `runtime-critical`：產品執行路徑需要
- `eval-tooling`：評估 / 論文 / 研究工作流需要
- `removable-artifacts`：可以清理的結果資料

## Runtime-Critical

主專案內，以下屬於產品路徑，不能當成 dead code：

- `src/job_spy_tw/assistant/`
- `src/job_spy_tw/resume/`
- `src/job_spy_tw/openai_usage.py`
- `src/job_spy_tw/store/metrics.py`
- `src/job_spy_tw/product_store.py`
- `src/job_spy_tw/ui/pages_resume_assistant.py`
- `src/job_spy_tw/ui/pages_backend_operations.py`

這些檔案負責：
- RAG retrieval
- assistant output
- resume extraction / matching
- token usage tracking
- AI telemetry / budget
- 產品端監控視圖

## Eval Tooling

外部 eval repo 內，以下屬於研究工具鏈，不是產品 runtime，但也不是 dead code：

- `scripts/run_baseline.py`
- `scripts/run_real_snapshot_eval.py`
- `scripts/run_real_model_eval.py`
- `scripts/run_ai_checks.py`
- `scripts/run_ai_regression.py`
- `scripts/run_latency_regression.py`
- `scripts/run_training_readiness.py`
- `scripts/run_resume_label_eval.py`
- `scripts/run_resume_warm_probe.py`
- `scripts/run_human_review_packet.py`
- `scripts/run_human_review_analysis.py`
- `job_radar_eval/experiment_artifacts.py`
- `job_radar_eval/human_review.py`
- `job_radar_eval/human_review_analysis.py`

這些檔案負責：
- regression
- real snapshot eval
- real model eval
- training readiness gate
- human review packet / aggregation
- thesis-ready artifacts

## Removable Artifacts

以下資料屬於結果產物，不是程式碼。只要已經有較新的等價輸出，就可以清理：

- 舊的 `results/baseline_*`
- 舊的 `results/ai_checks_*`
- 舊的 `results/ai_regression_*`
- 舊的 `results/human_review_packet_*`
- 舊的 `results/human_review_analysis_*`
- 舊的 `results/latency_regression_*`
- 舊的 `results/training_readiness_*`

建議保留策略：

- `baseline_*`：保留最新 `2~3` 份 milestone
- `real_snapshot_*`：保留最新 `2` 份
- `real_model_eval_*`：保留 milestone 與最新 `2` 份
- `human_review_packet_*`：只保留最新正式 packet
- `human_review_analysis_*`：保留最新正式分析與最新 smoke test 各 `1` 份

## Cleanup Rule

清理順序：

1. 先看 `manifest.json` 是否存在
2. 再看是否已有更新版本的等價輸出
3. 只刪 `results/` 內的 run directory
4. 不刪：
   - `fixtures/`
   - `job_radar_eval/`
   - `scripts/`
   - 主專案 `src/`
