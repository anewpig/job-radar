# 職缺雷達

職缺雷達（Job Radar）是一個面向台灣求職市場的 Streamlit 產品原型。
它會從 `104`、`1111`、`Cake`、`LinkedIn` 抓取公開職缺，整理成可操作的求職工作台，並把原始職缺內容進一步轉成：

- 職缺總覽與市場快照
- 工作內容與技能統計
- 履歷匹配與缺口分析
- AI 助手 / RAG 問答
- 已儲存搜尋、收藏、通知與投遞看板
- 後端 worker / scheduler / 備份維運工具

這個專案目前定位是「可實際操作的產品原型 + 可本地部署的單機服務」。
核心形態是 `Streamlit Web App + SQLite + JSON snapshot + background worker/scheduler`。

## 核心能力

### 1. 多來源職缺抓取

- 支援 `104`、`1111`、`Cake`、`LinkedIn`
- 可同時追蹤多個目標職缺與關鍵字
- 支援快速、平衡、完整等不同抓取節奏
- 會做去重、初步相關度評分與低相關過濾

### 2. 市場分析與整理

- 統計常見技能、工具與工作內容
- 比較不同來源的職缺量與分布
- 將搜尋結果保存為 snapshot，供後續頁面與 AI 助手共用

### 3. 履歷匹配

- 支援貼上文字、PDF、DOCX 履歷輸入
- 可做規則式或 LLM 輔助摘要
- 產生履歷與職缺的匹配結果、命中項與缺口項

### 4. AI 助手

- 以目前市場 snapshot 為知識基底做 RAG 問答
- 可回答技能缺口、優先投遞方向、常見工作內容與市場重點
- 可結合履歷摘要做更個人化的回答

### 5. 產品化功能

- 訪客 / 註冊 / 登入 / 忘記密碼
- 已儲存搜尋
- 收藏職缺
- 通知設定
- 投遞流程管理看板
- Email / LINE 通知通道

### 6. 營運與維護

- SQLite 備份 / 還原
- runtime cleanup
- backend status 檢查
- 本地 worker / scheduler / launchd 常駐模式
- Docker Compose / Render 部署

## 技術組成

- 前端與 UI：`Streamlit`
- 資料處理：`pandas`
- HTML 解析：`beautifulsoup4`、`lxml`
- 履歷抽字：`pypdf`、`python-docx`
- AI：`openai`
- 儲存：`SQLite` + `JSON snapshot` + 檔案快取
- 部署：`Docker`、`docker-compose`、`Render`

## 快速開始

### 需求

- Python `3.11+`
- 建議使用虛擬環境
- 若要啟用 AI 功能，需準備 `OPENAI_API_KEY`

### 1. 安裝

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

如果你要啟用 Streamlit 內建 OIDC 登入，再額外安裝：

```bash
source .venv/bin/activate
pip install "streamlit[auth]"
```

### 2. 建立環境設定

```bash
cp .env.example .env
```

`[.env.example](.env.example)` 預設把資料與 runtime 指到：

- `~/.job-radar-runtime`
- `~/.job-radar-data`

如果你只是本地開發，也可以改成專案內路徑，例如：

```env
JOB_SPY_DATA_DIR=./data
```

### 3. 啟動 Web App

```bash
source .venv/bin/activate
streamlit run app.py
```

啟動後預設網址：

```text
http://localhost:8501
```

## 啟動模式

### 只開 Web App

適合 UI 開發、手動操作與單人本地測試。

```bash
source .venv/bin/activate
streamlit run app.py
```

### 本地完整後端堆疊

適合模擬實際運作模式，會同時啟動：

- Streamlit app
- crawl scheduler
- crawl worker

```bash
source .venv/bin/activate
./scripts/start_backend_stack.sh
```

如果你要單獨啟動 worker / scheduler：

```bash
source .venv/bin/activate
./scripts/start_crawl_worker.sh
./scripts/start_crawl_scheduler.sh
```

### Docker Compose

```bash
docker compose up --build
```

