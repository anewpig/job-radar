from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


WIDTH = 2200
HEIGHT = 1360
BG = "#f6f2ff"
SURFACE = "#ffffff"
SURFACE_SOFT = "#f2ecff"
TEXT = "#1f1734"
MUTED = "#695f86"
ACCENT = "#6543e8"
LINE = "#dacff8"
GREEN = "#e6f7ef"
GOLD = "#fbf0d9"
RED = "#fde8ee"
BLUE = "#eaf0ff"
DARK_BG = "#181818"
DARK_PANEL = "#1f1f1f"
DARK_CLUSTER = "#232323"
DARK_NODE = "#2a2a2a"
DARK_LINE = "#6e6e6e"
DARK_TEXT = "#f2f2f2"
DARK_MUTED = "#b8b8b8"
DARK_ACCENT = "#b2a6ff"

FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_PATH_LIGHT = "/System/Library/Fonts/STHeiti Light.ttc"


@dataclass
class Node:
    title: str
    body: str
    fill: str = SURFACE
    tag: str | None = None


def font(size: int, light: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_PATH_LIGHT if light else FONT_PATH
    return ImageFont.truetype(path, size=size)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, text_font: ImageFont.FreeTypeFont) -> list[str]:
    words = list(text)
    lines: list[str] = []
    current = ""
    for ch in words:
        candidate = current + ch
        if draw.textbbox((0, 0), candidate, font=text_font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_round_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str = LINE, radius: int = 28, width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    lines: Iterable[str],
    text_font: ImageFont.FreeTypeFont,
    fill: str = TEXT,
    line_gap: int = 10,
) -> int:
    x, y = xy
    cursor = y
    for line in lines:
        draw.text((x, cursor), line, font=text_font, fill=fill)
        bbox = draw.textbbox((x, cursor), line, font=text_font)
        cursor = bbox[3] + line_gap
    return cursor


def draw_node(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    node: Node,
) -> None:
    x1, y1, x2, y2 = box
    draw_round_rect(draw, box, node.fill)
    pad = 26
    cursor_y = y1 + pad
    if node.tag:
        tag_box = (x1 + pad, cursor_y, x1 + pad + 150, cursor_y + 40)
        draw.rounded_rectangle(tag_box, radius=18, fill="#ffffff", outline=LINE, width=2)
        draw.text((tag_box[0] + 16, tag_box[1] + 8), node.tag, font=font(18), fill=ACCENT)
        cursor_y = tag_box[3] + 18
    title_lines = wrap_text(draw, node.title, x2 - x1 - pad * 2, font(30))
    cursor_y = draw_text_block(draw, (x1 + pad, cursor_y), title_lines, font(30)) + 4
    body_lines = wrap_text(draw, node.body, x2 - x1 - pad * 2, font(20, light=True))
    draw_text_block(draw, (x1 + pad, cursor_y), body_lines, font(20, light=True), fill=MUTED, line_gap=8)


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], fill: str = ACCENT, width: int = 8) -> None:
    draw.line([start, end], fill=fill, width=width)
    ex, ey = end
    draw.polygon([(ex, ey), (ex - 26, ey - 16), (ex - 26, ey + 16)], fill=fill)


