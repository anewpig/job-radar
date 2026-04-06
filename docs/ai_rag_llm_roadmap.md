# AI / RAG / LLM 技術地圖

這份文件是針對目前專案的 AI 能力所做的技術路線圖。目標不是先「訓練模型」，而是先把整個系統做成可量測、可調整、可迭代的架構。

適用範圍：

- AI 助理問答
- 市場摘要 / 求職報告
- 履歷擷取
- 履歷匹配
- 未來的 RAG / reranker / fine-tuning

不包含：

- 爬蟲本體效能優化
- OAuth / 產品帳號系統
- 前端視覺設計

---

## 1. 先講結論

你這個產品現在**不應該先做 fine-tuning**。

正確順序是：

1. 建立評估集與量測框架
2. 重做 chunk 與 retrieval
3. 補 hybrid retrieval 與 reranking
4. 把 LLM 輸出 schema 化
5. 把履歷匹配做成穩定可比較的 ranking pipeline
6. 最後才評估要不要做 training / fine-tuning

如果沒有前面 1 到 5，直接訓練只會讓你得到一個「看起來有變，但無法證明更好」的系統。

---

## 2. 目前系統現況

### 2.1 AI 助理

主要模組：

- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/service.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/service.py)
- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/chunks.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/chunks.py)
- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/retrieval.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/retrieval.py)
- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/prompts.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/prompts.py)

目前流程：

1. `build_chunks(snapshot, resume_profile)`
2. `EmbeddingRetriever.retrieve(question, chunks, top_k)`
3. `build_answer_prompt(...)`
4. `client.responses.create(...)`

目前限制：

- 每次提問都重新 build chunks
- retrieval 只有 embedding + cosine similarity
- 沒有 reranking
- 沒有 query classification
- 沒有 structured output schema
- 沒有完整 offline eval gating

### 2.2 履歷分析與匹配

主要模組：

- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/service.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/service.py)
- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/extractors.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/extractors.py)
- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/matchers.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/matchers.py)
- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/scoring.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/scoring.py)

目前流程：

1. 規則式 extractor 建 baseline profile
2. 若有 OpenAI，再走 LLM extractor
3. 匹配時優先走 AI matcher，失敗 fallback 到規則 matcher

目前限制：

- skill normalization 還不夠系統化
- 缺口分析仍偏 heuristic
- 沒有完整 ranking eval set
- 沒有 resume parsing gold labels

### 2.3 評估框架

外部 eval 工作區：

- `/Users/zhuangcaizhen/Desktop/專案/job-radar-eval`

這是正確方向。原因是：

- 評估和產品主程式解耦
- 可以版本化 baseline
- 方便做論文報告

但目前還要補：

- 更完整的題集
- 履歷擷取標註集
- 履歷匹配排序標註集
- AI 助理 answer quality rubric

---

## 3. 你真正要解的四類 AI 任務

不要把整個 AI 混成一件事。你要把它拆成四條 pipeline。

### A. RAG 問答

範例：

- 哪些技能最值得先學
- 某職缺的工作內容重點
- 某角色的薪資區間
- 履歷缺口是什麼

成功指標：

- citation 命中正確
- 回答切題
- 沒有 hallucination
- 回答有可執行建議

### B. 求職報告生成

範例：

- 產生市場摘要
- 產生履歷對市場的落差分析

成功指標：

- 報告內容完整
- 不重複
- 結構穩定
- 能引用市場證據

### C. 履歷擷取

範例：

- 從履歷抽出目標角色、核心技能、經驗、地點

成功指標：

- schema 欄位正確率
- 關鍵技能召回率
- 年資與角色判讀正確率

### D. 履歷匹配

範例：

- 履歷對多個職缺排序
- 缺口與適配理由解釋

成功指標：

- Top-1 / Top-3 排序品質
- gap explanation 合理性
- skill overlap 與 title match 的平衡

---

## 4. 核心原則

### 4.1 先做 evaluation，再做 optimization

沒有評估集，任何「變快」或「變準」都不可證明。

### 4.2 先做 retrieval，再做 generation

