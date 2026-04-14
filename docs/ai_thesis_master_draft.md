# 多來源職缺整合平台之 RAG 問答與履歷匹配系統設計與評估

作者：`[請填寫]`  
指導教授：`[請填寫]`  
學校 / 系所：`[請填寫]`  
日期：`[請填寫]`

---

# 中文摘要

本研究針對求職資訊分散、職缺描述不一致、履歷與市場需求難以對照等問題，提出一套面向求職場景的產品級 AI 輔助系統。系統以多來源職缺資料為基礎，建立統一的市場快照，並在此之上整合檢索增強生成（Retrieval-Augmented Generation, RAG）問答、履歷解析、職缺匹配、產品級觀測與正式評估流程。研究重點不在於訓練新的基礎模型，而在於驗證：在不進行 fine-tuning 的前提下，是否能僅透過資料流設計、retrieval、mode-aware 回答控制、排序方法與評估閉環，使系統達到產品可用水準。

本研究之系統主要包含四個層次：多來源職缺擷取與市場快照建立、RAG 問答與回答模式控制、履歷解析與職缺匹配，以及產品級 telemetry 與外部評估框架。AI 助理被拆分為 `market_summary`、`personalized_guidance` 與 `job_comparison` 三種回答模式，並分別設計 retrieval 策略、prompt 契約、citation selection 與前端 rendering。履歷匹配部分則採用 two-stage ranking，以兼顧匹配品質與延遲表現。為確保系統具備可量測性與可回歸性，本研究另建立 fixture baseline、real snapshot eval、real model eval、resume label eval、latency regression、training readiness gate 與 formal human review 等完整驗證流程。

正式實驗結果顯示，本研究之系統在主要 gate 上分別達成 `latency_regression = PASS`、`assistant_mode_gate = PASS` 與 `human_review_gate = PASS`。在真實模型條件下，三種 assistant 回答模式的 `citation_keyword_recall` 與 `evidence_sufficiency` 皆達到 `1.0`。履歷匹配方面，`top3_url_hit_rate = 1.0`、`matched_skill_recall_mean = 0.9688`，且 `resume_total_ms_mean = 9774.299 ms`，已落在可接受門檻內。正式人工評分方面，兩位 reviewer 對 `8` 個案例的最終聚合結果為 `overall_score_mean = 5.0`、`grounding_score_mean = 5.0`，且 `pairwise_verdict_agreement_rate = 1.0`。綜合各項正式結果，本研究的 `training_readiness` 判定為 `DEFER`，表示在目前資料規模與錯誤型態下，尚無足夠證據支持立即進行 fine-tuning。

本研究的主要貢獻有三。第一，提出一套以真實職缺市場快照為核心的求職 AI 系統架構，整合多來源資料、RAG 問答與履歷匹配。第二，提出一套可重複、可量測、可追溯的評估與觀測框架，使 AI 系統的品質、延遲、成本與人評結果能被一致性管理。第三，證明在求職場景中，透過 retrieval、mode-aware 回答控制、排序設計與正式評估閉環，可以在不進行 fine-tuning 的情況下建立產品可用的 AI 輔助系統。研究結果顯示，相較於直接進行模型訓練，系統工程與評估機制的完整性，對求職 AI 系統的實際落地更具關鍵性。

關鍵詞：求職輔助系統、檢索增強生成、履歷匹配、職缺市場快照、人工評分、產品級評估

---

# Abstract

This study addresses a practical problem in job seeking: job information is fragmented across multiple platforms, job descriptions are inconsistent, and it is difficult for applicants to align market demand with their own resumes. To address this problem, the study proposes a product-grade AI assistance system for job seeking. The system is built on unified market snapshots aggregated from multiple job sources and integrates Retrieval-Augmented Generation (RAG), resume parsing, job matching, product observability, and a formal evaluation workflow. The goal of the study is not to train a new foundation model, but to verify whether a product-usable AI system can be achieved without fine-tuning through system design, retrieval, mode-aware answer control, ranking, and evaluation loops.

The proposed system contains four major layers: multi-source job crawling and market snapshot construction, RAG-based question answering with answer-mode control, resume parsing and job ranking, and product-grade telemetry with an external evaluation workspace. The assistant is explicitly divided into three answer modes: `market_summary`, `personalized_guidance`, and `job_comparison`. Each mode uses its own retrieval strategy, prompt contract, citation selection, and rendering path. For resume matching, the system adopts a two-stage ranking pipeline to balance ranking quality and latency. To ensure reproducibility and operational validity, the study further establishes a complete evaluation framework, including fixture baseline evaluation, real snapshot evaluation, real model evaluation, resume label evaluation, latency regression, a training-readiness gate, and formal human review.

