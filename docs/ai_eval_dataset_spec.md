# AI 評估資料規格

這份文件是 `AI / RAG / LLM 技術地圖` 的第一步實作規格。  
目的只有一個：

- 先把評估資料格式定義清楚

這樣後面做 retrieval、prompt、resume matching、report generation 時，才有統一的 baseline 可以比較。

參考文件：

- [/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_rag_llm_roadmap.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/ai_rag_llm_roadmap.md)

---

## 1. 資料集總覽

這一階段要先建立三份資料集：

1. `assistant_questions.jsonl`
2. `resume_extraction_labels.jsonl`
3. `resume_match_labels.jsonl`

建議存放位置：

- 外部 eval repo：`/Users/zhuangcaizhen/Desktop/專案/job-radar-eval`

建議目錄：

```text
job-radar-eval/
  fixtures/
    assistant_questions.jsonl
    resume_extraction_labels.jsonl
    resume_match_labels.jsonl
```

格式建議採：

- `jsonl`

原因：

- 逐筆 append 容易
- Git diff 較清楚
- 後續轉 pandas / benchmark 容易

---

## 2. assistant question dataset

### 2.1 用途

拿來評估：

- RAG retrieval 命中
- answer quality
- citation quality
- report prompt quality

### 2.2 單筆欄位

```json
{
  "id": "qa_001",
  "category": "skill_gap",
  "question": "目前最值得優先補強的技能是什麼？",
  "expected_topics": ["Python", "LLM", "RAG"],
  "expected_keywords": ["技能", "市場", "補強"],
  "expected_source_types": ["market-skill", "job-skills", "resume-summary"],
  "expected_urls": [],
  "must_include": ["優先", "技能"],
  "must_not_include": ["無法判斷"],
  "notes": "用來測 skill-gap 類型問答"
}
```

### 2.3 欄位說明

- `id`
  - 唯一識別碼
- `category`
  - 問題分類
- `question`
  - 使用者實際會問的問題
- `expected_topics`
  - 回答理應涵蓋的主題
- `expected_keywords`
  - 回答中建議出現的關鍵字
- `expected_source_types`
  - 預期應該引用到的 chunk 類型
- `expected_urls`
  - 若有明確應引用的職缺 URL，可填
- `must_include`
  - 回答至少應提到的詞
- `must_not_include`
  - 不應出現的錯誤詞或模板詞
- `notes`
  - 標註備註

### 2.4 category 建議集合

- `skill_gap`
- `market_skill`
- `salary_range`
- `work_content`
- `job_compare`
- `resume_gap`
- `job_recommendation`
- `market_report`

### 2.5 第一版題量

建議先做：

- 每類 `10` 題
- 總計 `80` 題

---

## 3. resume extraction label dataset

### 3.1 用途

拿來評估：

- 履歷擷取 schema 正確率
- LLM extractor 與 rule extractor 比較

### 3.2 單筆欄位

```json
{
  "resume_id": "resume_001",
  "source_name": "sample_resume_001.txt",
  "resume_text": "完整履歷文字...",
  "target_roles": ["AI工程師", "AI應用工程師"],
  "core_skills": ["Python", "LLM", "RAG", "Docker"],
  "preferred_locations": ["台北市"],
  "experience_level": "1-3 年",
  "years_of_experience": 2.0,
  "summary": "有 Python、LLM、RAG 專案經驗，偏 AI 應用與模型整合。",
  "notes": ["轉職中", "可接受混合辦公"]
}
```

### 3.3 欄位說明

- `resume_id`
  - 唯一識別碼
- `source_name`
  - 來源檔名
- `resume_text`
  - 原始履歷文本
- `target_roles`
  - 標準答案角色
- `core_skills`
  - 標準答案技能
- `preferred_locations`
  - 標準答案地點
- `experience_level`
  - 文字級別分類
- `years_of_experience`
  - 數值年資
- `summary`
  - 濃縮摘要
- `notes`
  - 其他重要資訊

### 3.4 第一版題量

建議先做：

- `30` 份履歷先起步

理由：

- 先確保 schema 與標註規則穩
- 再擴到 `100~300`

---

## 4. resume match label dataset

### 4.1 用途

拿來評估：

- 履歷匹配排序
- Top-1 / Top-3 品質
- gap explanation 是否合理

### 4.2 單筆欄位

```json
{
  "case_id": "match_001",
  "resume_id": "resume_001",
  "job_id": "job_104_123",
  "job_title": "AI工程師",
  "fit_label": "high",
  "fit_score": 0.9,
  "fit_reason": ["skill_overlap", "matched_role", "location_fit"],
  "critical_gaps": ["MLOps"],
  "notes": "很適合作為前 3 名推薦"
}
```

### 4.3 fit_label 建議集合

- `high`
- `medium`
- `low`
- `reject`

### 4.4 第一版題量

建議先做：

- `20` 份履歷
- 每份對 `10` 個職缺標註
- 總計約 `200` 筆

---

## 5. 標註原則

### assistant questions

- 以「使用者真的會問」為原則，不要只寫研究題
- 問句應自然
- 同一類型至少有不同寫法，避免 prompt 過擬合

### resume extraction

- 只標文本裡可合理推得出的資訊
- 不要用標註者腦補
- 如果不確定，寧可留空或加 notes

### resume matching

- `fit_label` 要和真實求職情境一致
- 不要只看技能 overlap
- 要一起考慮：
  - role
  - title
  - experience
  - location
  - skill depth

---

## 6. 評估指標對應

### assistant

- retrieval:
  - `top1_hit_rate`
  - `recall_at_k`
  - `mrr`
- answer:
  - `citation_hit_rate`
  - `completeness`
  - `hallucination_rate`

### resume extraction

- `role_accuracy`
- `skill_precision`
- `skill_recall`
- `location_accuracy`
- `experience_accuracy`

### resume matching

- `top1_accuracy`
- `top3_accuracy`
- `ndcg`
- `mrr`
- `gap_reason_agreement`

---

## 7. 第一輪最小交付

這一輪先不要追求大資料量，先把格式定義穩。

建議你先做：

- `assistant_questions.jsonl`
  - `20` 題
- `resume_extraction_labels.jsonl`
  - `10` 份
- `resume_match_labels.jsonl`
  - `30` 筆

只要這三份能穩定跑 benchmark，我們就能開始下一步。

---

## 8. 下一步

下一步不是改模型，而是：

1. 建立這三份資料檔的第一版樣本
2. 把外部 eval repo 的 benchmark runner 接上這三份資料
3. 跑出第一版 baseline

完成後，才開始改：

- retrieval
- prompt
- resume matcher
