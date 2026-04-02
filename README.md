# 職缺雷達

職缺雷達是一個面向台灣求職市場的 Streamlit 產品原型。  
它會從 `104`、`1111`、`LinkedIn` 抓公開職缺，拆出原文中的工作內容、技能需求與條件，並把結果整理成：

- 職缺總覽
- 工作內容統計
- 技能地圖
- 履歷匹配
- AI 助理 / RAG 問答
- 追蹤中心 / 通知設定
- 投遞流程管理看板

目前專案已整理成「入口層 + UI 層 + 分析層 + 儲存層」的結構，後續要維修或加功能，不需要再一直往單一大檔裡堆。

## 功能概覽

### 1. 職缺抓取與市場整理

- 多來源抓取：`104`、`1111`、`LinkedIn`
- 追蹤多個目標職缺，支援優先序與關鍵字
- `快速 / 平衡 / 完整` 三種抓取模式
- 職缺原文條目解析：
  - 工作內容
  - 必備技能 / 條件
  - 其他要求
- 低相關職缺過濾，避免污染技能 / 工作內容統計

### 2. 分析與洞察

- 技能地圖：統計技能出現次數、重要度、分類
- 工作內容統計：彙整職缺最常出現的任務與主題
- 來源比較：比較各平台職缺量、角色分布、平均相關度

### 3. 個人化功能

- 履歷上傳或貼文字
- 規則式 / LLM 履歷摘要
- 履歷與職缺匹配
- 缺口分析：
  - 已命中技能
  - 已命中工作內容
  - 建議補強技能
  - 建議補強工作內容

### 4. AI 助理

- 用目前快照資料做 RAG 問答
- 可回答：
  - 優先學習技能
  - 技能缺口
  - 薪資區間
  - 常見工作內容
- 可依履歷或基本資料提供更個人化回答
- 可產生簡短求職報告

### 5. 產品化功能

- 使用者系統：註冊 / 登入 / 忘記密碼
- 每個使用者自己的：
  - 已儲存搜尋
  - 收藏職缺
  - 履歷摘要
  - 通知設定
- 追蹤中心：重跑搜尋、看新職缺通知
- 投遞看板：管理投遞狀態、日期、面試紀錄
- 通知通道：
  - 站內通知
  - Email
  - LINE

## 安裝

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 啟動方式

### Streamlit Web App

```bash
source .venv/bin/activate
streamlit run app.py
```

## 部署

目前我已經把專案整理成可直接用 Docker 部署的版本，核心檔案是：

- [Dockerfile](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/Dockerfile)
- [docker-compose.yml](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docker-compose.yml)
- [start_streamlit.sh](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/scripts/start_streamlit.sh)
- [config.toml](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/.streamlit/config.toml)

### 用 Docker 本機啟動

```bash
docker compose up --build
```

啟動後可從：

```text
http://localhost:8501
```

### 用 Docker 直接跑單容器

```bash
docker build -t job-radar .
docker run --rm -p 8501:8501 --env-file .env -v "$(pwd)/data:/app/data" job-radar
```

### 用 Render 部署

如果你不要再本機常駐跑，這個專案已經準備好 Render Blueprint：

- [render.yaml](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/render.yaml)
- [Dockerfile](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/Dockerfile)
- [start_streamlit.sh](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/scripts/start_streamlit.sh)

上線步驟：

1. 把專案推到 GitHub repository
2. 到 Render 建立 `Blueprint`
3. 選你的 repository
4. Render 會自動讀取 [render.yaml](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/render.yaml)
5. 在 Render 後台補上 secret 環境變數
6. 等待 build 完成後，就會拿到 `onrender.com` 網址

這份設定已經包含：

- Docker Web Service
- `/app/data` persistent disk
- Render 指定的 `PORT`
- 自動部署 `autoDeploy: true`

`JOB_RADAR_PUBLIC_BASE_URL` 在 Render 上通常填：

```text
https://你的服務名稱.onrender.com
```

### 上雲端平台前要注意

- 這個專案會把快照、SQLite、cache 寫到 `JOB_SPY_DATA_DIR`
- 部署到雲端時，建議把 `JOB_SPY_DATA_DIR` 指到有持久化的磁碟
- 如果沒有持久化磁碟，重新部署後：
  - 已儲存搜尋
  - 收藏
  - 通知設定
  - 帳號資料
  - 履歷摘要
  可能會一起消失

### 建議部署環境變數

至少建議設定：

- `JOB_SPY_DATA_DIR`
- `OPENAI_API_KEY`
- `JOB_RADAR_SMTP_HOST`
- `JOB_RADAR_SMTP_USERNAME`
- `JOB_RADAR_SMTP_PASSWORD`
- `JOB_RADAR_SMTP_FROM`

如果要用 LINE：

- `JOB_RADAR_LINE_CHANNEL_ACCESS_TOKEN`
- `JOB_RADAR_LINE_CHANNEL_SECRET`
- `JOB_RADAR_PUBLIC_BASE_URL`

### CLI

```bash
source .venv/bin/activate
job-spy
job-spy --query "AI工程師" --query "Machine Learning Engineer"
```