The final results show that the system achieved `PASS` on latency regression, assistant mode evaluation, and formal human review. Under real-model conditions, all three assistant modes reached `1.0` on citation keyword recall and evidence sufficiency. For resume matching, the system achieved `top3_url_hit_rate = 1.0`, `matched_skill_recall_mean = 0.9688`, and `resume_total_ms_mean = 9774.299 ms`, which remained within the acceptable latency budget. In formal human review, the aggregated results from two reviewers over eight cases yielded `overall_score_mean = 5.0`, `grounding_score_mean = 5.0`, and `pairwise_verdict_agreement_rate = 1.0`. Based on these results, the final `training_readiness` status remained `DEFER`, indicating that there is currently insufficient evidence to justify immediate fine-tuning.

This study makes three main contributions. First, it proposes a job-seeking AI system architecture centered on real-world market snapshots, integrating multi-source job data, RAG question answering, and resume matching. Second, it establishes a repeatable, measurable, and traceable evaluation and observability framework that jointly monitors quality, latency, token usage, and human-review outcomes. Third, it demonstrates that, in the job-seeking domain, a product-usable AI system can be achieved without fine-tuning by relying on retrieval design, mode-aware answer control, ranking, and a formal evaluation loop. The findings suggest that, for this class of applications, engineering rigor and evaluation completeness are more critical than immediate model training.

Keywords: job-seeking assistance system, retrieval-augmented generation, resume matching, market snapshot, human review, product-grade evaluation

---

# Chapter 1 緒論

## 1.1 研究背景

近年求職活動逐漸高度平台化，職缺資訊分散於多個網站與來源。對求職者而言，真正的困難不只是找到職缺，而是同時整理工作內容、技能需求、薪資、履歷缺口與角色差異。單純蒐集職缺列表並不足以支援實際求職決策，使用者真正需要的是一套能整合多來源職缺、以證據為基礎回答市場問題、依履歷提供個人化建議、比較不同職缺差異，並支援後續投遞流程的系統。

大型語言模型讓自然語言互動成為可能，但若直接使用通用聊天模型，常會面臨缺乏真實職缺證據、無法保證回答 grounding，以及難以支撐履歷匹配與產品級決策流程等問題。因此，本研究將問題定義為：如何在不依賴 fine-tuning 的前提下，利用真實職缺市場快照、RAG、履歷匹配與正式評估機制，建立一套可產品化的求職 AI 系統。

## 1.2 研究動機

本研究的動機來自三個層面。第一，多來源職缺平台在欄位命名、內容密度、薪資揭露與工作內容描述上不一致，使用者難以直接比較。第二，通用 LLM 雖然能生成流暢回答，但若沒有真實職缺證據與引用，容易造成誤導。第三，即使單題回答看似合理，也不代表整體系統具備產品可用性，因此還需要延遲、成本、人評與回歸機制。

## 1.3 研究目的

本研究有三項主要目的：

1. 建立多來源職缺 AI 輔助系統。
2. 建立可量測、可回歸的評估框架。
3. 驗證在不進行 fine-tuning 的前提下，系統是否已達產品可用性。

## 1.4 研究方法概述

本研究採取系統設計與實證評估並行的方法。整體流程可分為：

1. 多來源職缺資料擷取與市場快照建立。
2. RAG 問答與 mode-aware answer control。
3. 履歷解析與 two-stage job ranking。
4. 產品級 telemetry 與外部評估框架。

## 1.5 研究貢獻

本研究的主要貢獻為：

1. 提出一套面向求職場景的產品級 AI 系統架構。
2. 提出一套 mode-aware 的求職問答設計。
3. 建立履歷匹配與排序評估流程。
4. 建立產品級 observability 與 gate 框架。
5. 證明在不進行 fine-tuning 的前提下，系統仍可達到產品可用性。

## 1.6 論文架構

本論文後續章節安排如下：

- Chapter 2：相關研究
- Chapter 3：系統架構與方法
- Chapter 4：評估設計
- Chapter 5：實驗結果
- Chapter 6：結論與未來工作

## 1.7 本章結論

本章界定了本研究的核心問題與研究目標。後續章節將依序說明系統設計、評估方法與正式結果，並證明本研究所提出的系統已在不進行 fine-tuning 的前提下，達到產品可用水準。

---

# Chapter 2 相關研究

## 2.1 RAG 與 Evidence-Grounded Question Answering

大型語言模型具備強大的自然語言生成能力，但其知識來自訓練資料與模型參數，無法自然反映特定時間點的最新資訊，也難以保證每一段回答都能被具體證據支撐。對求職場景而言，這個限制特別明顯，因為職缺需求、薪資揭露與工作內容屬於高度時效性與來源依賴的資訊（Liang et al., 2023; Menick et al., 2022）。

