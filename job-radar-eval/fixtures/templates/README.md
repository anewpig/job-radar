# Evaluation Fixture Templates

這個資料夾放的是第一輪標註模板，不直接給目前 baseline runner 讀取。

用途：

- 先把資料規格固定下來
- 讓後續標註有一致格式
- 等模板累積到足夠題量後，再決定是否合併進正式 fixture 與 benchmark runner

目前提供三份模板：

- `assistant_questions_template.jsonl`
- `resume_extraction_labels_template.jsonl`
- `resume_match_labels_template.jsonl`
- `assistant_human_review_template.csv`

建議流程：

1. 先在這裡補資料
2. 先用人工 review 檢查格式與標註一致性
3. 題量夠之後再轉成 runner 正式使用的 fixture

格式採 `jsonl`：

- 一行一筆
- 方便逐筆追加
- Git diff 清楚

人工評分模板採 `csv`：

- 適合直接交給 reviewer 填寫
- 可搭配 `scripts/run_human_review_packet.py` 產生真實 case packet
