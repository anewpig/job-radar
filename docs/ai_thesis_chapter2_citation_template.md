# Chapter 2 文獻補引模板

這份文件是給 [ai_thesis_chapter2_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter2_draft.md) 用的補引模板。  
目的不是重寫正文，而是把每一段最需要補的引用類型先標出來，後面你只要把文獻塞進去即可。

建議做法：

1. 先找到對應 paper
2. 在這份模板把 `Citation Type` 改成具體 paper 名稱
3. 再回填到 `Chapter 2` 正文

---

## 2.1 RAG 與 Evidence-Grounded Question Answering

### 段落 2.1-A

- 正文位置：
  - `2.1` 第 1 段
- 段落用途：
  - 說明通用 LLM 的知識限制與時效性問題
- 建議引用類型：
  - `Survey / overview on LLM limitations`
  - `Paper on hallucination / factuality / temporal staleness`
- Citation Type：
  - `[CITE-RAG-01]`
  - `[CITE-RAG-02]`

### 段落 2.1-B

- 正文位置：
  - `2.1` 第 2 段
- 段落用途：
  - 定義 RAG 的基本概念與應用價值
- 建議引用類型：
  - `Foundational RAG paper`
  - `RAG survey / review`
- Citation Type：
  - `[CITE-RAG-03]`
  - `[CITE-RAG-04]`

### 段落 2.1-C

- 正文位置：
  - `2.1` 第 3 段
- 段落用途：
  - 說明 evidence-grounded QA 與 citation/attribution 問題
- 建議引用類型：
  - `Evidence-grounded QA`
  - `Attribution / citation in LLMs`
- Citation Type：
  - `[CITE-RAG-05]`
  - `[CITE-RAG-06]`

### 段落 2.1-D

- 正文位置：
  - `2.1` 第 4~5 段
- 段落用途：
  - 解釋為何求職問題是聚合型與決策型問題
- 建議引用類型：
  - `Applied QA / decision-support systems`
  - `RAG in domain-specific decision support`
- Citation Type：
  - `[CITE-RAG-07]`

### 段落 2.1-E

- 正文位置：
  - `2.1` 最後兩段
- 段落用途：
  - 收束既有工作不足與本研究切入點
- 建議引用類型：
  - 可不必大量引用
  - 若有接近你系統的 applied RAG paper，可補 `1` 篇對照
- Citation Type：
  - `[CITE-RAG-08]`

---

## 2.2 Resume Parsing 與 Job Matching

### 段落 2.2-A

- 正文位置：
  - `2.2` 第 1~2 段
- 段落用途：
  - 定義履歷解析與基本抽取任務
- 建議引用類型：
  - `Resume parsing / information extraction`
  - `NER / document IE for resumes`
- Citation Type：
  - `[CITE-RES-01]`
  - `[CITE-RES-02]`

### 段落 2.2-B

- 正文位置：
  - `2.2` 第 3~4 段
- 段落用途：
  - 說明 matching 不是單純欄位比對，而是 role/skill/ranking 問題
- 建議引用類型：
  - `Job-resume matching`
  - `Skill normalization / representation`
- Citation Type：
  - `[CITE-RES-03]`
  - `[CITE-RES-04]`

### 段落 2.2-C

- 正文位置：
  - `2.2` 第 5 段
- 段落用途：
  - 說明 Top-k、pairwise ordering、nDCG 等 ranking 脈絡
- 建議引用類型：
  - `Ranking / recommendation evaluation`
  - `Job recommendation ranking`
- Citation Type：
  - `[CITE-RES-05]`
  - `[CITE-RES-06]`

### 段落 2.2-D

- 正文位置：
  - `2.2` 第 6~7 段
- 段落用途：
  - 說明既有研究和產品場景之間的缺口
- 建議引用類型：
  - `Application/system paper close to resume-job matching`
- Citation Type：
  - `[CITE-RES-07]`

### 段落 2.2-E

- 正文位置：
  - `2.2` 最後兩段
- 段落用途：
  - 收束到本研究的定位
- 建議引用類型：
  - 不必太多
  - 保留 `1` 篇最接近的相關工作即可
- Citation Type：
  - `[CITE-RES-08]`

---

## 2.3 LLM Evaluation、Human Review 與 Observability

### 段落 2.3-A

- 正文位置：
  - `2.3` 第 1 段
- 段落用途：
  - 指出單次 benchmark 或單一自動指標的不足
- 建議引用類型：
  - `LLM evaluation survey`
  - `Limitations of automatic evaluation`
- Citation Type：
  - `[CITE-EVAL-01]`
  - `[CITE-EVAL-02]`

### 段落 2.3-B

- 正文位置：
  - `2.3` 第 2~3 段
- 段落用途：
  - 說明 correctness / grounding / usefulness / clarity 這類面向為何需要人評
- 建議引用類型：
  - `Human evaluation of LLM outputs`
  - `Human preference / rubric based evaluation`
- Citation Type：
  - `[CITE-EVAL-03]`
  - `[CITE-EVAL-04]`

### 段落 2.3-C

- 正文位置：
  - `2.3` 第 4~5 段
- 段落用途：
  - 說明 observability、latency、token cost 與 regression 的產品意義
- 建議引用類型：
  - `Production LLM systems / observability`
  - `Latency-cost evaluation`
- Citation Type：
  - `[CITE-EVAL-05]`
  - `[CITE-EVAL-06]`

### 段落 2.3-D

- 正文位置：
  - `2.3` 最後兩段
- 段落用途：
  - 收束既有研究斷裂與本研究定位
- 建議引用類型：
  - `1` 篇 closest system/evaluation pipeline paper 即可
- Citation Type：
  - `[CITE-EVAL-07]`

---

## 2.4 本研究定位與差異

### 段落 2.4-A

- 正文位置：
  - `2.4` 全節
- 段落用途：
  - 做文獻收束與本研究定位
- 建議引用類型：
  - 這裡不需要再塞很多新文獻
  - 主要引用前面三節已提到的代表性工作
- Citation Type：
  - `Reuse citations from 2.1~2.3`

建議表格：

| 面向 | 既有研究常見做法 | 本研究做法 |
| --- | --- | --- |
| 知識來源 | 靜態語料或單一資料集 | 多來源職缺市場快照 |
| 問答模式 | 單一 generic QA | mode-aware 三種回答模式 |
| 履歷匹配 | 單點分類或推薦 | two-stage ranking + label eval |
| 引用控制 | 通用 citation 或無 citation | mode-specific / comparison-specific citation |
| 評估 | 單一 benchmark | fixture + real snapshot + real model + human review |
| 產品觀測 | 較少討論 | telemetry + token/latency/reliability budget |
| 訓練決策 | 直接調模型 | 先經 training readiness gate |

---

## 建議最低引用數

若要先做一版可交稿的 Chapter 2，最低建議：

- `2.1`：`4~5` 個 citation
- `2.2`：`4~5` 個 citation
- `2.3`：`4~5` 個 citation
- `2.4`：主要重用前面 citation

總量大約：

- `12~15` 個 citation

---

## 最後回填順序

1. 先填 `2.1`
2. 再填 `2.2`
3. 再填 `2.3`
4. 最後整理 `2.4` 的比較表

這樣比較不會讓 Chapter 2 的論述失焦。

---

## 對應文件

- [ai_thesis_chapter2_draft.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter2_draft.md)
- [ai_thesis_chapter2_framework.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter2_framework.md)
- [ai_thesis_chapter2_literature_search_plan.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_thesis_chapter2_literature_search_plan.md)
