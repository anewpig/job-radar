# Chapter 1 緒論初稿

本章說明本研究的背景、動機、研究目標、方法概述、研究貢獻與論文章節安排。研究主題聚焦於求職場景中的 AI 輔助系統，核心不是訓練一個新模型，而是建立一套以真實職缺市場資料為基礎，整合 RAG 問答、履歷匹配、產品觀測與正式評估流程的產品級系統。

---

## 1.1 研究背景

近年求職活動逐漸高度平台化，職缺資訊分散於多個網站與來源，例如企業官網、職缺平台與社群型求職平台。對求職者而言，真正的困難不只是「找工作」，而是同時處理以下幾種資訊：

- 各平台職缺內容與格式不一致
- 工作內容、技能需求與薪資揭露方式差異很大
- 同一角色在不同來源上可能有不同描述與要求
- 求職者需要將市場需求與自身履歷條件做對照

因此，單純蒐集職缺列表並不足以支援實際求職決策。使用者真正需要的是一套能夠：

- 統整多來源職缺市場
- 以證據為基礎回答市場問題
- 依履歷提供個人化建議
- 比較不同職缺或角色差異
- 支援後續投遞與追蹤流程

的整合式系統。

大語言模型的普及使自然語言互動成為可能，但在求職場景中，若直接使用通用聊天模型，常會遇到兩個問題。第一，模型缺乏即時且具體的職缺市場證據；第二，單輪問答難以支撐履歷缺口分析、職缺比較與產品級決策流程。因此，本研究將問題定義為：如何在不依賴模型再訓練的前提下，利用真實職缺快照、RAG、履歷匹配與正式評估機制，建立一套可產品化的求職 AI 系統。

---

## 1.2 研究動機

本研究的動機主要來自三個層面。

### 1.2.1 求職資訊整合困難

多來源職缺平台在欄位命名、內容密度、薪資揭露與工作內容描述上並不一致。即使同樣是 `AI 工程師`、`PM` 或 `韌體工程師`，不同平台與不同公司對角色期待也可能有明顯差異。若缺乏整合機制，使用者只能手動比對大量文本，效率低且容易遺漏重要訊息。

### 1.2.2 通用聊天模型缺乏可驗證證據

一般 LLM 可以生成流暢回答，但若沒有對應的職缺證據、引用與市場上下文，回答很難作為真實求職決策依據。尤其在薪資、技能缺口、工作內容與角色比較等問題上，沒有 grounding 的回答容易造成誤導。因此，本研究將 evidence-grounded QA 視為求職 AI 的基本要求，而非附加能力。

### 1.2.3 單一模型指標不足以支撐產品化

即使某個回答看起來合理，也不代表整體系統具備產品可用性。對求職場景而言，系統至少還需要：

- 履歷解析與職缺匹配
- 模式化的回答控制
- 延遲與成本觀測
- 可重複、可回歸的評估流程
- 正式人工評分機制

因此，本研究的重點不放在單純提升模型分數，而是建立一條從市場資料、RAG 問答、履歷匹配，到 telemetry、gate 與 human review 的完整工程主線。

---

## 1.3 研究目的

基於上述背景與動機，本研究有以下三項主要目的。

### 1.3.1 建立多來源職缺 AI 輔助系統

本研究希望建立一套能整合多來源職缺資料，並提供下列核心能力的系統：

- 市場摘要型問答
- 個人化求職建議
- 職缺或角色比較
- 履歷解析與職缺匹配

### 1.3.2 建立可量測的評估與回歸框架

本研究不以主觀體感評估系統品質，而是建立一套可重複、可量測、可保存結果的驗證流程，包含：

- fixture baseline
- real snapshot eval
- real model eval
- latency regression
- training readiness gate
- formal human review

### 1.3.3 驗證在不進行 fine-tuning 下的產品可用性

本研究希望回答一個實務上重要的問題：在求職場景中，是否可以僅透過 retrieval、prompt contract、mode-aware control、resume ranking、telemetry 與 gate 設計，就把系統做到產品可用，而不必立刻進入模型 fine-tuning。

---

## 1.4 研究方法概述

本研究採取系統設計與實證評估並行的方法，而非先訓練模型再尋找應用場景。整體流程可概括為四個層次。

### 1.4.1 市場資料與快照建立

系統先從多個職缺來源擷取資料，經過去重、整併與 detail enrich 後，建立 `MarketSnapshot`。這份 snapshot 不只是 UI 顯示資料，也是 assistant 問答與 resume matching 的共同知識基礎。

