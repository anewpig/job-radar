# Chapter 4 評估設計初稿

本章說明本研究的評估設計。由於本研究的目標不是單純展示某個模型回答得「看起來不錯」，而是驗證一套求職 AI 系統是否具備產品可用性，因此評估設計同時涵蓋：

- 資料集與標註
- fixture baseline
- real snapshot eval
- real model eval
- resume ranking eval
- latency / budget / readiness gate
- formal human review

本章的核心思想是：求職場景中的 AI 系統不能只依賴單一自動指標，而必須同時觀察真實資料覆蓋、模型行為、延遲、產品觀測與人工評分結果。

---

## 4.1 評估目標

本研究的評估設計要回答以下四個問題：

1. 系統在固定資料與固定題集下，是否具備穩定的基本能力。
2. 系統在真實職缺快照下，是否仍能維持正確的 retrieval、citation 與回答品質。
3. 系統在真實模型條件下，是否具備可接受的延遲與排序品質。
4. 在目前資料規模與評估結果下，是否有必要進一步進行模型 fine-tuning。

因此，本研究將評估拆成多層，而不是只使用單一 benchmark。整體上分為：

- `offline fixture baseline`
- `real snapshot eval`
- `real model eval`
- `product telemetry / latency gate`
- `formal human review`

---

## 4.2 資料集與標註設計

本研究在 AI 評估上使用三組主要資料集，分別對應 assistant 問答、履歷抽取與履歷匹配。

### 4.2.1 Assistant 問答題集

assistant 評估題集目前包含 `100` 題，對應以下主要類型：

- `market_summary`
- `personalized_guidance`
- `job_comparison`
- 技能、薪資、工作內容、角色差異與市場摘要等子題型

此題集的目的不是訓練模型，而是作為 regression benchmark，驗證不同版本的 retrieval、prompt 契約與回答控制邏輯是否退化。

### 4.2.2 Resume extraction 標註集

履歷抽取標註集目前包含 `30` 筆資料，用於驗證：

- target roles 抽取
- extracted skills
- specialized role detection
- profile normalization

此資料集主要作為 extraction correctness 與 schema 穩定性的評估基礎。

### 4.2.3 Resume match 標註集

履歷匹配標註集目前包含 `60` 筆 label，用於量測：

- Top-1 最佳職缺命中
- Top-3 relevant recall
- pairwise order accuracy
- nDCG@3

此資料集將履歷匹配視為排序問題，而非單純二元分類。

### 4.2.4 資料集定位

這三組資料集的角色不同：

- `assistant_questions`
  - 驗證問答品質與 regression 穩定性
- `resume_extraction_labels`
  - 驗證履歷 profile 建立品質
- `resume_match_labels`
  - 驗證職缺排序品質

本研究在現階段將它們定位為 `evaluation datasets`，而不是 `training datasets`。原因在於目前資料量足以支撐評估與比較，但尚不足以直接支撐正式 fine-tuning。

---

## 4.3 Offline Fixture Baseline

本研究首先建立 offline fixture baseline，用固定 snapshot、固定 resume cases 與固定題集，驗證系統邏輯是否正確，並提供 regression 基準。

### 4.3.1 設計目的

offline fixture baseline 的用途有三點：

1. 在不受真實快照波動影響的情況下驗證邏輯正確性。
2. 作為 retrieval、prompt 與 ranking 調整時的第一層 regression。
3. 讓後續 real snapshot 與 real model eval 有可對照的基礎。

### 4.3.2 評估內容

offline fixture baseline 主要檢查：

- assistant keyword recall
- citation hit
- retrieval top-k type hit
- resume matching correctness

在此層中，系統更像是在驗證 pipeline 是否按預期工作，而不是驗證真實世界表現。

### 4.3.3 限制

fixture baseline 的限制在於：

- 快照是固定的
- 問題型態較乾淨
- 不會反映真實來源缺漏、欄位不一致或資料稀疏問題

因此本研究不以 fixture baseline 作為最終品質結論，而是把它當成第一層驗證。

---

## 4.4 Real Snapshot Eval

為了驗證系統在真實市場資料下的行為，本研究引入 real snapshot eval，直接以真實 `jobs_latest.json` 作為評估輸入。

### 4.4.1 設計目的

real snapshot eval 的目標是回答：

- 真實快照是否足以支撐模型品質判讀
- retrieval 是否能在真實資料缺漏下維持正確 evidence type
- assistant 與 resume 路徑是否能在真實資料條件下正常工作

### 4.4.2 Snapshot Health Gate

在 real snapshot eval 中，本研究先建立 `snapshot health gate`，檢查真實快照是否足以作為評估材料。檢查內容包括：

- 職缺數
- 來源數
- 角色覆蓋
- 薪資覆蓋率
- 工作內容覆蓋率
- 技能欄位覆蓋率

若快照覆蓋不足，則後續品質指標只能被解讀為 smoke check，而不能作為正式模型品質依據。

### 4.4.3 評估內容

real snapshot eval 主要觀察：

- assistant 的 citation type 命中
- citation keyword recall
- evidence sufficiency
- retrieval type recall
- resume 在真實快照下的 Top-k 表現

此層的特點是使用真實市場資料，但仍不一定每次都打真實模型，因此主要用來驗證資料條件與系統路徑是否合理。

---

## 4.5 Real Model Eval

為了驗證系統在真實模型條件下的最終表現，本研究進一步建立 real model eval。這一層會直接使用真實模型設定，而非 deterministic fake client。

### 4.5.1 設計目的

real model eval 用來回答以下問題：

