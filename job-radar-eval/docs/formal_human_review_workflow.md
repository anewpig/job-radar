# Formal Human Review Workflow

這份文件是正式 reviewer 執行流程的一頁版操作說明。

適用情境：
- 你要把 assistant 輸出交給 `2` 位 reviewer 做正式人工評分
- 你要把結果整理成論文可用的人評統計

不適用情境：
- smoke test
- resume matching label 評估
- latency / token budget 檢查

---

## 1. 先備條件

你需要先有一份最新的 `blind` reviewer packet。

目前最新可用檔案：
- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/human_review_packet_20260407_072226/assistant_review_packet_blind.csv](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/human_review_packet_20260407_072226/assistant_review_packet_blind.csv)

評分規則：
- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/human_review_rubric.md](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/docs/human_review_rubric.md)

如果要重新產生 packet：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_human_review_packet.py --limit 12
```

如果要直接產生可發給 `r1 / r2` 的 reviewer bundle：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_formal_reviewer_bundle.py --reviewer-ids r1,r2
```

---

## 2. 要發給 Reviewer 的東西

每位 reviewer 只需要兩個檔案：

1. `assistant_review_packet_blind.csv`
2. `docs/human_review_rubric.md`

不要發：
- `research` 版本
- `summary.json`
- 自動評分結果
- 任何內部解釋文件

原因：
- `blind` 版本不包含自動分數
- 可以避免 reviewer 被系統結果影響

---

## 3. Reviewer 要怎麼填

reviewer 只需要修改以下欄位：

- `reviewer_id`
- `correctness_score`
- `grounding_score`
- `usefulness_score`
- `clarity_score`
- `overall_score`
- `verdict`
- `notes`

其他欄位不要改：

- `review_id`
- `case_id`
- `question`
- `answer`
- `summary`
- `key_points`
- `limitations`
- `next_step`
- `citation_count`
- `citation_labels`
- `citation_snippets`

建議規則：
- `reviewer_id` 固定，例如 `r1`、`r2`
- `verdict` 只用：
  - `accept`
  - `minor_issue`
  - `major_issue`
  - `reject`
- `notes` 寫具體觀察，不要只寫「普通」或「怪怪的」

---

## 4. 收檔規則

建議你收回時改名成：

- `reviewer_a.csv`
- `reviewer_b.csv`

或更正式一點：

- `assistant_review_reviewer_r1.csv`
- `assistant_review_reviewer_r2.csv`

要求：
- 保持 UTF-8
- 不要改欄位順序
- 不要刪列
- 不要把 Excel 自動轉成別的格式

---

## 5. 如何跑正式彙整

拿到 reviewer CSV 之後，先驗證格式：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_human_review_validation.py \
  /path/to/reviewer_a.csv \
  /path/to/reviewer_b.csv \
  --require-completed
```

確認 validation 是 `PASS` 後，再執行：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_human_review_analysis.py \
  /path/to/reviewer_a.csv \
  /path/to/reviewer_b.csv
```

如果你不想分兩步跑，也可以直接用正式入口：

```bash
cd /Users/zhuangcaizhen/Desktop/專案/職缺爬蟲
source .venv/bin/activate
python /Users/zhuangcaizhen/Desktop/專案/job-radar-eval/scripts/run_formal_human_review.py \
  /path/to/reviewer_a.csv \
  /path/to/reviewer_b.csv
```

這會輸出一個新目錄：
- `results/human_review_analysis_<timestamp>/`

裡面主要看這幾個檔：

- `summary.json`
- `report.md`
- `thesis_tables.md`
- `thesis_tables.tex`
- `human_review_rows_cases.csv`
- `human_review_case_summary_cases.csv`
- `human_review_reviewer_summary_cases.csv`
- `manifest.json`

---

## 6. 這些輸出怎麼用

### `summary.json`

給程式或後續統整使用。

### `report.md`

給內部快速看結果。

### `thesis_tables.md`

給論文直接引用，現在已包含：
- aggregate table
- reviewer table
- case preview table
- reviewer agreement 指標

### `thesis_tables.tex`

給 LaTeX 論文直接引用。

如果你的論文主檔是 LaTeX，這份通常比 markdown 更直接。

### `human_review_case_summary_cases.csv`

做 error analysis 最有用。

### `human_review_reviewer_summary_cases.csv`

看 reviewer 間是否有明顯偏差。

---

## 7. 論文中最適合報的指標

建議至少報：

- `correctness_score_mean`
- `grounding_score_mean`
- `usefulness_score_mean`
- `clarity_score_mean`
- `overall_score_mean`
- `pairwise_verdict_agreement_rate`
- `cohens_kappa_verdict`

如果 reviewer 數只有 `2` 位，`Cohen's kappa` 很適合放主文。

如果 reviewer 數之後增加到 `3+` 位：
- 可以再擴充成多 reviewer agreement 指標

---

## 8. 正式版與 Smoke Test 的差別

目前已經有一份 smoke test 分析結果：
- [/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/human_review_analysis_20260407_185850/summary.json](/Users/zhuangcaizhen/Desktop/專案/job-radar-eval/results/human_review_analysis_20260407_185850/summary.json)

這份只能驗證流程是通的，不能當正式論文結果。

正式結果必須滿足：
- reviewer 不是你自己填的 smoke data
- reviewer 使用 `blind` packet
- 有固定 rubric
- 有 `manifest.json`

---

## 9. 最小正式流程

如果你要最小可行版本，照這個順序做：

1. 產生最新 `blind` packet
2. 發給 `2` 位 reviewer
3. 各評 `10~20` 筆
4. 跑 `run_human_review_validation.py`
5. 跑 `run_human_review_analysis.py`
6. 把 `thesis_tables.md` 放進論文草稿

這就是目前主線上，human review 的正式執行方式。
