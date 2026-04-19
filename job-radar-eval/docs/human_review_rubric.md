# Human Review Rubric

這份 rubric 用來補強目前的系統指標，讓 AI 助理結果除了自動分數之外，還能有人評資料可寫進論文。

適用範圍：
- `assistant_review_packet_blind.csv`
- `assistant_review_packet_blind.jsonl`
- `assistant_review_packet_research.csv`
- `assistant_review_packet_research.jsonl`

不適用範圍：
- resume extraction schema 正確率
- retrieval latency
- token budget

---

## 1. 評分單位

一筆人工評分對應一個 `review_id`，通常是一個 assistant case。

每筆 reviewer 會看到：
- `question`
- `answer`
- `summary`
- `key_points`
- `limitations`
- `next_step`
- `citation_labels`
- `citation_snippets`

正式 reviewer 建議使用：
- `assistant_review_packet_blind.*`

研究者內部對照用：
- `assistant_review_packet_research.*`

`research` 版本才會保留自動指標：
- `auto_total_ms`
- `auto_citation_keyword_recall`
- `auto_evidence_sufficient`
- `auto_issue_priority`

---

## 2. 評分欄位

### 2.1 correctness_score

回答是否正確、沒有明顯誤導。

- `5`：內容正確，沒有明顯錯誤
- `4`：大致正確，但有小幅不精確
- `3`：部分正確，但有重要遺漏
- `2`：錯誤明顯，容易誤導
- `1`：內容基本不可用

### 2.2 grounding_score

回答是否真的被引用證據支撐。

- `5`：主要結論都能從 citation 直接支持
- `4`：大部分有支持，少量推論
- `3`：只有部分有證據支撐
- `2`：多數結論缺乏證據
- `1`：幾乎沒有被證據支撐

### 2.3 usefulness_score

回答對求職者是否真的有用。

- `5`：可直接用來行動或做決策
- `4`：有實用價值，但仍需少量補充
- `3`：只有一般性幫助
- `2`：幫助有限
- `1`：幾乎沒有幫助

### 2.4 clarity_score

回答是否清楚、好讀、結構穩定。

- `5`：非常清楚，重點明確
- `4`：大致清楚，少量冗字
- `3`：可讀，但結構普通
- `2`：難讀或重點不清
- `1`：混亂、不易理解

### 2.5 overall_score

整體綜合評價，建議作為：

- `overall_score = round((correctness + grounding + usefulness + clarity) / 4)`

若 reviewer 有更明確判斷，可以人工覆寫。

---

## 3. verdict

建議使用固定值：

- `accept`
- `minor_issue`
- `major_issue`
- `reject`

判定建議：
- `accept`：可直接作為好案例
- `minor_issue`：小問題，不影響主要結論
- `major_issue`：有明顯缺口，需要修正
- `reject`：不建議引用為正面案例

---

## 4. notes

`notes` 要寫具體錯誤，不要只寫抽象評論。

好的寫法：
- `薪資結論有引用，但沒有提到區間上限。`
- `技能建議正確，但 citation 只支持其中兩項。`
- `回答清楚，但 next_step 太空泛。`

不好的寫法：
- `普通`
- `怪怪的`
- `感覺不準`

---

## 5. 論文建議用法

建議至少抽：
- `10~20` 筆 assistant case
- `2` 位 reviewer

可以報：
- 平均 `correctness / grounding / usefulness / clarity`
- `accept / reject` 比例
- reviewer disagreement ratio

這一批人工評分最適合拿來支撐：
- answer quality
- citation faithfulness
- product usefulness