- 在真實模型條件下，assistant 三種 mode 是否仍具備足夠 grounding 與 evidence sufficiency
- retrieval 在真實查詢與真實模型條件下是否仍能維持正確 evidence type
- resume extraction 與 matching 的實際延遲與排序品質如何

### 4.5.2 Assistant Mode-Aware 評估

assistant 不再被視為單一路徑，而是按三種模式分別觀察：

- `market_summary`
- `personalized_guidance`
- `job_comparison`

評估指標包括：

- structured output rate
- citation keyword recall
- evidence sufficiency
- avg latency

這使本研究能區分不同問題型態的強弱點，而非僅得到一個整體平均值。

### 4.5.3 Resume 路徑評估

resume 路徑在 real model eval 中主要量測：

- `top3_url_hit_rate`
- `top1_role_match_rate`
- `matched_skill_recall_mean`
- `build_profile_ms_mean`
- `match_jobs_ms_mean`
- `total_ms_mean`

此設計使研究能同時比較品質與成本，而不是只看匹配準確率。

---

## 4.6 Resume Label Ranking Eval

本研究額外建立 `resume_label_eval`，將履歷匹配正式建模為排序問題。

### 4.6.1 設計目的

此層的目的不是替代 real model eval，而是從標註資料角度量測職缺排序品質。與只看 Top-1 命中不同，排序評估能更準確反映：

- 最佳職缺是否排在前面
- 相關職缺是否被召回
- 不適合職缺是否被推到後面

### 4.6.2 指標

本研究主要使用：

- `top1_best_label_hit_rate`
- `top3_relevant_recall_mean`
- `top3_reject_free_rate`
- `pairwise_order_accuracy_mean`
- `nDCG@3`

這些指標讓履歷匹配從展示性功能提升為可正式評估的 ranking pipeline。

---

## 4.7 Latency、Budget 與 Product Telemetry

AI 系統若只有品質，沒有可接受的延遲與成本，仍不足以進入產品。為此，本研究在主產品路徑中加入 telemetry 與 budget evaluator。

### 4.7.1 Telemetry 內容

系統會記錄：

- `event_type`
- `status`
- `latency_ms`
- `model_name`
- `query_signature`
- `usage_input_tokens`
- `usage_output_tokens`
- `usage_total_tokens`
- `usage_cached_input_tokens`

這些資料會寫入產品狀態資料庫，用於後續 budget 分析與產品後台顯示。

### 4.7.2 Latency / Reliability / Token Budget

本研究建立的 budget 主要分成三類：

- latency budget
- reliability budget
- token budget

其中 latency budget 會針對：

- assistant
- retrieval
- resume build_profile
- resume match_jobs

等路徑設定門檻，並產出 `PASS / WARN / FAIL` 判定。

### 4.7.3 設計價值

這層設計讓 AI 系統的管理方式更接近正式軟體工程，而不是一次性研究實驗。也就是說，模型行為不再只透過單次 benchmark 判斷，而是能在產品運行中被持續觀測。

---

## 4.8 Formal Human Review

自動化指標雖然重要，但不足以完整評估使用者是否會接受 AI 回答。因此，本研究另外建立 formal human review 流程。

### 4.8.1 Review Packet 與 Blind Review

本研究會先從最新的 assistant case export 中抽樣，產生 blind reviewer packet。reviewer 只會看到：

- 問題
- 系統回答
- citation snippets

而不會看到研究內部自動分數。

### 4.8.2 評分維度

reviewer 需針對每題填寫：

- `correctness_score`
- `grounding_score`
- `usefulness_score`
- `clarity_score`
- `overall_score`
- `verdict`
- `notes`

其中 `verdict` 使用：

- `accept`
- `minor_issue`
- `major_issue`
- `reject`

### 4.8.3 Aggregation 與一致性

回收 reviewer 資料後，系統會做 validation 與 aggregation，並計算：

- average scores
- verdict distribution
- pairwise verdict agreement rate
- Cohen's kappa

本研究將 formal human review 視為最接近實際使用者接受度的正式 gate。

---

## 4.9 Training Readiness Gate

本研究的最後一層不是直接訓練模型，而是建立 `training_readiness gate`，判斷是否有必要進入 fine-tuning。

### 4.9.1 設計目的

training readiness 的目的不是鼓勵訓練，而是防止在缺乏充分證據時過早進入 fine-tuning。此 gate 綜合參考：

- snapshot health
- assistant mode gate
- latency regression
- resume ranking
- human review

### 4.9.2 判定邏輯

若品質、引用充分性、排序與延遲均已達標，但尚無證據顯示 fine-tuning 能帶來顯著額外收益，則判定為：

- `DEFER`

這代表：

- 現在不是 training 的最佳時機
- 下一步應優先做產品整合、真實觀測與 error collection

### 4.9.3 在本研究中的角色

這個 gate 使本研究能清楚區分：

- 哪些問題應透過 retrieval / prompt / system design 解決
- 哪些問題才真正值得用 training 解決

因此，training readiness gate 是本研究從工程實作走向研究判讀的關鍵橋梁。

---

## 4.10 本章結論

本章建立了本研究的完整評估方法。與只依賴單一 benchmark 的做法不同，本研究採用多層評估設計，從固定資料 regression、真實快照、真實模型、履歷排序、人評、產品觀測到 training gate，形成一個可重複、可追溯、可產品化的驗證閉環。

這樣的評估設計使本研究能夠在後續章節中，不只回答「模型答得好不好」，還能回答：

- 在真實市場資料下是否仍可靠
- 在產品條件下延遲是否可接受
- 使用者是否會接受這些回答
- 是否有必要進一步進行 fine-tuning

下一章將根據本章設計的評估流程，呈現本研究的正式實驗結果與最終判讀。
