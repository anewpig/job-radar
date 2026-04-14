# Chapter 6 結論與未來工作初稿

本章總結本研究的主要成果、研究限制與未來工作方向。研究主軸不是建立新的基礎模型，而是針對求職場景，設計並驗證一套結合多來源職缺快照、RAG 問答、履歷匹配、正式評估與產品級監控的 AI 系統。透過前述章節的系統設計與實驗結果，可以對本研究的成果與後續延伸做出明確判讀。

---

## 6.1 研究總結

本研究針對求職資訊分散、職缺內容不一致、履歷與市場需求難以對照等問題，建立了一套多來源職缺整合與 AI 輔助系統。該系統以真實市場快照為中心，向上支撐：

- 市場摘要型問答
- 個人化求職建議
- 職缺或角色比較
- 履歷解析與職缺匹配

同時，系統並非僅提供單次問答，而是進一步建立：

- external eval workspace
- real snapshot eval
- real model eval
- latency / token / reliability budget
- formal human review
- training readiness gate

因此，本研究的核心成果不只是 AI 功能本身，而是將 AI 能力、產品可觀測性與研究評估機制整合為一條可重複驗證的工程主線。

---

## 6.2 研究結論

根據本研究最終正式結果，可得到以下幾項結論。

### 6.2.1 多來源職缺快照可作為求職 AI 的有效知識基礎

本研究證明，透過 staged crawl、snapshot 統一表示、chunk 建立與 retrieval 設計，可以將多來源職缺資料轉化為 AI 問答與履歷匹配的共同知識基礎。這使系統不必直接依賴通用模型的靜態知識，而能以真實職缺市場資料提供回答與建議。

### 6.2.2 Mode-aware 回答控制能提升求職場景下的可用性

本研究將 assistant 回答分成：

- `market_summary`
- `personalized_guidance`
- `job_comparison`

三種模式，並為其分別設計 retrieval 策略、prompt 契約、citation selection 與前端 rendering。實驗結果顯示，這種 mode-aware 設計能有效穩定回答結構與證據充分性，避免不同問題類型共用單一回答模式所造成的不穩定。

### 6.2.3 履歷匹配可透過 two-stage ranking 兼顧品質與延遲

本研究在履歷路徑中加入 two-stage ranking、specialized role extraction 與 warm-path cache，最終在真實模型條件下達到穩定的排序品質與可接受延遲。這表示求職場景中的 resume-to-job ranking，不必一開始就依賴 fine-tuning，也能透過系統設計獲得高可用性。

### 6.2.4 系統工程與評估閉環比立即進行 fine-tuning 更關鍵

本研究的正式 gate 結果為：

- `latency_regression = PASS`
- `assistant_mode_gate = PASS`
- `human_review_gate = PASS`
- `training_readiness = DEFER`

這組結果支持本研究的核心論點：在求職場景中，產品品質與可用性主要是由 retrieval、citation selection、mode control、ranking pipeline、telemetry 與 formal evaluation 所決定，而非必須先進行 fine-tuning。

---

## 6.3 研究限制

雖然本研究已完成產品級 AI 主線與正式驗證，但仍存在以下限制。

### 6.3.1 真實快照覆蓋仍受當次搜尋條件影響

本研究雖已建立 snapshot health gate，但真實快照的角色分布、來源分布與欄位覆蓋率，仍會受實際搜尋 query 與資料來源限制。這意味著某些特定角色或冷門職缺在實驗中的代表性可能不足。

### 6.3.2 Human review 規模仍有限

本研究完成了 formal human review 與 targeted re-check，但 reviewer 數量與案例數仍偏小，較適合作為產品驗證與論文 proof-of-quality，而非大規模使用者研究。因此，未來若要更強地主張泛化品質，仍需更大規模的人評設計。

### 6.3.3 Training gate 尚未進入真正的訓練實驗階段

本研究最終將 `training_readiness` 判為 `DEFER`，其含義不是系統不足，而是目前尚未蒐集到足夠證據，證明 fine-tuning 會比持續產品整合與觀測更具投資報酬。因此，本研究沒有進一步驗證 fine-tuning 對本系統的邊際收益。

### 6.3.4 履歷資料規模仍以評估用途為主

本研究目前的履歷標註集已足夠支撐 extraction 與 ranking 的評估，但尚未達到可直接支撐正式模型訓練的規模。加上履歷資料牽涉隱私與授權問題，未來若要進入 training 階段，必須先建立更完整的資料治理與同意機制。

---

## 6.4 未來工作

基於本研究結果，未來工作可分成產品延伸與研究延伸兩條路線。

### 6.4.1 持續收集真實產品 telemetry

由於本研究已完成 token、latency 與 reliability telemetry，未來最有價值的工作是持續觀測真實使用情境，收集：

- 不同 answer mode 的實際使用頻率
- 真實延遲與 token 成本
- 使用者追問模式
- 穩定出現的錯誤型態

這些資料可作為後續開啟 training gate 的依據。

### 6.4.2 擴大 human review 與 error analysis

本研究已建立 blind packet、formal reviewer workflow 與 aggregation pipeline。未來可擴充 reviewer 人數與 case 覆蓋，進一步建立：

- 更完整的錯誤分類
- 不同 answer mode 的人評差異
- 不同 prompt 版本的人工比較

### 6.4.3 擴大履歷標註資料並建立合規資料流程

若未來要研究 fine-tuning 或更進階的 ranking 學習，應優先擴大：

- `resume_extraction_labels`
- `resume_match_labels`

但資料前提必須是：

- 有使用者同意
- 去識別化
- 可追溯標註版本
- 符合研究倫理與資料治理要求

### 6.4.4 重新評估 training gate

本研究目前結論為 `DEFER`，但未來若同時滿足以下條件，便可重新開啟 training gate：

- 真實產品中出現穩定且重複的錯誤型態
- 這些錯誤無法僅透過 prompt、retrieval 或 ranking 修正
- 有足夠標註資料支撐訓練實驗
- 可量化比較訓練前後差異

屆時，較合理的方向會是：

- 小型 fine-tuning 實驗
- reranker 訓練
- extraction / ranking 專用模型微調

而不是直接進行大規模 pretraining。

### 6.4.5 將評估與產品發布流程進一步整合

目前本研究已建立 `AI regression`、`training_readiness` 與 `formal human review` 工具鏈。未來可將這些流程更進一步整合至產品發布與版本管理流程，例如：

- 每次重大 AI 變更自動觸發 regression
- 每次 prompt 版本更新保留 case-level diff
- 在產品管理後台直接查看 mode-aware 品質變化

這能使 AI 系統維護更接近正式軟體工程的持續交付流程。

---

## 6.5 總結

本研究完成了一套面向求職場景的產品級 AI 系統，並以正式評估結果證明：

1. 多來源職缺市場快照可以作為有效的 AI 知識基礎。
2. mode-aware RAG 問答能支撐市場摘要、個人化建議與職缺比較。
3. 履歷匹配可在不依賴 fine-tuning 的前提下，透過系統設計達到高品質與可接受延遲。
4. 產品級 observability、formal evaluation 與 human review 對 AI 系統的實際落地至關重要。

總體而言，本研究的貢獻並不在於提出一個新的大型模型，而在於證明：透過合理的資料流設計、RAG 架構、answer mode 控制、排序方法與正式評估閉環，可以在求職場景中建立一套具有產品可用性的 AI 輔助系統。

最終正式判定顯示，本研究的系統已達產品可用階段，而未來是否進入模型訓練，應建立在真實產品資料與更大規模標註資料的基礎上，而非僅因具備訓練資源就提前啟動。
