# 維護指南

這份文件是給後續維修與擴充功能時快速定位用的。

延伸文件：

- [系統架構](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/architecture.md)
- [後端營運 Runbook](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/backend_runbook.md)
- [全面評估報告](/Users/zhuangcaizhen/Desktop/專案/職缺爬蟲/docs/review_report.md)

## 模組分層

### 1. 入口層

- `app.py` 
  - Streamlit 主入口
  - 只保留頁面流程、session state、頁籤切換與各服務串接
  - 不再承擔大量 UI helper 或資料轉換邏輯

  #筆記 app.py
  - 把畫面跑起來
  - 控制頁面流程
  - 管理目前使用者的狀態
  - 決定現在要顯示哪個頁面或哪個功能區塊
  - 串接後面的服務模組
  - 負責把 UI 和後端功能接起來

  #Streamlit 主入口
  - 設定頁面標題、icon、layout
  - 初始化 session state
  - 建立 sidebar 或主畫面導航
  - 決定使用者目前在哪個頁面
  - 呼叫其他模組來顯示內容


### 2. UI 層

- `src/job_spy_tw/ui/session.py`
  - `session_state` 初始化與同步
  - 通知偏好套用
  - 主頁籤切換
  - 快照 DataFrame 快取

  #筆記
  - 畫面目前切到哪裡
  - 使用者剛剛按了什麼
  - 哪些資料已經載入過
  - 哪些快取資料先留著不要重算

- `src/job_spy_tw/ui/resources.py`
  - Streamlit resource cache
  - `ProductStore` / `UserDataStore` / `NotificationService` / `RAG assistant` factory
- `src/job_spy_tw/ui/auth.py`
  - 右上角登入、註冊、忘記密碼 popover
- `src/job_spy_tw/ui/page_context.py`
  - 各頁面共用的 context dataclass
- `src/job_spy_tw/ui/pages_market.py`
  - 職缺總覽、工作內容統計、技能地圖、來源比較、下載資料
- `src/job_spy_tw/ui/pages_resume_assistant.py`
  - 履歷匹配、AI 助理
- `src/job_spy_tw/ui/pages_product.py`
  - 追蹤中心、投遞看板、通知設定
- `src/job_spy_tw/ui/styles.py`
  - 全域 CSS 與視覺樣式
- `src/job_spy_tw/ui/common.py`
  - 共用格式化、匯出、輔助組裝
- `src/job_spy_tw/ui/frames.py`
  - `JobListing` / `ResumeJobMatch` 等資料轉 DataFrame
- `src/job_spy_tw/ui/search.py`
  - 搜尋設定區、列資料整理與搜尋名稱建議
- `src/job_spy_tw/ui/renderers.py`
  - 各種卡片、區塊與畫面元件
- `src/job_spy_tw/ui/charts.py`
  - 圖表渲染邏輯

### 3. 履歷分析層

- `src/job_spy_tw/resume_analysis.py`
  - 相容入口
  - 對外仍維持原本匯入方式
- `src/job_spy_tw/resume/text.py`
  - 履歷抽字、個資遮罩、關鍵字清洗、文字安全處理
- `src/job_spy_tw/resume/extractors.py`
  - 規則式履歷擷取器
  - OpenAI 履歷擷取器
- `src/job_spy_tw/resume/matchers.py`
  - 規則式職缺匹配
  - OpenAI + embedding 職缺匹配
- `src/job_spy_tw/resume/scoring.py`
  - 分數權重、相似度與缺口摘要工具
- `src/job_spy_tw/resume/service.py`
  - 對外服務層
  - 負責 fallback 與 LLM / 規則切換
- `src/job_spy_tw/resume/schemas.py`
  - OpenAI / Pydantic 結構化輸出 schema

### 4. 產品狀態儲存層

- `src/job_spy_tw/product_store.py`
  - 相容 facade
  - 對外仍維持 `ProductStore`
- `src/job_spy_tw/store/database.py`
  - SQLite schema 與 migration-like 補欄位
- `src/job_spy_tw/store/saved_searches.py`
  - 已儲存搜尋條件與新職缺同步
- `src/job_spy_tw/store/favorites.py`
  - 收藏職缺與投遞狀態
- `src/job_spy_tw/store/notifications.py`
  - 通知偏好、通知紀錄、LINE 綁定碼
- `src/job_spy_tw/store/common.py`
  - 共用序列化、簽章、時間與 row mapping

### 5. 核心業務層

- `src/job_spy_tw/pipeline.py`
  - 搜尋、補抓 detail、去重、分析、儲存快照
- `src/job_spy_tw/analysis.py`
  - 相容入口
- `src/job_spy_tw/market_analysis/taxonomies.py`
  - 技能、工作內容、角色別名規則
- `src/job_spy_tw/market_analysis/analyzer.py`
  - 技能抽取、角色分析、技能與工作內容統計
- `src/job_spy_tw/rag_assistant.py`
  - 相容入口
- `src/job_spy_tw/assistant/models.py`
  - RAG 知識片段資料模型
  #筆記
  - 這段資料的 id 是什麼
  - 來源是哪裡
  - 標籤是什麼
  - 文字內容是什麼
  - 原始網址是什麼
  - 還有哪些額外資訊

- `src/job_spy_tw/assistant/chunks.py`
  - 將職缺、技能統計、工作內容統計、履歷轉成知識片段

  
- `src/job_spy_tw/assistant/retrieval.py`
  - embedding 檢索與快取
- `src/job_spy_tw/assistant/prompts.py`
  - AI 助理回答 prompt