def base_canvas(title: str, subtitle: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw_round_rect(draw, (40, 32, WIDTH - 40, HEIGHT - 32), fill="#fbf9ff", outline="#ede5ff", radius=40, width=2)
    draw.rounded_rectangle((86, 78, 386, 136), radius=28, fill="#ffffff", outline=LINE, width=2)
    draw.text((114, 92), "JOB RADAR DIAGRAM", font=font(22), fill=ACCENT)
    draw.text((88, 170), title, font=font(58), fill=TEXT)
    draw_text_block(draw, (92, 256), wrap_text(draw, subtitle, WIDTH - 220, font(24, light=True)), font(24, light=True), fill=MUTED, line_gap=10)
    return image, draw


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def build_overall(path: Path) -> None:
    width = 2400
    height = 2080
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    draw_round_rect(draw, (40, 32, width - 40, height - 32), fill="#fbf9ff", outline="#ede5ff", radius=40, width=2)
    draw.rounded_rectangle((86, 78, 430, 138), radius=28, fill="#ffffff", outline=LINE, width=2)
    draw.text((116, 92), "JOB RADAR SYSTEM DESIGN", font=font(24), fill=ACCENT)
    draw.text((88, 178), "總體架構圖", font=font(64), fill=TEXT)
    subtitle = "這版改成『分層主圖』：左邊只講系統層次，右邊講每層代表模組與責任，比原本多節點平鋪更適合面試講解。"
    draw_text_block(draw, (92, 270), wrap_text(draw, subtitle, width - 220, font(26, light=True)), font(26, light=True), fill=MUTED, line_gap=10)

    layers = [
        (
            "01. 使用者與入口",
            "Browser 使用者、管理者、後端控制台",
            BLUE,
            "一般使用者透過 Streamlit 工作台操作；管理者則透過 backend console、maintenance、backup/restore drill 觀察與維護系統。",
        ),
        (
            "02. Frontend 工作台",
            "app.py / bootstrap / session / router / pages",
            SURFACE,
            "承接搜尋設定、hero、頁面切換、assistant launcher、resume page、tracking center 與各種 session state。",
        ),
        (
            "03. Application 協調層",
            "crawl_application_service / assistant.service / resume.service",
            SURFACE_SOFT,
            "把 UI、cache、saved search、runtime queue、AI 問答與履歷匹配協調起來，這層是整個產品邏輯的中心。",
        ),
        (
            "04. Background Runtime",
            "crawl_scheduler / query_runtime / crawl_worker",
            GREEN,
            "scheduler 決定哪些查詢到期，worker 真正執行抓取與分析，runtime DB 則讓 UI 能輪詢進度與狀態。",
        ),
        (
            "05. Data Pipeline",
            "connectors / job_cleaning / pipeline / analyzer",
            GOLD,
            "把 raw jobs 轉成 canonical jobs、去重、角色配對、技能與任務 insights，最後形成 snapshot。",
        ),
        (
            "06. AI / RAG Layer",
            "chunks / vector_index / retrieval / OpenAI / resume matchers",
            RED,
            "AI 問答與履歷分析都建立在結構化資料之上：先建 chunks，再做 ANN candidate recall 與 hybrid rerank，最後才進 LLM。",
        ),
        (
            "07. Storage 與治理",
            "product_state / query_runtime / market_history / snapshots / cache",
            BLUE,
            "產品主資料、執行期資料、歷史 archive、快照與 cache 分層保存，方便維運、擴充與未來搬移。",
        ),
    ]

    left_x1, left_x2 = 140, 960
    right_x1, right_x2 = 1040, 2260
    start_y = 400
    box_h = 150
    gap = 58

    for idx, (title, sub, fill, detail) in enumerate(layers):
        y1 = start_y + idx * (box_h + gap)
        y2 = y1 + box_h

        draw_round_rect(draw, (left_x1, y1, left_x2, y2), fill=fill, radius=34, width=3)
        draw.rounded_rectangle((left_x1 + 24, y1 + 22, left_x1 + 230, y1 + 62), radius=18, fill="#ffffff", outline=LINE, width=2)
        draw.text((left_x1 + 46, y1 + 30), "SYSTEM LAYER", font=font(18), fill=ACCENT)
        draw_text_block(draw, (left_x1 + 24, y1 + 76), wrap_text(draw, title, left_x2 - left_x1 - 48, font(34)), font(34), fill=TEXT, line_gap=8)
        draw_text_block(draw, (left_x1 + 24, y1 + 116), wrap_text(draw, sub, left_x2 - left_x1 - 48, font(22, light=True)), font(22, light=True), fill=MUTED, line_gap=8)

        draw_round_rect(draw, (right_x1, y1, right_x2, y2), fill="#ffffff", radius=34, width=3)
        draw.rounded_rectangle((right_x1 + 24, y1 + 22, right_x1 + 250, y1 + 62), radius=18, fill="#ffffff", outline=LINE, width=2)
        draw.text((right_x1 + 48, y1 + 30), "代表模組與責任", font=font(18), fill=ACCENT)
        detail_lines = wrap_text(draw, detail, right_x2 - right_x1 - 48, font(24, light=True))
        draw_text_block(draw, (right_x1 + 24, y1 + 78), detail_lines, font(24, light=True), fill=MUTED, line_gap=10)

        if idx < len(layers) - 1:
            center_x = (left_x1 + left_x2) // 2
            draw_arrow(draw, (center_x, y2 + 8), (center_x, y2 + gap - 10))

    note_box = (140, 1885, 2260, 2015)
    draw_round_rect(draw, note_box, fill="#ffffff", radius=28, width=2)
    note = (
        "這張圖最適合當『第一張主圖』來講。建議順序：先講使用者問題，再講為什麼要有 Frontend 工作台；"
        "接著講 Application 協調層如何把同步與非同步任務拆開；再往下講 Data Pipeline、AI / RAG 與 Storage。"
    )
    draw_text_block(draw, (170, 1920), wrap_text(draw, note, 2040, font(24, light=True)), font(24, light=True), fill=MUTED, line_gap=10)

    save(image, path)


def build_query_flow(path: Path) -> None:
    image, draw = base_canvas(
        "手動查詢 / 自動刷新流程",
        "把使用者按下查詢、命中快取、建立 background job、worker finalize，以及 scheduler 自動刷新這兩條線拆開畫清楚。",
    )
    draw.rounded_rectangle((90, 340, WIDTH - 90, 770), radius=30, fill="#ffffff", outline=LINE, width=2)
    draw.text((116, 362), "手動查詢", font=font(28), fill=TEXT)

    manual_nodes = [
        Node("使用者輸入條件", "search_setup 收集角色、地區、關鍵字、自訂 query、頻率。", BLUE, "UI"),
        Node("maybe_start_crawl()", "crawl_application_service 先看 signature / saved search / 快取。", SURFACE_SOFT, "應用"),
        Node("命中快取", "直接回 snapshot、cache views、渲染 overview / market。", GREEN, "同步"),
        Node("未命中快取", "建立 crawl job / signal 到 query_runtime。", GOLD, "非同步"),
        Node("crawl_worker", "lease job 後執行 connectors、pipeline、analyzer。", RED, "背景"),
        Node("finalize", "UI 輪詢 signal，完成後重新載入 snapshot。", SURFACE, "收斂"),
    ]
    positions = [
        (120, 450, 420, 650),
        (480, 450, 820, 650),
        (860, 390, 1180, 560),
        (860, 590, 1180, 760),
        (1240, 590, 1560, 760),
        (1620, 520, 2000, 720),
    ]
    for box, node in zip(positions, manual_nodes):
        draw_node(draw, box, node)
    draw_arrow(draw, (430, 550), (468, 550))
    draw_arrow(draw, (830, 520), (848, 470))
    draw_arrow(draw, (830, 590), (848, 670))
    draw_arrow(draw, (1190, 675), (1228, 675))
    draw_arrow(draw, (1570, 640), (1608, 640))

    draw.rounded_rectangle((90, 830, WIDTH - 90, 1180), radius=30, fill="#ffffff", outline=LINE, width=2)
    draw.text((116, 852), "自動刷新", font=font(28), fill=TEXT)
    auto_nodes = [
        Node("crawl_scheduler", "掃描 due saved searches。", GREEN, "排程"),
        Node("建立 runtime job", "把應刷新查詢放入 query_runtime queue。", SURFACE_SOFT, "排程"),
        Node("crawl_worker", "執行抓取、分析、persist、通知。", RED, "背景"),
        Node("saved search 同步", "前端下次進站可直接看到最新結果。", BLUE, "產品"),
    ]
    auto_positions = [
        (120, 930, 450, 1085),
        (520, 930, 920, 1085),
        (990, 930, 1390, 1085),
        (1460, 930, 1990, 1085),
    ]
    for box, node in zip(auto_positions, auto_nodes):
        draw_node(draw, box, node)
    draw_arrow(draw, (460, 1008), (508, 1008))
    draw_arrow(draw, (930, 1008), (978, 1008))
    draw_arrow(draw, (1400, 1008), (1448, 1008))

    save(image, path)


def build_ai_flow(path: Path) -> None:
    image, draw = base_canvas(
        "AI / RAG 問答流程",
        "把從使用者問題、mode / intent、chunking、ANN 候選召回、hybrid rerank 到 grounded answer 的主路徑單獨拆成一張圖。",
    )
    top_nodes = [
        Node("Question", "使用者問題與對話上下文。", BLUE, "Input"),
        Node("Mode / Intent", "分類題型與 retrieval policy，決定是否強制走 RAG。", SURFACE_SOFT, "Routing"),
        Node("Chunk Build", "從 snapshot、resume、market insight 建立 knowledge chunks。", GOLD, "Knowledge"),
        Node("Persistent ANN Recall", "用 vector_index 做長期候選召回，再與 snapshot chunks 合併。", GREEN, "Recall"),
        Node("Hybrid Retrieval", "embedding + lexical + signal + source bonus + market penalty。", RED, "Ranking"),
        Node("LLM Answer", "用 grounded context 產出自然 QA 回答。", SURFACE, "Output"),
    ]
    x = 90
    widths = [280, 320, 320, 340, 360, 300]
    for idx, node in enumerate(top_nodes):
        w = widths[idx]
        draw_node(draw, (x, 380, x + w, 640), node)
        if idx < len(top_nodes) - 1:
            draw_arrow(draw, (x + w + 10, 510), (x + w + 48, 510))
        x += w + 58

    bottom_nodes = [
        Node("Snapshot / jobs_latest", "AI 主要依賴當前市場快照。", BLUE, "Data"),
        Node("Cache", "chunk cache、embedding memory cache、resume cache。", GREEN, "Perf"),
        Node("OpenAI Embeddings", "retrieval 與 resume match 的向量基礎。", RED, "LLM"),
        Node("AI Monitoring", "記錄 mode、latency、status、usage。", GOLD, "Observe"),
    ]
    positions = [(180, 860, 560, 1040), (650, 860, 1050, 1040), (1140, 860, 1540, 1040), (1630, 860, 2010, 1040)]
    for box, node in zip(positions, bottom_nodes):
        draw_node(draw, box, node)

    draw_arrow(draw, (760, 650), (760, 835))
    draw_arrow(draw, (1290, 650), (1290, 835))
    draw_arrow(draw, (1820, 650), (1820, 835))

    draw.rounded_rectangle((118, 1110, WIDTH - 118, 1248), radius=28, fill="#ffffff", outline=LINE, width=2)
    note = (
        "這張圖的重點不是『有沒有接 LLM』，而是：問題先被分類、知識先被建立、候選先被召回、"
        "再透過 hybrid retrieval 做排序，最後才把可追溯的 context 交給模型回答。"
    )
    draw_text_block(draw, (150, 1146), wrap_text(draw, note, WIDTH - 300, font(26, light=True)), font(26, light=True), fill=MUTED, line_gap=10)

    save(image, path)


def draw_module_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    subtitle: str,
    modules: list[str],
    fill: str,
) -> None:
    x1, y1, x2, y2 = box
    draw_round_rect(draw, box, fill=fill, radius=30, width=3)
    draw.rounded_rectangle((x1 + 24, y1 + 22, x1 + 210, y1 + 62), radius=18, fill="#ffffff", outline=LINE, width=2)
    draw.text((x1 + 48, y1 + 31), "SYSTEM BLOCK", font=font(18), fill=ACCENT)
    draw_text_block(draw, (x1 + 24, y1 + 84), wrap_text(draw, title, x2 - x1 - 48, font(36)), font(36), fill=TEXT, line_gap=8)
    draw_text_block(draw, (x1 + 24, y1 + 136), wrap_text(draw, subtitle, x2 - x1 - 48, font(22, light=True)), font(22, light=True), fill=MUTED, line_gap=8)
    cursor_y = y1 + 206
    for module in modules:
        bullet_box = (x1 + 26, cursor_y + 5, x1 + 38, cursor_y + 17)
        draw.ellipse(bullet_box, fill=ACCENT)
        lines = wrap_text(draw, module, x2 - x1 - 74, font(22, light=True))
        next_y = draw_text_block(draw, (x1 + 54, cursor_y), lines, font(22, light=True), fill=TEXT, line_gap=6)
        cursor_y = next_y + 8


