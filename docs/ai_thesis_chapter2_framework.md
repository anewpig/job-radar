# Chapter 2 相關研究寫作框架

這份文件不是正式文獻回顧正文，而是 `Chapter 2` 的寫作框架。目的有三個：

- 先把相關研究的論述結構定下來
- 明確知道每一節要回答什麼問題
- 讓後續找文獻、補引用與寫正文時不會散掉

本章建議定位為：**交代本研究站在哪些既有研究脈絡上，並說明本研究和它們的差異與補足點。**

---

## 2.1 本章目標

`Chapter 2` 不需要證明你的系統已經做得多好，那是 `Chapter 5` 的工作。  
這一章要做的是：

1. 說明求職 AI 相關問題在研究上可分成哪些脈絡
2. 交代既有方法通常怎麼做
3. 指出既有工作的不足
4. 自然導出你的研究定位

一句話版本：

> 既有研究分別處理了 RAG 問答、履歷解析、職缺匹配與 LLM 評估，但較少將真實職缺市場快照、mode-aware 問答控制、履歷匹配、產品級 observability 與 formal human review 整合成同一條可產品化的系統主線。

---

## 2.2 建議章節結構

建議 `Chapter 2` 分成四節：

1. `RAG 與 evidence-grounded QA`
2. `Resume parsing 與 job matching`
3. `LLM evaluation、human review 與 observability`
4. `本研究定位與差異`

這樣的好處是：

- 前三節交代外部研究脈絡
- 最後一節把你的系統放回研究空間裡

---

## 2.3 第一節：RAG 與 Evidence-Grounded QA

### 2.3.1 這節要回答的問題

- 為什麼需要 RAG，而不是只靠通用 LLM
- 什麼是 evidence-grounded QA
- retrieval、citation、answer control 在既有研究中通常怎麼設計

### 2.3.2 建議小節

1. `Large Language Models and Knowledge Limitations`
2. `Retrieval-Augmented Generation`
3. `Evidence-Grounded QA and Citation-Based Answering`
4. `Limitations of Generic RAG Pipelines in Domain-Specific Applications`

### 2.3.3 你要寫的重點

- 通用 LLM 在時效性、可驗證性與領域精確性上有限
- RAG 的核心不是生成，而是先找到對的證據
- evidence-grounded QA 強調回答必須由可檢查的內容支撐
- 多數通用 RAG 論文不會處理求職場景中的：
  - 多來源職缺快照
  - mode-aware 問答
  - 比較型回答
  - 個人化履歷條件

### 2.3.4 可查的關鍵字

- `retrieval augmented generation survey`
- `evidence grounded question answering`
- `citation grounded QA`
- `attribution in large language models`
- `retrieval reranking llm applications`

### 2.3.5 這節最後要收成的論點

> 既有 RAG 與 evidence-grounded QA 研究提供了可靠回答的基礎概念，但在求職場景中，仍缺乏針對多來源職缺市場、問題模式切換與產品級證據管理的完整系統設計。

---

## 2.4 第二節：Resume Parsing 與 Job Matching

### 2.4.1 這節要回答的問題

- 既有研究如何做履歷資訊抽取
- 既有研究如何做履歷與職缺匹配
- ranking、skill alignment、role alignment 通常怎麼量測

### 2.4.2 建議小節

1. `Resume Information Extraction`
2. `Skill Normalization and Role Representation`
3. `Job Recommendation and Resume-to-Job Matching`
4. `Ranking-Based Evaluation for Job Matching`

### 2.4.3 你要寫的重點

- 履歷抽取常見任務包含：
  - role extraction
  - skill extraction
  - experience parsing
- 履歷匹配不能只看分類正確率，排序品質同樣重要
- matching 問題通常需要：
  - role alignment
  - skill alignment
  - ranking metrics
- 既有研究常將 matching 當推薦或分類問題，但較少和：
  - 真實市場快照
  - 個人化問答
  - 產品級 latency / cost / telemetry
  一起設計

### 2.4.4 可查的關鍵字

- `resume parsing named entity recognition`
- `job resume matching survey`
- `job recommendation ranking resume`
- `skill extraction resume llm`
- `resume job matching ndcg`

### 2.4.5 這節最後要收成的論點

> 既有履歷抽取與職缺匹配研究奠定了 role/skill 表示與 ranking 評估基礎，但在求職產品情境中，仍缺乏與真實市場問答、模式化回答與產品監控整合的完整設計。

---

## 2.5 第三節：LLM Evaluation、Human Review 與 Observability

### 2.5.1 這節要回答的問題

