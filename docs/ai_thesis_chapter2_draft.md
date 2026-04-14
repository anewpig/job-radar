# Chapter 2 相關研究初稿

本章回顧與本研究有關的主要研究脈絡，並說明本研究在這些脈絡中的定位。由於本研究聚焦於求職場景中的產品級 AI 系統，因此相關研究不應只限於單一模型技術，而必須同時涵蓋檢索增強生成、履歷解析與職缺匹配、LLM 評估方法，以及產品化部署所需的 observability 與人工評分流程。透過本章的整理，可以更清楚說明：本研究並非單純將大型語言模型套用到求職資料上，而是將多種既有研究方向整合為一套可產品化、可驗證的系統工程主線。

---

## 2.1 RAG 與 Evidence-Grounded Question Answering

大型語言模型具備強大的自然語言理解與生成能力，但其知識來自訓練資料與模型參數，無法自然反映特定時間點的最新資訊，也難以保證每一段回答都能被具體證據支撐。對求職場景而言，這個限制特別明顯，因為職缺需求、薪資揭露與工作內容屬於高度時效性與來源依賴的資訊。若系統僅依賴通用模型直接回答，容易發生三種問題：第一，回答與真實市場脫節；第二，缺乏可驗證依據；第三，無法區分不同資料來源的差異（Liang et al., 2023; Menick et al., 2022）。

檢索增強生成（Retrieval-Augmented Generation, RAG）的基本概念，是先從外部知識來源中找出與問題最相關的內容，再將該內容作為模型生成回答的上下文。這使得模型不必完全依賴自身參數中的靜態知識，而可以以真實資料支撐回應。因此，RAG 在需要引用外部資料、重視資訊時效性、或要求答案可追溯的場景中，特別具有價值（Lewis et al., 2020; Gao et al., 2024）。

然而，通用 RAG pipeline 並不直接等同於可靠的 evidence-grounded QA。單純把檢索到的文件片段送進模型，仍可能出現回答過度概括、引用與結論不一致，或 retrieval 雖然命中但沒有真正支撐最終答案的情況。因此，evidence-grounded QA 的研究重點不只在檢索本身，也包括模型是否能依據證據回答，以及引用內容是否能被驗證（Menick et al., 2022; Gao et al., 2024）：

- retrieval 是否命中正確證據類型
- 模型回答是否被所提供的證據充分支撐
- 引用內容是否能被人工檢查與驗證

這些問題與一般 open-domain QA 不同。對求職場景而言，使用者常問的不只是單點事實，而是聚合性問題與決策性問題，例如：

- 市場最常見的技能是什麼
- 哪些工作內容最常出現
- 某個角色與另一個角色的差異是什麼
- 自己的履歷和市場要求相比還缺什麼

這些問題往往需要同時整合多筆職缺資料，而不是對單一文件做抽取式回答。因此，本研究認為求職場景中的 RAG 問題，本質上更接近「基於市場快照的證據整合與決策型問答」，而不是單純的文本檢索與生成（Lewis et al., 2020; Menick et al., 2022）。

在此脈絡下，既有 RAG 與 evidence-grounded QA 研究提供了重要啟發，但仍有三個不足。第一，多數研究假設知識來源較穩定，較少面對多來源職缺資料在欄位缺漏、內容密度與格式上的高度異質性。第二，通用 RAG 往往採單一路徑回答設計，較少根據問題類型動態調整 retrieval 與回答格式。第三，許多研究以自動指標為主，較少將 citation selection、人工評分與產品級行為觀測整合為一套完整驗證流程。

因此，本研究承接 RAG 與 evidence-grounded QA 的核心觀念，但將其延伸到求職產品情境中，進一步處理：

- 多來源職缺市場快照
- mode-aware retrieval 與 answer control
- comparison-specific 與 personalized citation selection
- 正式 human review 與 product telemetry

這也是本研究與一般 RAG 系統應用工作的主要差異之一。

---

## 2.2 Resume Parsing 與 Job Matching

求職場景中的第二條重要研究脈絡，是履歷解析與職缺匹配。與一般問答不同，履歷匹配的核心問題在於：如何從非結構化履歷中抽取可比較的資訊，並將其轉換為對職缺排序或推薦決策有意義的表示。

