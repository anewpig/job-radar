# 全文術語統一表

這份文件用來統一論文內的：

- 核心術語
- 中英文對應
- 建議寫法
- 避免混用的說法

目的很直接：

- 讓整份論文語氣一致
- 避免同一個概念在不同章節被寫成不同名稱
- 降低後期修稿成本

---

## 1. 使用原則

全文建議遵守以下原則：

1. 第一次出現時，用「中文（英文）」完整寫法
2. 第二次之後，固定用同一個簡稱
3. 同一個概念不要在不同章節切換不同說法
4. 若是你系統自己定義的詞，優先用系統內已定稿名稱

---

## 2. 核心術語統一表

| 概念 | 建議中文 | 建議英文 | 後續簡寫 | 不建議混用 |
| --- | --- | --- | --- | --- |
| 檢索增強生成 | 檢索增強生成 | Retrieval-Augmented Generation | RAG | 檢索式生成、檢索輔助生成 |
| 市場快照 | 市場快照 | market snapshot | snapshot | 職缺快照、市場資料快照（除非第一次完整說明） |
| 多來源職缺市場快照 | 多來源職缺市場快照 | multi-source job-market snapshot | market snapshot | 多平台快照、職缺集合 |
| AI 助理 | AI 助理 | assistant | assistant | 問答模組、聊天機器人 |
| 履歷匹配 | 履歷匹配 | resume matching | resume matching | 履歷推薦、履歷比對 |
| 履歷解析 | 履歷解析 | resume parsing | resume parsing | 履歷抽取（除非特指 extraction 任務） |
| 履歷抽取 | 履歷抽取 | resume extraction | extraction | 履歷剖析 |
| 職缺排序 | 職缺排序 | job ranking | ranking | 職缺推薦排序、職缺排名 |
| 引用 | 引用 | citation | citation | 參考、證據標註 |
| 證據充分性 | 證據充分性 | evidence sufficiency | evidence sufficiency | 證據完整度（除非特別說明） |
| grounding | 根據性 | grounding | grounding | 落地性、依據性 |
| 回答模式控制 | 回答模式控制 | answer-mode control | mode control | 模式切換邏輯 |
| 模式感知 | 模式感知 | mode-aware | mode-aware | aware-based |
| 市場摘要 | 市場摘要 | market summary | market_summary | 市場分析回答 |
| 個人化建議 | 個人化建議 | personalized guidance | personalized_guidance | 個人建議模式 |
| 職缺比較 | 職缺比較 | job comparison | job_comparison | 比較模式、角色比較模式 |
| 兩階段排序 | 兩階段排序 | two-stage ranking | two-stage ranking | 雙階段排序、兩段式排名 |
| 正式人工評分 | 正式人工評分 | formal human review | human review | 人工標註（除非特指 label） |
| 評估工作區 | 外部評估工作區 | external evaluation workspace | eval workspace | 測試 repo、評估 repo |
| 回歸檢查 | 回歸檢查 | regression | regression | 回歸測試（若不是程式單元測試語境） |
| 延遲回歸 | 延遲回歸 | latency regression | latency regression | latency 測試 |
| 訓練就緒判定 | 訓練就緒判定 | training readiness gate | training readiness | 訓練門檻、是否可訓練 |
| 產品級觀測 | 產品級觀測 | product-grade observability | observability | 監控（太泛） |
| 遙測資料 | telemetry | telemetry | telemetry | 監控資料、追蹤資料 |
| token 預算 | token 預算 | token budget | token budget | token 成本門檻 |
| 真實快照評估 | 真實快照評估 | real snapshot evaluation | real snapshot eval | live snapshot eval |
| 真實模型評估 | 真實模型評估 | real model evaluation | real model eval | 真模型評估 |
| 固定資料基準評估 | 固定資料基準評估 | fixture baseline evaluation | fixture baseline | baseline 測試 |

---

## 3. 系統內專有名詞的固定寫法

### 3.1 正式 gate 名稱

請固定寫成：

- `snapshot health gate`
- `assistant mode gate`
- `human review gate`
- `latency regression`
- `training readiness`

不建議改寫成：

- snapshot quality gate
- assistant quality gate
- reviewer gate
- latency gate
- training gate