`[docker-compose.yml](docker-compose.yml)` 會啟動三個服務：

- `job-radar`
- `job-radar-worker`
- `job-radar-scheduler`

## OIDC 登入設定

如果你要啟用 Google / Facebook 登入：

1. 安裝 `streamlit[auth]`
2. 複製 secrets 範例：

```bash
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
```

3. 填入 `[.streamlit/secrets.example.toml](.streamlit/secrets.example.toml)` 中的 OIDC 設定

目前結構如下：

- `auth.redirect_uri`
- `auth.cookie_secret`
- `auth.google.client_id`
- `auth.google.client_secret`
- `auth.google.server_metadata_url`

如果你要顯示 Facebook 登入按鈕，注意：

- Streamlit 內建登入只支援 **OIDC**
- Facebook 這裡不能直接填原生 OAuth authorize URL
- 實務上通常需要透過 Auth0 / Keycloak / 其他 broker 轉成 OIDC provider

## 常用 CLI / 維運指令

### 一次跑完整抓取

```bash
source .venv/bin/activate
job-spy
job-spy --query "AI工程師" --query "Machine Learning Engineer"
```

### Worker / Scheduler

```bash
source .venv/bin/activate
job-radar-crawl-worker
job-radar-crawl-scheduler
```

### 後端狀態與維護

```bash
source .venv/bin/activate
job-radar-backend-status
job-radar-backend-maintenance
```

或直接使用腳本：

```bash
source .venv/bin/activate
./scripts/run_backend_status.sh
./scripts/run_backend_maintenance.sh
```

### SQLite 備份與還原

建立備份：

```bash
source .venv/bin/activate
job-radar-sqlite-maintenance backup --base-dir .
```

如果要把 runtime DB 一起備份：

```bash
source .venv/bin/activate
job-radar-sqlite-maintenance backup --base-dir . --include-runtime
```

還原：

```bash
source .venv/bin/activate
job-radar-sqlite-maintenance restore --base-dir . --backup data/backups/sqlite/<backup-id> --yes
```

做還原演練：

```bash
source .venv/bin/activate
job-radar-sqlite-restore-drill --base-dir .
```

### LINE Webhook

如果你要啟用 LINE 綁定 / 推播 webhook：

```bash
source .venv/bin/activate
job-radar-line-webhook
```

## 部署

### Docker 單容器

```bash
docker build -t job-radar .
docker run --rm -p 8501:8501 --env-file .env -v "$(pwd)/data:/app/data" job-radar
```

### Docker Compose

```bash
docker compose up --build
```

### Render

專案內已提供 Render Blueprint：

- `[render.yaml](render.yaml)`
- `[Dockerfile](Dockerfile)`
- `[scripts/start_streamlit.sh](scripts/start_streamlit.sh)`

基本流程：

1. 推到 GitHub repository
2. 在 Render 建立 Blueprint
3. 讓 Render 讀取 `[render.yaml](render.yaml)`
4. 補上必要 secret
5. 等待 build 與 deploy 完成

目前 `[render.yaml](render.yaml)` 使用 `free` plan。
如果沒有接 persistent disk，重新部署後下列資料可能消失：

- 已儲存搜尋
- 收藏
- 通知設定
- 帳號資料
- 履歷摘要

建議至少設定：

