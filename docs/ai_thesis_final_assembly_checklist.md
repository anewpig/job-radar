# 論文最終組裝清單

這份文件的目的不是再增加內容，而是把目前已完成的論文材料收斂成一份可執行的組裝清單。你之後只要照這份順序走，就能把現有草稿整理成一份可提交的論文版本。

---

## 1. 目前已完成的材料

### 1.1 摘要與章節草稿

- [ai_thesis_abstract_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_abstract_draft.md)
- [ai_thesis_abstract_en_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_abstract_en_draft.md)
- [ai_thesis_chapter1_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter1_draft.md)
- [ai_thesis_chapter2_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter2_draft.md)
- [ai_thesis_chapter3_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter3_draft.md)
- [ai_thesis_chapter4_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter4_draft.md)
- [ai_thesis_chapter5_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter5_draft.md)
- [ai_thesis_chapter6_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter6_draft.md)

### 1.2 圖與表草稿

- [ai_thesis_figure_3_1_system_architecture.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_figure_3_1_system_architecture.md)
- [ai_thesis_figure_4_1_evaluation_flow.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_figure_4_1_evaluation_flow.md)
- [ai_thesis_figures_tables_plan.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_figures_tables_plan.md)
- [ai_thesis_chapter5_tables.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter5_tables.md)

### 1.3 AI 主線總結與研究素材

- [ai_mainline_summary.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_mainline_summary.md)
- [ai_thesis_outline.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_outline.md)
- [ai_eval_dataset_spec.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_eval_dataset_spec.md)

---

## 2. 正式結果來源

論文最終定稿時，以下結果應視為正式引用來源。

### 2.1 主線總 gate

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json)
- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/report.md](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/report.md)

### 2.2 Assistant 真實模型結果

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json)

### 2.3 Resume 真實模型結果

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json)

### 2.4 Resume label ranking 結果

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/resume_label_eval_20260407_044723/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/resume_label_eval_20260407_044723/summary.json)

### 2.5 Formal human review 結果

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json)
- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/thesis_tables.md](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/thesis_tables.md)
- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/thesis_tables.tex](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/thesis_tables.tex)

---

## 3. 最終組裝順序

### Step 1. 先凍結正式結果

先確認論文內所有數字都以這批結果為準：

- `ai_regression_20260408_002941`
- `real_model_eval_20260407_212848`
- `real_model_eval_20260407_215715`
- `resume_label_eval_20260407_044723`
- `formal_human_review_20260408_002923`

原則：

- 不要一邊寫論文一邊再改主線數字
- 若之後真的再重跑，必須整批同步更新

### Step 2. 組正文

依序組入：

1. 中文摘要
2. 英文摘要
3. Chapter 1
4. Chapter 2
5. Chapter 3
6. Chapter 4
7. Chapter 5
8. Chapter 6

建議做法：

- 先保留每章 Markdown 原文
- 再統一搬進 Word / LaTeX 主稿

### Step 3. 插入核心圖表

最優先插入：

1. Figure 3-1 系統整體架構圖
2. Figure 4-1 評估流程總覽圖
3. Table 5-1 主線總 gate
4. Table 5-3 Assistant mode-aware 結果
5. Table 5-4 Resume matching 結果
6. Table 5-6 Latency regression 結果
7. Table 5-7 Formal human review 結果

### Step 4. 統一術語

整份論文統一用語：

- `market snapshot`
- `assistant`
- `resume matching`
- `mode-aware answer control`
- `formal human review`
- `training readiness gate`

不要在不同章節來回切換成太多相似說法。

### Step 5. 補文獻引用

優先補在：

- Chapter 2
- Chapter 3 方法章中引用通用做法
- Chapter 4 評估方法中引用人評與 LLM evaluation 文獻

### Step 6. 最後修稿

最後才做：

- 語氣統一
- 段落銜接
- 表格編號
- 圖說格式
- 參考文獻格式

---

## 4. 建議優先完成的最終交稿版本

如果你要先做一版可交給老師看的版本，建議先組成：

### 必備

- 中文摘要
- 英文摘要
- Chapter 1
- Chapter 2
- Chapter 3
- Chapter 4
- Chapter 5
- Chapter 6

### 必備圖表

- Figure 3-1
- Figure 4-1
- Table 5-1
- Table 5-3
- Table 5-4
- Table 5-6
- Table 5-7

### 可先不放

- 太細的 appendix 案例表
- 次要表格
- 額外延伸圖

---

## 5. 現在還沒做的事

以下屬於論文收尾，但不是主線能力缺口：

1. Chapter 2 補正式文獻引用
2. 把 Mermaid 圖轉成正式論文圖
3. 把 Chapter 5 表格轉成 Word / LaTeX 最終格式
4. 全文語氣與格式統一
5. 參考文獻清單整理

---

## 6. 目前完成度判斷

### AI 系統主線

- 大約 `98%~99%`
- 剩下主要是持續產品 telemetry，不是再開新功能

### 論文整理主線

- 大約 `92%~95%`
- 剩下主要是：
  - 文獻補引
  - 圖表正式化
  - 全文格式統一

---

## 7. 最後一輪建議順序

若你接下來要最有效率地收尾，建議順序如下：

1. 先把 Figure 3-1 與 Figure 4-1 轉成正式圖
2. 把 Chapter 5 表格搬進主稿
3. 補 Chapter 2 文獻引用
4. 全文做一次語氣與術語統一
5. 最後再整理參考文獻與版面

---

## 8. 本文件的用途

這份文件的用途很單純：

- 當作你的交稿前 checklist
- 當作你和老師討論目前進度的總控表
- 避免後面在結果、圖表與章節版本之間反覆切換