檢索增強生成（Retrieval-Augmented Generation, RAG）的核心概念，是先從外部知識來源中找出與問題最相關的內容，再將該內容作為模型生成回答的上下文。這使模型不必完全依賴自身參數中的靜態知識，而可以用真實資料支撐回應（Lewis et al., 2020; Gao et al., 2024）。

然而，通用 RAG pipeline 並不直接等同於可靠的 evidence-grounded QA。單純把檢索到的文件片段送進模型，仍可能出現回答過度概括、引用與結論不一致，或 retrieval 雖然命中但沒有真正支撐最終答案的情況。因此，evidence-grounded QA 的研究重點不只在檢索本身，也包括 retrieval 是否命中正確證據類型、模型回答是否被證據充分支撐，以及引用內容是否能被人工檢查與驗證（Menick et al., 2022; Gao et al., 2024）。

對求職場景而言，使用者常問的不只是單點事實，而是聚合性與決策性問題，例如市場最常見的技能、工作內容分布、角色差異，以及履歷相對於市場要求的缺口。這些問題往往需要同時整合多筆職缺資料，而不是對單一文件做抽取式回答（Lewis et al., 2020; Menick et al., 2022）。

因此，本研究承接 RAG 與 evidence-grounded QA 的核心觀念，但將其延伸到求職產品情境中，進一步處理多來源職缺市場快照、mode-aware retrieval 與 answer control、comparison-specific 與 personalized citation selection，以及正式 human review 與 product telemetry。這也是本研究與一般 RAG 系統應用工作的主要差異之一。

## 2.2 Resume Parsing 與 Job Matching

求職場景中的第二條重要研究脈絡，是履歷解析與職缺匹配。履歷解析（resume parsing）可被視為資訊抽取問題，常見任務包括角色或職稱辨識、技能抽取、學經歷整理，以及年資與領域標記（Ling et al., 2025）。

在較早期的方法中，這些任務多以規則、詞典或命名實體辨識為主；在大型語言模型出現後，履歷抽取逐漸轉向 schema-based extraction 或 structured generation。然而，即使模型能從履歷中抽出若干技能與職稱，也不表示系統已經具備足夠的職缺匹配能力。原因在於求職匹配不是單純的欄位對欄位比對，而涉及技能名稱與別名對齊、角色語義對齊、市場需求與個人經驗的差異判讀，以及多筆職缺之間的排序（Ling et al., 2025; Bian et al., 2019）。

因此，履歷匹配更適合被視為 ranking 問題，而非單純二元分類。對求職者而言，系統的價值通常不是判斷某份履歷能不能投某份工作，而是提供一組合理排序的候選職缺，並說明為什麼這些職缺較適合、自己已具備哪些能力、還缺哪些能力，以及哪些缺口值得優先補強（Bian et al., 2019; Yu et al., 2025）。

既有履歷與職缺匹配研究，已經提供了 skill normalization、role representation 與 ranking metrics 的重要基礎。然而，這些研究在求職產品場景下仍有缺口：不少研究把 matching 問題視為離線資料集上的分類任務，較少處理真實職缺快照的欄位缺漏與來源不一致；許多研究重點在模型分數，而不是延遲、token 成本與實際互動；履歷匹配也往往與問答系統分開設計（Bian et al., 2019; Yu et al., 2025; Ling et al., 2025）。

本研究在此脈絡中的切入點，是將履歷匹配納入同一個 AI 系統主線，而不是把它當成獨立展示功能。具體而言，本研究將履歷路徑拆成 resume extraction、profile normalization、two-stage ranking 與 gap-oriented explanation，並用 `resume_extraction_labels`、`resume_match_labels` 與 `resume_label_eval` 正式衡量其品質。

## 2.3 LLM Evaluation、Human Review 與 Observability

大型語言模型相關研究的一個常見問題是，系統評估往往停留在單次 benchmark、單一自動指標，或少量質性範例展示。對研究原型而言，這種做法或許足夠；但對產品型 AI 系統而言，仍然遠遠不足（Liang et al., 2023; Chiang and Lee, 2023a）。

自動化指標雖然有助於快速比較版本差異，卻無法完整反映使用者對回答品質的接受度。尤其在求職場景中，使用者關心的不只是回答是否流暢，而是回答是否正確、是否有足夠根據、是否真的有幫助，以及是否容易理解。因此，human review 仍然是必要的評估層（Chiang and Lee, 2023a; Liu et al., 2023）。