- `JOB_SPY_DATA_DIR`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`（若需要）
- `JOB_RADAR_SMTP_*`（若需要 Email）
- `JOB_RADAR_LINE_*`（若需要 LINE）
- `JOB_RADAR_PUBLIC_BASE_URL`（若需要對外 webhook / callback）

## 重要環境變數

完整範例請看 `[.env.example](.env.example)`。

### 抓取與分析

- `JOB_SPY_REQUEST_TIMEOUT`
- `JOB_SPY_REQUEST_DELAY`
- `JOB_SPY_MAX_CONCURRENT_REQUESTS`
- `JOB_SPY_MAX_PAGES_PER_SOURCE`
- `JOB_SPY_MAX_DETAIL_JOBS_PER_SOURCE`
- `JOB_SPY_MIN_RELEVANCE_SCORE`
- `JOB_SPY_LOCATION`
- `JOB_SPY_ENABLE_CAKE`
- `JOB_SPY_ENABLE_LINKEDIN`

### 儲存與 runtime

- `JOB_RADAR_RUNTIME_ROOT`
- `JOB_SPY_DATA_DIR`
- `JOB_SPY_CACHE_BACKEND`
- `JOB_SPY_QUEUE_BACKEND`
- `JOB_SPY_DATABASE_BACKEND`
- `JOB_SPY_CRAWL_EXECUTION_MODE`
- `JOB_SPY_ENABLE_BACKEND_CONSOLE`

### AI

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `JOB_SPY_LLM_MODEL`
- `JOB_SPY_TITLE_MODEL`
- `JOB_SPY_EMBEDDING_MODEL`
- `JOB_SPY_ASSISTANT_MODEL`

### 通知

- `JOB_RADAR_SMTP_HOST`
- `JOB_RADAR_SMTP_PORT`
- `JOB_RADAR_SMTP_USERNAME`
- `JOB_RADAR_SMTP_PASSWORD`
- `JOB_RADAR_SMTP_FROM`
- `JOB_RADAR_LINE_CHANNEL_ACCESS_TOKEN`
- `JOB_RADAR_LINE_CHANNEL_SECRET`
- `JOB_RADAR_LINE_TO`
- `JOB_RADAR_PUBLIC_BASE_URL`

## 資料儲存位置

預設資料根目錄由 `JOB_SPY_DATA_DIR` 決定。

重要檔案包括：

- `jobs_latest.json`：最新市場快照
- `snapshots/`：歷史快照
- `cache/`：HTML / detail / search cache
- `product_state.sqlite3`：帳號、收藏、通知、已儲存搜尋、看板
- `user_submissions.sqlite3`：履歷與使用者提交資料
- `query_runtime.sqlite3`：queue / runtime 狀態
- `market_history.sqlite3`：歷史分析資料
- `backups/sqlite/`：SQLite 備份

## 專案結構

```text
.
├── app.py
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── scripts/
├── docs/
├── tests/
└── src/job_spy_tw/
    ├── assistant/          # RAG chunks / retrieval / prompts / service
    ├── connectors/         # 104 / 1111 / Cake / LinkedIn
    ├── market_analysis/    # 技能與工作內容分析
    ├── notifications/      # Email / LINE channel
    ├── resume/             # 履歷抽字 / 匹配 / 評分
    ├── settings/           # env 與 settings loader
    ├── store/              # SQLite repositories
    ├── ui/                 # Streamlit UI、routing、bootstrap、pages、styles
    ├── pipeline.py         # 抓取與快照組裝
    ├── product_store.py    # 產品層 facade
    ├── rag_assistant.py    # AI 助手 facade
    └── resume_analysis.py  # 履歷分析 facade
```

## 測試與驗證

最小 smoke test：

```bash
source .venv/bin/activate
env PYTHONPATH=src .venv/bin/python -c "import app; print('app import ok')"
```

語法檢查：

```bash
source .venv/bin/activate
python -m compileall app.py src/job_spy_tw
```

測試：

```bash
source .venv/bin/activate
python -m unittest discover -s tests -p "test_*.py"
```

## 延伸文件

- `[docs/architecture.md](docs/architecture.md)`：系統分層與資料流
- `[docs/backend_runbook.md](docs/backend_runbook.md)`：本地營運與日常操作
- `[docs/maintenance_guide.md](docs/maintenance_guide.md)`：維護導覽
- `[docs/review_report.md](docs/review_report.md)`：整體評估與風險盤點

## 注意事項

- 各求職網站頁面結構可能變動，connector 需要持續維護
- LinkedIn 公開頁面限制較多，資料穩定度可能不如其他來源
- 掃描型 PDF 履歷若沒有 OCR，抽字品質會受限
- 使用前請自行確認各平台服務條款、robots 與抓取頻率限制
