# Chapter 5 實驗結果初稿

本章整理本研究在 AI / RAG / LLM 主線上的正式實驗結果。所有數據皆來自已保存的實驗結果與正式 human review 結果，而非人工估計。主要目的是回答三個問題：

1. 系統在真實快照下是否具備足夠品質。
2. 系統在產品條件下是否具備可接受延遲。
3. 在目前資料與評估覆蓋下，是否已經有必要進行 fine-tuning。

本章對應的主結果來源如下：

- [AI regression summary](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/summary.json)
- [AI regression report](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/ai_regression_20260408_002941/report.md)
- [Assistant real-model summary](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_212848/summary.json)
- [Resume real-model summary](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/real_model_eval_20260407_215715/summary.json)
- [Resume label eval summary](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/resume_label_eval_20260407_044723/summary.json)
- [Formal human review summary](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/formal_human_review_20260408_002923/summary.json)

---

## 5.1 主線總 gate 結果

本研究將 AI 系統的正式判定分成五個 gate：

- snapshot health gate
- assistant mode gate
- human review gate
- latency regression
- training readiness

最終結果如表 5-1 所示。

| Gate | Status | 說明 |
| --- | --- | --- |
| Snapshot health gate | `READY` | 真實快照覆蓋率足夠，可用於模型品質判讀 |
| Assistant mode gate | `PASS` | `market_summary`、`personalized_guidance`、`job_comparison` 三種模式皆達標 |
| Human review gate | `PASS` | 正式 reviewer 人評通過 |
| Latency regression | `PASS` | 核心延遲指標均在門檻內 |
| Training readiness | `DEFER` | 品質已達標，但目前沒有足夠證據支持 fine-tuning |

這組結果表示，本研究完成的系統已具備產品可用性與正式評估覆蓋，但現階段最佳策略仍是優先做產品整合與持續觀測，而不是立即進入模型訓練。

---

## 5.2 Snapshot health 結果

在真實快照評估中，本研究先檢查資料本身是否足以支撐模型品質判讀。若快照覆蓋不足，後續品質指標將不具代表性。

本研究使用的真實快照 health gate 結果如下：

| 指標 | 實際值 | 門檻 | 結果 |
| --- | ---: | ---: | --- |
| 角色數 | `1` | `>= 1` | PASS |
| 職缺數 | `34` | `>= 30` | PASS |
| 來源數 | `3` | `>= 3` | PASS |
| 薪資覆蓋率 | `0.3529` | `>= 0.1` | PASS |
| 工作內容覆蓋率 | `0.8824` | `>= 0.7` | PASS |
| 必備技能覆蓋率 | `0.7059` | `>= 0.6` | PASS |

這表示本研究用於最終判讀的真實快照，在資料量、來源數與欄位覆蓋率上已達到可評估門檻，因此後續 assistant、resume 與 human review 的結果具備解釋價值。

---

## 5.3 Assistant mode-aware real-model 結果

本研究並未將 AI 助理視為單一問答器，而是拆成三種模式：

- `market_summary`
- `personalized_guidance`
- `job_comparison`

這三種模式在真實模型條件下的結果如表 5-2 所示。

| Mode | Case Count | Avg Latency (ms) | Structured Output | Citation Keyword Recall | Evidence Sufficiency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `market_summary` | `6` | `4739.479` | `1.0` | `1.0` | `1.0` |
| `personalized_guidance` | `1` | `4368.892` | `1.0` | `1.0` | `1.0` |
| `job_comparison` | `1` | `5262.343` | `1.0` | `1.0` | `1.0` |

從結果可見：

1. 三種模式都已具備完整結構化輸出能力。
2. 三種模式的引用關鍵詞召回率皆為 `1.0`。
3. 三種模式的 evidence sufficiency 皆為 `1.0`。

這表示本研究後期加入的：

- mode routing
- mode-specific prompt contract
- comparison-specific citation selection
- personalized guidance answer control

已經有效穩定三種核心回答型態。

---

## 5.4 Resume matching 結果

履歷分析與匹配路徑的目標，不只是讓 Top-1 命中，而是兼顧排序品質與延遲。

本研究在真實模型條件下的 resume 路徑結果如下：

| 指標 | 數值 |
| --- | ---: |
| `top3_url_hit_rate` | `1.0` |
| `top1_role_match_rate` | `1.0` |
| `matched_skill_recall_mean` | `0.9688` |
| `build_profile_ms_mean` | `5227.174` |
| `match_jobs_ms_mean` | `4547.125` |
| `total_ms_mean` | `9774.299` |
| `warm build_profile_ms_mean` | `2.041` |

結果顯示：

1. 履歷匹配在 Top-3 命中率與角色對齊上表現穩定。
2. `matched_skill_recall_mean = 0.9688`，代表技能對齊能力已接近完整覆蓋。
3. 透過 two-stage ranking 與 extractor cache，系統已將 warm path 的履歷建檔時間壓到毫秒級。

因此，本研究認為 resume pipeline 已具備產品可用性，而目前剩餘的優化重點不再是 correctness，而是長期真實使用條件下的成本與觀測。

---

