# AI / RAG / LLM 論文章節骨架

這份文件把目前專案已完成的 AI 主線成果，整理成可直接拿去寫論文的章節骨架。

定位：

- 以「系統工程 / 實作研究 / 評估導向」為主
- 不是預訓練模型論文
- 重點在：
  - 多來源職缺整合系統中的 RAG 問答
  - 履歷匹配
  - 評估框架
  - 產品級 observability 與 gate

最後更新時間：`2026-04-08`

---

## 1. 建議題目

可選題目方向：

1. `多來源職缺整合平台之 RAG 問答與履歷匹配系統設計與評估`
2. `面向求職場景的 RAG 問答與履歷匹配系統：設計、評估與產品化驗證`
3. `結合職缺市場快照、RAG 問答與履歷匹配之求職輔助系統研究`

如果你想更偏工程研究：

4. `A Product-Grade Evaluation Framework for Job-Market RAG and Resume Matching Systems`

---

## 2. 論文主張

這篇論文最適合主張的不是「訓練出更強模型」，而是：

1. 建立一套面向求職場景的 AI 系統架構  
   - 包含市場摘要、個人化建議、職缺比較、履歷匹配

2. 建立一套可重複、可量測、可回歸的評估流程  
   - fixture eval
   - real snapshot eval
   - real model eval
   - human review
   - latency / token / reliability monitoring

3. 證明在不進行 fine-tuning 的前提下  
   透過 retrieval、prompt、mode control、ranking、telemetry 與 gate 設計，仍可把系統做成產品可用狀態

---

## 3. 建議章節結構

### Chapter 1. 緒論

建議內容：

- 問題背景
  - 求職資訊分散在多個平台
  - 求職者很難同時整理：
    - 職缺工作內容
    - 技能需求
    - 薪資
    - 履歷缺口
- 研究動機
  - 一般聊天型 LLM 缺乏真實職缺證據
  - 單純問答不夠，還需要履歷匹配與市場分析
- 研究目標
  - 建立多來源職缺 AI 輔助系統
  - 建立評估與回歸框架
  - 驗證系統品質、延遲與可用性
- 研究貢獻

可引用文件：

- [AI 主線成果總結](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_mainline_summary.md)
- [AI / RAG / LLM 技術地圖](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_rag_llm_roadmap.md)

### Chapter 2. 相關研究

建議分三塊：

1. RAG 與 evidence-grounded QA
2. Resume parsing / job matching
3. LLM 系統評估與產品 observability

這一章你之後需要補文獻，不會直接從 repo 生成。

### Chapter 3. 系統架構與方法

建議分四節：

#### 3.1 系統整體架構

描述：

- crawler / snapshot
- assistant
- resume service
- product store
- external eval workspace

可引用文件：

- [architecture.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/architecture.md)
- [product_readiness_and_system_flow.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/product_readiness_and_system_flow.md)

#### 3.2 RAG 問答流程

建議寫：

1. snapshot -> chunk
2. retrieval
3. answer mode routing
4. prompt contract
5. citation selection
6. structured rendering

主程式入口：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/chunks.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/retrieval.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/service.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/prompts.py`

#### 3.3 履歷解析與匹配流程

建議寫：

1. resume extraction
2. profile normalization
3. two-stage job ranking
4. skill recall 與 role alignment

主程式入口：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/extractors.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/matchers.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/scoring.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/service.py`

#### 3.4 產品級監控與 gate

建議寫：

- telemetry
- token usage
- latency / reliability / token budget
- AI regression
- training readiness

