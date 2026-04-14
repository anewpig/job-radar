# Chapter 3 系統架構與方法初稿

本章說明本研究所實作之求職輔助系統架構與方法。系統目標不是單純提供聊天問答，而是建立一個以真實職缺市場快照為基礎，整合 RAG 問答、履歷解析、職缺匹配、監控與評估流程的產品級 AI 系統。

本系統主要由四個層次組成：

- 多來源職缺資料擷取與快照建立
- RAG 問答與 mode-aware 回答控制
- 履歷解析與職缺匹配
- 產品級 observability 與外部評估框架

對應的整體架構文件如下：

- [系統架構](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/architecture.md)
- [產品化與求職定位評估](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/product_readiness_and_system_flow.md)

---

## 3.1 系統整體架構

本研究的主系統以 Streamlit 為前端入口，並將資料處理、AI 問答、履歷匹配、狀態保存與評估模組拆分為可獨立維護的子系統。

整體上可分為以下層次：

1. `UI / orchestration layer`
2. `crawler / snapshot layer`
3. `assistant / resume intelligence layer`
4. `store / monitoring / evaluation layer`

### 3.1.1 UI 與 orchestration layer

系統以 `app.py` 作為主入口，但實際邏輯已拆至多個 UI runtime 模組，例如：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/bootstrap.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/router.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/crawl_runtime.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/pages_resume_assistant.py`

此層的責任包括：

- 啟動應用程式與 service / store
- 管理 session state
- 管理搜尋流程與頁面切換
- 顯示職缺總覽、AI 助理、履歷匹配與產品頁面

### 3.1.2 Crawler 與 snapshot layer

多來源職缺資料由 `pipeline.py` 與各 connector 共同完成。其核心輸出是一份 `MarketSnapshot`，作為 UI、assistant 與 resume matching 的共用市場資料。

核心模組包括：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/pipeline.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/connectors/site_104.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/connectors/site_1111.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/connectors/cake.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/connectors/linkedin.py`

### 3.1.3 Assistant 與 resume intelligence layer

AI 能力集中在兩條主線：

- `assistant`
- `resume`

前者負責市場問答、個人化建議與職缺比較；後者負責履歷抽取、履歷 profile 建立與職缺排序。

核心模組包括：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/`

### 3.1.4 Store、monitoring 與 evaluation layer

為了支撐產品運行與研究驗證，本系統同時包含：

- 本地 product store / SQLite
- AI telemetry 與 budget evaluator
- 外部 eval workspace

對應模組包括：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/store/database.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/store/metrics.py`
- `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval`

---

## 3.2 職缺資料流與市場快照

本研究使用 `MarketSnapshot` 作為整個系統的核心資料交換物件。資料流並非單次同步阻塞流程，而是 staged crawl 設計。

### 3.2.1 搜尋與快照建立流程

使用者在 UI 輸入目標職缺後，系統先建立搜尋 query，之後交由 `JobMarketPipeline` 執行：

1. 各來源搜尋頁抓取
2. dedupe
3. 初步 relevance scoring
4. 建立 partial snapshot
5. 顯示初步職缺結果
6. 補 detail enrich 與 analysis
7. 覆蓋為 final snapshot

這種 staged 設計的好處有三點：

1. 使用者不需要等待完整分析才看到第一批結果。
2. detail enrich 與統計分析不會阻塞 overview。
3. assistant、resume matching 與 analytics 能共享同一份最終快照。

### 3.2.2 Snapshot 的角色

`MarketSnapshot` 在本研究中扮演三個角色：

1. UI 顯示層的資料來源
2. assistant 的知識來源
3. resume matching 的市場對照基礎

因此 snapshot 不只是抓取結果保存，而是產品內部的統一市場表示。

---

## 3.3 RAG 問答流程

本研究的 assistant 並非直接把原始職缺資料送給模型，而是透過 chunk、retrieval 與 mode-aware answer control 形成完整的 RAG pipeline。

### 3.3.1 Chunk 建立

系統會根據 snapshot 與可用的 resume profile，建立多種 chunk 類型，例如：

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

對應模組：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/chunks.py`

這些 chunk 皆帶有 metadata，例如：

- source
- role
- location
- salary
- updated_at
- query signature

其目的是讓 retrieval 不只依賴向量相似度，也能透過 metadata 做更穩定的 rerank 與 citation selection。

### 3.3.2 Retrieval

本研究初期使用單純 embedding retrieval，後續升級為 hybrid retrieval 與 heuristic rerank。其主要原因是聚合型問題、比較型問題與個人化問題對證據類型的要求並不相同。

目前 retrieval 具備以下特性：

1. lexical / signal / type bonus
2. aggregate retrieval diversification
3. comparison-specific retrieval diversification
4. market chunk priority rerank

例如：

- 問技能時，系統會優先保留 `market-skill-insight + job-skills`
- 問工作內容時，系統會優先保留 `market-task-insight + job-work-content`
- 問比較問題時，系統會強制補齊兩個比較對象的證據

對應模組：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/retrieval.py`

### 3.3.3 多輪上下文

