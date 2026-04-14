"""Helpers and data assembly for the full system architecture page."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sqlite3

from ..storage import load_snapshot
from .page_context import PageContext


@dataclass(slots=True)
class OverviewMetric:
    label: str
    value: str
    detail: str


@dataclass(slots=True)
class TopologyCluster:
    icon: str
    title: str
    summary: str
    items: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ComponentSpec:
    icon: str
    title: str
    subtitle: str
    why: str
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    scaling: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FlowSpec:
    title: str
    description: str
    nodes: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class StoreSpec:
    icon: str
    title: str
    location: str
    purpose: str
    why: str
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    scaling: list[str] = field(default_factory=list)
    facts: list[tuple[str, str]] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExpansionSpec:
    title: str
    stage: str
    why: str
    actions: list[str] = field(default_factory=list)
    tradeoffs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BackendArchitectureData:
    overview_intro: str
    overview_metrics: list[OverviewMetric]
    topology_clusters: list[TopologyCluster]
    frontend_components: list[ComponentSpec]
    backend_components: list[ComponentSpec]
    ai_components: list[ComponentSpec]
    store_specs: list[StoreSpec]
    flow_specs: list[FlowSpec]
    expansion_specs: list[ExpansionSpec]
    runtime_cards: list[tuple[str, list[tuple[str, str]]]]
    storage_rows: list[tuple[str, str]]
    product_tables: list[str]
    user_tables: list[str]
    query_tables: list[str]
    history_tables: list[str]


def parse_iso(value: str) -> datetime | None:
    """Parse an ISO timestamp with a safe fallback."""
    try:
        return datetime.fromisoformat(str(value).strip())
    except Exception:  # noqa: BLE001
        return None


def format_relative_time(value: str) -> str:
    """Format a timestamp into a relative label."""
    parsed = parse_iso(value)
    if parsed is None:
        return "尚未建立"
    delta = datetime.now() - parsed
    seconds = max(0, int(delta.total_seconds()))
    if seconds < 60:
        return f"{seconds} 秒前"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} 分鐘前"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} 小時前"
    days = hours // 24
    return f"{days} 天前"


def format_timestamp(value: str) -> str:
    """Format a timestamp into an absolute label."""
    parsed = parse_iso(value)
    if parsed is None:
        return "尚未建立"
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def format_size(path: Path) -> str:
    """Format a file size for display."""
    if not path.exists() or not path.is_file():
        return "0 B"
    size = path.stat().st_size
    units = ["B", "KB", "MB", "GB"]
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    """Return whether a SQLite table exists."""
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return bool(row)


def count_rows(db_path: Path, table_name: str) -> int | None:
    """Count rows for a SQLite table if it exists."""
    if not db_path.exists():
        return None
    try:
        with sqlite3.connect(db_path) as connection:
            if not table_exists(connection, table_name):
                return None
            row = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    except sqlite3.Error:
        return None
    return int(row[0]) if row else 0


def collect_tables(db_path: Path) -> list[str]:
    """Collect SQLite table names from one database."""
    if not db_path.exists():
        return []
    try:
        with sqlite3.connect(db_path) as connection:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            ).fetchall()
    except sqlite3.Error:
        return []
    return [str(row[0]) for row in rows]


def count_snapshot_files(snapshot_dir: Path) -> int:
    """Count materialized snapshot json files."""
    if not snapshot_dir.exists():
        return 0
    return sum(1 for path in snapshot_dir.glob("*.json") if path.is_file())


def load_effective_snapshot(ctx: PageContext):
    """Resolve the currently effective snapshot for architecture inspection."""
    if ctx.snapshot.generated_at:
        return ctx.snapshot
    return load_snapshot(ctx.settings.snapshot_path)


def _display_count(value: int | None) -> str:
    if value is None:
        return "尚未建立"
    return f"{int(value):,}"


def _status_label(enabled: bool) -> str:
    return "已設定" if enabled else "未設定"


def _short_signature(value: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        return "尚未建立"
    if len(cleaned) <= 18:
        return cleaned
    return f"{cleaned[:12]}...{cleaned[-4:]}"


def build_backend_architecture_data(ctx: PageContext) -> BackendArchitectureData:
    """Build the current system architecture website data from live project state."""
    snapshot = load_effective_snapshot(ctx)
    snapshot_generated_at = snapshot.generated_at if snapshot is not None else ""
    snapshot_job_count = len(snapshot.jobs) if snapshot is not None else 0
    snapshot_skill_count = len(snapshot.skills) if snapshot is not None else 0
    snapshot_task_count = len(snapshot.task_insights) if snapshot is not None else 0
    snapshot_error_count = len(snapshot.errors) if snapshot is not None else 0

    product_db_path = ctx.settings.product_state_db_path
    user_db_path = ctx.settings.user_data_db_path
    query_db_path = ctx.settings.query_state_db_path
    history_db_path = ctx.settings.market_history_db_path
    snapshot_path = ctx.settings.snapshot_path
    snapshot_store_dir = ctx.settings.snapshot_store_dir
    cache_dir = ctx.settings.cache_dir

    product_counts = {
        "users": count_rows(product_db_path, "users"),
        "saved_searches": count_rows(product_db_path, "saved_searches"),
        "favorite_jobs": count_rows(product_db_path, "favorite_jobs"),
        "job_notifications": count_rows(product_db_path, "job_notifications"),
        "ai_monitoring_events": count_rows(product_db_path, "ai_monitoring_events"),
        "user_resume_profiles": count_rows(product_db_path, "user_resume_profiles"),
    }
    user_submission_count = count_rows(user_db_path, "user_submissions")
    query_runtime_counts = {
        "query_snapshots": count_rows(query_db_path, "query_snapshots"),
        "crawl_jobs": count_rows(query_db_path, "crawl_jobs"),
        "runtime_signals": count_rows(query_db_path, "runtime_signals"),
    }
    history_counts = {
        "crawl_runs": count_rows(history_db_path, "crawl_runs"),
        "job_posts": count_rows(history_db_path, "job_posts"),
        "crawl_run_jobs": count_rows(history_db_path, "crawl_run_jobs"),
    }

    product_tables = collect_tables(product_db_path)
    user_tables = collect_tables(user_db_path)
    query_tables = collect_tables(query_db_path)
    history_tables = collect_tables(history_db_path)

    connectors = ["104", "1111"]
    if ctx.settings.enable_cake:
        connectors.append("Cake")
    if ctx.settings.enable_linkedin:
        connectors.append("LinkedIn")

    execution_mode = str(ctx.settings.crawl_execution_mode).strip().lower() or "inline"
    runtime_mode_label = (
        "background worker + queue"
        if execution_mode == "worker"
        else "inline crawl + fragment finalize"
    )

    overview_intro = (
        "這頁不是抽象白板，而是直接根據你現在這個專案的實作整理出來的系統網站。"
        " 目前前端是 Streamlit 工作台，後端是 Python 模組化單體；抓取鏈採 cache-first + staged crawl；"
        " AI 分成履歷分析與 RAG 助理兩條能力線；資料層以 4 份 SQLite 搭配 JSON snapshot / cache 落地。"
    )

    overview_metrics = [
        OverviewMetric(
            label="前端形態",
            value="Streamlit 工作台",
            detail="app.py + session_state + thin page orchestrators",
        ),
        OverviewMetric(
            label="後端形態",
            value="Python 模組化單體",
            detail=f"service / pipeline / store 分層；目前模式 {runtime_mode_label}",
        ),
        OverviewMetric(
            label="AI 能力",
            value="履歷分析 + RAG 助理",
            detail=(
                "OpenAI 已設定"
                if bool(ctx.settings.openai_api_key)
                else "未設定 OpenAI 時會退回 rule-based / disabled flow"
            ),
        ),
        OverviewMetric(
            label="持久化主體",
            value="4 SQLite + JSON",
            detail="product_state / user_submissions / query_runtime / market_history + snapshots",
        ),
        OverviewMetric(
            label="來源整合",
            value=f"{len(connectors)} 個來源",
            detail=" / ".join(connectors),
        ),
        OverviewMetric(
            label="最近快照",
            value=format_relative_time(snapshot_generated_at),
            detail=(
                f"{format_timestamp(snapshot_generated_at)}｜"
                f"{snapshot_job_count} jobs / {snapshot_skill_count} skills / {snapshot_task_count} tasks"
            ),
        ),
        OverviewMetric(
            label="追蹤搜尋",
            value=_display_count(product_counts["saved_searches"]),
            detail=f"目前登入使用者可見 {len(ctx.saved_searches)} 組 saved search",
        ),
        OverviewMetric(
            label="Runtime Registry",
            value=_display_count(query_runtime_counts["query_snapshots"]),
            detail=(
                f"crawl_jobs {_display_count(query_runtime_counts['crawl_jobs'])}｜"
                f"runtime_signals {_display_count(query_runtime_counts['runtime_signals'])}"
            ),
        ),
    ]

    topology_clusters = [
        TopologyCluster(
            icon="UI",
            title="使用者與互動入口",
            summary="瀏覽器端只是一個 Streamlit front，但互動密度很高，所有工作台能力都從這裡進入。",
            items=[
                "搜尋設定 / Hero / 主頁籤",
                "登入 dialog / 第三方登入",
                "AI launcher / 漢堡 drawer",
                "追蹤中心 / 看板 / 通知頁",
            ],
        ),
        TopologyCluster(
            icon="APP",
            title="UI 協調層",
            summary="這層負責 bootstrap、session 恢復、PageContext 組裝，以及把頁面行為 dispatch 到 service。",
            items=[
                "app.py / bootstrap_*",
                "router_* / navigation_*",
                "context_builder / session_*",
                "search_setup_* / crawl_runtime_*",
            ],
        ),
        TopologyCluster(
            icon="SVC",
            title="核心服務層",
            summary="真正的業務能力集中在 crawl、resume、assistant、notification 等 service / pipeline。",
            items=[
                "crawl_application_service.py",
                "pipeline.py + connectors/*",
                "resume/service.py",
                "assistant/service.py",
                "notifications/service.py",
            ],
        ),
        TopologyCluster(
            icon="DB",
            title="持久化與背景執行",
            summary="產品狀態、queue runtime、歷史快照與排程 worker 都落在本機檔案與 SQLite。",
            items=[
                "product_state.sqlite3",
                "query_runtime.sqlite3",
                "market_history.sqlite3",
                "jobs_latest.json / snapshots/",
                "crawl_scheduler.py / crawl_worker.py",
            ],
        ),
        TopologyCluster(
            icon="EXT",
            title="外部系統",
            summary="抓取來源、LLM 與通知通道都被隔離在 adapter 邊界，不直接滲進 UI。",
            items=[
                "104 / 1111 / Cake / LinkedIn",
                "OpenAI Responses / Embeddings",
                "SMTP Email",
                "LINE Bot / LINE webhook",
            ],
        ),
    ]

    frontend_components = [
        ComponentSpec(
            icon="UI",
            title="App Shell 與 Session State",
            subtitle="以 Streamlit rerun 模型承接整個求職工作台",
            why=(
                "你現在這個產品最重要的是把搜尋、快照、履歷、AI、追蹤與通知放進同一個工作台；"
                " Streamlit 讓 Python 可以直接碰到 UI，而 `st.session_state` 則承接目前使用者、目前快照、"
                "crawl phase、launcher 狀態與頁面切換。"
            ),
            pros=[
                "Python 端一路到底，不需要先建 API 才能把產品跑起來。",
                "同一份市場快照可以直接在多頁共享，不用做額外序列化。",
                "原型迭代速度快，對單人或小團隊非常有效。",
            ],
            cons=[
                "UI render order 與 state key 命名會直接影響行為，心智負擔偏高。",
                "頁面層與應用流程仍有耦合，不像 API server 那樣自然分界。",
                "多人高併發或跨裝置同步時，session 模型很快會碰到邊界。",
            ],
            alternatives=[
                "React / Next.js + FastAPI 或 Flask 作為正式前後端分離架構。",
                "保留 Streamlit 作為內部工作台，但把寫入行為全部改成 API service。",
                "用更明確的 command / query 分離減少 session mutation。"
            ],
            scaling=[
                "持續收斂 session schema，讓所有 key 由 session_defaults / helpers 接管。",
                "把 page 變成純 orchestrator，真正 mutation 全數下沉到 service。",
                "未來若拆前後端，先保留 PageContext 對應的 DTO 契約。"
            ],
            modules=["app.py", "ui/bootstrap_*", "ui/session_*", "ui/context_builder.py"],
        ),
        ComponentSpec(
            icon="NAV",
            title="導航與頁面組裝",
            subtitle="router / navigation / pages_* 讓每頁變成薄 orchestrator",
            why=(
                "你已經做了大量 UI refactor，現在每頁多半只負責決定順序與上下文，真正的 section / action 被拆到子模組。"
                " 這讓產品工作台維持單體，但不必再讓任何一個 page 檔案扛 800~1000 行。"
            ),
            pros=[
                "頁面責任邊界清楚，改單一功能不容易牽動整頁。",
                "router / navigation / page surface 可以獨立演進。",
                "dev annotation 與 visual shell 也比較容易一致化。",
            ],
            cons=[
                "模組數變多後，新人閱讀專案會需要先理解 dispatch 結構。",
                "Streamlit 仍然依賴 render 順序，沒有真正 component tree 的生命週期。",
                "UI 測試若沒補上，拆檔只會改善可讀性，不會自動帶來回歸保證。",
            ],
            alternatives=[
                "改用 Streamlit multipage，把很多頁面拆成真正獨立路由。",
                "移到前端 SPA，讓導航與狀態交給前端框架。",
                "維持單檔 page，但導入更嚴格的 section convention。"
            ],
            scaling=[
                "替頁面入口與 router 補 smoke / navigation tests。",
                "把 page metadata 繼續集中在 registry，而不是散在多處。",
                "若未來做前端化，這層最先可以被替換掉。"
            ],
            modules=["ui/router_*", "ui/navigation_*", "ui/pages_*", "ui/page_context.py"],
        ),
        ComponentSpec(
            icon="UX",
            title="搜尋工作台與 Staged Feedback",
            subtitle="search_setup + crawl_runtime + hero 共同形成主要互動閉環",
            why=(
                "這個產品的核心不是表單送出後等很久，而是讓使用者先看到 partial snapshot，再慢慢補完 analysis。"
                " 因此搜尋設定、狀態提示與後續 finalize 被刻意設計成 staged feedback，而不是一次 blocking。"
            ),
            pros=[
                "第一屏結果更快可見，使用者不會等到所有 detail enrich 才有畫面。",
                "同一份 snapshot 會驅動總覽、技能、履歷匹配與 AI 助理。",
                "cache-first 讓相同查詢可以直接吃快照，不必每次都重抓。",
            ],
            cons=[
                "partial / final 兩種狀態讓 session sync 與 UI 行為更複雜。",
                "inline 模式下 finalize 仍由 UI fragment 推進，不是完全獨立背景任務。",
                "要做到真正即時 push 更新，現有 Streamlit fragment 模型還是不夠自然。",
            ],
            alternatives=[
                "把 UI 改成 enqueue-only，再做獨立的 job status 頁。",
                "用 websocket / SSE 推送進度，而不是輪詢 fragment。",
                "直接 blocking 到 final snapshot，犧牲體感換流程單純。"
            ],
            scaling=[
                "如果 worker 會常態開啟，就逐步讓 UI 只負責 enqueue 與 poll。",
                "為 partial / ready / stale / failed 狀態建立正式 state diagram。",
                "把 crawl progress 轉成可重用的站內通知或 status center。"
            ],
            modules=["ui/search_setup_*", "ui/crawl_runtime_*", "ui/search.py", "ui/common_hero.py"],
        ),
    ]

    backend_components = [
        ComponentSpec(
            icon="BOOT",
            title="Bootstrap 與 Resource Factory",
            subtitle="先建立 settings / store / service，再開始畫 UI",
            why=(
                "`bootstrap_runtime()` 會先同步 auth secrets、載入 settings、跑 runtime cleanup，"
                "然後建出 ProductStore、UserDataStore、NotificationService 與 guest user。"
                " 這種做法把整個 app 每輪 render 需要的生命週期物件集中在一個入口。"
            ),
            pros=[
                "service 建立點單一，方便統一接 settings 與 cache_resource。",
                "app.py 不需要知道每個 store / client 的初始化細節。",
                "guest session、visit count、notification state 可在 bootstrap 後統一恢復。",
            ],
            cons=[
                "如果 bootstrap 再膨脹，容易變成新的 god module。",
                "目前仍是 UI 啟動時建立，不是獨立 application container。",
                "要做多環境依賴切換時，仍需小心 Streamlit cache/resource 行為。",
            ],
            alternatives=[
                "顯式 dependency injection container。",
                "FastAPI lifespan / service registry。",
                "每個 page 各自 lazy-load，但那會重複依賴管理。"
            ],
            scaling=[
                "保持 bootstrap 只做 wiring，不把 domain logic 放進去。",
                "把 service provider 集中到 resources / factories。",
                "未來若拆 API server，bootstrap 是最容易搬過去的一層。"
            ],
            modules=["ui/bootstrap_*", "ui/resources.py", "settings/*"],
        ),
        ComponentSpec(
            icon="CRAWL",
            title="Crawl Application Service",
            subtitle="cache-first query runtime、queue payload、saved-search sync 的總協調層",
            why=(
                "`crawl_application_service.py` 負責 build queries、啟動 crawl、同步 saved search、排程 due search、"
                "queue polling 與 finalize batch。這層的目的就是讓 UI 不要直接碰 queue / snapshot registry / notification 的細節。"
            ),
            pros=[
                "inline 與 worker 兩種模式共用同一套 use-case 流程。",
                "saved search refresh、query signature、queue payload 都集中處理。",
                "對 UI 來說只剩 start / poll / finalize / sync 幾個抽象動作。",
            ],
            cons=[
                "這層目前仍然很大，跨了 crawl、queue、saved search、notification。",
                "還不是明確 command handler / event handler 的拆法。",
                "若後續再擴充更多排程策略，這裡仍有膨脹風險。",
            ],
            alternatives=[
                "按 use case 拆成 start-crawl / sync-search / schedule-refresh commands。",
                "改成 event-driven：crawl completed event 再觸發 sync / notify。",
                "把 scheduler / worker 邏輯收進獨立 runtime service。"
            ],
            scaling=[
                "下一步可把 queue/snapshot use cases 再拆成 command modules。",
                "把 saved-search sync 與 notification 轉為 completion hook 或 domain event。",
                "若上雲端，這層會是最適合放進 API / worker shared package 的地方。"
            ],
            modules=["crawl_application_service.py", "ui/crawl_runtime_flow.py", "crawl_tuning.py"],
        ),
        ComponentSpec(
            icon="PIPE",
            title="JobMarketPipeline 與 Connectors",
            subtitle="先搜首波、先給 partial，再補頁次與 detail enrich",
            why=(
                "`JobMarketPipeline` 把抓取拆成 initial wave、remaining waves、detail enrich、complete snapshot。"
                " 各來源以 connector adapter 實作，讓 104 / 1111 / Cake / LinkedIn 的差異被局部化。"
            ),
            pros=[
                "首波可見結果快，使用者先看到可用列表。",
                "每個來源有自己的 search/detail parsing 與 rate control。",
                "分析器只吃共用 `JobListing`，不必知道來源 HTML 長什麼樣。",
            ],
            cons=[
                "HTML scraper 天生脆弱，來源變版就要修 parser。",
                "目前還是 thread-based in-process concurrency，不是分散式抓取。",
                "detail enrich 的成本與品質受來源結構限制很大。",
            ],
            alternatives=[
                "改用 Playwright/Browser automation 提高穩定度。",
                "以 raw HTML archive + typed parser pipeline 做更正式 ETL。",
                "把 connector 拆成獨立 worker 或外部抓取服務。"
            ],
            scaling=[
                "做 per-source rate limiter、錯誤分類與 fallback parser。",
                "將 raw response / normalized payload 分層存檔，方便回放與 debug。",
                "如果來源量變大，再把 connector execution 從 app process 抽離。"
            ],
            modules=["pipeline.py", "connectors/*", "market_analysis/analyzer.py", "storage.py"],
        ),
        ComponentSpec(
            icon="OPS",
            title="Query Runtime、Scheduler、Worker、Cleanup",
            subtitle="用最少基礎設施做出 queue、lease、snapshot registry 與 heartbeat",
            why=(
                "你目前沒有引入 Redis/Celery，而是先用 `query_runtime.sqlite3` 承接 query_snapshots、crawl_jobs、runtime_signals。"
                " 這讓背景 worker、scheduler、cleanup 都能先落地，而且可以在本機環境直接 debug。"
            ),
            pros=[
                "少依賴、容易本機跑起來、檔案級可觀察性高。",
                "queue / snapshot freshness / lease owner 都有可見狀態。",
                "scheduler 與 worker 可以獨立成 CLI process，不必綁死在 UI。",
            ],
            cons=[
                "SQLite queue 適合低到中量負載，不適合高頻率競爭與大量 worker。",
                "lease / retry / cleanup 都要自己維護，沒有成熟 broker 幫你扛。",
                "如果 app instance 增加，跨機器一致性與鎖競爭會變麻煩。",
            ],
            alternatives=[
                "Redis + RQ / Celery / Dramatiq。",
                "Postgres queue + SKIP LOCKED。",
                "雲端 managed queue（SQS / Cloud Tasks / PubSub）。"
            ],
            scaling=[
                "當排程量與 worker 數量成長時，優先把 queue 換掉，不要先硬撐 SQLite。",
                "snapshot 可移到 object storage，registry metadata 留在 DB。",
                "再往上就要補 metrics、dead-letter queue、job retry policy。"
            ],
            modules=["query_runtime.py", "crawl_scheduler.py", "crawl_worker.py", "runtime_maintenance_service.py"],
        ),
        ComponentSpec(
            icon="MSG",
            title="通知與綁定邊界",
            subtitle="NotificationService 統一 Email / LINE；LINE webhook 獨立進程處理綁定",
            why=(
                "通知偏好與通知記錄先存進產品 DB，真正發送由 `NotificationService` 統一包。"
                " LINE 綁定又另外用 `line_webhook.py` 承接回呼，避免把 webhook server 混進主要 UI 進程。"
            ),
            pros=[
                "Email / LINE 發送介面一致，saved search sync 可直接觸發。",
                "LINE webhook 和主 app 解耦，不會把接收入口塞進 Streamlit。",
                "通知偏好、通知記錄、發送結果都有落地可追。",
            ],
            cons=[
                "發送與 webhook 目前都還是單機流程，沒有 message bus。",
                "若未來通知通道變多，NotificationService 仍可能膨脹。",
                "Webhook 的可用性與部署方式要另外照顧。",
            ],
            alternatives=[
                "改用專門 notification worker / provider abstraction。",
                "讓 Email / LINE 都透過 queue 異步送出。",
                "改接第三方通知平台。"
            ],
            scaling=[
                "把通知發送做成 background job，避免卡住主流程。",
                "把 webhook 進一步拆到獨立 service，補簽章驗證與監控。",
                "如果通道成長，改成 provider plugin registry。"
            ],
            modules=["notifications/service.py", "line_webhook.py", "product_store.py"],
        ),
    ]

    ai_components = [
        ComponentSpec(
            icon="CV",
            title="ResumeAnalysisService",
            subtitle="規則分析先保底，OpenAI extractor / matcher 再往上疊",
            why=(
                "履歷分析不能被單一 LLM 依賴綁死，所以現在是 rule-based extractor / matcher 先保底，"
                "有 API key 才啟用 OpenAI extractor 與 embedding/title similarity matcher。"
            ),
            pros=[
                "沒有 OpenAI 時產品仍可用，不會整條履歷功能失效。",
                "可依成本與品質需求在 rule-based 與 AI 之間切換。",
                "履歷抽取與職缺匹配拆成兩步，資料結構明確。",
            ],
            cons=[
                "規則與 AI 雙軌要一起維護，邏輯較重。",
                "品質可能隨模式不同而有落差，使用者體感不完全一致。",
                "履歷文本若非常雜亂，rule-based 抽取的穩定性有限。",
            ],
            alternatives=[
                "完全改成 LLM JSON extraction + vector matching。",
                "只做 rule-based，不承擔 LLM 成本與延遲。",
                "把履歷解析外包成獨立 resume parsing service。"
            ],
            scaling=[
                "把 profile schema 版本化，讓未來模型升級可重跑。",
                "把檔案原文與解析結果分層存放，避免每次都重抽。",
                "若履歷量變大，改成 async resume analysis job。"
            ],
            modules=["resume/service.py", "resume/extractors.py", "resume/matchers.py", "ui/pages_resume_actions.py"],
        ),
        ComponentSpec(
            icon="RAG",
            title="JobMarketRAGAssistant",
            subtitle="以市場快照為知識底，embedding retrieval 後再交給 OpenAI 回答",
            why=(
                "AI 助理不是泛用聊天，而是回答『目前這批職缺』的市場問題，所以先把 snapshot 與履歷輪廓 chunk 化，"
                "再做 embedding retrieval，最後讓 `responses.create` 產生結構化回答與 citation。"
            ),
            pros=[
                "答案有 grounding，不只靠模型記憶。",
                "能切市場摘要、個人化建議、職缺比較三種 answer mode。",
                "citation 與 retrieval notes 對使用者與開發都比較透明。",
            ],
            cons=[
                "retrieval 品質非常依賴 chunk 設計、taxonomies 與 query rewriting。",
                "embedding + generation 會帶來明顯成本與延遲。",
                "快照如果本身偏舊或不完整，回答也會跟著偏。"
            ],
            alternatives=[
                "純統計 / SQL 驅動的問答，不用 LLM。",
                "改接真正的向量資料庫，而不是檔案快取 embeddings。",
                "走 agent + tools 路線，讓模型自己查各個子系統。"
            ],
            scaling=[
                "把 embeddings / retrieval 改成持久化索引，不要每次只靠檔案快取。",
                "為常見問題與報告加 response cache / precompute。",
                "為 prompt / answer schema 做版本管理與離線評估。"
            ],
            modules=["assistant/service.py", "assistant/retrieval.py", "assistant/prompts.py", "ui/assistant_actions.py"],
        ),
        ComponentSpec(
            icon="MON",
            title="AI 監控、回退與成本邊界",
            subtitle="每次 AI 動作都留監控事件，失敗則優先回退成可用模式",
            why=(
                "AI 在這個系統不是裝飾，而是影響履歷與求職建議的核心能力，所以現在會把 latency、status、model、token usage 等資訊寫進 `ai_monitoring_events`。"
                " 同時多數 AI 流程都有 fallback，避免模型不可用時整頁掛掉。"
            ),
            pros=[
                "可以看最近 AI 行為是否超出延遲或 token budget。",
                "失敗時有 graceful degradation，不是整條功能直接失效。",
                "後續要做 model comparison 或成本治理有資料可依。"
            ],
            cons=[
                "目前監控仍以 SQLite + page report 為主，沒有集中 observability 平台。",
                "回退模式多了之後，測試矩陣會變大。",
                "如果未來模型種類增多，記錄維度可能需要再擴充。"
            ],
            alternatives=[
                "直接上外部 observability / tracing 系統。",
                "簡化成只記錄失敗，不追 token 與 latency budget。",
                "把 AI 監控從 product DB 拆到獨立 analytics pipeline。"
            ],
            scaling=[
                "把 AI event 與 OpenAI usage 轉到正式 metrics / tracing stack。",
                "建立 quality dashboard，而不只是 latency dashboard。",
                "把 fallback matrix 和 prompt versions 一起納入 regression test。"
            ],
            modules=["store/metrics.py", "ui/assistant_actions.py", "ui/pages_resume_actions.py", "openai_usage.py"],
        ),
    ]

    store_specs = [
        StoreSpec(
            icon="PDB",
            title="product_state.sqlite3",
            location=str(product_db_path),
            purpose="產品狀態主資料庫：帳號、saved search、收藏、通知、AI monitoring、履歷 profile。",
            why=(
                "這是產品操作最核心的狀態，所以集中在同一份 SQLite。對目前單機型產品來說，"
                "它兼具可備份、可檢查、可本機攜帶的優點。"
            ),
            pros=[
                "交易型產品資料集中，備份與搬移簡單。",
                "repository 分層已經清楚，表結構不是直接散在 UI。",
                "對小量使用者與單機部署很實用。"
            ],
            cons=[
                "多使用者寫入競爭與 schema evolution 之後會開始吃力。",
                "auth、notifications、product metrics、AI monitoring 都在同一檔，成長後會變重。",
                "跨機器部署時會碰到檔案同步與鎖問題。"
            ],
            alternatives=[
                "Postgres / Supabase 作為正式產品 DB。",
                "Auth 交給外部 provider，產品狀態留在 SQL DB。",
                "把 metrics / monitoring 拆到 analytics store。"
            ],
            scaling=[
                "優先把這份 DB 搬到 Postgres，再考慮多 app instance。",
                "將 auth / monitoring / notifications 分 schema 或分 service。",
                "替 saved_searches、favorites、notifications 補更完整索引與 migration strategy。"
            ],
            facts=[
                ("users", _display_count(product_counts["users"])),
                ("saved_searches", _display_count(product_counts["saved_searches"])),
                ("favorite_jobs", _display_count(product_counts["favorite_jobs"])),
                ("job_notifications", _display_count(product_counts["job_notifications"])),
                ("ai_monitoring_events", _display_count(product_counts["ai_monitoring_events"])),
                ("user_resume_profiles", _display_count(product_counts["user_resume_profiles"])),
            ],
            tables=product_tables,
        ),
        StoreSpec(
            icon="QDB",
            title="query_runtime.sqlite3",
            location=str(query_db_path),
            purpose="抓取執行期資料庫：query snapshot registry、crawl queue、runtime heartbeat。",
            why=(
                "這份 DB 不是產品資料，而是讓 cache-first crawl、queued worker、scheduler 與 cleanup 能先運作起來。"
                " 它把 runtime concern 和產品資料分開，是很重要的設計。"
            ),
            pros=[
                "queue / snapshot registry / heartbeat 都可直接觀察與 debug。",
                "不需要先引入 Redis 等外部基礎設施。",
                "讓同一個 query signature 可以被 cache 命中、租約保護與背景處理。"
            ],
            cons=[
                "SQLite 不適合高量 queue throughput 與多 worker 競爭。",
                "lease / retry / cleanup 都是自己維護的基礎設施。",
                "如果未來多機部署，這層會是第一個痛點。"
            ],
            alternatives=[
                "Redis + queue worker framework。",
                "Postgres queue + SKIP LOCKED。",
                "雲端 managed queue + object storage snapshots。"
            ],
            scaling=[
                "先把 queue 換到 Redis / Postgres，再保留 registry 作 metadata。",
                "ready / partial snapshot 改放 object storage，只留 key 在 DB。",
                "補 dead-letter queue、job retry policy、signal retention dashboard。"
            ],
            facts=[
                ("query_snapshots", _display_count(query_runtime_counts["query_snapshots"])),
                ("crawl_jobs", _display_count(query_runtime_counts["crawl_jobs"])),
                ("runtime_signals", _display_count(query_runtime_counts["runtime_signals"])),
                ("snapshot files", f"{count_snapshot_files(snapshot_store_dir):,}"),
            ],
            tables=query_tables,
        ),
        StoreSpec(
            icon="UDB",
            title="user_submissions.sqlite3",
            location=str(user_db_path),
            purpose="履歷投稿與使用者提交內容的遮罩後留存資料。",
            why=(
                "履歷原文與求職輪廓具有較高敏感性，因此你現在至少先把它與 product_state 分檔，"
                "而且保存前會做個資遮罩，這是很正確的資料分流。"
            ),
            pros=[
                "敏感資料與一般產品操作資料分離。",
                "mask_personal_text / items 讓保留資料更適合開發與分析。",
                "日後若要加 TTL、加密或稽核，切入點更明確。"
            ],
            cons=[
                "雖然遮罩了，但仍然是本地磁碟資料，需要備份與權限管理。",
                "目前只有 submissions 表，後續若要版本化履歷會再長大。",
                "如果未來支援更多檔案格式與附件，這份 DB 會不夠。"
            ],
            alternatives=[
                "加密資料庫或外部 secrets / vault 管理。",
                "把原始檔丟 object storage，DB 只存 mask metadata。",
                "更嚴格地只保留衍生 profile，不留原文 mask。"
            ],
            scaling=[
                "加上 retention policy 與刪除機制。",
                "必要時把原文與 profile 拆成不同儲存層，PII 另行加密。",
                "若企業版要做合規，這塊要最先重整。"
            ],
            facts=[
                ("user_submissions", _display_count(user_submission_count)),
                ("目前 resume profile", _display_count(product_counts["user_resume_profiles"])),
            ],
            tables=user_tables,
        ),
        StoreSpec(
            icon="HIS",
            title="market_history.sqlite3",
            location=str(history_db_path),
            purpose="市場歷史資料庫：crawl runs、job posts、crawl_run_jobs，用來做長期趨勢與回顧。",
            why=(
                "live snapshot 只代表最新結果，真正想做市場趨勢、角色變化、技能成長，就需要把每輪 crawl 分離保存。"
                " 因此 market_history 與 product_state / runtime DB 分開是對的。"
            ),
            pros=[
                "歷史分析不會污染 live product tables。",
                "可追一個 query fingerprint 多次跑出的職缺變化。",
                "日後要接 dashboard 或趨勢圖，已有基礎資料模型。"
            ],
            cons=[
                "長期下來檔案會持續膨脹，需要 retention 與 prune。",
                "仍是 SQLite，本質上不是分析型資料倉。",
                "目前還偏向 history archive，不是正式 BI schema。"
            ],
            alternatives=[
                "Parquet / DuckDB / warehouse 作分析層。",
                "Postgres + materialized views。",
                "直接推到雲端 analytics warehouse。"
            ],
            scaling=[
                "當 crawl run 數量提升後，把歷史層移到 warehouse 或至少 DuckDB/Parquet。",
                "建立 query fingerprint 與 role target 維度表，方便趨勢分析。",
                "把長期統計從 app render 移到預先彙總的報表管線。"
            ],
            facts=[
                ("crawl_runs", _display_count(history_counts["crawl_runs"])),
                ("job_posts", _display_count(history_counts["job_posts"])),
                ("crawl_run_jobs", _display_count(history_counts["crawl_run_jobs"])),
            ],
            tables=history_tables,
        ),
        StoreSpec(
            icon="SNAP",
            title="JSON Snapshot / HTTP Cache",
            location=f"{snapshot_path} | {snapshot_store_dir} | {cache_dir}",
            purpose="最新市場快照、partial snapshots 與抓取 HTML/HTTP cache 的檔案落點。",
            why=(
                "你現在同時需要『最新快照可直接重載』與『query signature 對應的 partial/ready snapshot』，"
                " 還要保留 connector 的 HTTP cache，所以 JSON + 檔案目錄是最直接的落地方式。"
            ),
            pros=[
                "可讀性高，debug 時直接開檔就能看。",
                "不必每次都反查 SQL 才知道最新快照內容。",
                "和 query registry 分工明確：檔案存 payload，DB 存 metadata。"
            ],
            cons=[
                "檔案生命周期要另外管理，容易有 orphan / stale file。",
                "跨機器部署時要處理 shared filesystem 或 object storage。",
                "資料量大時，單檔 JSON 不適合做複雜查詢。"
            ],
            alternatives=[
                "把 snapshot 存到 object storage。",
                "把 latest snapshot 轉成 DB JSONB / blob。",
                "只保留 normalized relational tables，不留 JSON snapshot。"
            ],
            scaling=[
                "若上雲端，先把 snapshots/ cache 移到 object storage，再保留 local dev fallback。",
                "替 snapshot file 加 checksum / manifest，減少 orphan 與覆寫問題。",
                "需要高頻查詢時，把 snapshot 轉成 read-optimized materialized view。"
            ],
            facts=[
                ("jobs_latest.json", f"{format_size(snapshot_path)}｜{'存在' if snapshot_path.exists() else '不存在'}"),
                ("snapshot store files", f"{count_snapshot_files(snapshot_store_dir):,}"),
                ("snapshot errors", str(snapshot_error_count)),
            ],
            tables=[],
        ),
    ]

    flow_specs = [
        FlowSpec(
            title="使用者手動查詢資料流",
            description="這是目前產品最主要的互動閉環：輸入角色條件後，先回 partial snapshot，再補完整分析。",
            nodes=[
                "搜尋設定",
                "maybe_start_crawl",
                "start_crawl",
                "query runtime / cache",
                "JobMarketPipeline 首波搜尋",
                "partial snapshot",
                "finalize enrich",
                "總覽 / 履歷 / AI 共用 snapshot",
            ],
            notes=[
                "query_signature 會先拿去查 cache，命中 fresh snapshot 就直接回用，不重抓。",
                "初波 wave 先讓 UI 有可見結果，後續 detail enrich 與更多頁次再補。",
                "完成後會再同步到 saved search、favorites、notifications 這條產品狀態鏈。",
            ],
        ),
        FlowSpec(
            title="排程自動刷新資料流",
            description="scheduler 只負責找出 due saved search 並 enqueue；worker 真的去跑 crawl 與後續同步。",
            nodes=[
                "scheduler",
                "collect_due_saved_searches",
                "enqueue crawl_jobs",
                "worker lease job",
                "process_queued_crawl_job",
                "query_snapshots ready",
                "saved search sync",
                "站內通知 / Email / LINE",
            ],
            notes=[
                "這條流讓已存的搜尋條件可以在沒有使用者當下操作時繼續刷新。",
                "scheduler / worker 都會寫 runtime_signals，所以營運頁能看到 heartbeat。",
                "這也是為什麼 query runtime 與 product state 要分開：一個是執行期，一個是產品資料。",
            ],
        ),
        FlowSpec(
            title="履歷分析與匹配資料流",
            description="履歷頁先抽 profile，再用當前 market snapshot 去做匹配與缺口分析。",
            nodes=[
                "履歷檔 / 貼上文字",
                "ResumeAnalysisService.build_profile",
                "masked user_submissions",
                "match_jobs(snapshot.jobs)",
                "ResumeJobMatch",
                "履歷匹配頁",
            ],
            notes=[
                "build_profile 先產出結構化 ResumeProfile，再讓 match_jobs 對照快照職缺。",
                "同一條流程有 rule-based fallback，不會因 OpenAI 不可用而整頁失效。",
                "履歷分析不是獨立資料源，而是強依賴當前市場快照。"
            ],
        ),
        FlowSpec(
            title="AI 助理 / 報告資料流",
            description="AI 助理會把市場快照、履歷輪廓、對話上下文一起轉成檢索與回答素材。",
            nodes=[
                "問題 + 快照 + 履歷輪廓",
                "chunk build",
                "embedding retrieval",
                "OpenAI Responses",
                "AssistantResponse + citations",
                "AI 助理頁 / launcher / report",
            ],
            notes=[
                "RAG 助理的核心價值是 grounding，避免只靠模型記憶回答。",
                "assistant 與 resume 是兩條 AI 能力鏈，但都共用同一份市場資料底。",
                "AI 事件會回寫 ai_monitoring_events，方便後續看 latency、status 與 token usage。"
            ],
        ),
    ]

    expansion_specs = [
        ExpansionSpec(
            title="前後端分離",
            stage="適用時機：你要做正式網站、多人協作前端、或行動端接入",
            why=(
                "現在的 Streamlit 工作台很適合快速迭代，但若產品要長期演進，"
                "UI 與 application service 邊界最好明確成 API。"
            ),
            actions=[
                "先把 crawl / assistant / resume / notifications 抽成 API-facing service layer。",
                "定義 PageContext 對應的 read DTO 與 write commands。",
                "前端可改成 Next.js / React，先保留現有 Python services。"
            ],
            tradeoffs=[
                "開發與部署複雜度上升。",
                "要補 API auth、schema versioning、前端狀態管理。",
            ],
        ),
        ExpansionSpec(
            title="更多使用者與更高寫入",
            stage="適用時機：同時在線使用者增加、saved search / favorites / notifications 寫入頻率上升",
            why=(
                "SQLite 對目前單機型產品很省事，但一旦寫入競爭與多 instance 出現，就會先卡在資料層。"
            ),
            actions=[
                "優先把 product_state.sqlite3 移到 Postgres。",
                "把 query runtime queue 從 SQLite 換到 Redis 或 Postgres queue。",
                "讀多寫少的最新快照維持 cache/read model，減少主庫壓力。"
            ],
            tradeoffs=[
                "你會失去『單一檔案即完整資料』的便利。",
                "需要 migration、backup、連線池與雲端 DB 維運。"
            ],
        ),
        ExpansionSpec(
            title="更大規模抓取與排程",
            stage="適用時機：來源更多、刷新頻率更高、要同時跑更多 worker",
            why=(
                "現在的 staged crawl 與 queue 雛形已經正確，但要走向高量抓取，必須把 runtime 從單機型假設中解放。"
            ),
            actions=[
                "把 connector execution 拆成 source-aware workers 與 rate limit policy。",
                "加入 dead-letter queue、重試策略分級、原始頁面快取保留。",
                "snapshot 轉 object storage，registry 只保 metadata 與 freshness。"
            ],
            tradeoffs=[
                "營運與 observability 成本上升。",
                "每個來源的異常處理與封鎖風險要更嚴格管理。"
            ],
        ),
        ExpansionSpec(
            title="更重的 AI 與知識庫",
            stage="適用時機：AI 問答量變大、要做知識庫、對話記憶、模型比較與成本治理",
            why=(
                "目前的 embedding cache 與 prompt flow 足夠支撐工作台型產品，但如果 AI 成為主產品，"
                "retrieval、observability、成本控制都要升級。"
            ),
            actions=[
                "把 embeddings / retrieval 轉到正式 vector index。",
                "建立 prompt/version registry、response cache、quality evaluation dataset。",
                "把 AI report / resume analysis 改成可排隊的 async job。"
            ],
            tradeoffs=[
                "系統會明顯複雜化，且需要更多離線評估與監控基礎。",
                "模型與知識庫版本管理會成為新的核心工程工作。"
            ],
        ),
    ]

    runtime_cards = [
        (
            "目前 UI / Runtime",
            [
                ("目前搜尋名稱", ctx.current_search_name or "未命名搜尋"),
                ("目前搜尋簽章", _short_signature(ctx.current_signature)),
                ("crawl_phase", str(ctx.crawl_phase or "idle")),
                ("detail enrich", f"{ctx.crawl_detail_cursor} / {ctx.crawl_detail_total}"),
                ("執行模式", runtime_mode_label),
            ],
        ),
        (
            "功能與外部服務",
            [
                ("啟用來源", ", ".join(connectors)),
                ("OpenAI", _status_label(bool(ctx.settings.openai_api_key))),
                ("Email 通知", _status_label(ctx.notification_service.email_service_configured)),
                ("LINE 通知", _status_label(ctx.notification_service.line_service_configured)),
                ("max concurrent", str(ctx.settings.max_concurrent_requests)),
                ("max pages/source", str(ctx.settings.max_pages_per_source)),
            ],
        ),
        (
            "資料與快取",
            [
                ("jobs_latest.json", f"{format_size(snapshot_path)}｜{'存在' if snapshot_path.exists() else '不存在'}"),
                ("snapshot store", f"{count_snapshot_files(snapshot_store_dir):,} files"),
                ("query_snapshots", _display_count(query_runtime_counts["query_snapshots"])),
                ("crawl_jobs", _display_count(query_runtime_counts["crawl_jobs"])),
                ("runtime_signals", _display_count(query_runtime_counts["runtime_signals"])),
                ("crawl_runs", _display_count(history_counts["crawl_runs"])),
            ],
        ),
    ]

    storage_rows = [
        ("data dir", str(ctx.settings.data_dir)),
        ("市場快照", str(snapshot_path)),
        ("snapshot store", str(snapshot_store_dir)),
        ("HTTP cache", str(cache_dir)),
        ("產品狀態 DB", str(product_db_path)),
        ("履歷投稿 DB", str(user_db_path)),
        ("Query Runtime DB", str(query_db_path)),
        ("市場歷史 DB", str(history_db_path)),
    ]

    return BackendArchitectureData(
        overview_intro=overview_intro,
        overview_metrics=overview_metrics,
        topology_clusters=topology_clusters,
        frontend_components=frontend_components,
        backend_components=backend_components,
        ai_components=ai_components,
        store_specs=store_specs,
        flow_specs=flow_specs,
        expansion_specs=expansion_specs,
        runtime_cards=runtime_cards,
        storage_rows=storage_rows,
        product_tables=product_tables,
        user_tables=user_tables,
        query_tables=query_tables,
        history_tables=history_tables,
    )
