from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup


UI_ROOT = Path("/Users/zhuangcaizhen/Desktop/專案/UI練習")
INDEX_PATH = UI_ROOT / "index.html"
LEGACY_INDEX_PATH = UI_ROOT / "legacy-system-design-course.html"
TODAY = "2026-04-12"

DOC_LINKS = [
    ("文件首頁", "index.html"),
    ("總架構手冊", "job-radar-system-architecture.html"),
    ("完整結構圖", "job-radar-complete-structure-diagram.html"),
    ("AI 詳細流程", "job-radar-ai-detailed-flow.html"),
    ("AI / LLM / RAG 報告", "job-radar-ai-llm-rag-report.html"),
    ("DB Schema 手冊", "job-radar-db-schema-handbook.html"),
    ("產品與系統 Playbook", "job-radar-product-system-playbook.html"),
    ("Testing 手冊", "job-radar-testing-handbook.html"),
    ("學習地圖", "job-radar-learning-curriculum.html"),
    ("UI Catalog", "ui-catalog.html"),
    ("歷史保留", "legacy-system-design-course.html"),
]

PAGE_TITLES = {
    "job-radar-ai-detailed-flow.html": "Job Radar AI Detailed Flow",
    "job-radar-ai-llm-rag-report.html": "Job Radar AI / LLM / RAG 完整報告",
    "job-radar-complete-structure-diagram.html": "Job Radar 完整結構圖",
    "job-radar-db-schema-handbook.html": "Job Radar DB Schema Handbook",
    "job-radar-learning-curriculum.html": "Job Radar Learning Curriculum",
    "job-radar-product-system-playbook.html": "Job Radar Product & System Design Playbook",
    "job-radar-system-architecture.html": "Job Radar System Architecture",
    "job-radar-testing-handbook.html": "Job Radar Testing Handbook",
    "ui-catalog.html": "Job Radar UI Catalog",
}

PAGE_SUMMARIES = {
    "job-radar-system-architecture.html": "這份頁面是 Job Radar 的主架構手冊，負責把產品邊界、模組分工、資料流、故障模式與演進路線串成主線故事。",
    "job-radar-complete-structure-diagram.html": "這份頁面是完整版結構圖說明，適合拿來對照模組、資料層與主要服務之間的實際連接方式。",
    "job-radar-ai-detailed-flow.html": "這份頁面聚焦 AI 助理與履歷分析流程，負責把 mode routing、retrieval、prompt、resume matching 與後續擴充講清楚。",
    "job-radar-ai-llm-rag-report.html": "這份頁面是 AI / LLM / RAG 深度報告，重點在模型路由、chunking、retrieval、benchmark、延遲與演進順序。",
    "job-radar-db-schema-handbook.html": "這份頁面聚焦資料落地策略，說明 product_state、query_runtime、user_submissions、market_history 與 cache 的邊界。",
    "job-radar-product-system-playbook.html": "這份頁面從產品思維切入，整理價值鏈、使用者回訪機制、功能優先序與系統設計判斷。",
    "job-radar-learning-curriculum.html": "這份頁面是學習地圖，適合拿來規劃你接下來要補強的工程、AI、資料與測試能力。",
    "job-radar-testing-handbook.html": "這份頁面聚焦 testing 與 regression 策略，對應這個專案的高風險資料流、背景流程與 AI 模組。",
    "ui-catalog.html": "這份頁面是 UI 元件與設計語言目錄，現在也被納入 Job Radar 文件站的導覽結構中。",
}


