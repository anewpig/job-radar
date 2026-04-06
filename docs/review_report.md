# 全面評估報告

這份報告分成四個視角：

- 使用者視角
- 工程視角
- 資料視角
- 產品視角

## 1. 使用者視角

### 優點

1. 求職流程集中
   - 同時覆蓋搜尋、分析、履歷匹配、AI 問答、追蹤、投遞
   - 使用者不需要在不同網站和工具間來回切換

2. 首屏價值清楚
   - hero 已經能直接說清楚產品定位
   - `Search Setup` 與 CTA 都能快速理解用途

3. 主要頁面已經產品化
   - `職缺總覽`
   - `搜尋設定`
   - `追蹤中心`
   - `投遞看板`
   - `通知設定`

4. 抓取速度體感已有改善
   - staged crawl 讓使用者先看到職缺列表
   - 不必等所有 detail enrich 完成

### 缺點

1. 資訊密度仍偏高
   - 功能很多，第一次進來的人還是需要適應
   - 即使 UI 已重整，整體仍接近 power-user 工具

2. AI 助理入口與主導航並存
   - 目前同時有主頁切換與浮動入口
   - 對一般使用者來說，互動模型仍有點重疊

3. 搜尋設定仍有隱性複雜度
   - `更新模式 / 快取 / 強制更新`
   - 這些概念對一般使用者不一定直覺

4. 分析頁與工作流的連接仍可再強化
   - 使用者看到技能/工作內容後，下一步推薦不夠明顯

### 建議

1. 增加首次使用導引
2. 在分析頁加入明確下一步 CTA
3. 對技術名詞做更強的白話轉譯

## 2. 工程視角

### 優點

1. 模組化方向正確
   - UI、store、resume、assistant、notifications、connectors 已基本分層

2. facade 相容策略合理
   - `resume_analysis.py`
   - `product_store.py`
   - `analysis.py`
   - `config.py`
   - `notification_service.py`
   都保留相容入口，避免大面積 import 震盪

3. staged crawl 架構有明確邏輯邊界
   - `collect_jobs()`
   - `finalize_snapshot()`
   - 比舊的單一同步 `run()` 更可維護

4. UI 样式已开始去耦
   - `styles.py` 不再是单一超大 CSS 文本
   - style fragment 化已经建立方向

### 缺點

1. `app.py` 仍然过重
   - 仍承担 too much orchestration
   - staged crawl state machine 仍集中在入口层

2. UI page module 仍偏大
   - `pages_product.py`
   - `pages_market.py`
   - `pages_resume_assistant.py`
   依然是维护热点

3. session_state 复杂度高
   - Streamlit 天生会导致 UI state / feature state 混杂
   - 当前已整理，但复杂度仍高于传统前后端分离结构

4. 历史相容字段仍残留
   - 例如 search row 内部仍带 `priority`
   - UI 已隐藏，但模型仍隐性依赖

### 建議

1. 再拆 page module
2. 把 crawl orchestration 從 `app.py` 抽出
3. 逐步移除 UI 已不再暴露的 legacy state

## 3. 資料視角

### 優點

1. 已有明確 snapshot 心智模型
   - `MarketSnapshot` 是目前最重要的資料交換物件

2. 已做結構化整理
   - 工作內容
   - 技能需求
   - 其他條件
   - 履歷匹配結果

3. 下載功能完整
   - jobs
   - skills
   - tasks
   - resume matches
   - bundle export

4. staged crawl 對資料狀態更可觀測
   - partial snapshot
   - finalized snapshot
   邊界比以前清楚

### 缺點

1. partial snapshot 與 final snapshot 的語意仍需小心
   - 若後續開發者不理解 staged 機制，容易混用半成品資料

2. 統計仍高度依賴 detail enrich 完整度
   - detail 未補齊時，skill/task insights 就不能穩定代表全貌

3. 缺少 TTL cache 與 freshness policy
   - 現在仍是 `快取 / 強制更新` 二分
   - 缺少資料新鮮度層級

4. 多來源欄位標準化仍可再強化
   - 公司名
   - 地點
   - 薪資
   - posted time

### 建議

1. 引入 cache TTL
2. 補欄位標準化規則
3. 在 partial snapshot 明確標記統計不可用狀態

## 4. 產品視角

### 優點

1. 產品主軸清楚
   - 「把多個求職平台內容統整成一個工作台」
   - 這個定位是成立的

2. 功能鏈接完整
   - 搜尋
   - 分析
   - 履歷匹配
   - AI 問答
   - 收藏/通知
   - 投遞管理

3. 差異化明顯
   - 不只是單純職缺聚合
   - 有履歷匹配與 AI 層

4. 已具備內建留存機制
   - 搜尋保存
   - 通知
   - 投遞看板

### 缺點

1. 功能邊界開始接近過寬
   - 若再持續加功能，容易失焦
   - 核心主線需要持續收斂

2. 目前 still prototype-ish
   - 雖然 UI 已產品化很多，但整體仍有工具感

3. 公開測試前還缺 onboarding
   - 首次用戶仍可能不清楚先做什麼

4. 通知與登入等產品能力已存在，但信任感建設還不足
   - 例如資料保存範圍、更新節奏、通知時機，需要更明確說明

### 建議

1. 維持主軸，不再擴張功能面
2. 優先打磨 onboarding、分析頁下一步、資料更新心智模型
3. 把「找到工作」工作流做得更順，而不是再加新分支

## 5. 總結

### 目前最強的地方

- 產品主線成立
- 功能串接完整
- 架構已開始從單體大檔走向可維護模組
- staged crawl 已明顯改善體感

### 目前最大的風險

- 入口層與大頁模組仍偏重
- UI state 與 feature state 仍容易糾纏
- 資料 freshness / partial-finalized snapshot 邊界需要持續守住

### 接下來最值得做的 3 件事

1. 再拆 `pages_product.py` 和 `pages_resume_assistant.py`
2. 將 crawl orchestration 從 `app.py` 抽出
3. 補 onboarding 與分析頁的下一步 CTA