def build_overall_detailed(path: Path) -> None:
    width = 3000
    height = 2380
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    draw_round_rect(draw, (36, 28, width - 36, height - 28), fill="#fbf9ff", outline="#ede5ff", radius=42, width=2)
    draw.rounded_rectangle((84, 74, 470, 138), radius=28, fill="#ffffff", outline=LINE, width=2)
    draw.text((114, 90), "JOB RADAR DETAILED SYSTEM MAP", font=font(24), fill=ACCENT)
    draw.text((86, 178), "完整系統設計圖（細版）", font=font(66), fill=TEXT)
    subtitle = (
        "這張圖把主要模組真的展開：前端工作台、application 協調層、scheduler/worker、data pipeline、"
        "AI / RAG、resume intelligence、以及多資料庫與 cache。這張才是拿來 deep dive 的版本。"
    )
    draw_text_block(draw, (92, 272), wrap_text(draw, subtitle, width - 220, font(28, light=True)), font(28, light=True), fill=MUTED, line_gap=10)

    left_x = 100
    right_x = 1560
    col_w = 1320
    card_h = 430
    row_gap = 46
    start_y = 390

    draw_module_card(
        draw,
        (left_x, start_y, left_x + col_w, start_y + card_h),
        "01. Frontend / Streamlit 工作台",
        "這一層承接所有使用者互動，負責 session、頁面切換、查詢設定、輪詢狀態與結果渲染。",
        [
            "app.py：整體入口、boot loading、bootstrap、hero、auth、page dispatch。",
            "ui/bootstrap_*：建立 runtime services、user context、初始 snapshot hydrate。",
            "ui/session_*：session defaults、user switching、main tab、snapshot view cache。",
            "ui/router_* + navigation_*：主 tab、drawer、surface dispatch。",
            "ui/search_setup_* + ui/crawl_runtime_*：查詢列、saved search、發起 crawl、輪詢 finalize。",
            "ui/pages_*：overview、market、resume、assistant、tracking、board、notifications、backend console。",
            "ui/assistant_launcher_*：浮動 AI 助手、說明與通知入口。",
        ],
        fill=SURFACE,
    )

    draw_module_card(
        draw,
        (right_x, start_y, right_x + col_w, start_y + card_h),
        "02. Application / Orchestration",
        "這一層不直接抓資料，也不直接負責 UI，而是協調產品邏輯、快取命中、runtime queue、AI 與通知。",
        [
            "crawl_application_service：signature 比對、cache 命中、建立 crawl jobs、同步 saved search 結果。",
            "notification_service + notifications/*：LINE / Email channel、message builder、測試通知。",
            "assistant/service.py：問題分類、chunk build、ANN recall、hybrid retrieval、responses.create。",
            "resume/service.py：履歷抽取、resume match、推薦結果彙整。",
            "runtime_maintenance_service：cache 清理、runtime hygiene、統一 maintenance。",
            "backend_status_service / backend_operations_service：後端控制台的觀測與操作視圖。",
        ],
        fill=SURFACE_SOFT,
    )

    y2 = start_y + card_h + row_gap
    draw_module_card(
        draw,
        (left_x, y2, left_x + col_w, y2 + card_h),
        "03. Background Runtime / Process Topology",
        "這一層處理所有非同步工作，讓 UI 不需要直接承擔長任務。",
        [
            "crawl_scheduler.py：週期掃描 due saved searches，決定哪些查詢該刷新。",
            "crawl_worker.py：真正執行 connectors、pipeline、analysis、notification、finalize。",
            "backend_maintenance.py / sqlite_backup.py / sqlite_restore_drill.py：維運、備份、演練。",
            "line_webhook.py：LINE 綁定與通知回應入口。",
            "query_runtime.py：runtime queue / signal / lease API 的核心封裝。",
        ],
        fill=GREEN,
    )

    draw_module_card(
        draw,
        (right_x, y2, right_x + col_w, y2 + card_h),
        "04. Data Pipeline / Market Intelligence",
        "這一層把 raw jobs 轉成產品與 AI 可直接消費的 snapshot、insight 與 canonical data。",
        [
            "connectors/*：104、1111、Cake、LinkedIn 搜尋與 detail 萃取。",
            "detail_parsing.py：把網站 detail 內容轉成結構化 section / requirement / task items。",
            "job_cleaning.py：canonical title/company/location/salary/url、cross-source merge key。",
            "pipeline.py：dedupe、merge、relevance filter、persist orchestration。",
            "market_analysis/analyzer.py：role match、relevance、skills、tasks、source/location/role summary。",
            "market_history_store.py：把重要結果寫入歷史 archive，支撐後續回看與全庫檢索。",
        ],
        fill=GOLD,
    )

    y3 = y2 + card_h + row_gap
    draw_module_card(
        draw,
        (left_x, y3, left_x + col_w, y3 + card_h),
        "05. AI / RAG / Retrieval",
        "這一層是 AI 助理主路徑。重點不是只有模型，而是 knowledge construction、candidate recall、hybrid rank 與 monitoring。",
        [
            "assistant/chunks.py：job-summary、job-skills、job-work-content、market insight、resume-summary chunks。",
            "assistant/retrieval.py：intent signals、coarse candidate selection、embedding similarity、source bonus、market penalty、dynamic top-k。",
            "assistant/vector_index.py：長期持久化 ANN recall，從 jobs_latest / snapshots / market_history 補候選。",
            "assistant/prompts.py + question_presets.py：正式 QA / 一般 QA 的回答風格與 prompt contract。",
            "assistant/chunking_eval.py + benchmark_chunking_strategies.py：離線 benchmark、realistic evaluation set。",
            "openai_usage.py：usage merge 與成本觀測支援。",
        ],
        fill=RED,
    )

    draw_module_card(
        draw,
        (right_x, y3, right_x + col_w, y3 + card_h),
        "06. Resume Intelligence",
        "這一層專門負責履歷抽取、履歷 profile、matching 與建議。",
        [
            "resume/extractors.py：從履歷原文抽 salient lines，建立 summary、skills、tasks、keywords。",
            "resume/matchers.py：exact overlap + semantic similarity + title similarity + market fit。",
            "resume/scoring.py：role / skill / task / keyword / title 的加權整合。",
            "resume/service.py：把抽取、匹配、推薦卡與 UI 消費格式整合起來。",
            "resume/schemas.py / text.py：輸入 schema 與清理工具。",
        ],
        fill=BLUE,
    )

    y4 = y3 + card_h + row_gap
    draw_module_card(
        draw,
        (left_x, y4, left_x + col_w, y4 + card_h),
        "07. Storage / State / Cache",
        "資料層不是單一 DB，而是依 ownership、生命週期與用途分離。",
        [
            "product_state.sqlite3：saved searches、favorites、notification prefs、auth refs、AI monitoring。",
            "query_runtime.sqlite3：crawl jobs、runtime signals、queue、leases、background status。",
            "user_submissions.sqlite3：履歷與使用者提交內容。",
            "market_history.sqlite3：歷史市場職缺 archive。",
            "jobs_latest.json / data/snapshots：目前快照與頁面、RAG 最常消費的資料。",
            "cache/：embeddings、resume_match cache、RAG cache、runtime cache，需要固定 maintenance。",
        ],
        fill=SURFACE,
    )

    draw_module_card(
        draw,
        (right_x, y4, right_x + col_w, y4 + card_h),
        "08. External Systems / Integrations",
        "外部依賴不只 job sites，也包含通知與模型供應商。",
        [
            "104 / 1111 / Cake / LinkedIn：職缺來源。",
            "OpenAI：responses、responses.parse、embeddings。",
            "LINE / Email：通知與 webhook 流程。",
            "本地檔案系統：snapshot、cache、backup artifact。",
            "Streamlit runtime：承接所有頁面與互動生命週期。",
        ],
        fill=SURFACE_SOFT,
    )

    center_x = width // 2
    for y_start in [start_y + card_h, y2 + card_h, y3 + card_h]:
        draw_arrow(draw, (center_x, y_start + 8), (center_x, y_start + row_gap - 10))

    footer_box = (100, 2190, 2900, 2315)
    draw_round_rect(draw, footer_box, fill="#ffffff", radius=28, width=2)
    note = (
        "這張細版圖最適合第二階段講解。第一階段先用簡版主圖講『系統層次』，第二階段再用這張補模組細節。"
        "這樣不會一開始資訊過載，也不會像剛剛那張一樣省略太多。"
    )
    draw_text_block(draw, (130, 2230), wrap_text(draw, note, 2700, font(24, light=True)), font(24, light=True), fill=MUTED, line_gap=10)

    save(image, path)