履歷解析（resume parsing）傳統上可被視為資訊抽取問題，常見任務包括：

- 角色或職稱辨識
- 技能抽取
- 學經歷整理
- 年資與領域標記

在較早期的方法中，這些任務多以規則、詞典或命名實體辨識為主；在大型語言模型出現後，履歷抽取逐漸轉向以 schema-based extraction 或 structured generation 的方式進行。然而，即使模型能從履歷中抽出若干技能與職稱，也不表示系統已經具備足夠的職缺匹配能力。原因在於求職匹配不是單純的欄位對欄位比對，而涉及技能別名、角色語義與經驗層次的對齊（Ling et al., 2025; Bian et al., 2019）：

- 技能名稱與別名的對齊
- 角色語義的對齊
- 市場需求與個人經驗的差異判讀
- 多筆職缺之間的排序

因此，履歷匹配更適合被視為 ranking 問題，而非單純二元分類。對求職者而言，系統的價值通常不是判斷某份履歷「能不能」投某一份工作，而是提供一組合理排序的候選職缺，並進一步說明（Bian et al., 2019; Yu et al., 2025）：

- 為什麼這些職缺較適合
- 自己已具備哪些能力
- 還缺哪些能力
- 哪些缺口值得優先補強

既有履歷與職缺匹配研究，已經提供了若干重要基礎。首先，skill normalization 與 role representation 的研究使我們理解，匹配問題的核心不在表面關鍵字重合，而在語義層次與結構層次的對齊。其次，推薦系統與 ranking 研究提供了排序品質評估方法，例如 Top-k 命中率、pairwise ordering 與 nDCG。第三，近年的 LLM 應用研究也顯示，大型語言模型可作為履歷理解、技能萃取與匹配說明的工具（Bian et al., 2019; Yu et al., 2025; Ling et al., 2025）。

然而，這些研究在求職產品場景下仍有幾個缺口。第一，不少研究把 matching 問題視為離線資料集上的分類任務，較少處理真實職缺快照中資料欄位不完整、來源不一致與市場變動的情況。第二，許多研究重點在模型分數，而不是產品要求，例如延遲、token 成本與是否能支援實際使用者互動。第三，履歷匹配往往與問答系統分開處理，較少與個人化建議、比較型回答與產品級 telemetry 一起設計。

本研究在此脈絡中的切入點，是將履歷匹配納入同一個 AI 系統主線，而不是把它當成獨立展示功能。具體而言，本研究將履歷路徑拆成：

- resume extraction
- profile normalization
- two-stage ranking
- gap-oriented explanation

並用 `resume_extraction_labels`、`resume_match_labels` 與 `resume_label_eval` 正式衡量其品質。也就是說，本研究承接既有履歷解析與匹配研究的問題意識，但強調其必須與真實市場快照、個人化問答與產品監控一同被設計與驗證。

---

## 2.3 LLM Evaluation、Human Review 與 Observability

大型語言模型相關研究的一個常見問題是：系統評估往往停留在單次 benchmark、單一自動指標，或少量質性範例展示。對研究原型而言，這種做法或許足夠；但對產品型 AI 系統而言，這仍然遠遠不足。

首先，自動化指標雖然有助於快速比較版本差異，卻無法完整反映使用者對回答品質的接受度。尤其在求職場景中，使用者關心的不只是回答是否語意流暢，而是：

- 回答是否正確
- 是否有足夠根據
- 是否真的有幫助
- 是否容易理解

這些面向很難只靠單一文字相似度或分類分數完整表示，因此 human review 仍然是必要的評估層（Chiang and Lee, 2023a; Liu et al., 2023）。

其次，LLM 系統若要進入產品環境，除了 correctness 之外，還必須同時觀察：

- latency
- reliability
- token usage
- warm/cold path 差異
- regression stability

換句話說，研究若只報回答品質而不報延遲與成本，將不足以支撐產品決策。同理，若只報單次人評結果而沒有 validation、aggregation 與 reviewer agreement，也無法形成穩定的正式判讀（Liang et al., 2023; Zheng et al., 2023）。