另一方面，LLM 系統若要進入產品環境，除了 correctness 之外，還必須同時觀察 latency、reliability、token usage、warm/cold path 差異與 regression stability。研究若只報回答品質而不報延遲與成本，將不足以支撐產品決策；若只報單次人評結果而沒有 validation、aggregation 與 reviewer agreement，也無法形成穩定的正式判讀（Liang et al., 2023; Zheng et al., 2023）。

近年有關 LLM evaluation 的研究已逐漸注意到這些問題，例如自動評估與人工評分的混合設計、LLM-as-a-judge 的限制、人評一致性檢查、case-level export 與 error analysis 等做法（Chiang and Lee, 2023a; Chiang and Lee, 2023b; Liu et al., 2023; Zheng et al., 2023）。

本研究在此脈絡中的主要貢獻，是把這些元件真正接成同一條流程。除了 fixture baseline、real snapshot eval 與 real model eval 之外，本研究還建立 latency regression、token / reliability budget、formal human review、manifest 與 case-level export，以及 training readiness gate，使系統的品質判讀不再是單次實驗輸出，而是一套可回歸、可追溯、可產品化的驗證機制。

## 2.4 本研究定位與差異

綜合前述三條研究脈絡，可以看出：RAG、履歷匹配與 LLM evaluation 各自都有成熟的研究基礎，但它們在求職產品場景中仍存在整合上的空缺。本研究的定位不是提出新的 foundation model，也不是單獨優化某一個 retrieval 演算法，而是將這些分散的方法與觀點整合為一套產品級 AI 系統。

相較於既有工作，本研究有以下幾個明確差異：

| 面向 | 既有研究常見做法 | 本研究做法 |
| --- | --- | --- |
| 知識來源 | 靜態語料或單一資料集 | 多來源職缺市場快照 |
| 問答模式 | 單一 generic QA | mode-aware 三種回答模式 |
| 履歷匹配 | 單點分類或推薦 | two-stage ranking + label eval |
| 引用控制 | 通用 citation 或無 citation | mode-specific / comparison-specific citation |
| 評估 | 單一 benchmark | fixture + real snapshot + real model + human review |
| 產品觀測 | 較少討論 | telemetry + token/latency/reliability budget |
| 訓練決策 | 直接調模型 | 先經 training readiness gate |

本研究的差異不在於提出新的大型模型，而在於將真實市場快照、mode-aware 問答、履歷匹配、產品 observability 與 formal human review 整合成一條可產品化、可回歸的 AI 系統主線。

## 2.5 本章結論

本章回顧了三條與本研究最相關的研究脈絡：RAG 與 evidence-grounded QA、履歷解析與職缺匹配，以及 LLM evaluation 與產品 observability。這些既有研究分別提供了重要方法基礎，但在求職產品情境下，仍缺乏將真實市場資料、模式化回答控制、履歷排序、正式人評與產品級回歸機制整合為單一系統主線的完整設計。

本研究因此選擇從系統工程與評估整合切入，而非直接將焦點放在模型訓練。後續章節將依序說明本研究的系統架構、評估設計與正式實驗結果，並展示這條整合式設計如何使求職 AI 系統在不進行 fine-tuning 的前提下，仍能達到產品可用性。

---

# Chapter 3 系統架構與方法

## 3.1 系統整體架構

本研究的主系統以 Streamlit 為前端入口，並將資料處理、AI 問答、履歷匹配、狀態保存與評估模組拆分為可獨立維護的子系統。整體上可分為以下層次：

1. `UI / orchestration layer`
2. `crawler / snapshot layer`
3. `assistant / resume intelligence layer`
4. `store / monitoring / evaluation layer`

![Figure 3-1. Overall Architecture of the Job-Market AI Assistance System](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/thesis_assets/figure_3_1_system_architecture.svg)

Figure 3-1. Overall Architecture of the Job-Market AI Assistance System.

UI 層負責啟動應用程式、管理 session state、搜尋流程與頁面切換。Crawler 與 snapshot 層由 `pipeline.py` 與多個 connector 組成，其核心輸出是一份 `MarketSnapshot`，作為 UI、assistant 與 resume matching 的共同市場資料。Assistant 與 resume intelligence 層分別負責市場問答、個人化建議、職缺比較、履歷抽取與職缺排序。最後，store、monitoring 與 evaluation 層提供 SQLite 狀態保存、AI telemetry、budget evaluator 與外部評估工作區。

## 3.2 職缺資料流與市場快照

本研究使用 `MarketSnapshot` 作為整個系統的核心資料交換物件。資料流並非單次同步阻塞流程，而是 staged crawl 設計。使用者在 UI 輸入目標職缺後，系統先建立搜尋 query，之後交由 `JobMarketPipeline` 執行各來源搜尋、dedupe、初步 relevance scoring、建立 partial snapshot、顯示初步職缺結果，再補 detail enrich 與 analysis，最後覆蓋為 final snapshot。這種 staged 設計使使用者不必等待完整分析才看到第一批結果，也使 assistant、resume matching 與 analytics 能共享同一份市場表示。