def build_footer_fragment(summary: str) -> str:
    links_html = "".join(
        (
            f'<a href="{href}" '
            'style="display:inline-flex;align-items:center;justify-content:center;'
            'padding:0.62rem 0.9rem;border-radius:999px;border:1px solid rgba(90,79,136,0.18);'
            'background:rgba(255,255,255,0.72);color:inherit;text-decoration:none;'
            'font-size:0.92rem;font-weight:700;">'
            f"{label}</a>"
        )
        for label, href in DOC_LINKS
    )
    return f"""
<p>{summary}</p>
<div style="display:flex;flex-wrap:wrap;gap:0.7rem;margin-top:1rem;">{links_html}</div>
<div style="margin-top:1rem;font-size:0.92rem;line-height:1.75;color:rgba(79,72,107,0.88);">
  最後整理：{TODAY}。主入口、文件串接與頁尾導覽已統一，舊的股票盯盤課程內容已移到
  <a href="legacy-system-design-course.html" style="color:inherit;font-weight:700;">歷史保留頁</a>。
</div>
"""


def build_index_html() -> str:
    cards = [
        {
            "label": "主架構",
            "title": "Job Radar 全系統架構",
            "href": "job-radar-system-architecture.html",
            "desc": "先用這頁建立全局視角，理解 Streamlit UI、背景流程、AI、資料層與治理邊界。",
        },
        {
            "label": "流程圖",
            "title": "完整結構圖",
            "href": "job-radar-complete-structure-diagram.html",
            "desc": "看模組與資料層怎麼連起來，適合面試時拿來對照檔案與服務。",
        },
        {
            "label": "AI 流程",
            "title": "AI 詳細流程",
            "href": "job-radar-ai-detailed-flow.html",
            "desc": "把 AI 助理、履歷分析、RAG 邊界、chunking 與 matching 分開看清楚。",
        },
        {
            "label": "AI 報告",
            "title": "AI / LLM / RAG 完整報告",
            "href": "job-radar-ai-llm-rag-report.html",
            "desc": "適合面試時講 AI 成熟度、延遲、精準度、benchmark 與下一步演進。",
        },
        {
            "label": "資料層",
            "title": "DB Schema 手冊",
            "href": "job-radar-db-schema-handbook.html",
            "desc": "理解 product_state、query_runtime、market_history、user_submissions 與 cache 的分工。",
        },
        {
            "label": "產品思維",
            "title": "產品與系統 Playbook",
            "href": "job-radar-product-system-playbook.html",
            "desc": "從產品價值鏈出發，整理功能優先序、留存設計與系統取捨。",
        },
        {
            "label": "測試",
            "title": "Testing 手冊",
            "href": "job-radar-testing-handbook.html",
            "desc": "把測試策略、mock 邊界、手動回歸清單與 repo 現況收斂成一頁。",
        },
        {
            "label": "學習",
            "title": "學習地圖",
            "href": "job-radar-learning-curriculum.html",
            "desc": "如果你要持續補強這個專案，這頁是課表與技能樹。",
        },
        {
            "label": "設計資產",
            "title": "UI Catalog",
            "href": "ui-catalog.html",
            "desc": "集中整理 UI 元件、文案、互動與展示範例，方便後續視覺整理。",
        },
        {
            "label": "歷史保留",
            "title": "舊版系統設計課 Archive",
            "href": "legacy-system-design-course.html",
            "desc": "舊首頁的股票盯盤課程已保留在這裡，不刪除，但不再作為主入口。",
        },
    ]
    cards_html = "".join(
        f"""
        <a class="card" href="{item['href']}">
          <div class="card-label">{item['label']}</div>
          <h3>{item['title']}</h3>
          <p>{item['desc']}</p>
        </a>
        """
        for item in cards
    )
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Job Radar 文件中心</title>
    <style>
      :root {{
        --bg: #f5f1ff;
        --panel: rgba(255, 255, 255, 0.82);
        --panel-strong: #ffffff;
        --ink: #201a45;
        --muted: #655e87;
        --line: rgba(97, 77, 177, 0.14);
        --brand: #6d57f7;
        --mint: #48c59d;
        --gold: #ffc969;
        --shadow: 0 24px 60px rgba(63, 43, 138, 0.12);
        --radius-xl: 32px;
        --radius-lg: 24px;
        --radius-md: 18px;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: "Avenir Next", "PingFang TC", "Noto Sans TC", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(255,255,255,0.88), transparent 28%),
          radial-gradient(circle at 88% 8%, rgba(109,87,247,0.16), transparent 22%),
          linear-gradient(145deg, #f8f5ff 0%, #f0ebff 48%, #f6fbff 100%);
      }}
      .shell {{
        max-width: 1320px;
        margin: 0 auto;
        padding: 28px 24px 80px;
      }}
      .hero, .section, .footer {{
        border: 1px solid var(--line);
        border-radius: var(--radius-xl);
        background: var(--panel);
        backdrop-filter: blur(16px);
        box-shadow: var(--shadow);
      }}
      .hero {{
        padding: 36px;
        display: grid;
        grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
        gap: 24px;
      }}
      .eyebrow {{
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 0.45rem 0.75rem;
        border-radius: 999px;
        background: rgba(109,87,247,0.1);
        color: var(--brand);
        font-size: 0.88rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }}
      h1 {{
        margin: 18px 0 14px;
        font-size: clamp(2.2rem, 4vw, 4.4rem);
        line-height: 1.04;
      }}
      .hero p {{
        margin: 0;
        color: var(--muted);
        line-height: 1.8;
        font-size: 1rem;
      }}
      .hero-panel {{
        padding: 22px;
        border-radius: var(--radius-lg);
        border: 1px solid rgba(97, 77, 177, 0.1);
        background: var(--panel-strong);
      }}
      .hero-panel h2, .section h2 {{
        margin: 0 0 12px;
        font-size: 1.28rem;
      }}
      .hero-list, .reading-list, .history-list {{
        display: grid;
        gap: 12px;
        padding: 0;
        margin: 0;
        list-style: none;
      }}
      .hero-list li, .reading-list li, .history-list li {{
        padding: 14px 16px;
        border-radius: 18px;
        border: 1px solid rgba(97, 77, 177, 0.1);
        background: rgba(245, 241, 255, 0.72);
        color: var(--muted);
        line-height: 1.7;
      }}
      .section {{
        margin-top: 24px;
        padding: 30px;
      }}
      .section-head {{
        display: flex;
        justify-content: space-between;
        gap: 18px;
        align-items: end;
        margin-bottom: 20px;
      }}
      .section-head p {{
        margin: 0;
        color: var(--muted);
        line-height: 1.75;
        max-width: 760px;
      }}
      .pill {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 0.42rem 0.7rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 800;
        background: rgba(72, 197, 157, 0.12);
        color: #218366;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 18px;
      }}
      .card {{
        display: block;
        padding: 22px;
        border-radius: var(--radius-lg);
        border: 1px solid rgba(97, 77, 177, 0.12);
        background: var(--panel-strong);
        box-shadow: 0 18px 42px rgba(63, 43, 138, 0.08);
        transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
      }}
      .card:hover {{
        transform: translateY(-4px);
        border-color: rgba(109,87,247,0.26);
        box-shadow: 0 22px 48px rgba(63, 43, 138, 0.12);
      }}
      .card-label {{
        display: inline-flex;
        padding: 0.36rem 0.6rem;
        border-radius: 999px;
        background: rgba(109,87,247,0.1);
        color: var(--brand);
        font-size: 0.8rem;
        font-weight: 800;
      }}
      .card h3 {{
        margin: 14px 0 10px;
        font-size: 1.25rem;
      }}
      .card p {{
        margin: 0;
        color: var(--muted);
        line-height: 1.78;
      }}
      .reading-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
      }}
      .reading-item {{
        padding: 18px;
        border-radius: var(--radius-md);
        border: 1px solid rgba(97, 77, 177, 0.1);
        background: rgba(255,255,255,0.72);
      }}
      .reading-item strong {{
        display: block;
        margin-bottom: 8px;
        font-size: 1rem;
      }}
      .reading-item p {{
        margin: 0;
        color: var(--muted);
        line-height: 1.72;
      }}
      .footer {{
        margin-top: 24px;
        padding: 24px 28px;
      }}
      .footer p {{
        margin: 0;
        color: var(--muted);
        line-height: 1.8;
      }}
      .footer-links {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 16px;
      }}
      .footer-link {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.62rem 0.9rem;
        border-radius: 999px;
        border: 1px solid rgba(90,79,136,0.18);
        background: rgba(255,255,255,0.72);
        color: inherit;
        text-decoration: none;
        font-size: 0.92rem;
        font-weight: 700;
      }}
      .footer-note {{
        margin-top: 12px;
        font-size: 0.92rem;
      }}
      @media (max-width: 980px) {{
        .hero, .grid, .reading-grid {{
          grid-template-columns: 1fr;
        }}
      }}
      @media (max-width: 640px) {{
        .shell {{ padding: 16px 14px 72px; }}
        .hero, .section, .footer {{ padding: 22px 18px; border-radius: 24px; }}
        h1 {{ font-size: 2.3rem; }}
      }}
    </style>
  </head>
  <body>
    <div class="shell">
      <section class="hero">
        <div>
          <span class="eyebrow">Docs Hub</span>
          <h1>Job Radar 文件中心</h1>
          <p>
            這次整理把 UI 練習資料夾裡的 Job Radar 手冊頁重新收斂成單一入口。主入口現在只服務
            Job Radar 文件，舊的股票盯盤課程內容不刪除，但已移到歷史保留頁。你之後要看架構、AI、DB、
            testing、產品思維或學習地圖，都可以從這裡進去。
          </p>
        </div>
        <div class="hero-panel">
          <h2>這次整理重點</h2>
          <ul class="hero-list">
            <li>主首頁改成 Job Radar 文件中心，不再混用舊題材。</li>
            <li>所有 Job Radar 手冊頁的 footer 與交叉連結統一。</li>
            <li>保留舊首頁內容，避免先前教學素材遺失。</li>
            <li>新增清楚的閱讀順序，方便面試與複習時快速進場。</li>
          </ul>
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <div>
            <span class="pill">Current Docs</span>
            <h2>主文件入口</h2>
            <p>如果你要對面試官展示完整系統，先從主架構與完整結構圖開始；如果要講 AI，則直接走 AI 報告與詳細流程。</p>
          </div>
        </div>
        <div class="grid">
          {cards_html}
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <div>
            <span class="pill">Reading Order</span>
            <h2>建議閱讀順序</h2>
            <p>這樣讀可以最快把產品、系統、AI、資料與 testing 講成同一條故事線。</p>
          </div>
        </div>
        <div class="reading-grid">
          <div class="reading-item">
            <strong>1. 建立全局</strong>
            <p>先看總架構手冊，再對照完整結構圖，確立模組邊界與資料層分工。</p>
          </div>
          <div class="reading-item">
            <strong>2. 進入 AI 主線</strong>
            <p>接著看 AI / LLM / RAG 報告，再補 AI 詳細流程，把 retrieval、prompt、resume matching 講清楚。</p>
          </div>
          <div class="reading-item">
            <strong>3. 補上資料與品質</strong>
            <p>再讀 DB Schema 與 Testing 手冊，讓設計不只停在功能，而是延伸到資料與回歸控制。</p>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <div>
            <span class="pill">History</span>
            <h2>歷史保留策略</h2>
            <p>這次沒有刪除舊資料，而是把不再作為主入口的內容獨立保留。這樣主線更乾淨，同時不會失去先前累積的教學材料。</p>
          </div>
        </div>
        <ul class="history-list">
          <li><strong>已保留：</strong>原本的股票盯盤 Web 系統設計課首頁內容已封存到 <a href="legacy-system-design-course.html">legacy-system-design-course.html</a>。</li>
          <li><strong>主入口已更新：</strong>新首頁只保留 Job Radar 相關文件，避免兩條題材混雜。</li>
          <li><strong>交叉導覽已補齊：</strong>各文件頁尾都可以互相跳轉，不需要再回頭找散落的單頁。</li>
        </ul>
      </section>

      <footer class="footer">
        <p>
          最後整理：{TODAY}。這個入口現在的角色是 Job Radar 文件中心，不再兼任其他題材的首頁。
          如果你要示範「我如何從專案整理出架構、AI、DB、測試與學習材料」，這頁可以直接當成你的起點。
        </p>
        <div class="footer-links">
          {''.join(f'<a class="footer-link" href="{href}">{label}</a>' for label, href in DOC_LINKS)}
        </div>
        <div class="footer-note">歷史資料已保留；主入口已收斂；後續若再新增手冊頁，建議直接從這裡掛入口，不要再另開平行首頁。</div>
      </footer>
    </div>
  </body>