- `src/job_spy_tw/assistant/service.py`
  - RAG 問答與報告生成服務
- `src/job_spy_tw/notification_service.py`
  - Email / LINE 發送
- `src/job_spy_tw/line_webhook.py`
  - LINE webhook 與綁定入口

### 6. 資料模型與設定

- `src/job_spy_tw/models.py`
  - dataclass / model 定義
- `src/job_spy_tw/config.py`
  - 相容入口
- `src/job_spy_tw/settings/env.py`
  - `.env` 載入與布林環境變數處理
- `src/job_spy_tw/settings/models.py`
  - `Settings` dataclass
- `src/job_spy_tw/settings/loader.py`
  - 執行設定組裝與預設值

### 7. 通知服務層

- `src/job_spy_tw/notification_service.py`
  - 相容入口
- `src/job_spy_tw/notifications/message_builder.py`
  - 通知文案、收件者整理、LINE target 驗證
- `src/job_spy_tw/notifications/email_channel.py`
  - SMTP 發送
- `src/job_spy_tw/notifications/line_channel.py`
  - LINE API request 與 SSL fallback 判斷
- `src/job_spy_tw/notifications/service.py`
  - Email / LINE 推播協調器

## 常見修改入口

### 改 UI 排版

優先看：

- `app.py`
- `src/job_spy_tw/ui/pages_market.py`
- `src/job_spy_tw/ui/pages_resume_assistant.py`
- `src/job_spy_tw/ui/pages_product.py`
- `src/job_spy_tw/ui/renderers.py`
- `src/job_spy_tw/ui/charts.py`
- `src/job_spy_tw/ui/styles.py`

### 改搜尋設定或自動推薦關鍵字

優先看：

- `src/job_spy_tw/ui/search.py`
- `src/job_spy_tw/search_keyword_recommender.py`
- `src/job_spy_tw/targets.py`

### 改履歷匹配邏輯

優先看：

- `src/job_spy_tw/resume/scoring.py`
- `src/job_spy_tw/resume/matchers.py`
- `src/job_spy_tw/resume/service.py`

### 改技能分析 / 工作內容統計 / 角色匹配

優先看：

- `src/job_spy_tw/market_analysis/taxonomies.py`
- `src/job_spy_tw/market_analysis/analyzer.py`

### 改履歷抽字或個資清洗

優先看：

- `src/job_spy_tw/resume/text.py`
- `src/job_spy_tw/resume/extractors.py`

### 改 AI 助理 / RAG / 報告生成

優先看：

- `src/job_spy_tw/assistant/chunks.py`
- `src/job_spy_tw/assistant/retrieval.py`
- `src/job_spy_tw/assistant/prompts.py`
- `src/job_spy_tw/assistant/service.py`

### 改追蹤中心 / 收藏 / 通知 / 投遞看板

優先看：

- `src/job_spy_tw/ui/pages_product.py`
- `src/job_spy_tw/product_store.py`
- `src/job_spy_tw/store/favorites.py`
- `src/job_spy_tw/store/notifications.py`
- `src/job_spy_tw/store/saved_searches.py`
- `src/job_spy_tw/notifications/service.py`

### 改爬蟲平台

優先看：

- `src/job_spy_tw/connectors/site_104.py`
- `src/job_spy_tw/connectors/site_1111.py`
- `src/job_spy_tw/connectors/linkedin.py`
- `src/job_spy_tw/pipeline.py`

### 改環境變數 / 啟動設定 / 路徑

優先看：

- `src/job_spy_tw/settings/models.py`
- `src/job_spy_tw/settings/loader.py`
- `src/job_spy_tw/settings/env.py`

## 相容原則

目前有兩個刻意保留的相容入口：

- `src/job_spy_tw/resume_analysis.py`
- `src/job_spy_tw/product_store.py`

如果後續還要拆模組，建議先維持這兩個 facade 不動，讓 `app.py`、tests、其他服務不必一起改。

## 維修建議

1. 新功能先決定落在哪一層，再寫程式，不要直接塞回 `app.py`
2. 新頁面優先拆進 `src/job_spy_tw/ui/pages_*.py`
3. 任何需要持久化的功能，優先拆到 `src/job_spy_tw/store/`
4. 履歷與匹配邏輯，優先放進 `src/job_spy_tw/resume/`
5. `session_state` 與 service factory 優先放進 `src/job_spy_tw/ui/session.py` / `src/job_spy_tw/ui/resources.py`
6. 保留 facade，避免大面積 import 震盪

## 驗證指令

```bash
source .venv/bin/activate
python -m compileall app.py src/job_spy_tw
python -m unittest discover -s tests
```

## 這次整理後的重點

- `app.py` 已降到以頁面流程為主
- `app.py` 現在主要負責：搜尋設定、爬取流程、快照摘要、頁面 dispatch
- UI 頁面已拆成 `pages_market.py`、`pages_resume_assistant.py`、`pages_product.py`
- session / auth / resource 初始化已拆成 `session.py`、`auth.py`、`resources.py`
- `resume_analysis.py` 改成 facade，履歷分析拆成 6 個子模組
- `product_store.py` 改成 facade，資料儲存拆成 4 個責任模組
- `analysis.py` 改成 facade，市場分析拆成 taxonomy + analyzer
- `rag_assistant.py` 改成 facade，AI 助理拆成 chunk / retrieval / prompt / service
- `config.py` 改成 facade，設定拆成 env / models / loader
- `notification_service.py` 改成 facade，通知拆成 message / email / line / service
- 之後維護可以先從 `docs/maintenance_guide.md` 找入口，再進對應模組