## 3.3 RAG 問答流程

本研究的 assistant 並非直接把原始職缺資料送給模型，而是透過 chunk、retrieval 與 mode-aware answer control 形成完整的 RAG pipeline。系統會建立多種 chunk 類型，例如：

- `job-summary`
- `job-salary`
- `job-skills`
- `job-work-content`
- `market-skill-insight`
- `market-task-insight`
- `market-source-summary`
- `market-role-summary`
- `market-location-summary`
- `resume-summary`

這些 chunk 帶有 source、role、location、salary、updated_at 與 query signature 等 metadata，使 retrieval 不只依賴 embedding 相似度，也能透過 type bonus、lexical signal 與 rerank 穩定選取證據。

系統將 assistant 回答拆為三種模式：

- `market_summary`
- `personalized_guidance`
- `job_comparison`

三種模式分別對應不同的 retrieval 策略、prompt 契約、citation selection 與 render path。這使求職場景中常見的市場總結、履歷缺口分析與職缺比較問題，都能有更穩定的回答結構與證據支撐。

## 3.4 履歷解析與職缺匹配流程

履歷輸入後，系統先建立 baseline profile，必要時再呼叫 LLM extractor。研究後期逐步補齊了 specialized role detection，例如 `RAG AI Engineer`、`LLM Engineer`、`Embedded Linux Firmware Engineer` 與 `Product Manager`。extractor 的輸出會被整理成 `ResumeProfile`，包含 target roles、extracted skills、summary 與 profile metadata。

在匹配層，本研究採用 two-stage ranking：

1. 粗篩：規則分數與基礎語義相似
2. 精排：只對前段候選做較昂貴的 LLM / semantic scoring

這種設計同時兼顧品質與延遲，使 resume matching 不再只是展示性功能，而能被正式當作 ranking pipeline 評估。

## 3.5 產品級監控與 Gate

本研究將 telemetry 與觀測納入系統設計。AI 路徑會記錄 event type、status、latency、model name、query signature 與 token usage，並計算 latency、reliability 與 token budget。外部評估工作區則負責 fixture baseline、real snapshot eval、real model eval、human review 與 AI regression。這使整個系統不只「能跑」，而且能被正式判讀與回歸。

## 3.6 本章結論

本章說明了本研究的系統架構與方法。核心在於以 `MarketSnapshot` 作為共同知識表示，整合 mode-aware RAG 問答、履歷解析與排序，以及產品級觀測與正式評估工作區，形成一條可產品化、可驗證的 AI 主線。

---

# Chapter 4 評估設計

## 4.1 評估目標

本研究的評估設計要回答以下問題：

1. 系統在固定資料與固定題集下是否具備穩定基本能力。
2. 系統在真實職缺快照下是否仍能維持正確 retrieval、citation 與回答品質。
3. 系統在真實模型條件下是否具備可接受延遲與排序品質。
4. 在目前資料規模與評估結果下，是否有必要進行 fine-tuning。

## 4.2 資料集與標註設計

本研究的主要評估資料集包括：

- `assistant_questions = 100`
- `resume_extraction_labels = 30`
- `resume_match_labels = 60`

這三組資料分別用於問答 regression、履歷抽取驗證與履歷匹配排序評估。現階段將它們定位為 evaluation datasets，而非 training datasets。

## 4.3 Offline Fixture Baseline

offline fixture baseline 使用固定 snapshot、固定 resume cases 與固定題集，主要用途是：

1. 驗證邏輯正確性
2. 作為 retrieval、prompt 與 ranking 調整時的第一層 regression
3. 提供 real snapshot 與 real model eval 的對照基礎

## 4.4 Real Snapshot Eval

real snapshot eval 直接使用真實 `jobs_latest.json` 作為輸入，先以 `snapshot health gate` 檢查資料是否具備足夠覆蓋率，再觀察 assistant、retrieval 與 resume 在真實市場資料條件下的行為。

## 4.5 Real Model Eval

real model eval 在真實模型設定下分別量測：

- assistant 三種 mode 的 structured output、citation keyword recall、evidence sufficiency 與 latency
- retrieval 的 evidence type 與延遲
- resume extraction / matching 的排序品質與總延遲

## 4.6 Resume Label Ranking Eval

本研究另外建立 `resume_label_eval`，將履歷匹配視為 ranking 問題，使用：

- `top1_best_label_hit_rate`
- `top3_relevant_recall_mean`
- `top3_reject_free_rate`
- `pairwise_order_accuracy_mean`
- `nDCG@3`