主程式入口：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/store/metrics.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/store/database.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/pages_backend_operations.py`

### Chapter 4. 評估設計

這章是論文核心之一。

建議分成：

#### 4.1 Dataset 與標註

目前可寫：

- `assistant_questions = 100`
- `resume_extraction_labels = 30`
- `resume_match_labels = 60`

對照文件：

- [ai_eval_dataset_spec.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_eval_dataset_spec.md)

#### 4.2 Offline fixture baseline

說明：

- 固定 snapshot
- 固定 resume cases
- 固定題集
- deterministic baseline 的目的

參考：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/evaluation_methodology.md](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/evaluation_methodology.md)

#### 4.3 Real snapshot eval

說明：

- 用真實 `jobs_latest.json`
- 檢查 snapshot health
- 驗證 real-world retrieval / assistant / resume 路徑

#### 4.4 Real model eval

說明：

- 真實模型條件下的 assistant / retrieval / resume 表現

#### 4.5 Human review

說明：

- reviewer 數量
- 評分 rubric
- blind packet
- aggregation
- 一致性指標

參考文件：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/human_review_rubric.md](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/human_review_rubric.md)
- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/formal_human_review_workflow.md](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/formal_human_review_workflow.md)

### Chapter 5. 實驗結果

建議分成五節：

#### 5.1 主線總 gate 結果

直接引用：

- [ai_regression_20260408_002941/report.md](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/report.md)

核心結論：

- `Snapshot health gate = READY`
- `Assistant mode gate = PASS`
- `Human review gate = PASS`
- `Latency regression = PASS`
- `Training readiness = DEFER`

#### 5.2 Assistant mode-aware 結果

建議用表格列：

- `market_summary`
- `personalized_guidance`
- `job_comparison`

來源：

- [real_model_eval_20260407_212848/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json)

#### 5.3 Resume matching 結果

重點指標：

- `top3_url_hit_rate`
- `matched_skill_recall_mean`
- `build_profile_ms_mean`
- `match_jobs_ms_mean`

來源：

- [real_model_eval_20260407_215715/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json)

#### 5.4 Latency / Budget 結果

來源：

- [ai_regression_20260408_002941/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json)

#### 5.5 Human review 結果

來源：

- [formal_human_review_20260408_002923/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json)
- [formal_human_review_20260408_002923/thesis_tables.md](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/thesis_tables.md)
- [formal_human_review_20260408_002923/thesis_tables.tex](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/thesis_tables.tex)

### Chapter 6. 討論

這章建議寫三件事：

1. 為什麼沒有直接做 fine-tuning
   - 因為在 prompt / retrieval / ranking / mode control / telemetry / human review 都過線後
   - `training_readiness = DEFER`
   - 代表目前沒有足夠證據支持 training 的必要性

2. 系統工程比單純模型能力更影響產品可用性
   - evidence sufficiency
   - answer mode control
   - citation selection
   - latency regression

3. 限制
   - 真實快照仍受查詢與來源覆蓋影響
   - `resume_match_labels = 60` 尚非大型 training dataset
   - human review case 數仍偏小

### Chapter 7. 結論與未來工作

建議收斂成：

- 本研究完成一個產品級求職 AI 系統
- 建立了完整的 evaluation / regression / human review 流程
- 在不進行 fine-tuning 的前提下，已達產品可用門檻
- 未來工作：
  - 擴大正式標註集
  - 蒐集更多真實使用數據
  - 重新評估 training readiness

---

## 4. 可直接放進論文的表格

### Table A. 主線總 gate

來源：

- [ai_regression_20260408_002941/report.md](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/report.md)

建議欄位：

- Snapshot health gate
- Assistant mode gate
- Human review gate
- Latency regression
- Training readiness

### Table B. Assistant mode-aware 結果

建議欄位：

- Mode
- Case count
- Avg latency
- Citation keyword recall
- Evidence sufficiency

### Table C. Resume matching 結果

建議欄位：

- Top3 URL hit rate
- Matched skill recall
- Build profile latency
- Match jobs latency
- Total latency

### Table D. Human review aggregate

已可直接使用：

- [formal_human_review_20260408_002923/thesis_tables.md](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/thesis_tables.md)
- [formal_human_review_20260408_002923/thesis_tables.tex](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/thesis_tables.tex)

---

## 5. 建議圖表

### Figure 1. 系統總架構圖

畫出：

- crawler / snapshot
- assistant
- resume service
- UI
- product telemetry
- external eval workspace

### Figure 2. Assistant pipeline

畫出：

- question
- context
- routing
- retrieval
- prompt
- structured answer
- citations

### Figure 3. Resume pipeline

畫出：

- resume text
- extraction
- profile normalization
- two-stage ranking
- top matches

### Figure 4. 評估框架流程圖

畫出：

- fixture baseline
- real snapshot eval
- real model eval
- human review
- AI regression / training readiness

---

## 6. 寫作順序建議

不要從摘要開始。建議順序：

1. Chapter 3 系統架構與方法
2. Chapter 4 評估設計
3. Chapter 5 實驗結果
4. Chapter 6 討論
5. Chapter 7 結論
6. Chapter 1 緒論
7. 摘要

這樣最好寫，因為結果與方法都已經有材料。

---

## 7. 現在還缺什麼

目前不是缺系統或缺數據，而是缺論文寫作材料的組裝。

還缺的主要是：

1. 相關研究文獻整理
2. 架構圖與流程圖
3. 把各 summary / report 的數字摘成正式論文表
4. 中英文摘要

---

## 8. 你現在最合理的下一步

1. 用這份骨架先開論文文件
2. 先寫 Chapter 3~5
3. 我下一步幫你把：
   - `表格初稿`
   - `章節段落初稿`
   做出來

如果只選一個最有效的下一步，先做：

- `Chapter 5 實驗結果初稿`
