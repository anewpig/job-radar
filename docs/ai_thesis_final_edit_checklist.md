# 全文統一修稿清單

這份文件是論文最後一輪修稿的操作清單。目的不是新增內容，而是確保目前已完成的章節、圖表與正式結果在整份論文中保持一致。

---

## 1. 修稿總原則

最後一輪修稿只做四件事：

1. 統一術語
2. 校對數字與正式結果來源
3. 統一語氣與論證強度
4. 整理圖表、章節引用與格式

不要在這一輪再新增新的研究主張或大幅改方法描述，避免把已經定稿的結果打亂。

---

## 2. 核心結果先凍結

全文中所有正式數字，優先以這批結果為準：

- 主線總 gate  
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json)
- assistant real-model  
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json)
- resume real-model  
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json)
- resume label eval  
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/resume_label_eval_20260407_044723/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/resume_label_eval_20260407_044723/summary.json)
- formal human review  
  - [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json)

檢查項：

- [ ] 論文內所有正式數字都能回溯到上述結果檔
- [ ] 沒有混入舊版 run 的數字
- [ ] 同一個指標在不同章節沒有出現不同數值

---

## 3. 術語一致性檢查

對照文件：

- [ai_thesis_term_style_guide.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_term_style_guide.md)

檢查項：

- [ ] `market snapshot` 全文寫法一致
- [ ] `assistant`、`resume matching`、`mode-aware answer control` 寫法一致
- [ ] `market_summary`、`personalized_guidance`、`job_comparison` 三種模式寫法一致
- [ ] `snapshot health gate`、`assistant mode gate`、`human review gate`、`latency regression`、`training readiness` 寫法一致
- [ ] `RAG`、`resume parsing`、`resume extraction`、`two-stage ranking` 沒有混用替代詞

---

## 4. 語氣與論證強度檢查

檢查目標：

- 保持客觀
- 先描述事實，再下結論
- 避免過度宣稱

建議保留的說法：

- `本研究觀察到`
- `結果顯示`
- `可見`
- `因此，本研究認為`

需要避免的說法：

- `完全解決`
- `顯著超越所有方法`
- `效果非常優秀`
- `明顯證明所有情境皆適用`

檢查項：

- [ ] Chapter 1 沒有過度宣稱研究價值
- [ ] Chapter 2 以文獻脈絡為主，沒有偷塞實驗結論
- [ ] Chapter 3 只講方法與系統，不先評論結果
- [ ] Chapter 5 只根據正式數據下結論
- [ ] Chapter 6 對未來工作保持審慎，不把 `DEFER` 寫成 `READY`

---

## 5. 章節銜接檢查

檢查項：

- [ ] 摘要中的研究問題能在 Chapter 1 找到完整展開
- [ ] Chapter 1 的研究目標能在 Chapter 3、4、5 找到對應方法與結果
- [ ] Chapter 2 的文獻脈絡能自然導到 Chapter 3 的方法設計
- [ ] Chapter 4 的評估流程能對應到 Chapter 5 的結果表
- [ ] Chapter 6 的結論能直接回扣 Chapter 1 的研究目標

---

## 6. 圖表一致性檢查

對照文件：

- [ai_thesis_figures_tables_plan.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_figures_tables_plan.md)
- [ai_thesis_figure_3_1_system_architecture.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_figure_3_1_system_architecture.md)
- [ai_thesis_figure_4_1_evaluation_flow.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_figure_4_1_evaluation_flow.md)
- [ai_thesis_chapter5_tables.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter5_tables.md)

檢查項：

- [ ] Figure 3-1 名稱、圖說與 Chapter 3 內文一致
- [ ] Figure 4-1 名稱、圖說與 Chapter 4 內文一致
- [ ] Table 5-1 到 Table 5-7 的表號與正文引用一致
- [ ] 圖說與表說使用相同語氣
- [ ] 圖表中的指標名稱與正文完全一致

---

## 7. 數字與單位檢查

建議統一格式：

- 比率與平均分數：保留到 `4` 位小數
- latency：保留到 `3` 位小數並加 `ms`
- gate 狀態：保留英文大寫，如 `PASS`、`READY`、`DEFER`

檢查項：

- [ ] `0.9688`、`1.0` 等值在全文格式一致
- [ ] latency 一律寫成 `xxxx.xxx ms`
- [ ] `PASS / READY / DEFER` 沒有被寫成中文狀態字
- [ ] 表格與正文中的同一數字沒有被不同方式四捨五入

---

## 8. 正式結論檢查

這是最重要的部分。全文最後必須維持同一個正式結論：

- `latency_regression = PASS`
- `assistant_mode_gate = PASS`
- `human_review_gate = PASS`
- `training_readiness = DEFER`

檢查項：

- [ ] 摘要中的結論和 Chapter 5、Chapter 6 一致
- [ ] 沒有任何段落把 `training_readiness = DEFER` 寫成建議立即 fine-tuning
- [ ] 沒有任何段落暗示目前已完成模型訓練
- [ ] 結論明確指出：現階段重點是產品整合與持續觀測，而不是直接進訓練

---

## 9. 文獻引用檢查

主要影響章節：

- Chapter 2
- Chapter 3
- Chapter 4

檢查項：

- [ ] Chapter 2 每一節至少有基本代表性引用
- [ ] Chapter 3 的 RAG、resume parsing、ranking、evaluation 方法若提到通用概念，有對應引用
- [ ] Chapter 4 的 human review 與 LLM evaluation 方法論有對應引用
- [ ] 參考文獻格式一致

---

## 10. 最後排版檢查

檢查項：

- [ ] 章節編號連續
- [ ] 圖號與表號連續
- [ ] 中英文標點格式一致
- [ ] 英文術語大小寫一致
- [ ] Mermaid 圖若要正式提交，已轉成正式圖片
- [ ] Markdown 草稿內容已搬到最終論文主稿

---

## 11. 建議最後執行順序

1. 先做術語與數字統一
2. 再補 Chapter 2 文獻
3. 再把 Figure 3-1 與 Figure 4-1 轉成正式圖
4. 再把 Chapter 5 表格轉進主稿
5. 最後做全文通讀與格式整理

---

## 12. 完成判定

若以下條件都成立，就表示論文主線已基本收尾：

- [ ] 所有章節都已進入主稿
- [ ] 兩張核心圖已正式化
- [ ] Chapter 5 核心表格已正式化
- [ ] Chapter 2 已補最基本文獻引用
- [ ] 全文術語與結論一致
- [ ] 正式結果只引用同一批 run

到這一步，剩下就只是口試與投稿層級的微調，不再是主線內容缺口。
