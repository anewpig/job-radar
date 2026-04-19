# Job Radar Evaluation Framework

這個資料夾是獨立於主專案 `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲` 的評估工作區。

目的：
- 建立可重跑的 baseline 評估流程
- 保存每次評估的延遲、品質代理指標與原始輸出
- 產出可直接放進論文/報告的 Markdown 報告

目前涵蓋三個核心評估對象：
- `assistant/service.py`：AI 助理問答
- `resume/service.py`：履歷解析與職缺匹配
- `assistant/retrieval.py`：知識片段檢索

目前有兩條評估線：
- `fixture baseline`：固定題集回歸
- `real snapshot smoke`：真實 `jobs_latest.json` 流程檢查
- `real model eval`：用真實模型設定跑 fixture + real snapshot

## 目錄結構
- `fixtures/`：固定測題與測例
- `job_radar_eval/`：評估邏輯
- `scripts/`：可直接執行的腳本
- `results/`：每次執行後保存的數據與報告
- `docs/`：評估方法與論文模板

## 如何執行
請使用主專案的虛擬環境：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_baseline.py
```

若要指定迭代次數：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_baseline.py --iterations 7
```

若要只跑真實快照：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_real_snapshot_eval.py
```

若要跑整合 AI checks：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_ai_checks.py
```

若要跑 `resume_match_labels` 排序評估：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_resume_label_eval.py
```


若要跑真實模型評估：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_real_model_eval.py
```

日常檢查建議先跑 `pilot`：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_real_model_eval.py --profile pilot
```

`pilot` 預設會套用：
- `fixture_case_limit = 18`
- `real_case_limit = 8`

若要自訂大小或跑更完整的檢查，再加 `--fixture-case-limit` / `--real-case-limit`。

第一次打真實模型時，建議配合低迭代數：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_real_model_eval.py --profile pilot --fixture-iterations 1 --real-iterations 1
```

若目前 `jobs_latest.json` 只有單一角色，想補 `job_comparison` 的真實模型驗證，可以先組一份多角色 eval snapshot：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/build_eval_snapshot.py \
  --snapshot-path /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/jobs_latest.json \
  --snapshot-path /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/releases/personal_use_20260401_235434/data/jobs_latest.json
```

接著把輸出的 `comparison_snapshot.json` 丟給 `run_real_model_eval.py --snapshot-path ...`。

## 產出內容
每次執行都會在 `results/<timestamp>/` 生成：
- `summary.json`
- `manifest.json`
- `assistant_cases.csv`
- `assistant_cases.jsonl`
- `resume_cases.csv`
- `resume_cases.jsonl`
- `report.md`
- `retrieval_cases.csv`
- `retrieval_cases.jsonl`

`resume label eval` 會在 `results/resume_label_eval_<timestamp>/` 生成：
- `summary.json`
- `manifest.json`
- `resume_label_cases.csv`
- `resume_label_cases.jsonl`
- `report.md`

整合 AI checks 會在 `results/ai_checks_<timestamp>/` 下生成：
- `summary.json`
- `manifest.json`
- `report.md`
- `baseline/`
- `real_snapshot/`

真實模型評估會在 `results/real_model_eval_<timestamp>/` 下生成：
- `summary.json`
- `manifest.json`
- `report.md`
- `fixture/`
- `real_snapshot/`

`manifest.json` 會記：
- git commit / branch / dirty state
- model config
- dataset fixture 指紋
- snapshot 指紋
- CLI args
- case export 清單

這份 manifest 很適合直接拿來做論文或實驗紀錄的追溯資料。

若要產生 assistant 人工評分 packet：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_human_review_packet.py --limit 12
```

這會自動抓最新的 `real_model_eval` assistant case export，並生成：
- `assistant_review_packet_blind.csv`
- `assistant_review_packet_blind.jsonl`
- `assistant_review_packet_research.csv`
- `assistant_review_packet_research.jsonl`
- `manifest.json`