等指標做正式評估。

## 4.7 Latency、Budget 與 Product Telemetry

本研究在產品主路徑中加入 telemetry，記錄 latency、status、model name、query signature 與 token usage，並建立 latency、reliability 與 token budget。這使系統不只在研究環境中可評估，也能在產品運行過程中被持續觀測。

## 4.8 Formal Human Review

本研究使用 blind review packet 與正式 reviewer workflow，要求 reviewer 對每題回答填寫：

- `correctness_score`
- `grounding_score`
- `usefulness_score`
- `clarity_score`
- `overall_score`
- `verdict`
- `notes`

再由 aggregation 流程計算平均分數、verdict 分布、agreement 與 kappa。

## 4.9 Training Readiness Gate

本研究的最後一層不是直接訓練模型，而是建立 `training_readiness gate`，綜合 snapshot health、assistant quality、latency、resume ranking 與 human review，判斷是否有必要進入 fine-tuning。若品質與延遲已達標，但缺乏證據支持訓練收益，則維持 `DEFER`。

![Figure 4-1. Overview of the Evaluation Pipeline](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/thesis_assets/figure_4_1_evaluation_flow.svg)

Figure 4-1. Overview of the Evaluation Pipeline.

## 4.10 本章結論

本章建立了完整評估方法，形成從固定資料 regression、真實快照、真實模型、履歷排序、人評、產品觀測到 training gate 的多層驗證閉環。

---

# Chapter 5 實驗結果

## 5.1 主線總 Gate 結果

本研究將 AI 系統的正式判定分成五個 gate：

- snapshot health gate
- assistant mode gate
- human review gate
- latency regression
- training readiness

| Gate | Status | 說明 |
| --- | --- | --- |
| Snapshot health gate | `READY` | 真實快照覆蓋率足夠，可用於模型品質判讀 |
| Assistant mode gate | `PASS` | `market_summary`、`personalized_guidance`、`job_comparison` 三種模式皆達標 |
| Human review gate | `PASS` | 正式 reviewer 人評通過 |
| Latency regression | `PASS` | 核心延遲指標均在門檻內 |
| Training readiness | `DEFER` | 品質已達標，但目前沒有足夠證據支持 fine-tuning |

這組結果表示，本研究完成的系統已具備產品可用性與正式評估覆蓋，但現階段最佳策略仍是優先做產品整合與持續觀測，而不是立即進入模型訓練。

## 5.2 Snapshot Health 結果

| 指標 | 實際值 | 門檻 | 結果 |
| --- | ---: | ---: | --- |
| 角色數 | `1` | `>= 1` | PASS |
| 職缺數 | `34` | `>= 30` | PASS |
| 來源數 | `3` | `>= 3` | PASS |
| 薪資覆蓋率 | `0.3529` | `>= 0.1` | PASS |
| 工作內容覆蓋率 | `0.8824` | `>= 0.7` | PASS |
| 必備技能覆蓋率 | `0.7059` | `>= 0.6` | PASS |

這表示本研究用於最終判讀的真實快照，在資料量、來源數與欄位覆蓋率上已達到可評估門檻，因此後續 assistant、resume 與 human review 的結果具備解釋價值。

## 5.3 Assistant Mode-Aware Real-Model 結果

| Mode | Case Count | Avg Latency (ms) | Structured Output | Citation Keyword Recall | Evidence Sufficiency |
| --- | ---: | ---: | ---: | ---: | ---: |
| `market_summary` | `6` | `4739.479` | `1.0` | `1.0` | `1.0` |
| `personalized_guidance` | `1` | `4368.892` | `1.0` | `1.0` | `1.0` |
| `job_comparison` | `1` | `5262.343` | `1.0` | `1.0` | `1.0` |

從結果可見，三種模式都已具備完整結構化輸出能力，引用關鍵詞召回率皆為 `1.0`，evidence sufficiency 也皆為 `1.0`。這表示 mode routing、mode-specific prompt contract、comparison-specific citation selection 與 personalized guidance answer control 已有效穩定三種核心回答型態。

## 5.4 Resume Matching 結果

| 指標 | 數值 |
| --- | ---: |
| `top3_url_hit_rate` | `1.0` |
| `top1_role_match_rate` | `1.0` |
| `matched_skill_recall_mean` | `0.9688` |
| `build_profile_ms_mean` | `5227.174` |
| `match_jobs_ms_mean` | `4547.125` |
| `total_ms_mean` | `9774.299` |
| `resume_warm_build_profile_ms_mean` | `2.041` |