原因是你目前正式結果與文件都已經以這組名稱定稿。

### 3.2 Assistant 三種模式

論文中第一次出現時建議寫：

- 市場摘要（`market_summary`）
- 個人化建議（`personalized_guidance`）
- 職缺比較（`job_comparison`）

後續若在技術描述中，可直接用：

- `market_summary`
- `personalized_guidance`
- `job_comparison`

若在一般敘述段落中，則可用中文：

- 市場摘要模式
- 個人化建議模式
- 職缺比較模式

但不要在不同地方混用成：

- comparison mode
- compare mode
- job compare

---

## 4. 評估相關術語的固定寫法

### 4.1 指標名稱

這些指標在正文中建議保留英文原名，避免翻譯後失真：

- `citation_keyword_recall_mean`
- `evidence_sufficiency_rate`
- `top3_url_hit_rate`
- `top1_role_match_rate`
- `matched_skill_recall_mean`
- `pairwise_order_accuracy_mean`
- `nDCG@3`
- `pairwise_verdict_agreement_rate`
- `cohens_kappa_verdict`

第一次出現時可在文字中加解釋，例如：

> 本研究使用 `pairwise_order_accuracy_mean` 作為排序關係正確率指標。

### 4.2 PASS / READY / DEFER

建議保留英文狀態字，不要全文翻成中文。原因：

- 這些值來自正式 gate 結果
- 與實驗結果檔案一致

可在第一次出現時加中文說明，例如：

- `READY`：可正式判讀
- `PASS`：達標
- `DEFER`：暫緩進入訓練

---

## 5. 常見容易混用的詞

### 5.1 「模型訓練」相關

建議區分：

- `pretraining`
- `post-training`
- `fine-tuning`

論文裡不要全部統稱成「訓練」。若只是在談目前不建議進一步調整模型，請優先寫：

- `fine-tuning`

因為本研究的 gate 判定是針對這個層級的決策，不是在討論大型基礎模型 pretraining。

### 5.2 「評估」與「驗證」

建議：

- `evaluation` 翻成「評估」
- `validation` 翻成「驗證」

使用方式：

- human review validation：人工評分檔驗證
- real model evaluation：真實模型評估

不要混成同一個中文詞。

### 5.3 「快照」與「資料集」

建議區分：

- `dataset`：標註集 / 題集 / fixture
- `snapshot`：真實市場資料快照

不要把 `jobs_latest.json` 叫成 dataset，除非你特別在某個段落把它當評估輸入資料說明。

---

## 6. 建議全文語氣

整份論文建議維持這種語氣：

- 客觀
- 系統工程導向
- 避免過度宣稱
- 先描述事實，再下結論

建議用法：

- `本研究觀察到`
- `結果顯示`
- `可見`
- `因此，本研究認為`
- `這表示`

不建議用法：

- `本系統非常優秀`
- `顯著超越所有方法`
- `完全解決`
- `效果極佳`

除非你有明確對照實驗支撐，否則不要用過強措辭。

---

## 7. 建議數字呈現方式

### 7.1 小數位數

建議統一：

- 比率與平均分數：最多 `4` 位小數
- latency：最多 `3` 位小數
- gate 狀態：直接用英文狀態字

例如：

- `0.9688`
- `4758.514 ms`
- `PASS`

### 7.2 表格與正文一致

若表格中寫：

- `matched_skill_recall_mean = 0.9688`

正文就不要改寫成：

- 約 `0.97`

除非你刻意在文字中做摘要，否則盡量一致。

---

## 8. 最後修稿時的檢查順序

全文修稿時，建議照這個順序檢查：

1. 章節標題與章節名稱是否一致
2. 核心術語是否一致
3. gate 名稱是否一致
4. 三種 answer mode 是否一致
5. 指標名稱與數字是否一致
6. 圖表標題與正文引用是否一致

---

## 9. 本文件的用途

這份文件不是理論內容，而是最後修稿的控制文件。  
你之後在：

- Chapter 2 補文獻
- Chapter 5 改表格
- 摘要與結論收斂

時，都應該先回來對照這份術語表，避免整份論文的名稱與語氣跑掉。