### LINE Webhook

如果你要啟用 LINE 自動綁定：

```bash
source .venv/bin/activate
job-radar-line-webhook
```

## 環境變數

可以先複製 [`.env.example`](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/.env.example)。

### 抓取設定

- `JOB_SPY_DATA_DIR`
- `JOB_SPY_REQUEST_TIMEOUT`
- `JOB_SPY_REQUEST_DELAY`
- `JOB_SPY_MAX_CONCURRENT_REQUESTS`
- `JOB_SPY_MAX_PAGES_PER_SOURCE`
- `JOB_SPY_MAX_DETAIL_JOBS_PER_SOURCE`
- `JOB_SPY_MIN_RELEVANCE_SCORE`
- `JOB_SPY_LOCATION`
- `JOB_SPY_ENABLE_LINKEDIN`

### OpenAI / AI 助理

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `JOB_SPY_LLM_MODEL`
- `JOB_SPY_TITLE_MODEL`
- `JOB_SPY_EMBEDDING_MODEL`
- `JOB_SPY_ASSISTANT_MODEL`

### Email 通知

- `JOB_RADAR_SMTP_HOST`
- `JOB_RADAR_SMTP_PORT`
- `JOB_RADAR_SMTP_USERNAME`
- `JOB_RADAR_SMTP_PASSWORD`
- `JOB_RADAR_SMTP_FROM`
- `JOB_RADAR_SMTP_USE_TLS`
- `JOB_RADAR_SMTP_USE_SSL`

### LINE 通知 / 綁定

- `JOB_RADAR_LINE_CHANNEL_ACCESS_TOKEN`
- `JOB_RADAR_LINE_CHANNEL_SECRET`
- `JOB_RADAR_LINE_TO`
- `JOB_RADAR_PUBLIC_BASE_URL`
- `JOB_RADAR_LINE_WEBHOOK_HOST`
- `JOB_RADAR_LINE_WEBHOOK_PORT`

## 專案結構

```text
.
├── app.py
├── README.md
├── docs/
│   └── maintenance_guide.md
├── data/
├── tests/
└── src/job_spy_tw/
    ├── assistant/              # RAG chunks / retrieval / prompts / service
    ├── connectors/             # 104 / 1111 / LinkedIn
    ├── market_analysis/        # 技能與工作內容分析
    ├── notifications/          # Email / LINE channel
    ├── resume/                 # 履歷抽字 / 擷取 / 匹配 / 評分
    ├── settings/               # Settings / env / loader
    ├── store/                  # SQLite repositories
    ├── ui/
    │   ├── auth.py
    │   ├── charts.py
    │   ├── common.py
    │   ├── frames.py
    │   ├── page_context.py
    │   ├── pages_market.py
    │   ├── pages_product.py
    │   ├── pages_resume_assistant.py
    │   ├── resources.py
    │   ├── search.py
    │   ├── session.py
    │   └── styles.py
    ├── analysis.py             # facade
    ├── config.py               # facade
    ├── notification_service.py # facade
    ├── product_store.py        # facade
    ├── rag_assistant.py        # facade
    └── resume_analysis.py      # facade
```

## 目前資料儲存

### 快照 / 快取

- [data/jobs_latest.json](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/jobs_latest.json)
- [data/cache](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/cache)

### 使用者與產品狀態

- [data/product_state.sqlite3](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/product_state.sqlite3)
  - 帳號
  - 已儲存搜尋
  - 收藏職缺
  - 通知設定
  - 投遞看板
  - 來訪人次
- [data/user_submissions.sqlite3](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/data/user_submissions.sqlite3)
  - 匿名化履歷分析資料
  - 求職基本資料

## 測試

```bash
source .venv/bin/activate
python -m compileall app.py src/job_spy_tw
python -m unittest discover -s tests
```

## 維護建議

### 要改 UI

優先看：

- [app.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/app.py)
- [pages_market.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/pages_market.py)
- [pages_resume_assistant.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/pages_resume_assistant.py)
- [pages_product.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/pages_product.py)
- [renderers.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/renderers.py)
- [charts.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/charts.py)

### 要改履歷匹配

優先看：

- [service.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/service.py)
- [matchers.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/matchers.py)
- [scoring.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/resume/scoring.py)

### 要改追蹤 / 通知 / 看板

優先看：

- [pages_product.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/ui/pages_product.py)
- [product_store.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/product_store.py)
- [favorites.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/store/favorites.py)
- [notifications.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/store/notifications.py)
- [service.py](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/src/job_spy_tw/notifications/service.py)

## 注意事項

- 求職網站版型可能變動，connector selector 未來仍可能需要調整。
- LinkedIn 對公開頁面限制較多，detail 內容可能不如 104 穩定。
- PDF / DOCX 履歷抽字依賴對應套件與檔案本身品質；掃描版 PDF 可能需要 OCR。
- 使用前請自行確認各平台服務條款、robots 與抓取頻率限制。

## 延伸文件

- 維護導覽：[docs/maintenance_guide.md](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/maintenance_guide.md)