近年有關 LLM evaluation 的研究已逐漸注意到這些問題。例如，自動評估與人工評分的混合設計、LLM-as-a-judge 的限制、人評一致性檢查、case-level export 與 error analysis 等做法，都是試圖讓 LLM 評估更具可重複性與可解釋性（Chiang and Lee, 2023a; Chiang and Lee, 2023b; Liu et al., 2023; Zheng et al., 2023）。同時，隨著 LLM 系統進入產品部署，observability 也成為重要議題，包括：

- 如何追蹤模型輸入輸出與 token 使用
- 如何監測延遲與錯誤率
- 如何建立 regression gate 與 release gate

然而，既有研究在這方面仍有兩個常見斷裂。第一，學術型評估常缺乏產品運行所需的 telemetry 與 budget 管理。第二，產品實作常有觀測，但沒有和正式研究式評估、人評流程與 case-level 結果做一致性整合。

本研究在此脈絡中的主要貢獻，是把這些元件真正接成同一條流程。具體而言，本研究不只做：

- fixture baseline
- real snapshot eval
- real model eval

還進一步建立：

- latency regression
- token / reliability budget
- formal human review
- manifest 與 case-level export
- training readiness gate

這使系統的品質判讀不再是單次實驗輸出，而是一套可回歸、可追溯、可產品化的驗證機制。從研究方法的角度來看，這也是本研究相對於單一模型評測或單點 RAG 應用工作的關鍵差異。

---

## 2.4 本研究定位與差異

綜合前述三條研究脈絡，可以看出：RAG、履歷匹配與 LLM evaluation 各自都有成熟的研究基礎，但它們在求職產品場景中仍存在整合上的空缺。本研究的定位不是提出新的 foundation model，也不是單獨優化某一個 retrieval 演算法，而是將這些分散的方法與觀點整合為一套產品級 AI 系統。

相較於既有工作，本研究有以下幾個明確差異。

第一，本研究的知識基礎不是單一靜態語料，而是多來源職缺市場快照。這使系統能直接面對來源異質性、欄位缺漏與真實市場波動，而不是只在乾淨的研究資料集上操作。

第二，本研究將問答任務拆成三種模式：

- `market_summary`
- `personalized_guidance`
- `job_comparison`

這種設計承認不同問題類型對 retrieval、prompt 與 evidence 的要求不同，也使系統能針對求職場景中的常見任務做更穩定的回答控制。

第三，本研究將履歷匹配正式視為排序問題，並透過 label-based ranking eval 量測 Top-k 與 ordering quality，而不是僅以單一匹配分數展示結果。這使履歷路徑能和問答路徑一樣，被納入正式評估與回歸。

第四，本研究將產品 observability 視為研究設計的一部分，而非部署後附加的工程工作。透過 telemetry、latency budget、token budget、formal human review 與 training readiness gate，本研究建立了一套從系統輸出到研究判讀的完整閉環。

第五，本研究的最終結論並不是「模型需要立刻訓練」，而是證明在求職場景中，系統工程與評估閉環本身就足以讓系統達到產品可用狀態。這個結論與許多以 fine-tuning 為主要優化方向的工作不同，也反映出本研究對產品實作成本與研究可追溯性的重視。

因此，本研究的定位可以概括如下：

> 本研究不是提出新的大型模型，而是提出一套面向求職場景的產品級 AI 系統設計與驗證方法，整合真實市場快照、mode-aware 問答、履歷匹配、產品 observability 與 formal human review，並以正式 gate 判斷系統是否達到產品可用性。

---

## 2.5 本章結論

本章回顧了三條與本研究最相關的研究脈絡：RAG 與 evidence-grounded QA、履歷解析與職缺匹配、以及 LLM evaluation 與產品 observability。這些既有研究分別提供了重要方法基礎，但在求職產品情境下，仍缺乏將真實市場資料、模式化回答控制、履歷排序、正式人評與產品級回歸機制整合為單一系統主線的完整設計。

本研究因此選擇從系統工程與評估整合切入，而非直接將焦點放在模型訓練。後續章節將依序說明本研究的系統架構、評估設計與正式實驗結果，並展示這條整合式設計如何使求職 AI 系統在不進行 fine-tuning 的前提下，仍能達到產品可用性。
