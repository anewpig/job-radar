# 論文圖表與表格清單

這份文件整理目前論文最適合放入的：

- 圖
- 表
- 對應章節
- 可直接使用的資料來源

目的不是直接產出最終圖表，而是先把論文需要哪些視覺材料定義清楚，避免後面寫正文時才回頭找資料。

---

## 1. 使用原則

本研究的圖表應該服務三件事：

1. 讓讀者快速理解系統架構
2. 讓讀者快速比較核心結果
3. 讓評估與正式 gate 的結論可追溯

因此不建議放過多裝飾性圖表。優先保留：

- 系統架構圖
- 資料流圖
- gate summary 表
- mode-aware 結果表
- latency 表
- human review 表

---

## 2. Chapter 1 適合的圖表

### Figure 1-1 研究問題情境圖

- 用途：
  - 交代求職者同時面對多來源職缺、履歷缺口與決策壓力
- 形式：
  - 概念圖
- 建議內容：
  - 多個職缺來源
  - 市場快照
  - AI 助理
  - 履歷匹配
  - 使用者決策
- 狀態：
  - 尚未畫

### Table 1-1 研究問題與對應方法

- 用途：
  - 在緒論快速對齊「問題 -> 方法」
- 建議欄位：
  - 問題
  - 對應模組
  - 對應評估
- 狀態：
  - 可直接依 `Chapter 1` 與 `Chapter 3/4` 內容整理

---

## 3. Chapter 3 適合的圖表

### Figure 3-1 系統整體架構圖

- 用途：
  - 展示整個系統的四層架構
- 建議內容：
  - UI / orchestration
  - crawler / snapshot
  - assistant / resume intelligence
  - store / monitoring / evaluation
- 主要依據：
  - [ai_thesis_chapter3_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter3_draft.md)
  - [architecture.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/architecture.md)
- 狀態：
  - 建議用 Mermaid 先出第一版

### Figure 3-2 職缺資料流與快照生成流程

- 用途：
  - 解釋 staged crawl 到 `MarketSnapshot` 的流程
- 建議內容：
  - source search
  - dedupe
  - scoring
  - partial snapshot
  - enrich
  - final snapshot
- 依據：
  - `pipeline.py`
  - `crawl_runtime.py`
- 狀態：
  - 尚未畫

### Figure 3-3 Assistant 問答流程圖

- 用途：
  - 說明 RAG pipeline 與 mode-aware control
- 建議內容：
  - snapshot -> chunk -> retrieval -> answer mode routing -> prompt -> citation -> render
- 依據：
  - `assistant/chunks.py`
  - `assistant/retrieval.py`
  - `assistant/service.py`
  - `assistant/prompts.py`
- 狀態：
  - 尚未畫

### Figure 3-4 Resume matching 流程圖

- 用途：
  - 說明 extraction、profile normalization 與 two-stage ranking
- 建議內容：
  - resume input
  - extractor
  - profile
  - coarse ranking
  - fine ranking
  - output jobs
- 依據：
  - `resume/extractors.py`
  - `resume/service.py`
  - `resume/matchers.py`
- 狀態：
  - 尚未畫

### Table 3-1 Assistant 三種 answer mode 定義

- 建議欄位：
  - mode
  - 問題類型
  - retrieval 特徵
  - 輸出結構
- 內容來源：
  - `service.py`
  - `prompts.py`
- 狀態：
  - 可直接整理

### Table 3-2 主要 chunk 類型與用途

- 建議欄位：
  - chunk type
  - 內容來源
  - 典型用途
- 內容來源：
  - `assistant/chunks.py`
- 狀態：
  - 可直接整理

---

## 4. Chapter 4 適合的圖表

### Figure 4-1 評估流程總覽圖

- 用途：
  - 把整個 evaluation stack 一次講清楚
- 建議內容：
  - fixture baseline
  - real snapshot eval
  - real model eval
  - resume label eval
  - human review
  - latency regression
  - training readiness
- 主要依據：
  - [ai_thesis_chapter4_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter4_draft.md)
- 狀態：
  - 建議優先做

### Table 4-1 評估資料集摘要

- 建議欄位：
  - dataset
  - size
  - 用途
  - 對應任務
- 目前可填：
  - `assistant_questions = 100`
  - `resume_extraction_labels = 30`
  - `resume_match_labels = 60`
- 來源：
  - [ai_eval_dataset_spec.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_eval_dataset_spec.md)
  - [ai_mainline_summary.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_mainline_summary.md)
- 狀態：
  - 可直接整理

### Table 4-2 各評估層的目的與輸出

- 建議欄位：
  - 評估層
  - 輸入
  - 指標
  - 主要輸出檔案
- 可列：
  - fixture baseline
  - real snapshot eval
  - real model eval
  - resume label eval
  - human review
  - ai regression
- 來源：
  - `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results`
- 狀態：
  - 可直接整理

---

## 5. Chapter 5 適合的圖表

### Table 5-1 主線總 gate 結果