RAG 系統的第一性原理是：

- 先找到對的證據
- 再用 LLM 做整理與表達

### 4.3 不要太早 fine-tune

只要 chunk、metadata、retrieval、reranking、prompt 還沒穩，fine-tuning 幾乎都不是最划算的投資。

### 4.4 任務分開優化

問答、報告、履歷擷取、履歷匹配要各自評估、各自優化，不要混成同一個分數。

---

## 5. 技術路線圖

## Phase 0：建立 baseline 與觀測能力

目標：

- 知道現在系統到底快不快、準不準

交付物：

- assistant baseline metrics
- retrieval baseline metrics
- resume baseline metrics
- 每次實驗可比對的報表格式

要做的事：

- 擴充外部 eval repo 題集
- 固定測試案例
- 固定輸出 summary
- 保存 baseline artifacts

完成標準：

- 每次改 prompt / retrieval / matcher 都能跑出前後對照

## Phase 1：資料與標註準備

目標：

- 建立後面優化會用到的黃金資料集

要準備三類資料：

### 1. RAG 問題集

建議至少 100 題，分類如下：

- 技能
- 工作內容
- 薪資
- 缺口分析
- 推薦職缺
- 市場摘要

每題要有：

- `question`
- `expected_topics`
- `expected_citations`
- `must_include`
- `must_not_include`

### 2. 履歷擷取標註集

建議至少 100~300 份履歷。

每份要標：

- `target_roles`
- `core_skills`
- `years_of_experience`
- `preferred_locations`
- `summary`

### 3. 履歷匹配標註集

建議至少 300~1000 組 pair 或 ranking case。

每組要標：

- `resume_id`
- `job_id`
- `fit_label`
- `fit_reason`
- 或 `top_k expected ranking`

完成標準：

- 至少能支撐 retrieval / resume / report 三條線的回歸測試

## Phase 2：重做 chunk 與 metadata

目標：

- 讓 retrieval 的輸入品質更穩定

你現在的 chunk 還可以更細化。

建議 chunk 類型：

- `job-summary`
- `job-skills`
- `job-work-content`
- `job-salary`
- `market-skill-insight`
- `market-task-insight`
- `resume-summary`

每個 chunk 應補 metadata：

- `source`
- `url`
- `matched_role`
- `location`
- `salary`
- `source_type`
- `updated_at`
- `query_signature`

要改的檔案：

- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/chunks.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/chunks.py)
- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/models.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/models.py)

完成標準：

- 相同問題能穩定召回更像人的證據集合

## Phase 3：retrieval 升級成 hybrid + rerank

目標：

- 不只 embedding 相似，而是更像實際搜尋

你現在的 [retrieval.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/retrieval.py) 只有 embedding 檢索。

建議升級為：

1. `embedding recall`
2. `keyword / lexical recall`
3. `merge candidates`
4. `rerank`

第一版 rerank 不一定要模型，可以先做 rule-based：

- keyword overlap boost
- matched_role boost
- salary keyword boost
- source diversity penalty
- duplicate penalty

完成標準：

- retrieval eval 的 `top1 / recall@k / mrr` 穩定上升

## Phase 4：生成層 schema 化

目標：

- 回答穩定、可驗證、可做 UI 展示

目前 `assistant/service.py` 是自由文本輸出。建議改成 schema output：

- `summary`
- `evidence`
- `recommendations`
- `citations`

報告也做 schema：

- `market_snapshot`
- `skill_gaps`
- `salary_range`
- `recommended_actions`

要改的檔案：

- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/service.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/service.py)
- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/prompts.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/assistant/prompts.py)
- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/models.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/models.py)

完成標準：

- 回答格式穩定
- citation 可被自動驗證
- UI 可直接消費結構化欄位

## Phase 5：履歷 pipeline 強化

目標：

- 讓履歷擷取與匹配變成獨立且可量測的 AI 子系統

優先順序：

1. skill normalization
2. coarse filtering
3. ranking / rerank
4. gap explanation quality

要改的檔案：

- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/extractors.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/extractors.py)
- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/matchers.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/matchers.py)
- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/scoring.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/scoring.py)
- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/service.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/service.py)

完成標準：

- Top-1 / Top-3 排名更穩
- gap explanation 不再只是列關鍵字

## Phase 6：決定是否訓練 / fine-tune

只有在下面條件都成立時，才考慮訓練：

- 評估集已穩定
- retrieval 已做到可接受水準
- prompt 與 schema 已成熟
- 錯誤類型是固定且可被 supervision 修正的
- 你有足夠高品質標註資料

建議門檻：

- 問答 / 報告：200~500 組高品質 supervision
- 履歷擷取：100~300 份 schema-labeled resume
- 履歷匹配：500+ ranking / pairwise labels

在這之前，不建議花精力在 fine-tuning。

---

## 6. 你要準備哪些資料

## A. 問題集

檔案建議格式：

```json
{
  "id": "qa_001",
  "category": "skill_gap",
  "question": "目前最值得優先補強的技能是什麼？",
  "expected_topics": ["Python", "LLM", "RAG"],
  "expected_citations": ["job-summary-12", "market-skill-2"],
  "must_include": ["市場", "技能"],
  "must_not_include": ["無法判斷"]
}
```

## B. 履歷標註

檔案建議格式：

```json
{
  "resume_id": "resume_001",
  "target_roles": ["AI工程師", "AI應用工程師"],
  "core_skills": ["Python", "LLM", "RAG", "Docker"],
  "years_of_experience": "1-3 年",
  "preferred_locations": ["台北市"],
  "summary": "..."
}
```

## C. 履歷匹配標註

檔案建議格式：

```json
{
  "case_id": "match_001",
  "resume_id": "resume_001",
  "job_id": "job_104_123",
  "fit_label": "high",
  "fit_reason": ["skill_overlap", "matched_role", "location_fit"]
}
```

---

## 7. 每一階段的成功指標

### RAG 問答

- `top1_hit_rate`
- `recall_at_k`
- `mrr`
- `citation_hit_rate`
- `answer_completeness`
- `hallucination_rate`
- latency: `retrieve_ms / llm_ms / total_ms`

### 履歷擷取

- role extraction accuracy
- skill recall / precision
- years extraction accuracy
- location extraction accuracy

### 履歷匹配

- `Top1 accuracy`
- `Top3 accuracy`
- `NDCG / MRR`
- gap explanation agreement

### 報告生成

- section completeness
- factual consistency
- citation coverage

---

## 8. 你接下來的執行順序

這是實際操作順序，不是理想論。

### Step 1

擴充外部 eval repo 的資料規格，先把問題集、履歷標註集、匹配標註集定義好。

### Step 2

把 assistant chunks 做 schema 與 metadata 重構。

### Step 3

把 retrieval 做成 hybrid recall + rerank。

### Step 4

把 AI 助理與報告輸出改成 structured output。

### Step 5

把 resume matching 做成可量測的 ranking pipeline。

### Step 6

只有當前面都穩，才做 training / fine-tuning。

---

## 9. 我接下來會怎麼帶你做

我們不要一次同時改很多東西。接下來按這個節奏：

### 第一步

先把 `評估資料規格` 固定下來。

你要先產出：

- assistant question spec
- resume extraction label spec
- resume matching label spec

### 第二步

我再帶你建立：

- sample fixtures
- baseline rubric
- 第一版標註格式

### 第三步

才開始改程式：

- `assistant/chunks.py`
- `assistant/retrieval.py`
- `resume/matchers.py`

---

## 10. 這一階段不要做的事

- 不要先 fine-tune
- 不要先換很多模型
- 不要先追求超長 prompt
- 不要在沒有 eval set 的情況下憑感覺改 retrieval
- 不要把 RAG、履歷擷取、履歷匹配混成同一個分數

---

## 11. 下一步

下一步只做一件事：

**建立 AI 評估資料規格與樣本模板。**

也就是：

- 定義 assistant 問題集格式
- 定義 resume extraction 標註格式
- 定義 resume matching 標註格式

這會是後面所有優化的基礎。