def draw_dark_round_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str = "#363636", radius: int = 24, width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_dark_text_block(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    max_width: int,
    size: int,
    fill: str = DARK_TEXT,
    light: bool = False,
    line_gap: int = 8,
) -> int:
    lines = wrap_text(draw, text, max_width, font(size, light=light))
    return draw_text_block(draw, xy, lines, font(size, light=light), fill=fill, line_gap=line_gap)


def draw_dark_node(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    subtitle: str,
) -> None:
    x1, y1, x2, y2 = box
    draw_dark_round_rect(draw, box, fill=DARK_NODE, outline="#383838", radius=18, width=2)
    draw_dark_text_block(draw, (x1 + 18, y1 + 14), title, x2 - x1 - 36, 22, fill=DARK_TEXT)
    draw_dark_text_block(draw, (x1 + 18, y1 + 56), subtitle, x2 - x1 - 36, 15, fill=DARK_MUTED, light=True, line_gap=5)


def draw_cluster(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
) -> None:
    x1, y1, x2, y2 = box
    draw_dark_round_rect(draw, box, fill=DARK_CLUSTER, outline="#2e2e2e", radius=28, width=2)
    draw.text((x1 + 18, y1 + 14), title, font=font(18), fill="#d8d8d8")


def draw_dark_arrow(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], fill: str = DARK_LINE, width: int = 3) -> None:
    if len(points) < 2:
      return
    draw.line(points, fill=fill, width=width)
    ex, ey = points[-1]
    px, py = points[-2]
    if abs(ex - px) >= abs(ey - py):
        direction = 1 if ex >= px else -1
        arrow = [(ex, ey), (ex - 16 * direction, ey - 10), (ex - 16 * direction, ey + 10)]
    else:
        direction = 1 if ey >= py else -1
        arrow = [(ex, ey), (ex - 10, ey - 16 * direction), (ex + 10, ey - 16 * direction)]
    draw.polygon(arrow, fill=fill)