為了支援追問，本研究將最近幾輪 `assistant_history` 接入 retrieval query 與 answer prompt。這使得像「那薪資呢？」、「台北的呢？」這類問題不會被視為完全無上下文的新 query。

### 3.3.4 Answer mode routing

本研究將 assistant 回答拆成三種 mode：

- `market_summary`
- `personalized_guidance`
- `job_comparison`

這個設計的原因是三種任務型態對 retrieval、prompt 與答案格式的要求不同。

1. `market_summary`
   - 著重市場分布、技能、工作內容、薪資趨勢
2. `personalized_guidance`
   - 著重履歷缺口、補強優先順序與投遞建議
3. `job_comparison`
   - 著重兩類角色或職缺的差異、適合對象與選擇建議

### 3.3.5 Structured output 與 rendering

為了避免自由文本造成不穩定輸出，本研究要求 assistant 產生結構化回應。最終 `AssistantResponse` 中可包含：

- `summary`
- `key_points`
- `limitations`
- `next_step`
- `market_sections`
- `guidance_sections`
- `comparison_sections`

前端則依 `answer_mode` 走不同的 render path，例如：

- `market_summary` 顯示市場摘要段落
- `personalized_guidance` 顯示市場需求、目前缺口、優先補強、投遞建議
- `job_comparison` 顯示比較結論、差異段落與下一步

對應模組：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/service.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/prompts.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/renderers.py`

---

## 3.4 履歷解析與職缺匹配流程

本研究的履歷能力並非只做摘要，而是建立一條獨立的 resume-to-jobs ranking pipeline。

### 3.4.1 Resume extraction

履歷輸入後，系統先建立 baseline profile，必要時再呼叫 LLM extractor。為提升實用性，本研究逐步補齊了 specialized role detection，例如：

- `RAG AI Engineer`
- `LLM Engineer`
- `Embedded Linux Firmware Engineer`
- `韌體工程師`
- `Product Manager`

### 3.4.2 Profile normalization

extractor 的輸出會被整理成 `ResumeProfile`，其中包含：

- target roles
- extracted skills
- summary
- profile metadata

這份 profile 可被儲存，也可作為 assistant 個人化建議的條件輸入。

### 3.4.3 Two-stage ranking

職缺匹配在本研究後期改為 two-stage ranking：

1. 粗篩：
   - 規則分數
   - 基礎語義相似
2. 精排：
   - 只對前段候選做較昂貴的 LLM / semantic scoring

這樣的設計可以同時兼顧：

- Top-k 排序品質
- latency

### 3.4.4 Skill recall 與 role alignment

為了避免匹配只看職稱，本研究額外追蹤：

- `matched_skill_recall`
- `missing_skill_recall`
- `top1_role_match_rate`
- `top3_url_hit_rate`

因此匹配的判斷不只看「有沒有排到對的職缺」，也看：

- 技能重疊是否合理
- 缺口是否被正確指出
- 角色對齊是否穩定

對應模組：

- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/extractors.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/matchers.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/scoring.py`
- `/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/service.py`

---

## 3.5 產品級 observability 與 gate

本研究的重要特點之一，是不將 AI 功能視為黑盒，而是對其建立產品級觀測與 gate。

### 3.5.1 Telemetry

系統在產品路徑中記錄：

- event type
- status
- latency
- model name
- query signature
- token usage
- citation count
- used chunks
- matches count

這些資料會寫入 product state database 中的 `ai_monitoring_events`。

### 3.5.2 Budget evaluator

在 telemetry 基礎上，本研究建立三類 budget：

- latency budget
- reliability budget
- token budget

這使得系統不只可以做離線評估，也可以在產品中持續觀察：

- 是否變慢
- 是否出錯
- token 成本是否異常

### 3.5.3 External eval workspace

為了避免將研究評估與產品主程式混在一起，本研究將評估框架獨立於外部工作區：

- `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval`

其中包含：

- fixture baseline
- real snapshot eval
- real model eval
- resume label eval
- human review
- latency regression
- training readiness
- AI regression

### 3.5.4 Formal gate

最終系統以五個 gate 作為正式判定：

- snapshot health gate
- assistant mode gate
- human review gate
- latency regression
- training readiness

這種做法的目的，是讓系統的每次改動都能被正式判讀，而不是憑主觀感覺認定「模型變好」。

---

## 3.6 本章結論

本章說明，本研究的核心不只是引入 LLM，而是將：

- 真實市場資料
- RAG 檢索
- mode-aware 問答控制
- 履歷解析與匹配
- telemetry
- regression gate

整合成一套可運作、可量測、可比較的求職 AI 系統。

相較於單純聊天式問答，本研究更強調：

1. 使用真實市場快照作為知識基礎。
2. 將問答任務拆為多種 answer mode。
3. 將履歷匹配獨立為 ranking 問題。
4. 以 observability 與 gate 作為產品化與研究驗證的核心支撐。

因此，本研究的方法論主張並非「訓練一個更大的模型」，而是透過系統工程與評估設計，把求職輔助 AI 做成可正式驗證的產品級能力。