### 1.4.2 RAG 問答與 mode-aware 回答控制

本研究將 snapshot 轉成多種 chunk 類型，透過 hybrid retrieval 與 rerank 取得對應證據，再根據問題類型切換不同回答模式：

- `market_summary`
- `personalized_guidance`
- `job_comparison`

每種模式都有各自的 prompt 契約、citation selection 與 rendering path。

### 1.4.3 履歷解析與職缺匹配

履歷路徑先建立 resume profile，再使用 two-stage ranking 對市場職缺做排序。系統不僅輸出 Top-k 結果，也同時追蹤：

- skill recall
- role alignment
- latency

### 1.4.4 產品級觀測與正式評估

為了讓結果可被驗證與回溯，本研究另建立：

- external eval workspace
- latency / reliability / token budget
- AI regression
- training readiness gate
- formal human review 流程

因此，本研究的方法並非單一模型比較，而是將系統能力、真實快照、延遲、token 使用與人評結果一併納入分析。

---

## 1.5 研究貢獻

本研究的主要貢獻如下。

### 1.5.1 提出一套面向求職場景的產品級 AI 系統架構

本研究不是單純打造聊天介面，而是提出一套整合：

- 多來源職缺快照
- RAG 問答
- 履歷解析
- 職缺匹配
- 產品監控

的完整系統架構。

### 1.5.2 提出 mode-aware 的求職問答設計

本研究將 AI 助理回答明確拆成三種模式：

- 市場摘要
- 個人化建議
- 職缺比較

並為三種模式設計不同的 retrieval、prompt 契約、citation selection 與前端 render path，降低單一泛化回答格式帶來的品質不穩定問題。

### 1.5.3 建立履歷匹配與排序評估流程

本研究不只產生匹配分數，也建立：

- `resume_extraction_labels`
- `resume_match_labels`
- `resume_label_eval`

用以量測 Top-k 命中、pairwise order accuracy 與 nDCG@3，使履歷匹配從展示性功能提升為可正式評估的排序問題。

### 1.5.4 建立產品級 observability 與 gate 框架

本研究將 AI 系統驗證擴展到產品層，建立：

- snapshot health gate
- assistant mode gate
- latency regression
- training readiness
- token / reliability budget
- formal human review

使系統可以被持續觀測，而不是只在單次實驗中取得一次性結果。

### 1.5.5 證明在不進行 fine-tuning 的前提下，系統仍可達到產品可用性

本研究最後的正式結果顯示：

- `latency_regression = PASS`
- `assistant_mode_gate = PASS`
- `human_review_gate = PASS`
- `training_readiness = DEFER`

這表示在目前資料規模與問題型態下，透過系統工程與評估閉環，已可使求職 AI 系統達到產品可用程度，而不必直接進入 fine-tuning。

---

## 1.6 論文架構

本論文後續章節安排如下。

### Chapter 2 相關研究

回顧與本研究有關的文獻，包含：

- RAG 與 evidence-grounded QA
- 履歷解析與職缺匹配
- LLM 評估與產品 observability

### Chapter 3 系統架構與方法

說明本研究系統的整體架構、資料流、RAG 問答流程、履歷解析與匹配流程，以及產品級監控與 gate 設計。

### Chapter 4 評估設計

說明資料集、標註方式、fixture baseline、real snapshot eval、real model eval、human review 與回歸 gate 的設計。

### Chapter 5 實驗結果

呈現 AI 主線的正式結果，包括：

- snapshot health
- assistant mode-aware real-model
- resume matching
- resume label ranking
- latency regression
- formal human review

並解釋為何目前的正式結論是 `training_readiness = DEFER`。

### Chapter 6 結論與未來工作

總結研究成果，討論系統限制，並說明未來在：

- 更大規模標註資料
- 長期產品 telemetry
- training / fine-tuning gate

上的可能延伸。

---

## 1.7 本章結論

本章界定了本研究的核心問題：在求職場景中，如何以真實職缺市場快照為基礎，建立一套兼顧證據、匹配、評估與產品化要求的 AI 系統。與其將研究重點放在模型訓練，本研究更強調系統架構、retrieval、回答控制、排序方法與正式評估閉環。

後續章節將依序說明系統設計、評估方法與正式結果，並證明本研究所提出的系統已在不進行 fine-tuning 的前提下，達到產品可用水準。
