# 摘要初稿

本研究針對求職資訊分散、職缺描述不一致、履歷與市場需求難以對照等問題，提出一套面向求職場景的產品級 AI 輔助系統。系統以多來源職缺資料為基礎，建立統一的市場快照，並在此之上整合檢索增強生成（Retrieval-Augmented Generation, RAG）問答、履歷解析、職缺匹配、產品級觀測與正式評估流程。研究重點不在於訓練新的基礎模型，而在於驗證：在不進行 fine-tuning 的前提下，是否能僅透過資料流設計、retrieval、mode-aware 回答控制、排序方法與評估閉環，使系統達到產品可用水準。

本研究之系統主要包含四個層次：多來源職缺擷取與市場快照建立、RAG 問答與回答模式控制、履歷解析與職缺匹配，以及產品級 telemetry 與外部評估框架。AI 助理被拆分為 `market_summary`、`personalized_guidance` 與 `job_comparison` 三種回答模式，並分別設計 retrieval 策略、prompt 契約、citation selection 與前端 rendering。履歷匹配部分則採用 two-stage ranking，以兼顧匹配品質與延遲表現。為確保系統具備可量測性與可回歸性，本研究另建立 fixture baseline、real snapshot eval、real model eval、resume label eval、latency regression、training readiness gate 與 formal human review 等完整驗證流程。

正式實驗結果顯示，本研究之系統在主要 gate 上分別達成 `latency_regression = PASS`、`assistant_mode_gate = PASS` 與 `human_review_gate = PASS`。在真實模型條件下，三種 assistant 回答模式的 `citation_keyword_recall` 與 `evidence_sufficiency` 皆達到 `1.0`。履歷匹配方面，`top3_url_hit_rate = 1.0`、`matched_skill_recall_mean = 0.9688`，且 `resume_total_ms_mean = 9774.299 ms`，已落在可接受門檻內。正式人工評分方面，兩位 reviewer 對 `8` 個案例的最終聚合結果為 `overall_score_mean = 5.0`、`grounding_score_mean = 5.0`，且 `pairwise_verdict_agreement_rate = 1.0`。綜合各項正式結果，本研究的 `training_readiness` 判定為 `DEFER`，表示在目前資料規模與錯誤型態下，尚無足夠證據支持立即進行 fine-tuning。

本研究的主要貢獻有三。第一，提出一套以真實職缺市場快照為核心的求職 AI 系統架構，整合多來源資料、RAG 問答與履歷匹配。第二，提出一套可重複、可量測、可追溯的評估與觀測框架，使 AI 系統的品質、延遲、成本與人評結果能被一致性管理。第三，證明在求職場景中，透過 retrieval、mode-aware 回答控制、排序設計與正式評估閉環，可以在不進行 fine-tuning 的情況下建立產品可用的 AI 輔助系統。研究結果顯示，相較於直接進行模型訓練，系統工程與評估機制的完整性，對求職 AI 系統的實際落地更具關鍵性。

關鍵詞：求職輔助系統、檢索增強生成、履歷匹配、職缺市場快照、人工評分、產品級評估
