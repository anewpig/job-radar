# 後端營運 Runbook

這份文件只處理「夠用服務」模式下的日常營運，不討論 schema 設計或大規模擴展。

目前預設營運基線是：

- `1` 個 Streamlit app
- `1` 個 crawl scheduler
- `1` 個 crawl worker
- `SQLite + JSON snapshot + cache`

## 1. 服務邊界

### Web App

- 用途：提供使用者操作頁面與查詢入口
- 程式入口：[app.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/app.py)
- 本地啟動腳本：[start_backend_stack.sh](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/scripts/start_backend_stack.sh)
- Docker 啟動腳本：[start_streamlit.sh](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/scripts/start_streamlit.sh)

### Scheduler

- 用途：巡檢 `saved searches`，把到期查詢排進 queue
- 程式入口：[crawl_scheduler.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/crawl_scheduler.py)
- Docker 啟動腳本：[start_crawl_scheduler.sh](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/scripts/start_crawl_scheduler.sh)

### Worker

- 用途：從 queue 取 job，執行抓取、finalize、通知同步
- 程式入口：[crawl_worker.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/crawl_worker.py)
- Docker 啟動腳本：[start_crawl_worker.sh](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/scripts/start_crawl_worker.sh)

## 2. 重要資料位置

- 主資料目錄：`JOB_SPY_DATA_DIR`，預設是 [data](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data)
- 產品資料庫：[product_state.sqlite3](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/product_state.sqlite3)
- 使用者投遞資料庫：[user_submissions.sqlite3](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/user_submissions.sqlite3)
- Runtime 資料庫：[query_runtime.sqlite3](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/query_runtime.sqlite3)
- 歷史分析資料庫：[market_history.sqlite3](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/market_history.sqlite3)
- 最新快照：[jobs_latest.json](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/jobs_latest.json)
- Snapshot 目錄：[snapshots](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/snapshots)
- SQLite 備份目錄：[data/backups/sqlite](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/backups/sqlite)

## 3. 建議環境設定

夠用服務模式建議至少設：

```text
JOB_SPY_CRAWL_EXECUTION_MODE=worker
JOB_SPY_ENABLE_BACKEND_CONSOLE=false
JOB_SPY_RUNTIME_JOB_MAX_RETRIES=1
JOB_SPY_RUNTIME_CLEANUP_INTERVAL_SECONDS=21600
```

完整範本見 [`.env.example`](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/.env.example)。

## 4. 啟動方式

### 本地單機

```bash
source .venv/bin/activate
./scripts/start_backend_stack.sh
```

這個模式會同時啟動：

- app
- scheduler
- worker

如果只是要看網頁又不需要背景工作，可以單獨開：

```bash
source .venv/bin/activate
streamlit run app.py
```

### Docker Compose

```bash
docker compose up --build
```

Compose 目前會同時啟動：

- `job-radar`
- `job-radar-worker`
- `job-radar-scheduler`

設定位置見 [docker-compose.yml](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docker-compose.yml)。

### macOS launchd 常駐

如果你要讓 `worker`、`scheduler`、每日 maintenance 在本機登入後常駐：

```bash
source .venv/bin/activate
./scripts/install_launch_agents.sh
```

注意：

- 目前專案位於 `Desktop`，這是 macOS 受保護路徑
- `launchd` 不能直接從這個路徑常駐執行 shell script
- 安裝腳本因此會先同步一份 runtime 到 `~/.job-radar-runtime`
- 共用資料則落在 `~/.job-radar-data`

## 5. 停機方式

### 本地單機

- 如果是用 `./scripts/start_backend_stack.sh` 啟動，直接在前景程序按 `Ctrl+C`
- 如果是個別開程序，依序停掉 `streamlit`、`scheduler`、`worker`

### Docker Compose

```bash
docker compose down
```

## 6. 日常檢查

每次部署或重啟後，至少確認：

1. Web App 可以開啟首頁
2. 手動查詢能建立或更新 snapshot
3. `saved search` 到期後 scheduler 會 enqueue job
4. worker 能把 job 從 `pending` 推到 `completed` 或 `failed`
5. 備份目錄可正常寫入

最基本 smoke check：