## 5.5 Resume label ranking 結果

為了讓履歷匹配不只停留在 Top-1 命中，本研究另建立了 `resume_label_eval` 來量測排序品質。其 aggregate 結果如下：

| 指標 | 數值 |
| --- | ---: |
| `top1_best_label_hit_rate` | `1.0` |
| `top3_relevant_recall_mean` | `0.8` |
| `pairwise_order_accuracy_mean` | `0.9667` |
| `nDCG@3` | `0.8763` |

這組結果代表：

1. 最佳標籤職缺幾乎都能排在最前方。
2. 排序關係整體正確。
3. 雖然 Top-3 相關職缺召回尚未達到滿分，但已具備穩定的排序表現。

因此，本研究認為目前 resume matching 已足以支撐產品級使用與後續論文分析。

---

## 5.6 Latency regression 結果

系統若只有品質而沒有可接受延遲，仍不足以成為產品。為此，本研究建立 latency regression gate，觀測 assistant、retrieval 與 resume 三條路徑的核心延遲。

最終結果如表 5-3 所示。

| 指標 | 實際值 (ms) | 門檻 (ms) | 結果 |
| --- | ---: | ---: | --- |
| Assistant total latency | `4758.514` | `<= 8000` | PASS |
| Retrieval cold latency | `1476.403` | `<= 2000` | PASS |
| Retrieval warm latency | `165.345` | `<= 400` | PASS |
| Resume build_profile latency | `5227.174` | `<= 6000` | PASS |
| Resume match_jobs latency | `4547.125` | `<= 7000` | PASS |
| Resume total latency | `9774.299` | `<= 13000` | PASS |
| Resume warm build_profile latency | `2.041` | `<= 250` | PASS |

這表示：

1. assistant 路徑已不再是不可接受的慢點。
2. retrieval 冷啟動時間已壓到 `2s` 內。
3. resume 路徑雖仍相對昂貴，但已進入可接受區間。

因此 latency regression 在本研究最後階段可正式標記為 `PASS`。

---

## 5.7 Formal human review 結果

自動指標不足以完全反映使用者可接受性，因此本研究進一步進行正式人工評分。最後使用兩位 reviewer，對 `8` 個 case 做 blind review，並在最後一輪將原先爭議的 `3` 題重新評分後合併判讀。

最終 human review aggregate 結果如下：

| 指標 | 數值 |
| --- | ---: |
| `reviewer_count` | `2` |
| `case_count` | `8` |
| `correctness_score_mean` | `4.9375` |
| `grounding_score_mean` | `5.0` |
| `usefulness_score_mean` | `5.0` |
| `clarity_score_mean` | `5.0` |
| `overall_score_mean` | `5.0` |
| `pairwise_verdict_agreement_rate` | `1.0` |
| `cohens_kappa_verdict` | `1.0` |

verdict 分布為：

- `accept = 16`

這代表：

1. 正式 reviewer 對最終答案已沒有明顯保留意見。
2. 回答不僅正確，且 grounding、usefulness 與 clarity 皆達高分。
3. 經過最後一輪 targeted re-check 之後，原本 reviewer 分歧已被消除。

因此，本研究中的 `human_review_gate` 最終可標示為 `PASS`。

---

## 5.8 綜合討論

綜合上述結果，本研究得到以下三點結論。

### 5.8.1 系統品質已達產品可用水準

assistant mode-aware quality、resume matching、human review 與 latency regression 均已通過正式 gate。這表示本研究完成的系統已從功能原型進入產品可用階段。

### 5.8.2 問題主要透過系統工程而非訓練解決

本研究觀察到，影響品質與使用者接受度的主要因素包括：

- retrieval 設計
- citation selection
- answer mode control
- prompt 契約
- ranking pipeline
- telemetry 與 gate

也就是說，本研究最關鍵的進展並非來自模型訓練，而是來自系統工程與評估閉環。

### 5.8.3 現階段不建議直接進行 fine-tuning

雖然品質與延遲皆已達標，但 `training_readiness` 的最終判定仍為 `DEFER`。這不是因為系統不足，而是因為目前尚無足夠證據顯示 fine-tuning 會帶來比產品整合與持續觀測更高的收益。

因此，本研究目前的最佳策略是：

- 持續收集真實產品 telemetry
- 觀察是否出現新的穩定錯誤型態
- 在資料量與錯誤模式更明確時，再重新評估是否開啟 training 階段

---

## 5.9 本章結論

本章證明，本研究所提出的 AI 主線系統在真實快照、真實模型與正式 reviewer 條件下，已同時滿足：

- 品質
- 引用充分性
- 模式覆蓋
- 排序品質
- 延遲門檻
- 人工評分一致性

最終結果為：

- `Snapshot health gate = READY`
- `Assistant mode gate = PASS`
- `Human review gate = PASS`
- `Latency regression = PASS`
- `Training readiness = DEFER`

這組結果支持本研究的核心論點：在求職場景中，透過 RAG、mode-aware answer control、resume ranking 與完整 evaluation / observability 設計，可以在不進行 fine-tuning 的前提下，建立一套產品級可用的 AI 輔助系統。