</html>
"""


def archive_current_index() -> None:
    current_html = INDEX_PATH.read_text(encoding="utf-8")
    if "股票盯盤 Web 系統設計課" not in current_html:
        return
    if not LEGACY_INDEX_PATH.exists():
        archived_html = current_html.replace(
            "<title>股票盯盤 Web 系統設計課</title>",
            "<title>Legacy System Design Course Archive</title>",
            1,
        )
        archive_banner = """
        <div style="margin:0 auto 18px;max-width:1480px;padding:0 28px;">
          <div style="padding:14px 16px;border-radius:18px;border:1px solid rgba(24,21,17,0.12);background:rgba(255,250,240,0.86);font-size:0.94rem;line-height:1.7;color:#62594c;">
            這頁是歷史保留頁。原本的首頁內容已封存於此，新的 Job Radar 文件中心請回
            <a href="index.html" style="color:inherit;font-weight:700;">index.html</a>。
          </div>
        </div>
        """
        archived_html = archived_html.replace('<div class="shell">', archive_banner + '\n    <div class="shell">', 1)
        LEGACY_INDEX_PATH.write_text(archived_html, encoding="utf-8")


def update_html_page(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    if soup.title and path.name in PAGE_TITLES:
        soup.title.string = PAGE_TITLES[path.name]

    summary = PAGE_SUMMARIES.get(path.name)
    if summary:
        footer = soup.find("footer", class_="footer")
        if footer is None:
            footer = soup.new_tag("footer")
            footer["class"] = ["footer"]
            footer["style"] = (
                "margin:32px auto 0;max-width:1320px;padding:24px;border-radius:24px;"
                "border:1px solid rgba(97,77,177,0.14);background:rgba(255,255,255,0.82);"
                "box-shadow:0 24px 60px rgba(63,43,138,0.12);"
            )
            body = soup.body
            if body is not None:
                body.append(footer)

        footer.clear()
        footer_fragment = BeautifulSoup(build_footer_fragment(summary), "html.parser")
        for node in list(footer_fragment.contents):
            footer.append(node)

    if path.name == "ui-catalog.html":
        body = soup.body
        if body is not None and soup.find("footer", class_="footer") is None:
            footer = soup.new_tag("footer")
            footer["class"] = ["footer"]
            footer["style"] = (
                "max-width:1320px;margin:24px auto 36px;padding:24px;border-radius:24px;"
                "border:1px solid rgba(97,77,177,0.14);background:rgba(255,255,255,0.82);"
                "box-shadow:0 24px 60px rgba(63,43,138,0.12);"
            )
            footer_fragment = BeautifulSoup(build_footer_fragment(PAGE_SUMMARIES[path.name]), "html.parser")
            for node in list(footer_fragment.contents):
                footer.append(node)
            scripts = body.find_all("script")
            if scripts:
                scripts[0].insert_before(footer)
            else:
                body.append(footer)

    rendered = str(soup)
    if not rendered.lstrip().lower().startswith("<!doctype html>"):
        rendered = "<!DOCTYPE html>\n" + rendered
    path.write_text(rendered, encoding="utf-8")


def main() -> None:
    archive_current_index()
    INDEX_PATH.write_text(build_index_html(), encoding="utf-8")

    for page in sorted(UI_ROOT.glob("*.html")):
        if page.name in {"index.html", LEGACY_INDEX_PATH.name}:
            continue
        update_html_page(page)


if __name__ == "__main__":
    main()
