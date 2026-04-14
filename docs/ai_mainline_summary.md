# AI 主線成果總結

這份文件整理目前 `AI / RAG / LLM` 主線的完成狀態、正式結果、主要產物與下一步建議。

最後更新時間：`2026-04-08`

---

## 1. 結論

目前 AI 主線已完成核心建設與正式驗證，狀態如下：

- `latency_regression = PASS`
- `assistant_mode_gate = PASS`
- `human_review_gate = PASS`
- `training_readiness = DEFER`

正式總結結果：

- `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json`
- `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/report.md`

這代表：

- 產品品質已達標
- 三種回答模式都已過正式 gate
- 延遲已在可接受範圍
- 正式 reviewer 人評已過線
- 目前**不建議**直接進行 fine-tuning

---

## 2. 目前主線做到哪裡

### 2.1 已完成的能力

#### A. RAG / Retrieval

- 建立 chunk / metadata pipeline
- 從純 embedding baseline 升級成 hybrid retrieval + rerank
- 補齊聚合型問題的 chunk 類型
  - `market-source-summary`
  - `market-role-summary`
  - `market-location-summary`
- 補 comparison-specific retrieval diversification
- 補 comparison-specific citation selection

主要模組：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/chunks.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/retrieval.py`

#### B. Assistant 回答控制

- 補多輪上下文
- 補 query routing / answer mode control
- 正式拆成三種模式：
  - `market_summary`
  - `personalized_guidance`
  - `job_comparison`
- 三種模式都有各自 prompt 契約、render path、citation 策略
- 完成最後一輪 reviewer-driven prompt 校正

主要模組：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/service.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/prompts.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/renderers.py`

#### C. Resume extraction / matching

- 補 specialized role extraction
- 補 matcher semantic floor / exact title bonus
- 改成 two-stage ranking
- 壓低 `build_profile` 與 `match_jobs` latency
- 補 warm-path cache 驗證

主要模組：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/extractors.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/matchers.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/service.py`

#### D. 評估與觀測

- 建立 external eval workspace
- 建立 fixture baseline / real snapshot eval / real model eval
- 建立 latency regression / training readiness / AI regression
- 建立 telemetry / token usage / budget evaluator
- 建立 human review packet / validation / aggregation / thesis export

主要工作區：

- `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval`

---

## 3. 正式 gate 結果

### 3.1 AI Regression

來源：

- `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json`

結果：

- `Snapshot health gate = READY`
- `Assistant mode gate = PASS`
- `Human review gate = PASS`
- `Latency regression = PASS`
- `Training readiness = DEFER`

### 3.2 Assistant mode-aware real-model

來源：

- `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json`

結果：

- `market_summary`
  - `case_count = 6`
  - `citation_keyword_recall_mean = 1.0`
  - `evidence_sufficiency_rate = 1.0`
- `personalized_guidance`
  - `case_count = 1`
  - `citation_keyword_recall_mean = 1.0`
  - `evidence_sufficiency_rate = 1.0`
- `job_comparison`
  - `case_count = 1`
  - `citation_keyword_recall_mean = 1.0`
  - `evidence_sufficiency_rate = 1.0`

### 3.3 Latency regression

來源：

- `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json`

關鍵值：

- `assistant_total_ms_mean = 4758.514`
- `retrieval_cold_ms_mean = 1476.403`
- `retrieval_warm_ms_mean = 165.345`
- `resume_build_profile_ms_mean = 5227.174`
- `resume_match_jobs_ms_mean = 4547.125`
- `resume_total_ms_mean = 9774.299`
- `resume_warm_build_profile_ms_mean = 2.041`

判定：

- `PASS`

### 3.4 Formal human review

來源：

- `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json`

結果：

- `reviewer_count = 2`
- `case_count = 8`
- `overall_score_mean = 5.0`
- `grounding_score_mean = 5.0`
- `pairwise_verdict_agreement_rate = 1.0`
- `cohens_kappa_verdict = 1.0`
- `verdict_distribution = {"accept": 16}`

判定：

- `PASS`

---

## 4. Dataset / Eval 進度

依 `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_eval_dataset_spec.md` 目前狀態：

- `assistant_questions = 100`
- `resume_extraction_labels = 30`
- `resume_match_labels = 60`

解讀：

- `assistant_questions`：已達標且超過第一版目標
- `resume_extraction_labels`：已達第一版目標
- `resume_match_labels`：已脫離 seed 階段，足以支撐排序評估，但還不是大型 training set

---

## 5. Human review 最後修正軌跡

最初完整 reviewer 結果中，分歧集中在：

- `real_skill_focus`
- `real_personalized_gap`
- `real_task_focus`

後續處理：

- 在 `prompts.py` 對這三類問題補 guardrails
- 產生 targeted 3-case reviewer packet
- 重新收 reviewer 回填
- 將 `8` 題完整 review 與 `3` 題重評合併成 consolidated formal review

最終結果：

- 分歧被消除
- `human_review_gate` 由 `FAIL` 轉為 `PASS`

---

## 6. 為什麼現在不做 fine-tuning

正式判定是：

- `training_readiness = DEFER`

這不是因為系統不夠好，而是因為：

- 品質已達標
- citation / evidence / mode coverage 已達標
- latency 已達標
- human review 已達標

因此目前沒有足夠證據顯示：

- 進行 fine-tuning 會比繼續做產品整合更有投資報酬

也就是說，現在最合理的工作不是 training，而是：

- 持續收真實使用 telemetry
- 觀察是否出現穩定錯誤型態
- 之後再重新打開 training gate

---

## 7. 目前不建議做的事

- 不要為了 training 去抓平台履歷
  - `104 / 1111 / LinkedIn / Cake` 履歷資料有授權與隱私問題
- 不要現在就做 pretraining
- 不要因為 Colab 有額度就直接做 fine-tuning

如果未來真的要進 training，資料前提應該是：

- 有同意
- 去識別化
- 可標註
- 類型分布清楚

---

## 8. 接下來建議

### 路線 A：產品整合

優先建議。

- 持續收 `ai_monitoring_events`
- 觀察三種 answer mode 的真實使用分布
- 觀察 token / latency / error pattern
- 等有新的穩定缺口，再回來判斷是否需要 training

### 路線 B：論文整理

目前已具備材料：

- regression 結果
- mode-aware eval
- real snapshot eval
- real model eval
- human review
- thesis tables / LaTeX export

可直接開始整理章節：

- 方法
- 評估設計
- 結果
- human review
- 討論與限制

---

## 9. 核心產物索引

### 主專案

- Roadmap
  - `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_rag_llm_roadmap.md`
- Dataset spec
  - `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_eval_dataset_spec.md`
- 本文件
  - `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_mainline_summary.md`

### Eval / Research

- AI regression
  - `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json`
- Training readiness
  - `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/training_readiness_20260408_002941/summary.json`
- Formal human review
  - `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json`
- Thesis tables
  - `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/thesis_tables.md`
  - `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/thesis_tables.tex`

### 產品監控

- DB
  - `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/product_state.sqlite3`
- table
  - `ai_monitoring_events`

---

## 10. 最終一句話

AI 主線目前已經從「功能原型」走到「有正式評估、有正式人評、有正式 gate 的產品級能力」。  
現階段應先做產品整合與論文整理，而不是直接進 training。
