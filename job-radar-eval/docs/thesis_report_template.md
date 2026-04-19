# 論文/報告模板

## 題目
多平台職缺整合系統之 AI 問答與履歷匹配模組效能與品質評估

## 1. 研究背景
- 求職平台資訊分散
- 求職者需要跨平台整理職缺內容、技能要求與投遞流程
- 本系統提供職缺整合、履歷匹配與 AI 問答功能

## 2. 研究目的
- 建立一套可重複執行的評估框架
- 量化系統在延遲與品質上的表現
- 作為後續優化前後比較依據

## 3. 系統架構摘要
- 主系統：職缺整合平台
- 評估系統：獨立於主系統之外的 baseline framework
- 評估模組：
  - AI 助理問答
  - 履歷分析與職缺匹配

## 4. 評估資料與方法
### 4.1 固定測題
- 使用 `fixtures/assistant_questions.json`

### 4.2 固定履歷測例
- 使用 `fixtures/resume_cases.json`

### 4.3 固定職缺快照
- 使用 `job_radar_eval.fixtures.build_market_snapshot_fixture()`

### 4.4 指標
- AI 助理：`build_chunks_ms`, `retrieve_ms`, `llm_ms`, `total_ms`, `keyword_recall`, `citation_ok`
- 履歷匹配：`build_profile_ms`, `match_jobs_ms`, `total_ms`, `top1_url_match`, `top1_role_match`, `matched_skill_recall`, `missing_skill_recall`

## 5. 實驗結果
將 `results/<timestamp>/report.md` 的摘要貼於此。

### 5.1 AI 助理結果
- 平均延遲：
- P95 延遲：
- 關鍵詞召回率：
- 引用命中率：

### 5.2 履歷匹配結果
- 平均解析延遲：
- 平均匹配延遲：
- Top1 正確率：
- 技能召回率：

## 6. 討論
- 哪些優化能明顯降低延遲
- 哪些優化會造成品質退化
- 在 deterministic baseline 與真實世界表現之間的差異

## 7. 結論
- 評估框架的價值
- 系統目前最值得優化的模組
- 後續研究方向


## Retrieval 評估
- 固定問題與固定知識片段
- 指標包含冷快取延遲、熱快取延遲、Top1 命中率、Recall@K、MRR