結果顯示，履歷匹配在 Top-3 命中率與角色對齊上表現穩定，技能對齊能力已接近完整覆蓋，且透過 two-stage ranking 與 extractor cache，warm path 的履歷建檔時間已壓到毫秒級。

## 5.5 Resume Label Ranking 結果

| 指標 | 數值 |
| --- | ---: |
| `top1_best_label_hit_rate` | `1.0` |
| `top3_relevant_recall_mean` | `0.8` |
| `top3_reject_free_rate` | `1.0` |
| `pairwise_order_accuracy_mean` | `0.9667` |
| `nDCG@3` | `0.8763` |

這代表最佳標籤職缺幾乎都能排在最前方，排序關係整體正確，雖然 Top-3 相關職缺召回尚未達到滿分，但已具備穩定排序表現。

## 5.6 Latency Regression 結果

| 指標 | 實際值 (ms) | 門檻 (ms) | 結果 |
| --- | ---: | ---: | --- |
| Assistant total latency | `4758.514` | `<= 8000` | PASS |
| Retrieval cold latency | `1476.403` | `<= 2000` | PASS |
| Retrieval warm latency | `165.345` | `<= 400` | PASS |
| Resume build_profile latency | `5227.174` | `<= 6000` | PASS |
| Resume match_jobs latency | `4547.125` | `<= 7000` | PASS |
| Resume total latency | `9774.299` | `<= 13000` | PASS |
| Resume warm build_profile latency | `2.041` | `<= 250` | PASS |

這表示 assistant 路徑已不再是不可接受的慢點，retrieval 冷啟動已壓到 `2s` 內，resume 路徑雖仍相對昂貴，但已進入可接受區間。

## 5.7 Formal Human Review 結果

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

verdict 分布：

| Verdict | Count |
| --- | ---: |
| `accept` | `16` |
| `minor_issue` | `0` |
| `major_issue` | `0` |
| `reject` | `0` |

這代表兩位 reviewer 對最終回答已沒有明顯保留意見，回答在 correctness、grounding、usefulness 與 clarity 上皆達高分，且經過 targeted re-check 後，原本 reviewer 分歧已被消除。

## 5.8 綜合討論

綜合上述結果，本研究得到三點結論：

1. 系統品質已達產品可用水準。
2. 問題主要透過系統工程而非訓練解決。
3. 現階段不建議直接進行 fine-tuning。

品質提升的關鍵因素包括 retrieval 設計、citation selection、answer mode control、ranking pipeline、telemetry 與 formal evaluation，而非模型訓練本身。

## 5.9 本章結論

本章證明，本研究所提出的 AI 主線系統在真實快照、真實模型與正式 reviewer 條件下，已同時滿足品質、引用充分性、模式覆蓋、排序品質、延遲門檻與人工評分一致性。最終結果為：

- `Snapshot health gate = READY`
- `Assistant mode gate = PASS`
- `Human review gate = PASS`
- `Latency regression = PASS`
- `Training readiness = DEFER`

這組結果支持本研究的核心論點：在求職場景中，透過 RAG、mode-aware answer control、resume ranking 與完整 evaluation / observability 設計，可以在不進行 fine-tuning 的前提下，建立一套產品級可用的 AI 輔助系統。

---

# Chapter 6 結論與未來工作

## 6.1 研究總結

本研究針對求職資訊分散、職缺內容不一致、履歷與市場需求難以對照等問題，建立了一套多來源職缺整合與 AI 輔助系統。該系統以真實市場快照為中心，向上支撐市場摘要型問答、個人化求職建議、職缺或角色比較與履歷解析與職缺匹配；同時，系統並非僅提供單次問答，而是進一步建立 external eval workspace、real snapshot eval、real model eval、latency / token / reliability budget、formal human review 與 training readiness gate。

## 6.2 研究結論

根據本研究最終正式結果，可得到以下結論：

1. 多來源職缺快照可作為求職 AI 的有效知識基礎。
2. Mode-aware 回答控制能提升求職場景下的可用性。
3. 履歷匹配可透過 two-stage ranking 兼顧品質與延遲。
4. 系統工程與評估閉環比立即進行 fine-tuning 更關鍵。

## 6.3 研究限制

本研究仍有以下限制：

1. 真實快照覆蓋仍受當次搜尋條件影響。
2. Human review 規模仍有限。
3. Training gate 尚未進入真正的訓練實驗階段。
4. 履歷資料規模仍以評估用途為主。

## 6.4 未來工作

未來工作可分成產品延伸與研究延伸兩條路線：

1. 持續收集真實產品 telemetry。
2. 擴大 human review 與 error analysis。
3. 擴大履歷標註資料並建立合規資料流程。
4. 在條件成熟時重新評估 training gate。
5. 將評估與產品發布流程進一步整合。