- 用途：
  - 這是本論文最重要的總覽表
- 建議欄位：
  - gate
  - status
  - 解釋
- 來源：
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json)
- 狀態：
  - 已在 `Chapter 5` 文字初稿中，可轉正式表格

### Table 5-2 Snapshot health 結果

- 用途：
  - 說明真實快照可用於正式判讀
- 建議欄位：
  - 指標
  - 實際值
  - 門檻
  - 結果
- 來源：
  - `ai_regression` summary 中的 snapshot health
- 狀態：
  - 已在 `Chapter 5` 文字初稿中

### Table 5-3 Assistant mode-aware real-model 結果

- 用途：
  - 呈現三種 mode 的品質與延遲
- 建議欄位：
  - mode
  - case count
  - avg latency
  - structured output
  - citation keyword recall
  - evidence sufficiency
- 來源：
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json)
- 狀態：
  - 已在 `Chapter 5` 文字初稿中

### Table 5-4 Resume matching 真實模型結果

- 用途：
  - 呈現履歷路徑的排序品質與延遲
- 建議欄位：
  - 指標
  - 數值
- 來源：
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json)
- 狀態：
  - 已在 `Chapter 5` 文字初稿中

### Table 5-5 Resume label ranking 結果

- 用途：
  - 補充排序角度的正式評估
- 建議欄位：
  - metric
  - value
- 來源：
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/resume_label_eval_20260407_044723/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/resume_label_eval_20260407_044723/summary.json)
- 狀態：
  - 已在 `Chapter 5` 文字初稿中

### Table 5-6 Latency regression 結果

- 用途：
  - 證明產品延遲已在可接受範圍
- 建議欄位：
  - 指標
  - 實際值
  - 門檻
  - 結果
- 來源：
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json)
- 狀態：
  - 已在 `Chapter 5` 文字初稿中

### Table 5-7 Formal human review 結果

- 用途：
  - 作為人工評分總結表
- 建議欄位：
  - reviewer count
  - case count
  - correctness
  - grounding
  - usefulness
  - clarity
  - overall
  - agreement
  - kappa
- 來源：
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json)
- 狀態：
  - 已在 `Chapter 5` 文字初稿中

### Figure 5-1 Assistant 三種模式延遲比較圖

- 用途：
  - 用圖快速看 mode-aware 差異
- 形式：
  - bar chart
- 欄位：
  - `market_summary`
  - `personalized_guidance`
  - `job_comparison`
- 來源：
  - `real_model_eval_20260407_212848/summary.json`
- 狀態：
  - 尚未繪製

### Figure 5-2 Gate summary 視覺總覽

- 用途：
  - 一圖展示最終 `PASS / READY / DEFER`
- 形式：
  - status dashboard 圖或簡化流程圖
- 來源：
  - `ai_regression_20260408_002941/summary.json`
- 狀態：
  - 尚未繪製

---

## 6. Appendix 適合的圖表

### Appendix Table A-1 Human review rubric

- 用途：
  - 放正式 reviewer 維度與說明
- 來源：
  - `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/human_review_rubric.md`
- 狀態：
  - 可整理成表格

### Appendix Table A-2 Assistant case 範例

- 用途：
  - 放 `question / answer / citation / reviewer verdict` 範例
- 來源：
  - `formal_human_review_*`
  - `assistant cases export`
- 狀態：
  - 後續可挑 2~3 筆代表案例

### Appendix Figure A-1 Formal human review 流程圖

- 用途：
  - 說明 blind packet -> reviewer -> validation -> aggregation
- 來源：
  - `formal_human_review_workflow.md`
- 狀態：
  - 尚未繪製

---

## 7. 優先製作順序

如果要有效率，建議優先順序如下：

1. `Figure 3-1` 系統整體架構圖
2. `Figure 4-1` 評估流程總覽圖
3. `Table 5-1` 主線總 gate 結果
4. `Table 5-3` Assistant mode-aware 結果
5. `Table 5-6` Latency regression 結果
6. `Table 5-7` Formal human review 結果
7. `Figure 5-1` Mode latency comparison

原因很直接：

- 這幾張最能支撐你的核心論點
- 而且大部分數據已經定稿

---

## 8. 目前可直接引用的結果檔

論文最關鍵的結果來源目前是這幾個：

- 主線總 gate：
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json)
- assistant real-model：
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json)
- resume real-model：
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json)
- resume label eval：
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/resume_label_eval_20260407_044723/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/resume_label_eval_20260407_044723/summary.json)
- formal human review：
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json)

---

## 9. 本文件的用途

這份清單的作用是讓你後面寫論文時：

- 知道每章該放什麼圖表
- 知道哪些資料已經可以直接用
- 知道哪些圖還需要補畫

下一步如果要繼續推論文主線，最合理的是：

1. 直接做 `Figure 3-1 系統整體架構圖`
2. 再做 `Figure 4-1 評估流程總覽圖`
3. 同時把 `Chapter 5` 的表格正式化