評分規則請看：
- `docs/human_review_rubric.md`
- 正式 reviewer 執行流程：
  - `docs/formal_human_review_workflow.md`

建議：
- reviewer 實際填寫時用 `blind` 版本
- 研究者自己做誤差分析時用 `research` 版本

若要把最新版 packet 整理成可直接發給 `r1 / r2` 的 reviewer bundle：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_formal_reviewer_bundle.py --reviewer-ids r1,r2
```

這會生成：
- `assistant_review_r1.csv`
- `assistant_review_r2.csv`
- `human_review_rubric.md`
- `formal_human_review_workflow.md`
- `README.md`
- `manifest.json`

若要彙整 reviewer 填完的結果：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_human_review_analysis.py \
  /path/to/reviewer_a.csv \
  /path/to/reviewer_b.csv
```

若要先驗證 reviewer 回傳檔格式是否正確：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_human_review_validation.py \
  /path/to/reviewer_a.csv \
  /path/to/reviewer_b.csv \
  --require-completed
```

若要直接跑正式 human review（先驗證，再彙整）：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_formal_human_review.py \
  /path/to/reviewer_a.csv \
  /path/to/reviewer_b.csv
```

這會生成：
- `summary.json`
- `report.md`
- `human_review_rows.csv/jsonl`
- `human_review_case_summary.csv/jsonl`
- `human_review_reviewer_summary.csv/jsonl`
- `thesis_tables.md`
- `thesis_tables.tex`

## 指標說明
### AI 助理
- `build_chunks_ms`
- `retrieve_ms`
- `llm_ms`
- `total_ms`
- `keyword_recall`
- `citation_ok`
- `used_chunks`

### 履歷匹配
- `build_profile_ms`
- `match_jobs_ms`
- `total_ms`
- `top1_url_match`
- `top1_role_match`
- `matched_skill_recall`
- `missing_skill_recall`

### Retrieval
- `cold_ms`
- `warm_ms`
- `speedup_ratio`
- `top1_hit_rate`
- `recall_at_k`
- `mrr`

## 設計原則
- 與主專案解耦
- 預設使用 deterministic fake client，避免每次跑 baseline 都受外部 API 波動影響
- 真實模型評估獨立成另一條路徑，避免和 regression baseline 混在一起
- 結果落盤，方便做論文圖表與前後版本比較

若要跑 training readiness，現在需要同時提供 resume label eval：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_training_readiness.py \
  --assistant-summary <assistant-summary.json> \
  --retrieval-summary <retrieval-summary.json> \
  --resume-summary <resume-summary.json> \
  --resume-label-summary <resume-label-summary.json>
```

若要把 `AI checks / latency regression / training readiness` 一次收成固定回歸報表：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_ai_regression.py
```

這個腳本會自動抓最新的：
- `ai_checks_*`
- `real_model_eval_*`（assistant / retrieval / resume）
- `resume_label_eval_*`
- `resume_warm_probe_*`

也可以手動覆蓋各個 summary 路徑。

## Colab Post-Training

如果要在 Colab A100 上跑第一版 `SFT -> DPO` post-training，請看：

- `docs/post_training_colab_workflow.md`
- 主腳本：`scripts/run_post_training_colab.py`

最小指令：

```bash
python /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/job-radar-eval/scripts/run_post_training_colab.py \
  --hf-owner <your-hf-username>
```

訓練完成後，接著用這支腳本產生 `Base / SFT / DPO` comparison manifest：

```bash
python /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/job-radar-eval/scripts/run_post_training_local_eval.py \
  --sft-model-source <your-sft-model-repo-or-local-dir> \
  --dpo-model-source <your-dpo-model-repo-or-local-dir> \
  --dataset-version <your-dpo-dataset-version> \
  --embedding-api-key $OPENAI_API_KEY \
  --artifact-repo <artifact-repo>
```