## 6.5 總結

本研究完成了一套面向求職場景的產品級 AI 系統，並以正式評估結果證明：

1. 多來源職缺市場快照可以作為有效的 AI 知識基礎。
2. Mode-aware RAG 問答能支撐市場摘要、個人化建議與職缺比較。
3. 履歷匹配可在不依賴 fine-tuning 的前提下，透過系統設計達到高品質與可接受延遲。
4. 產品級 observability、formal evaluation 與 human review 對 AI 系統的實際落地至關重要。

總體而言，本研究的貢獻不在於提出新的大型模型，而在於證明：透過合理的資料流設計、RAG 架構、answer mode 控制、排序方法與正式評估閉環，可以在求職場景中建立一套具有產品可用性的 AI 輔助系統。最終正式判定顯示，本研究的系統已達產品可用階段，而未來是否進入模型訓練，應建立在真實產品資料與更大規模標註資料的基礎上，而非僅因具備訓練資源就提前啟動。

---

# 參考文獻

1. Bian, S., Zhao, W. X., Song, Y., Zhang, T., and Wen, J.-R. 2019. Domain Adaptation for Person-Job Fit with Transferable Deep Global Match Network. In *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)*, pages 4692-4702. Association for Computational Linguistics. URL: https://aclanthology.org/D19-1487/
2. Chiang, C.-H., and Lee, H.-y. 2023a. Can Large Language Models Be an Alternative to Human Evaluations? In *Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 15607-15631. Association for Computational Linguistics. URL: https://aclanthology.org/2023.acl-long.870/
3. Chiang, C.-H., and Lee, H.-y. 2023b. A Closer Look into Using Large Language Models for Automatic Evaluation. In *Findings of the Association for Computational Linguistics: EMNLP 2023*, pages 8928-8942. Association for Computational Linguistics. URL: https://aclanthology.org/2023.findings-emnlp.599/
4. Gao, Y., Xiong, Y., Gao, X., Jia, K., Pan, J., Bi, Y., Dai, Y., Sun, J., Wang, M., and Wang, H. 2024. Retrieval-Augmented Generation for Large Language Models: A Survey. *arXiv preprint* arXiv:2312.10997. URL: https://arxiv.org/abs/2312.10997
5. Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Kuttler, H., Lewis, M., Yih, W.-t., Rocktaschel, T., Riedel, S., and Kiela, D. 2020. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. In *Advances in Neural Information Processing Systems 33 (NeurIPS 2020)*. URL: https://papers.nips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html
6. Liang, P., Bommasani, R., Lee, T., Tsipras, D., Soylu, D., Yasunaga, M., and many others. 2023. Holistic Evaluation of Language Models. *arXiv preprint* arXiv:2211.09110. URL: https://arxiv.org/abs/2211.09110
7. Ling, Z., Zhang, H., Cui, J., Wu, Z., Sun, X., Li, G., and He, X. 2025. Beyond Human Labels: A Multi-Linguistic Auto-Generated Benchmark for Evaluating Large Language Models on Resume Parsing. In *Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing*. Association for Computational Linguistics. URL: https://aclanthology.org/2025.emnlp-main.1626/
8. Liu, Y., Iter, D., Xu, Y., Wang, S., Xu, R., and Zhu, C. 2023. G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment. *arXiv preprint* arXiv:2303.16634. URL: https://arxiv.org/abs/2303.16634
9. Menick, J., Trebacz, M., Mikulik, V., Aslanides, J., Song, F., Chadwick, M., Glaese, M., Young, S., Campbell-Gillingham, L., Irving, G., and McAleese, N. 2022. Teaching Language Models to Support Answers with Verified Quotes. *arXiv preprint* arXiv:2203.11147. URL: https://arxiv.org/abs/2203.11147
10. Yu, X., Xu, R., Xue, C., Zhang, J., Ma, X., and Yu, Z. 2025. ConFit v2: Improving Resume-Job Matching using Hypothetical Resume Embedding and Runner-Up Hard-Negative Mining. In *Findings of the Association for Computational Linguistics: ACL 2025*. Association for Computational Linguistics. URL: https://aclanthology.org/2025.findings-acl.661/
11. Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E. P., Zhang, H., Gonzalez, J. E., and Stoica, I. 2023. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. *arXiv preprint* arXiv:2306.05685. URL: https://arxiv.org/abs/2306.05685

---

# Appendix

建議可放入：

1. Human review rubric
2. Formal human review workflow 摘要
3. 額外 case 範例
4. 補充表格或補充圖

候選來源：

- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/human_review_rubric.md](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/human_review_rubric.md)
- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/formal_human_review_workflow.md](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/formal_human_review_workflow.md)