```bash
source .venv/bin/activate
env PYTHONPATH=src .venv/bin/python -c "import app; print('app import ok')"
env PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

如果你不想打開 backend web 頁，也可以直接看 CLI 狀態：

```bash
source .venv/bin/activate
./scripts/run_backend_status.sh
```

如果你要把它接進監控檢查：

```bash
source .venv/bin/activate
./scripts/run_backend_status.sh --strict
```

只要有 issue，這個指令就會回傳 non-zero exit code。

## 7. 備份流程

### 建立備份

```bash
source .venv/bin/activate
job-radar-sqlite-maintenance backup --base-dir .
```

預設會備份：

- `product_state.sqlite3`
- `user_submissions.sqlite3`
- `market_history.sqlite3`

如果你要連 runtime queue 一起備份：

```bash
source .venv/bin/activate
job-radar-sqlite-maintenance backup --base-dir . --include-runtime
```

備份結果會落在：

- [data/backups/sqlite](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/backups/sqlite)

每次備份會建立一個時間戳目錄，內含：

- SQLite 檔案副本
- `manifest.json`

### 固定備份流程

如果你要把這件事變成固定操作，直接跑：

```bash
source .venv/bin/activate
./scripts/run_sqlite_backup.sh
```

這個腳本會：

- 建立一份 SQLite 備份
- 預設保留最近 `14` 份備份
- 可用 `JOB_SPY_SQLITE_BACKUP_KEEP_LAST` 調整保留數量
- 可用 `JOB_SPY_SQLITE_BACKUP_INCLUDE_RUNTIME=true` 把 runtime 也一起備份

### 每日營運入口

如果你要把日常維護收成一個命令，直接跑：

```bash
source .venv/bin/activate
./scripts/run_backend_maintenance.sh
```

這個入口會順序執行：

- runtime cleanup
- SQLite backup

可調整的設定：

- `JOB_SPY_SQLITE_BACKUP_KEEP_LAST`
- `JOB_SPY_SQLITE_BACKUP_INCLUDE_RUNTIME`
- `JOB_SPY_BACKEND_MAINTENANCE_FORCE_CLEANUP`

## 8. 還原流程

還原前先停掉 app、scheduler、worker，避免還原時仍有寫入。

### 還原 persistent 資料

```bash
source .venv/bin/activate
job-radar-sqlite-maintenance restore --base-dir . --backup data/backups/sqlite/<backup-id> --yes
```

### 還原時包含 runtime

```bash
source .venv/bin/activate
job-radar-sqlite-maintenance restore --base-dir . --backup data/backups/sqlite/<backup-id> --include-runtime --yes
```

還原時系統會先做一份 `pre-restore-*` 安全備份，再覆蓋目標 SQLite。

## 9. 常見故障判讀

### UI 查詢一直停在 pending

先看：

- scheduler 有沒有啟動
- worker 有沒有啟動
- `JOB_SPY_CRAWL_EXECUTION_MODE` 是否是 `worker`

如果 app 在 `worker` 模式，但 worker 沒跑，job 會排進 queue 但不會被處理。

### Job 常常失敗

先確認：

- 外部網站是否限流
- `OPENAI_API_KEY` 是否正常
- 網路是否不穩
- worker 是否反覆重啟

目前系統預設只做有限重試，不會無限重跑。

### SQLite 越跑越大

先確認：

- cleanup 有沒有持續跑
- backup 目錄是否堆太多舊備份
- `data/cache` 是否需要清理

目前 runtime cleanup 只會清 runtime artifacts，不會清你手動保留的 SQLite 備份。

### 還原後資料不對

先看：

- 還原用的是不是正確 `backup-id`
- 是否把 `include-runtime` 誤用在不需要的情況
- `pre-restore-*` 安全備份是否還在

如果 restore 後發現選錯版本，可以再用 `pre-restore-*` 回滾。

## 10. 建議操作原則

- 不要把 `backend console` 長期開在正式網站
- 不要在 app / worker / scheduler 還在寫資料時直接 restore
- 不要預設備份 `query_runtime.sqlite3`，除非你真的需要保留 queue 狀態
- 不要先做大型基礎設施升級，先把這套單機後端跑穩

## 11. 相關文件

- [README.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/README.md)
- [維護指南](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/maintenance_guide.md)
- [系統架構](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/architecture.md)
