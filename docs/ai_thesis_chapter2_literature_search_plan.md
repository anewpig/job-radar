# Chapter 2 文獻搜尋清單

這份文件的目的，是把 `Chapter 2` 後續要補的文獻搜尋工作收成一份可執行清單。重點不是先把所有 paper 找齊，而是先明確：

- 每一節要找哪一類文獻
- 每類至少需要幾篇
- 用哪些關鍵字找
- 找到後要放進章節的哪個位置

---

## 1. 搜尋原則

### 1.1 優先順序

文獻優先順序建議如下：

1. `survey / review paper`
2. `代表性方法論文`
3. `與求職或 recommendation 場景接近的應用論文`
4. `產品級 LLM evaluation / observability` 相關論文或官方技術報告

### 1.2 文獻數量目標

若先做一版可交稿的 Chapter 2，建議最低需求：

- RAG / evidence-grounded QA：`3~5` 篇
- resume parsing / job matching：`3~5` 篇
- evaluation / human review / observability：`3~5` 篇

總量先抓：

- `10~15` 篇

若之後要加強文獻厚度，再擴到：

- `15~20` 篇

### 1.3 選文標準

優先選：

- 能清楚定義問題的 survey
- 被廣泛引用的方法論文
- 與你的研究問題直接相關的應用論文
- 近 `3~5` 年內和 LLM / RAG / evaluation 直接相關的工作

避免：

- 和主題太遠，只因為是 LLM 就硬放進來
- 只談模型能力，和求職、RAG、matching、evaluation 沒關聯
- 沒有方法或沒有明確貢獻的文章

---

## 2. Section 2.1：RAG 與 Evidence-Grounded QA

### 2.1.1 這節需要的文獻類型

至少需要：

- `1~2` 篇 RAG survey / overview
- `1~2` 篇 evidence-grounded QA / attribution / citation 相關
- `1` 篇 retrieval / reranking 在實務系統中的代表性工作

### 2.1.2 搜尋關鍵字

可用關鍵字：

- `retrieval augmented generation survey`
- `retrieval-augmented generation review`
- `evidence grounded question answering`
- `citation grounded qa llm`
- `attribution large language models`
- `retrieval reranking llm systems`

### 2.1.3 找到後放進哪裡

放進：

- [ai_thesis_chapter2_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter2_draft.md)
  - `2.1` 第一段：補 RAG 背景與限制
  - `2.1` 第二段：補 evidence-grounded QA 脈絡
  - `2.1` 最後一段：補為何通用 RAG 不足以直接解決求職場景

### 2.1.4 你最後要寫出的論點

這節最後要收成：

> RAG 與 evidence-grounded QA 為真實資料支撐回答提供了方法基礎，但在求職場景中，仍需處理多來源市場快照、問題模式切換與 citation 管理等額外挑戰。

---

## 3. Section 2.2：Resume Parsing 與 Job Matching

### 3.1 這節需要的文獻類型

至少需要：

- `1~2` 篇 resume parsing / information extraction
- `1~2` 篇 job matching / recommendation / ranking
- `1` 篇 skills 或 roles 對齊相關工作

### 3.2 搜尋關鍵字

可用關鍵字：

- `resume parsing information extraction`
- `resume parsing named entity recognition`
- `skill extraction from resumes`
- `job resume matching survey`
- `resume to job matching ranking`
- `job recommendation ranking resume`
- `skill normalization job matching`

### 3.3 找到後放進哪裡

放進：

- [ai_thesis_chapter2_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter2_draft.md)
  - `2.2` 前段：補 resume parsing 研究脈絡
  - `2.2` 中段：補 matching 與 ranking 研究
  - `2.2` 後段：補既有工作對產品場景的不足

### 3.4 你最後要寫出的論點

這節最後要收成：

> 既有履歷抽取與職缺匹配研究已提供 role/skill 表示與 ranking 評估基礎，但較少將其與真實市場問答、模式化回答與產品級觀測整合為一條完整系統主線。

