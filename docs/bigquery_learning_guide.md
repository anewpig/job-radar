# Job Radar BigQuery 學習指南

這份指南的目標不是把目前系統直接改成跑在 BigQuery 上，而是讓你用**現有本地資料**，建立一份適合練習 BigQuery 的分析副本。

## 先建立正確心態

你現在的系統：
- 主執行環境：本地 Streamlit / Python / SQLite / JSON
- 資料型態：混合 operational data、snapshot data、history data、AI monitoring data

BigQuery 在這裡最適合扮演的是：
- 分析資料倉
- 歷史報表查詢
- SQL 練習環境
- dashboard / mart 的後端

BigQuery **不適合**直接接手你目前這些角色：
- session state
- runtime queue
- crawl job lease
- 即時小筆交易寫入

一句話：**先把 BigQuery 當分析副本，而不是主系統資料庫。**

---

## 第一階段要搬哪些資料

建議你先搬這四類：

### 1. 市場歷史資料

來源：`data/market_history.sqlite3`

推薦表：
- `crawl_runs`
- `job_posts`
- `crawl_run_jobs`

這三張最適合學：
- 職缺量趨勢
- 不同來源的資料量
- 不同 role / skill 的市場分布
- 某次 crawl 與 job 明細關聯

### 2. 最新市場快照

來源：
- `data/jobs_latest.json`
- `data/snapshots/*.json`

適合學：
- JSON schema
- raw landing table
- 將 snapshot 整理成 mart

### 3. AI / agent / audit 資料

來源：`data/product_state.sqlite3`

推薦表：
- `ai_monitoring_events`
- `audit_events`
- `feedback_events`
- `agent_memories`

適合學：
- latency / usage 分析
- event log 分析
- agent workflow 分析
- 使用者互動與稽核分析

### 4. runtime 監控資料

來源：`data/query_runtime.sqlite3`

推薦表：
- `query_snapshots`
- `crawl_jobs`
- `runtime_signals`

這一類可以練習：
- 系統健康狀態
- queue backlog
- snapshot freshness

但它比較偏 runtime，不是最適合一開始先學的主資料。

---

## 哪些資料先不要搬

除非你非常清楚資料治理，不然這些先不要：

- `users`
- `password_reset_tokens`
- `user_identities`
- 原始履歷全文
- auth / session / secret 類資料

理由：
- 安全敏感
- 分析價值相對低
- 容易把 BigQuery 學習和個資風險綁在一起

---

## 我幫你加的本地匯出腳本

腳本位置：

`scripts/export_bigquery_learning_bundle.py`

這支腳本會做的事：
- 從本地 SQLite 讀指定表
- 把 JSON 字串欄位轉成真正 JSON 結構
- 輸出成 BigQuery 比較好吃的 `NDJSON`
- 複製 `jobs_latest.json`
- 複製部分 snapshot 檔案
- 生成：
  - `bundle_manifest.json`
  - `BIGQUERY_LOAD_GUIDE.md`

---

## 你現在可以怎麼跑

在專案根目錄執行：

```bash
./.venv/bin/python scripts/export_bigquery_learning_bundle.py
```

如果你也想把已遮罩的 `user_submissions` 一起匯出：

```bash
./.venv/bin/python scripts/export_bigquery_learning_bundle.py --include-sensitive
```

輸出會落在：

`data/bigquery_exports/job_radar_bigquery_bundle_<timestamp>/`

---

## 建議的 BigQuery dataset 規劃

### Dataset 1：`job_radar_raw`

放原始匯入資料：
- `raw_market_history_crawl_runs`
- `raw_market_history_job_posts`
- `raw_market_history_crawl_run_jobs`
- `raw_product_ai_monitoring_events`
- `raw_product_audit_events`
- `raw_query_runtime_query_snapshots`

### Dataset 2：`job_radar_mart`

放整理後分析表：
- `fact_job_posts`
- `fact_crawl_runs`
- `fact_ai_events`
- `dim_source`
- `dim_role`

第一階段只做 `job_radar_raw` 就夠了。

---

## BigQuery 上的第一批練習題

### 練習 1：看不同來源的職缺量

```sql
SELECT
  source,
  COUNT(*) AS job_count
FROM `your_project.job_radar_raw.raw_market_history_job_posts`
GROUP BY source
ORDER BY job_count DESC;
```

### 練習 2：看最近有哪些 role 最常出現

```sql
SELECT
  matched_role,
  COUNT(*) AS job_count
FROM `your_project.job_radar_raw.raw_market_history_crawl_run_jobs`
WHERE matched_role IS NOT NULL
  AND matched_role != ''
GROUP BY matched_role
ORDER BY job_count DESC
LIMIT 20;
```

### 練習 3：看 AI 事件延遲

```sql
SELECT
  event_type,
  status,
  ROUND(AVG(latency_ms), 2) AS avg_latency_ms,
  COUNT(*) AS event_count
FROM `your_project.job_radar_raw.raw_product_ai_monitoring_events`
GROUP BY event_type, status
ORDER BY avg_latency_ms DESC;
```

### 練習 4：看 agent memory 的類型分布

```sql
SELECT
  memory_type,
  COUNT(*) AS memory_count
FROM `your_project.job_radar_raw.raw_product_agent_memories`
GROUP BY memory_type
ORDER BY memory_count DESC;
```

---

## 你在 BigQuery 最值得學的觀念

### 1. Partition

像這些欄位很適合 partition：
- `generated_at`
- `created_at`
- `updated_at`
- `last_seen_at`

目的：
- 降低掃描成本
- 讓查詢更快

### 2. Cluster

像這些欄位可以考慮 cluster：
- `source`
- `matched_role`
- `event_type`
- `status`
- `memory_type`

### 3. Raw vs Mart

不要一開始就直接改原始資料。  
先保留 raw table，再另外做整理後的 mart table，這比較像正式資料倉做法。

### 4. Nested JSON

你這個專案很多欄位是：
- `*_json`
- 陣列欄位
- 結構化 payload

這正好很適合練：
- `UNNEST`
- nested field 查詢
- JSON schema 理解

---

## 你接下來最好的學習順序

### 第一步

先跑匯出腳本，確認你看得懂輸出 bundle 裡有哪些檔案。

### 第二步

先把這三張匯進 BigQuery：
- `raw_market_history_crawl_runs`
- `raw_market_history_job_posts`
- `raw_market_history_crawl_run_jobs`

### 第三步

先只寫最基本的：
- `SELECT`
- `WHERE`
- `GROUP BY`
- `ORDER BY`

### 第四步

再開始練：
- `JOIN`
- `window functions`
- `partition / cluster`

### 第五步

最後才碰：
- event log 分析
- agent memory 分析
- feedback / audit 分析

---

## 最後一句建議

你現在最該學的不是「怎麼把整個系統改成 BigQuery」，  
而是：

**怎麼把 operational system 的資料，整理成可以進資料倉分析的副本。**

這個能力更接近真實工作，也更容易在面試裡講清楚。