- LLM 系統通常如何評估
- 自動指標與人工評分各自的角色是什麼
- 為什麼產品級系統需要 observability 與 gate

### 2.5.2 建議小節

1. `Automatic Evaluation for LLM Systems`
2. `Human Review and Preference-Based Assessment`
3. `Latency, Cost, and Reliability in LLM Applications`
4. `Evaluation Pipelines and Regression Gates`

### 2.5.3 你要寫的重點

- 自動指標適合做回歸與大規模比較，但不能完全代表使用者接受度
- human review 是檢查 correctness、grounding、usefulness、clarity 的必要補充
- LLM 系統若要產品化，不能只看品質，還要看：
  - latency
  - token usage
  - reliability
  - regression stability
- 很多研究只報單次 benchmark，但產品系統需要：
  - repeated evaluation
  - manifest
  - case-level export
  - formal review workflow

### 2.5.4 可查的關鍵字

- `llm evaluation survey`
- `human evaluation large language models`
- `llm observability production`
- `latency and cost evaluation llm applications`
- `regression testing for llm systems`

### 2.5.5 這節最後要收成的論點

> 既有研究已指出自動指標與人工評分的重要性，但較少將 snapshot health、mode-aware 評估、latency gate、token budget、formal human review 與 training readiness 一起設計成產品級驗證流程。

---

## 2.6 第四節：本研究定位與差異

這節是 `Chapter 2` 最重要的收束點。前三節談別人做了什麼，這一節要明確說你補了什麼。

### 2.6.1 建議寫法

可用表格整理：

| 面向 | 既有研究常見做法 | 本研究做法 |
| --- | --- | --- |
| 知識來源 | 靜態語料或單一資料集 | 多來源職缺市場快照 |
| 問答模式 | 單一 generic QA | mode-aware 三種回答模式 |
| 履歷匹配 | 單點分類或推薦 | two-stage ranking + label eval |
| 證據控制 | 通用 citation 或無 citation | comparison-specific / mode-specific citation |
| 評估 | 單一 benchmark | fixture + real snapshot + real model + human review |
| 產品觀測 | 較少討論 | telemetry + token/latency/reliability budget |
| 訓練判定 | 直接調模型 | 先用 training readiness gate 判斷 |

### 2.6.2 這節最後要收成的論點

> 本研究的差異不在於提出新的大型模型，而在於把求職場景中的多來源市場資料、RAG 問答、履歷匹配、產品觀測與正式評估整合成一條完整、可回歸、可產品化的 AI 系統主線。

---

## 2.7 建議寫作策略

`Chapter 2` 不建議一開始就追求寫成完整正式文稿。建議分兩輪。

### 第一輪

先把每節的：

- 核心論點
- 關鍵字
- 比較框架

寫好，不急著補滿文獻。

### 第二輪

再去補：

- 代表性 survey / seminal work
- 與你的系統最接近的 application paper
- 評估與 human review 的方法論引用

這樣比較不會在一開始就掉進文獻堆裡。

---

## 2.8 你後續補文獻時的最低需求

如果你的目標是先把論文寫成可提交版本，`Chapter 2` 每一節至少要有：

- `2~3` 篇代表性文獻
- `1` 個收束段落

也就是大概：

- RAG / evidence-grounded QA：`3~5` 篇
- resume parsing / matching：`3~5` 篇
- evaluation / observability：`3~5` 篇

總量先抓 `10~15` 篇，夠把章節站穩。

---

## 2.9 與你現有章節的銜接

這份框架和你已經完成的章節對應如下：

- [ai_thesis_chapter1_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter1_draft.md)
  - 交代問題背景與研究目標
- [ai_thesis_chapter3_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter3_draft.md)
  - 交代你怎麼做
- [ai_thesis_chapter4_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter4_draft.md)
  - 交代你怎麼評估
- [ai_thesis_chapter5_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter5_draft.md)
  - 交代你做出什麼結果
- [ai_thesis_chapter6_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter6_draft.md)
  - 交代結論與未來工作

所以 `Chapter 2` 的任務不是再講一次系統，而是建立「你的方法放在什麼研究脈絡中」。

---

## 2.10 本章框架結論

`Chapter 2` 的最佳寫法，不是把很多文獻堆在一起，而是圍繞一個核心主張展開：

> 既有研究分別提供了 RAG、履歷匹配與 LLM 評估的重要基礎，但缺乏一套面向求職產品場景，能同時整合真實市場快照、mode-aware 問答、履歷排序、產品 observability 與 formal human review 的完整系統設計與驗證流程。

只要這個核心主張寫穩，後面補文獻會容易很多。