---

## 4. Section 2.3：LLM Evaluation、Human Review 與 Observability

### 4.1 這節需要的文獻類型

至少需要：

- `1~2` 篇 LLM evaluation / benchmark survey
- `1~2` 篇 human evaluation / human preferences / rubric 相關
- `1~2` 篇 LLM systems observability / production evaluation / latency-cost discussion

### 4.2 搜尋關鍵字

可用關鍵字：

- `llm evaluation survey`
- `human evaluation large language models`
- `llm as a judge limitations`
- `human preferences llm evaluation`
- `production llm observability`
- `latency cost evaluation llm systems`
- `regression testing llm applications`

### 4.3 找到後放進哪裡

放進：

- [ai_thesis_chapter2_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter2_draft.md)
  - `2.3` 第一段：補自動評估的侷限
  - `2.3` 第二段：補 human review 的必要性
  - `2.3` 第三段：補 observability / latency / token budget 的產品脈絡

### 4.4 你最後要寫出的論點

這節最後要收成：

> 既有研究已強調自動評估與人工評分的重要性，但較少將 snapshot health、mode-aware 評估、latency budget、token budget、formal human review 與 training readiness 一起設計成產品級驗證流程。

---

## 5. Section 2.4：本研究定位與差異

這一節不需要另外找很多新文獻，重點是把前三節文獻收束到你的研究定位。

### 5.1 需要準備的內容

你要做的是整理一張比較表，至少包含：

- 知識來源
- 問答模式
- 履歷匹配設計
- citation / grounding
- evaluation
- observability
- training decision

### 5.2 這節放進哪裡

放進：

- [ai_thesis_chapter2_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter2_draft.md)
  - `2.4` 整節

### 5.3 你最後要寫出的論點

> 本研究的差異不在於提出新的大型模型，而在於將真實市場快照、mode-aware 問答、履歷排序、產品 observability 與 formal human review 整合成一條可產品化、可回歸的 AI 系統主線。

---

## 6. 搜文時的實際操作順序

建議你真的開始查文獻時，照這個順序，不要同時亂開很多分支。

### Step 1

先找每一節的 `survey / review paper`

目標：

- 快速建立該領域的總論述

### Step 2

每一節再找 `2~3` 篇代表性方法論文

目標：

- 讓文獻回顧不只有 survey，還有具體方法依據

### Step 3

最後補與你最接近的 `application / systems` 類工作

目標：

- 幫你的研究定位找到最近的對照點

---

## 7. 建議紀錄方式

你查到 paper 後，建議先不要直接塞進正文。先另外記一份簡表，至少記：

- 標題
- 作者 / 年份
- 類型：survey / method / application
- 放在哪一節
- 一句話重點
- 和你研究的關聯

可先用 Markdown 表或 Excel 都可以。

建議欄位：

| paper | year | type | section | key point | relation to this thesis |
| --- | --- | --- | --- | --- | --- |

---

## 8. 最低可交稿版本

如果你現在時間有限，Chapter 2 先做到這個程度就夠：

- Section 2.1：`3` 篇
- Section 2.2：`3` 篇
- Section 2.3：`3` 篇
- Section 2.4：用比較表收束

也就是總共：

- `9~10` 篇左右

這樣就足以把章節立起來，不會空。

---

## 9. 和目前文件的對應

這份清單要搭配以下文件使用：

- [ai_thesis_chapter2_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter2_draft.md)
- [ai_thesis_chapter2_framework.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter2_framework.md)
- [ai_thesis_term_style_guide.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_term_style_guide.md)

---

## 10. 下一步建議

這份文件完成後，最合理的下一步只有兩種：

1. 真的開始找文獻，先補 `Section 2.1`
2. 如果你想先把論文版本收束，就先做全文統一修稿

如果要繼續走論文主線，我會建議先補：

- `Section 2.1` 的第一批代表性文獻