def build_system_flowchart_detailed(path: Path) -> None:
    width = 3400
    height = 2100
    image = Image.new("RGB", (width, height), DARK_BG)
    draw = ImageDraw.Draw(image)
    draw_dark_round_rect(draw, (20, 20, width - 20, height - 20), fill=DARK_PANEL, outline="#2a2a2a", radius=36, width=2)
    draw.text((58, 52), "Job Radar / Detailed System Flowchart", font=font(28), fill=DARK_ACCENT)

    # clusters
    draw_cluster(draw, (60, 1460, 360, 1770), "使用者與入口")
    draw_cluster(draw, (420, 1180, 1380, 1870), "Frontend / Streamlit UI")
    draw_cluster(draw, (1460, 980, 2160, 1485), "Application / Orchestration")
    draw_cluster(draw, (1460, 240, 2160, 930), "Background Jobs / Runtime")
    draw_cluster(draw, (2240, 360, 2900, 980), "Data Pipeline")
    draw_cluster(draw, (2240, 1160, 2960, 1800), "AI / LLM / RAG")
    draw_cluster(draw, (2700, 110, 3340, 1540), "Storage / State")
    draw_cluster(draw, (2280, 40, 2850, 300), "External Systems")

    # users / entry
    draw_dark_node(draw, (90, 1540, 320, 1618), "使用者入口", "一般使用者 / Browser")
    draw_dark_node(draw, (90, 1650, 320, 1728), "後端管理者", "維運與觀察")
    draw_dark_node(draw, (450, 1500, 670, 1582), "app.py", "Streamlit 入口")
    draw_dark_node(draw, (730, 1500, 1030, 1582), "bootstrap_runtime", "建立 runtime services")
    draw_dark_node(draw, (1080, 1500, 1360, 1582), "initialize_session_state", "補齊 session defaults")
    draw_dark_node(draw, (520, 1620, 820, 1702), "resolve_current_user", "還原 user context")
    draw_dark_node(draw, (880, 1620, 1200, 1702), "router / navigation", "tab + drawer + dispatch")
    draw_dark_node(draw, (620, 1740, 960, 1822), "render_top_header / auth", "header + auth popover")

    # frontend features
    draw_dark_node(draw, (480, 1225, 780, 1307), "render_search_setup", "搜尋條件工作台")
    draw_dark_node(draw, (850, 1225, 1180, 1307), "maybe_start_crawl", "發起查詢或命中快取")
    draw_dark_node(draw, (520, 1350, 860, 1432), "render_finalize_worker_fragment", "輪詢 finalize 狀態")
    draw_dark_node(draw, (930, 1350, 1280, 1432), "dispatch_main_tab", "渲染各頁主內容")
    draw_dark_node(draw, (500, 1460, 840, 1542), "render_assistant_launcher", "浮動 AI 助手 / 說明 / 通知")
    draw_dark_node(draw, (900, 1460, 1260, 1542), "pages_resume / pages_assistant", "履歷分析與 AI 助手頁")

    # application
    draw_dark_node(draw, (1500, 1030, 1810, 1112), "crawl_application_service", "查詢協調中心")
    draw_dark_node(draw, (1840, 1030, 2130, 1112), "notification_service", "通知協調")
    draw_dark_node(draw, (1500, 1160, 1780, 1242), "assistant.service", "RAG answer orchestration")
    draw_dark_node(draw, (1810, 1160, 2130, 1242), "resume.service", "履歷分析協調")
    draw_dark_node(draw, (1570, 1290, 2060, 1372), "runtime_maintenance_service", "maintenance / cache purge / hygiene")

    # background runtime
    draw_dark_node(draw, (1510, 300, 1760, 378), "crawl_scheduler", "掃描 due saved searches")
    draw_dark_node(draw, (1510, 430, 1760, 508), "query_runtime", "queue / signals API")
    draw_dark_node(draw, (1510, 560, 1760, 638), "crawl_worker", "背景抓取執行")
    draw_dark_node(draw, (1510, 690, 1760, 768), "backend_maintenance", "維護流程入口")
    draw_dark_node(draw, (1510, 820, 1760, 898), "sqlite_backup / restore", "備份與演練")
    draw_dark_node(draw, (1850, 430, 2130, 508), "line_webhook", "LINE webhook 入口")

    # pipeline
    draw_dark_node(draw, (2280, 420, 2580, 502), "connectors/*.py", "104 / 1111 / Cake / LinkedIn")
    draw_dark_node(draw, (2280, 550, 2580, 632), "detail_parsing.py", "detail sections / requirements")
    draw_dark_node(draw, (2280, 680, 2580, 762), "job_cleaning.py", "canonical normalization")
    draw_dark_node(draw, (2620, 550, 2890, 632), "pipeline.py", "dedupe / merge / persist")
    draw_dark_node(draw, (2620, 680, 2890, 762), "market_analysis.analyzer", "skills / tasks / role / relevance")
    draw_dark_node(draw, (2620, 810, 2890, 892), "market_history_store", "history archive")

    # AI
    draw_dark_node(draw, (2280, 1220, 2580, 1302), "assistant.chunks", "knowledge chunks")
    draw_dark_node(draw, (2280, 1340, 2580, 1422), "assistant.vector_index", "persistent ANN recall")
    draw_dark_node(draw, (2280, 1460, 2580, 1542), "assistant.retrieval", "hybrid rank / rerank")
    draw_dark_node(draw, (2620, 1220, 2920, 1302), "assistant.prompts", "mode-specific prompt contract")
    draw_dark_node(draw, (2620, 1340, 2920, 1422), "resume.extractors", "resume profile build")
    draw_dark_node(draw, (2620, 1460, 2920, 1542), "resume.matchers / scoring", "semantic + exact match")
    draw_dark_node(draw, (2460, 1600, 2740, 1682), "OpenAI responses", "LLM answer / parse")
    draw_dark_node(draw, (2780, 1600, 3060, 1682), "OpenAI embeddings", "vector similarity")

    # storage
    draw_dark_node(draw, (2750, 340, 3300, 422), "product_state.sqlite3", "saved searches / favorites / notification prefs / AI monitoring")
    draw_dark_node(draw, (2750, 490, 3300, 572), "query_runtime.sqlite3", "crawl jobs / signals / leases / runtime queue")
    draw_dark_node(draw, (2750, 640, 3300, 722), "user_submissions.sqlite3", "resume / user submissions")
    draw_dark_node(draw, (2750, 790, 3300, 872), "jobs_latest.json / snapshots", "current market snapshot")
    draw_dark_node(draw, (2750, 940, 3300, 1022), "market_history.sqlite3", "historical jobs archive")
    draw_dark_node(draw, (2750, 1090, 3300, 1172), "cache/", "embeddings / resume / runtime cache")

    # external
    draw_dark_node(draw, (2300, 90, 2540, 168), "104 / 1111 / Cake / LinkedIn", "job sources")
    draw_dark_node(draw, (2580, 90, 2720, 168), "LINE", "notification")
    draw_dark_node(draw, (2580, 200, 2720, 278), "Email", "notification")
    draw_dark_node(draw, (2760, 90, 2840, 168), "OpenAI", "LLM / embeddings")

    # arrows
    draw_dark_arrow(draw, [(322, 1578), (438, 1542)])
    draw_dark_arrow(draw, [(672, 1542), (718, 1542)])
    draw_dark_arrow(draw, [(1032, 1542), (1070, 1542)])
    draw_dark_arrow(draw, [(1030, 1542), (1030, 1660), (872, 1660)])
    draw_dark_arrow(draw, [(1202, 1660), (1478, 1070)])
    draw_dark_arrow(draw, [(848, 1660), (848, 1266), (838, 1266)])
    draw_dark_arrow(draw, [(782, 1266), (840, 1266)])
    draw_dark_arrow(draw, [(1190, 1266), (1490, 1070)])
    draw_dark_arrow(draw, [(860, 1390), (918, 1390)])
    draw_dark_arrow(draw, [(1282, 1390), (1490, 1070)])
    draw_dark_arrow(draw, [(842, 1502), (1490, 1198)])
    draw_dark_arrow(draw, [(1262, 1502), (1490, 1200)])
    draw_dark_arrow(draw, [(2062, 1330), (2748, 1130)])
    draw_dark_arrow(draw, [(2062, 1330), (2748, 530)])

    draw_dark_arrow(draw, [(1762, 470), (2748, 530)])
    draw_dark_arrow(draw, [(1762, 470), (1498, 600), (1498, 600)])
    draw_dark_arrow(draw, [(1762, 600), (2278, 460)])
    draw_dark_arrow(draw, [(1762, 600), (1498, 1070)])
    draw_dark_arrow(draw, [(1762, 340), (1762, 470)])
    draw_dark_arrow(draw, [(1762, 720), (1570, 1330)])
    draw_dark_arrow(draw, [(2132, 470), (2132, 1070), (1842, 1070)])

    draw_dark_arrow(draw, [(2542, 130), (2430, 420)])
    draw_dark_arrow(draw, [(2722, 130), (1842, 1070)])
    draw_dark_arrow(draw, [(2722, 240), (1842, 1070)])
    draw_dark_arrow(draw, [(2842, 130), (2922, 1640)])

    draw_dark_arrow(draw, [(2582, 590), (2618, 590)])
    draw_dark_arrow(draw, [(2582, 720), (2618, 720)])
    draw_dark_arrow(draw, [(2892, 590), (2892, 720)])
    draw_dark_arrow(draw, [(2892, 720), (2892, 850)])
    draw_dark_arrow(draw, [(2892, 720), (2748, 830)])
    draw_dark_arrow(draw, [(2892, 850), (2748, 980)])
    draw_dark_arrow(draw, [(2892, 590), (2748, 830)])
    draw_dark_arrow(draw, [(2582, 460), (2748, 830)])

    draw_dark_arrow(draw, [(1812, 1200), (2278, 1260)])
    draw_dark_arrow(draw, [(1812, 1200), (2618, 1260)])
    draw_dark_arrow(draw, [(1782, 1200), (2618, 1380)])
    draw_dark_arrow(draw, [(1782, 1200), (2618, 1500)])
    draw_dark_arrow(draw, [(2582, 1260), (2618, 1260)])
    draw_dark_arrow(draw, [(2582, 1380), (2618, 1380)])
    draw_dark_arrow(draw, [(2582, 1500), (2618, 1500)])
    draw_dark_arrow(draw, [(2922, 1260), (2460, 1640)])
    draw_dark_arrow(draw, [(2922, 1380), (2780, 1640)])
    draw_dark_arrow(draw, [(2922, 1500), (2780, 1640)])
    draw_dark_arrow(draw, [(2742, 1640), (1490, 1200)])
    draw_dark_arrow(draw, [(3062, 1640), (2280, 1380)])
    draw_dark_arrow(draw, [(2748, 1130), (2280, 1380)])
    draw_dark_arrow(draw, [(2748, 830), (2280, 1260)])
    draw_dark_arrow(draw, [(2748, 830), (1490, 1200)])
    draw_dark_arrow(draw, [(2748, 680), (2618, 1380)])

    footer = (
        "這張圖是功能框框版：把主要功能、模組與資料庫都拆成獨立節點。"
        "如果你還要更細，我下一張可以繼續拆成『AI / RAG 專用 flowchart』或『資料庫 / state 專用 flowchart』。"
    )
    draw_dark_round_rect(draw, (80, 1940, 3320, 2050), fill="#202020", outline="#2f2f2f", radius=22, width=2)
    draw_dark_text_block(draw, (110, 1972), footer, 3150, 22, fill=DARK_MUTED, light=True)

    save(image, path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate large system design diagram images.")
    parser.add_argument("--output-dir", default="/private/tmp/job-radar-diagrams", help="Output directory")
    args = parser.parse_args()
    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    build_overall(output_dir / "job-radar-overall-architecture.png")
    build_overall_detailed(output_dir / "job-radar-overall-architecture-detailed.png")
    build_system_flowchart_detailed(output_dir / "job-radar-system-flowchart-detailed.png")
    build_query_flow(output_dir / "job-radar-query-refresh-flow.png")
    build_ai_flow(output_dir / "job-radar-ai-rag-flow.png")
    print(output_dir)


if __name__ == "__main__":
    main()
