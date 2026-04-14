# 論文進度摘要（給老師）

## 一、目前主題定位

本研究聚焦於求職場景中的產品級 AI 輔助系統，核心不在於訓練新的基礎模型，而在於整合：

- 多來源職缺市場快照
- RAG 問答
- 履歷解析與職缺匹配
- 產品級 telemetry 與 budget
- 正式評估與人工評分流程

研究問題可概括為：

> 在不進行 fine-tuning 的前提下，是否能透過 retrieval、mode-aware 回答控制、排序方法與正式評估閉環，建立一套產品可用的求職 AI 系統。

---

## 二、目前完成的核心結果

目前 AI 主線已完成正式驗證，主結果如下：

- `latency_regression = PASS`
- `assistant_mode_gate = PASS`
- `human_review_gate = PASS`
- `training_readiness = DEFER`

正式總結果來源：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json)

補充結果：

### 1. Assistant 真實模型結果

- 三種回答模式：
  - `market_summary`
  - `personalized_guidance`
  - `job_comparison`
- `citation_keyword_recall = 1.0`
- `evidence_sufficiency = 1.0`

來源：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json)

### 2. Resume matching 真實模型結果

- `top3_url_hit_rate = 1.0`
- `matched_skill_recall_mean = 0.9688`
- `resume_total_ms_mean = 9774.299 ms`

來源：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json)

### 3. Formal human review

- `reviewer_count = 2`
- `case_count = 8`
- `overall_score_mean = 5.0`
- `pairwise_verdict_agreement_rate = 1.0`

來源：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json)

---

## 三、目前研究判讀

目前的正式結論是：

1. 系統在品質、引用充分性、履歷排序品質與延遲上都已達到可接受門檻。
2. 目前沒有足夠證據支持立即進入 fine-tuning。
3. 因此研究主張不是「訓練出更強模型」，而是：
   - 透過系統工程
   - retrieval 設計
   - mode-aware 回答控制
   - ranking pipeline
   - 正式評估閉環

   即可在求職場景中做出產品可用的 AI 系統。

也就是說，目前論文的重點更接近：

- 系統設計與驗證
- 產品級 AI observability
- RAG 與 matching 的整合應用

而不是模型訓練論文。

---

## 四、論文章節目前進度

目前已完成或接近完成的草稿如下：

- 中文摘要  
  - [ai_thesis_abstract_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_abstract_draft.md)
- 英文摘要  
  - [ai_thesis_abstract_en_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_abstract_en_draft.md)
- Chapter 1 緒論  
  - [ai_thesis_chapter1_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter1_draft.md)
- Chapter 2 相關研究初稿  
  - [ai_thesis_chapter2_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter2_draft.md)
- Chapter 3 系統架構與方法  
  - [ai_thesis_chapter3_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter3_draft.md)
- Chapter 4 評估設計  
  - [ai_thesis_chapter4_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter4_draft.md)
- Chapter 5 實驗結果  
  - [ai_thesis_chapter5_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter5_draft.md)
- Chapter 6 結論與未來工作  
  - [ai_thesis_chapter6_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter6_draft.md)

另外已完成：

- 系統架構圖草稿  
  - [ai_thesis_figure_3_1_system_architecture.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_figure_3_1_system_architecture.md)
- 評估流程圖草稿  
  - [ai_thesis_figure_4_1_evaluation_flow.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_figure_4_1_evaluation_flow.md)
- Chapter 5 表格版  
  - [ai_thesis_chapter5_tables.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter5_tables.md)

---

## 五、目前還剩的工作

目前已不是系統能力缺口，主要剩論文收尾工作：

1. Chapter 2 補正式文獻引用
2. 將 Mermaid 圖轉成正式論文圖
3. 將各章 Markdown 草稿搬入最終主稿
4. 全文術語、數字與格式統一

對應控制文件：

- [ai_thesis_final_assembly_checklist.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_final_assembly_checklist.md)
- [ai_thesis_final_edit_checklist.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_final_edit_checklist.md)
- [ai_thesis_term_style_guide.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_term_style_guide.md)

---

## 六、目前完成度判斷

若分成兩條線來看：

- AI 系統主線：`約 99%`
- 論文整理主線：`約 98%`

因此，現在研究本身已接近完成，後續主要是：

- 文獻與寫作整理
- 圖表正式化
- 論文定稿

---

## 七、接下來最合理的順序

1. 先完成 Chapter 2 文獻引用
2. 將 Figure 3-1、Figure 4-1 轉成正式圖
3. 將 Chapter 5 表格搬入主稿
4. 最後做全文修稿與格式統一

---

## 八、目前可請老師協助回饋的重點

若要和老師討論，最有價值的回饋點是：

1. 論文定位是否更偏：
   - 系統工程 / 應用研究
   - 還是 AI 方法研究
2. Chapter 2 文獻回顧應補到什麼深度
3. Chapter 5 的結果呈現是否已足夠支撐主要結論
4. 是否需要額外補一組對照實驗或更多 human review case
