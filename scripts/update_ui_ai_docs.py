from __future__ import annotations

from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup


DETAIL_PATH = Path("/Users/zhuangcaizhen/Desktop/專案/UI練習/job-radar-ai-detailed-flow.html")
REPORT_PATH = Path("/Users/zhuangcaizhen/Desktop/專案/UI練習/job-radar-ai-llm-rag-report.html")


DETAIL_RAG_FLOW_HTML = """
<section class="section" id="rag-flow">
  <div class="section-header">
    <div class="kicker">04 RAG Flow</div>
    <h2>AI 助理 / 市場問答詳細流程圖</h2>
    <p>
      主線仍然是 snapshot-centered RAG：回答依賴這次搜尋抓回來、清洗完、分析完的市場快照，而不是整個歷史世界。
      另外現在 <code>general_chat</code> 也會保留市場檢索當語境；若是具體職缺薪資題且該職缺沒有真實薪資，
      則會在 retrieval 後再接一條薪資預估支線。
    </p>
  </div>
  <div class="flow-line">
    <article class="flow-step">
      <div class="index">1</div>
      <h3>問題進站與 mode routing</h3>
      <p>先判斷這題要走 <code>market_summary</code>、<code>personalized_guidance</code>、<code>job_comparison</code> 還是 <code>general_chat</code>，再把最近最多 2 輪問答摘要合進 retrieval query。</p>
      <div class="pill-row">
        <span class="pill">answer_mode</span>
        <span class="pill">2-turn context</span>
      </div>
    </article>
    <article class="flow-step">
      <div class="index">2</div>
      <h3>從 snapshot / resume 建 chunks</h3>
      <p>把 jobs、salary、skills、work content、market aggregate，以及履歷 facets + resume windows 轉成結構化 knowledge chunks，而不是直接把整份資料庫丟去做向量搜尋。</p>
      <div class="pill-row">
        <span class="pill">job-summary</span>
        <span class="pill">resume-window</span>
      </div>
    </article>
    <article class="flow-step">
      <div class="index">3</div>
      <h3>Hybrid Retrieval</h3>
      <p>先做 coarse candidate selection，再用 embedding、lexical overlap、signal overlap、source type bonus、role alignment、job reference bonus 與 market penalty 混合排序。</p>
      <div class="pill-row">
        <span class="pill">hybrid score</span>
        <span class="pill">candidate pruning</span>
      </div>
    </article>
    <article class="flow-step">
      <div class="index">4</div>
      <h3>Prompt + 回答 / 薪資支線</h3>
      <p>一般題目走回答模型的結構化 JSON 輸出；如果是具體職缺薪資題、職缺本身沒薪資，則再接 <code>Hybrid RAG + Ridge interval estimation</code>，用相似揭露薪資職缺做證據。</p>
      <div class="pill-row">
        <span class="pill">control / compact_qa</span>
        <span class="pill">salary estimate</span>
      </div>
    </article>
    <article class="flow-step">
      <div class="index">5</div>
      <h3>整理引用與前端區塊</h3>
      <p>回答完成後不直接照抄 retrieval 排序，而是重新挑 citation chunks；若有薪資預估，也會附帶 evidence citations 與限制說明。</p>
      <div class="pill-row">
        <span class="pill">citations</span>
        <span class="pill">section builder</span>
      </div>
    </article>
  </div>
  <div class="arrow-row"><div>→</div><div>→</div><div>→</div><div>→</div></div>
  <div class="three-col" style="margin-top:16px;">
    <article class="callout good">
      <h3>為什麼用 Market Snapshot 做 RAG</h3>
      <p>因為這個產品要回答的是「這次搜尋結果代表的市場」，不是做職涯百科。用 snapshot 做上下文，回答才會和畫面上的職缺、技能洞察與工作內容對得起來。</p>
    </article>
    <article class="callout warn">
      <h3>general_chat 現在的邊界</h3>
      <p><code>general_chat</code> 不再等於完全不檢索。它會保留市場脈絡與可選外部查詢，但 prompt 明確禁止硬把所有問題拉回求職市場。</p>
    </article>
    <article class="callout">
      <h3>這樣做的限制</h3>
      <p>回答仍以當前 snapshot 為核心。如果使用者問的是跨多次搜尋、跨月份或跨產業長期趨勢，仍需要獨立 historical retrieval 層，而不是直接混進目前 hot path。</p>
    </article>
  </div>
  <div class="callout" style="margin-top:16px;">
    <h3>薪資預測支線現在怎麼掛進來</h3>
    <p>
      這條線只處理「具體職缺」且「原始職缺沒有薪資」的情況。若原職缺已有真實薪資，就直接優先顯示真實資料；
      若是「AI 工程師市場薪資大概多少」這種市場題，仍維持 RAG-only，不會硬做泛化預測。
    </p>
  </div>
</section>
"""


DETAIL_RETRIEVAL_HTML = """
<section class="section" id="retrieval-deep-dive">
  <div class="section-header">
    <div class="kicker">05 Retrieval Deep Dive</div>
    <h2>RAG 檢索器怎麼挑資料</h2>
    <p>
      這套檢索器不是單純 embedding nearest neighbor。它會先從問題抽 signals / intents，再把 chunk 類型、角色對齊、
      job reference、aggregate/specific-job 差異一起考慮，目的是讓答案更像「產品化市場助理」，而不是只會把語意相近的字串拉上來。
    </p>
  </div>
  <div class="two-col">
    <article class="subcard">
      <h3>問題先做哪些理解</h3>
      <ul class="decision-list">
        <li>抽取 signals：例如 <code>python</code>、<code>rag</code>、<code>salary</code>、<code>location</code>、<code>role</code>。</li>
        <li>判斷 intents：例如 <code>skill_gap</code>、<code>work_content</code>、<code>salary</code>、<code>market</code>、<code>source_distribution</code>。</li>
        <li>判斷是不是 aggregate 問題，像「目前常見技能」會優先偏向 market aggregate chunks。</li>
        <li>判斷是不是 specific job 問題，像「這個職缺主要做什麼」會壓低 market chunks 的權重。</li>
        <li>comparison 題還會額外做 comparison coverage，避免只檢到其中一邊。</li>
      </ul>
    </article>
    <article class="subcard">
      <h3>Hybrid score 真正考慮什麼</h3>
      <ul class="decision-list">
        <li><strong>embedding</strong>：0.52，提供語意近似底盤。</li>
        <li><strong>lexical overlap</strong>：0.18，補字面命中。</li>
        <li><strong>signal overlap</strong>：0.22，補技能 / 類型訊號。</li>
        <li><strong>source type bonus</strong>：依 intent 加成最適合的 chunk 類型。</li>
        <li><strong>market priority bonus</strong>：把 <code>occurrences / importance</code> 轉成市場型 chunk 的偏好。</li>
        <li><strong>role alignment / job reference bonus</strong>：如果問題和 chunk 指向同一角色或同一職缺，會再加權。</li>
        <li><strong>specific-job market penalty</strong>：問具體職缺時，避免 market-skill / market-task 把 job-detail 蓋掉。</li>
      </ul>
    </article>
  </div>
  <div class="table-wrap">
    <table>
      <caption>Chunk 類型與用途</caption>
      <thead>
        <tr>
          <th>Chunk 類型</th>
          <th>來源</th>
          <th>適合回答什麼</th>
          <th>為什麼要保留</th>
          <th>問題點</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>job-summary</code></td>
          <td>每筆職缺的 title / company / source / summary / skills</td>
          <td>職缺比較、個別 JD 參考、來源例子</td>
          <td>最通用，是其他細類型 chunk 的保底證據</td>
          <td>資訊粒度混雜，不一定是回答某個子題最精準的來源</td>
        </tr>
        <tr>
          <td><code>job-salary</code></td>
          <td>有薪資資訊的職缺</td>
          <td>薪資區間、薪資揭露情況</td>
          <td>把薪資問題從一般 JD 摘要拆出去，避免被其他訊號淹沒</td>
          <td>很多平台本來就沒薪資，coverage 不完整</td>
        </tr>
        <tr>
          <td><code>job-skills</code></td>
          <td>required skill items / extracted skills</td>
          <td>技能需求、技能缺口</td>
          <td>讓技能回答更具體，不只停在 summary 文字</td>
          <td>技能欄位品質很吃 connector 與清洗規則</td>
        </tr>
        <tr>
          <td><code>job-work-content</code></td>
          <td>work content items</td>
          <td>工作內容、任務型問題</td>
          <td>支援「這個職位平常在做什麼」類問題</td>
          <td>若來源站點切段不穩，內容粒度可能很不一致</td>
        </tr>
        <tr>
          <td><code>market-skill-insight</code></td>
          <td>市場技能聚合結果</td>
          <td>常見技能、核心技能、優先補強</td>
          <td>能回答「整體市場」而不是只回答單筆職缺</td>
          <td>失去職缺細節，需要配 citation 才不會太抽象</td>
        </tr>
        <tr>
          <td><code>market-task-insight</code></td>
          <td>市場工作內容聚合結果</td>
          <td>常見工作內容、職責分布</td>
          <td>符合產品定位，讓助理更像市場分析器</td>
          <td>統計方法若太粗，會把不同細任務混在一起</td>
        </tr>
        <tr>
          <td><code>resume-summary</code></td>
          <td>履歷摘要、facets、resume windows</td>
          <td>個人化建議、技能缺口、投遞建議</td>
          <td>已不再只有單塊 summary，能提供比較細的個人背景證據</td>
          <td>還沒有做到 project / accomplishment 等更細層級</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div class="choice-grid" style="margin-top:16px;">
    <article class="stack-box">
      <h3>為什麼不是純向量檢索</h3>
      <p>純向量很容易把「語意像但資料型態不對」的 chunk 拉上來，例如問薪資卻拿到技能摘要。source type bonus、job reference bonus 與 market penalty 就是為了修這個問題。</p>
    </article>
    <article class="stack-box">
      <h3>為什麼要做 candidate 粗篩</h3>
      <p>全量 chunks 一多，全部做 embedding + hybrid rerank 的成本會膨脹。先粗篩候選，再精排，延遲和成本都比較可控。</p>
    </article>
    <article class="stack-box">
      <h3>citation 為什麼獨立選</h3>
      <p>最適合生成答案的 chunk，不一定最適合拿來展示證據。citation selection 應視為獨立步驟，這樣才能同時照顧回答可讀性與證據可查性。</p>
    </article>
  </div>
</section>
"""


DETAIL_ASSISTANT_MODES_HTML = """
<section class="section" id="assistant-modes">
  <div class="section-header">
    <div class="kicker">06 Answer Modes</div>
    <h2>AI 助理的四種回答模式</h2>
    <p>
      這裡沒有先做超複雜的 planner，而是先用輕量 mode routing 把回答風格、retrieval 策略與 section builder 收斂住。
      值得注意的是：<code>general_chat</code> 不代表完全不檢索，只是 prompt 會明確禁止硬把問題拉回求職市場。
    </p>
  </div>
  <div class="two-col">
    <article class="callout">
      <h3>market_summary</h3>
      <p>預設模式。適合問「目前常見技能是什麼」「這批職缺重點是什麼」。輸出會偏市場分布、核心技能、薪資樣態、趨勢提醒。</p>
    </article>
    <article class="callout">
      <h3>personalized_guidance</h3>
      <p>只有在有 <code>resume_profile</code> 且問題含「我 / 我的 / 履歷 / 適合我」等線索時才走。輸出會偏缺口、優先補強、投遞建議。</p>
    </article>
    <article class="callout">
      <h3>job_comparison</h3>
      <p>問題裡有「比較 / 差異 / vs / 哪個比較適合」等線索時走。除了檢索外，還會額外做 comparison coverage，保證比較對象都被帶進來。</p>
    </article>
    <article class="callout">
      <h3>general_chat</h3>
      <p>當問題不直接屬於求職主線時走這條。它仍可補市場檢索與可選外部查詢當語境，但回答會偏自然 QA，不會強制套用市場分析格式。</p>
    </article>
  </div>
  <div class="table-wrap">
    <table>
      <caption>這種 mode routing 的設計取捨</caption>
      <thead>
        <tr>
          <th>面向</th>
          <th>目前做法</th>
          <th>優點</th>
          <th>缺點</th>
          <th>替代方案</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>路由邏輯</td>
          <td>用 heuristics 判斷 <code>comparison / personalized / market / general_chat</code>。</td>
          <td>成本低、可預期、快、好 debug。</td>
          <td>語言表達一變，仍可能誤判 mode。</td>
          <td>可改成小模型 classifier，或拆成 <code>subject_mode / tone_mode / retrieval_mode</code> 三層。</td>
        </tr>
        <tr>
          <td>回答格式</td>
          <td>每種 mode 固定自己的 section builder。</td>
          <td>前端展示穩、容易做結構化 UI。</td>
          <td>自由度較低，對複合問題比較僵。</td>
          <td>可改成更通用的 section schema，再由前端動態 render。</td>
        </tr>
        <tr>
          <td>上下文來源</td>
          <td>主要來自 snapshot、optional resume profile，以及 general_chat 的語境補充。</td>
          <td>邊界清楚、易引用。</td>
          <td>無法自然回答跨 snapshot 的長期趨勢。</td>
          <td>可加歷史層 retrieval，但必須把資料層來源清楚標示。</td>
        </tr>
      </tbody>
    </table>
  </div>
</section>
"""


REPORT_ANN_HTML = """
<section class="section" id="ann">
  <div class="section-header">
    <div class="kicker">ANN / Vector Index</div>
    <h2>長期持久化向量索引目前做到哪裡</h2>
    <p>
      專案裡的 <code>PersistentANNIndex</code> 已不是只有空骨架。現在本地 <code>data/assistant_vector_index.sqlite3</code> 已實際存在，
      而且程式路徑能同步 <code>runtime snapshot / snapshot_file / snapshot_store / market_history</code>。目前比較準確的說法是：
      這塊已經進入「可工作的本地 persistent ANN」階段，但還不是多實例共享、獨立向量服務化的 production 最終形態。
    </p>
  </div>
  <div class="grid-2">
    <article class="panel">
      <h3>目前已具備</h3>
      <ul>
        <li>SQLite-backed persistent vector corpus</li>
        <li>random-projection LSH band search</li>
        <li>可同步 runtime snapshot</li>
        <li>可同步 snapshot file / snapshot store</li>
        <li>可同步 market_history job_posts</li>
        <li>runtime snapshot sync 已改成 hash-based incremental style</li>
        <li>本地已觀察到 <code>assistant_vector_index.sqlite3</code> 實體檔案，表示 steady-state index 不再只是理論 code path</li>
      </ul>
    </article>
    <article class="panel">
      <h3>目前仍然要誠實講的限制</h3>
      <ul>
        <li>現在是 product-local SQLite index，不是 shared vector service</li>
        <li>還沒有外部 dashboard 去追 corpus growth、fan-out、recall 趨勢</li>
        <li>多實例上線時不能直接把這一顆本地 SQLite 當共享索引</li>
        <li>若未來 corpus 持續擴大，仍建議升級成獨立索引服務或共享 backend</li>
      </ul>
    </article>
  </div>
  <div class="callout">
    這一段面試時可以這樣講：<strong>我不是只停在 embedding cache，而是已把 persistent ANN index 路徑落地到本地可運作狀態；下一步要補的是 shared backend、observability 與多實例部署策略。</strong>
  </div>
</section>
"""


REPORT_SCOPE_HTML = """
<section class="section" id="scope">
  <div class="section-header">
    <div class="kicker">Scope</div>
    <h2>AI 在這個專案裡到底做哪些工作</h2>
    <p>
      這個專案的 AI 不是只有一條鏈。它至少有四個實際工作面：求職問答、履歷 profile 建構、履歷與職缺語意匹配，以及檢索層的 embedding / persistent ANN。
    </p>
  </div>
  <div class="grid-2">
    <article class="panel">
      <h3>1. AI 助理問答</h3>
      <p>
        由 <code>JobMarketRAGAssistant</code> 驅動。它會先分類回答模式，再決定如何檢索、組 prompt、選 citations；具體職缺薪資題現在還會接薪資預估支線。
      </p>
      <ul>
        <li>主問題：市場摘要、個人化建議、職缺比較、一般對話</li>
        <li>核心價值：把當前快照轉成可問答的求職市場語境</li>
        <li>風險：回答品質高度依賴 chunking 與 retrieval，不是只靠模型本身</li>
      </ul>
    </article>
    <article class="panel">
      <h3>2. 履歷 profile 建構</h3>
      <p>
        使用 LLM 將履歷文字抽成 <code>summary / target_roles / core_skills / preferred_tasks / match_keywords</code>，供後續 match 與 personalized guidance 使用。
      </p>
      <ul>
        <li>不是把整份履歷直接丟給回答 prompt，而是先做 profile 化</li>
        <li>有 cache，可避免相同履歷反覆抽取</li>
        <li>缺點是目前仍偏摘要級，experience / project 尚未 chunk 化</li>
      </ul>
    </article>
    <article class="panel">
      <h3>3. 履歷與職缺匹配</h3>
      <p>
        這條鏈不是傳統 RAG，而是語意比對。會把履歷與職缺技能/任務/關鍵字轉成 embedding，再計算 semantic similarity。
      </p>
      <ul>
        <li>另有 title similarity LLM 與 rule-based scorer</li>
        <li>目前比較像 ranking system，不是聊天式回答</li>
        <li>這條鏈對面試很重要，因為它能證明你不只做 chatbot</li>
      </ul>
    </article>
    <article class="panel">
      <h3>4. 長期向量與檢索 cache</h3>
      <p>
        專案裡不只有 embedding cache，現在本地也已經有 <code>assistant_vector_index.sqlite3</code>。比較準確的描述是：persistent ANN 已能在本地工作，但還不是 shared vector service。
      </p>
      <ul>
        <li>local <code>assistant_vector_index.sqlite3</code>：已存在</li>
        <li><code>rag_embeddings</code>：主助理熱路徑的磁碟 cache</li>
        <li><code>resume_match_embeddings</code>：履歷 matching 的語意 cache</li>
        <li>下一步：shared backend、health metrics、multi-instance strategy</li>
      </ul>
    </article>
  </div>
</section>
"""


REPORT_LIVE_HTML = """
<section class="section" id="live">
  <div class="section-header">
    <div class="kicker">Live Snapshot</div>
    <h2>目前本地資料面可直接拿來講的狀態</h2>
    <p>
      這一段只保留能直接從目前 repo / data 目錄驗證的資訊，不再硬寫過期的事件筆數或平均延遲。這樣文件比較適合當現在版本的真實快照。
    </p>
  </div>
  <div class="grid-3">
    <article class="note-card">
      <h3>模型配置</h3>
      <ul>
        <li>Assistant Model：<code>gpt-4.1-mini</code></li>
        <li>Embedding Model：<code>text-embedding-3-large</code></li>
        <li>Resume LLM：<code>gpt-4.1-mini</code></li>
        <li>Title Similarity LLM：<code>gpt-4.1-mini</code></li>
        <li>Assistant fast profile output budget：<code>market 300 / personalized 320 / comparison 380 / general 220</code></li>
        <li>Persistent source sync interval：<code>900 秒 / 15 分鐘</code></li>
      </ul>
    </article>
    <article class="note-card">
      <h3>cache / 向量現況</h3>
      <ul>
        <li><code>rag_embeddings</code>：3818 檔，約 177.67 MB</li>
        <li><code>resume_match_embeddings</code>：2032 檔，約 122.70 MB</li>
        <li>總 cache：9090 檔，約 590.28 MB</li>
        <li>ANN index 檔案：已建立，約 1.48 MB</li>
        <li>runtime snapshot sync 已改成「snapshot hash 變動才同步」</li>
      </ul>
    </article>
    <article class="note-card">
      <h3>觀測與文件策略</h3>
      <ul>
        <li><code>ai_monitoring_events</code> 的 schema 與寫入路徑已在 codebase</li>
        <li>但這份本地資料不把事件筆數 / 平均延遲當固定 live 指標</li>
        <li>這頁現在優先使用能直接從檔案系統與設定驗證的數據</li>
        <li>如果要講延遲，建議用 backend console 或最新的實際執行樣本，不要背舊報表</li>
      </ul>
    </article>
  </div>
  <div class="grid-2" style="margin-top:16px;">
    <article class="panel">
      <h3>這輪可明確講的延遲控制</h3>
      <ul>
        <li>Assistant chunk build 有 process 內快取，同一份 snapshot / resume 組合不重建。</li>
        <li>Persistent ANN 的 runtime snapshot sync 只在 snapshot hash 變動時執行。</li>
        <li>Persistent source sync 節流到 <code>900 秒</code>，不再每次互動都碰長期 corpus。</li>
        <li>Assistant embedding 有 memory cache + disk cache，不必每次都重新打遠端 embedding。</li>
        <li>Assistant 回答長度改成 mode-aware output budget，而不是固定一個大 token 上限。</li>
      </ul>
    </article>
    <article class="panel">
      <h3>目前仍然要誠實講的限制</h3>
      <ul>
        <li>本地 SQLite ANN 可工作，但不是 shared vector service。</li>
        <li>cache 體積已經不小，之後仍需要更正式的 GC / shared backend 策略。</li>
        <li>這份本地資料不適合再硬寫舊的平均延遲數字，容易過期。</li>
        <li>如果要做 release-level latency 對照，還需要 steady-state telemetry 報表。</li>
      </ul>
    </article>
  </div>
</section>
"""


REPORT_EMBEDDING_HTML = """
<section class="section" id="embedding">
  <div class="section-header">
    <div class="kicker">Embedding / Cache Layer</div>
    <h2>Embedding、cache 與向量層在系統裡的實際角色</h2>
    <p>
      目前預設 embedding model 是 <code>text-embedding-3-large</code>。系統不是把所有原始資料直接丟去做 embedding，
      而是先把 snapshot / resume 轉成結構化 chunks，再把 retrieval query 與 candidate chunks 一起向量化。也就是說，
      embedding 在這裡負責「先找語意近的候選」，最後排名仍要靠 hybrid score 收斂。
    </p>
  </div>
  <div class="table-wrap">
    <table>
      <caption>目前 embedding / cache 分層</caption>
      <thead>
        <tr>
          <th>層</th>
          <th>目前用途</th>
          <th>資料位置</th>
          <th>目前優點</th>
          <th>目前缺口</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>process memory cache</td>
          <td>降低同一輪互動重複 embedding / profile / title 計算</td>
          <td>app process memory</td>
          <td>對熱路徑延遲很有效</td>
          <td>重啟後會消失，沒有跨 process reuse</td>
        </tr>
        <tr>
          <td>disk cache</td>
          <td>保存 assistant / resume embeddings 與中間結果</td>
          <td><code>data/cache/rag_embeddings</code>、其他 resume caches</td>
          <td>成本低、易維護，而且 repeated question 不必每次都打遠端 embedding API</td>
          <td>仍不是正式的 metrics backend，也缺 cache hit 長期趨勢圖</td>
        </tr>
        <tr>
          <td>persistent ANN index</td>
          <td>做長期候選召回</td>
          <td><code>data/assistant_vector_index.sqlite3</code></td>
          <td>已能承接 runtime / snapshot / history 三種來源</td>
          <td>還不是 shared backend，也未拆成獨立索引服務</td>
        </tr>
        <tr>
          <td>monitoring metadata</td>
          <td>追 cache hits、remote embeddings、ANN fan-out</td>
          <td><code>ai_monitoring_events</code></td>
          <td>已能回看是哪一層 cache 沒打中</td>
          <td>還沒做長期 trend dashboard 與告警</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div class="grid-2" style="margin-top:16px;">
    <article class="panel">
      <h3>實際被拿去 embed 的不是什麼</h3>
      <ul>
        <li>不是整份 HTML 原文。</li>
        <li>不是整個 JSON snapshot 一次送進去。</li>
        <li>而是 <code>job-summary / job-salary / job-skills / job-work-content / market-* / resume-*</code> 這些結構化 chunk。</li>
        <li>query 也不是只用原句，而是會帶上 answer mode 與最多 2 輪對話摘要。</li>
      </ul>
    </article>
    <article class="panel">
      <h3>這條路徑為什麼不是純 cosine similarity</h3>
      <ul>
        <li>embedding 先把語意近的候選拉出來。</li>
        <li>lexical overlap / signal overlap 補字面與任務訊號。</li>
        <li>source type bonus 把對的資料型態往前推。</li>
        <li>specific-job 問題還會壓低 market chunks，避免「語意像但類型錯」的證據搶位。</li>
      </ul>
    </article>
  </div>
  <div class="callout">
    這條鏈真正的意思是：<strong>embedding 在系統裡不是單一功能，而是 retrieval、matching、latency control、cost control 的共同基礎層。</strong>
  </div>
</section>
"""


REPORT_SALARY_HTML = """
<section class="section" id="salary-prediction">
  <div class="section-header">
    <div class="kicker">2026-04-14 Update</div>
    <h2>薪資預測 v1：Hybrid RAG + Interval Estimation</h2>
    <p>
      AI 助理現在除了傳統 RAG 問答，還多了一條「具體職缺薪資題」支線。這一版不是做全市場盲猜，而是只在
      <strong>具體職缺、原始職缺沒有真實薪資</strong> 的情況下，回傳 <code>AI 預估月薪區間 + 相似職缺證據 + 限制說明</code>。
    </p>
  </div>
  <div class="grid-2">
    <article class="panel">
      <h3>產品行為</h3>
      <ul>
        <li>若 job card 或 assistant 指到的職缺已經有真實薪資，就直接優先顯示真實薪資。</li>
        <li>若是具體職缺薪資題，且職缺沒有真實薪資，就走薪資預估支線。</li>
        <li>若是「AI 工程師市場薪資大概多少」這種市場題，仍維持 RAG-only，不會硬做泛化預測。</li>
        <li>若模型檔不存在、信心不足、或特徵不足，assistant 會回退到純 RAG，job card 則不顯示 AI 預估 chip。</li>
      </ul>
    </article>
    <article class="panel">
      <h3>模型與證據層</h3>
      <ul>
        <li>baseline 模型走 <code>TF-IDF + OneHot + numeric features + Ridge low/high regressor</code>。</li>
        <li>訓練資料來自 <code>jobs_latest.json</code> 與 <code>market_history.sqlite3</code> 的可解析薪資職缺。</li>
        <li>預測後不是只丟一組數字，而是再檢索 2-3 筆相似且有揭露薪資的職缺作 evidence。</li>
        <li>這條線是 <strong>Hybrid RAG + prediction</strong>，不是單純 LLM 自由生成，也不是純回歸黑盒。</li>
      </ul>
    </article>
  </div>
  <div class="table-wrap" style="margin-top:16px;">
    <table>
      <caption>薪資預測路徑何時會啟動</caption>
      <thead>
        <tr>
          <th>情境</th>
          <th>目前做法</th>
          <th>原因</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>職缺已有真實薪資</td>
          <td>直接顯示原始薪資，不覆蓋成 AI 預測</td>
          <td>避免和來源資料衝突，也保留資料可信度</td>
        </tr>
        <tr>
          <td>具體職缺 + 無薪資 + 模型可用 + confidence 足夠</td>
          <td>顯示 <code>AI 預估月薪 xx-yy</code>，並附 evidence citations</td>
          <td>這時候預測有明確對象，也有相似職缺可以支撐</td>
        </tr>
        <tr>
          <td>市場型薪資問題</td>
          <td>維持 RAG-only 市場摘要</td>
          <td>避免把角色市場行情和單一職缺估值混在一起</td>
        </tr>
        <tr>
          <td>模型不存在 / 信心不足 / 特徵不足</td>
          <td>assistant fallback 到純 RAG；job card 不顯示預估</td>
          <td>這條線寧願保守，不亂給數字</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div class="callout" style="margin-top:16px;">
    這個設計很值得講，因為它代表你沒有把「薪資預測」做成脫離產品脈絡的研究模型，而是把它收斂成
    <strong>只在證據足夠、場景明確、UI 不會和真實資料衝突時才啟用</strong> 的產品能力。
  </div>
</section>
"""


REPORT_VECTOR_NOTE_HTML = """
<article class="note-card">
  <h3>3. 本地向量索引已存在，但 shared corpus 還未成熟</h3>
  <p>
    現在本地已經能看到 <code>assistant_vector_index.sqlite3</code>，代表 persistent ANN 不再只是空的 code path。不過它目前仍是 product-local SQLite index，
    不是多實例共享的索引服務，因此「有本地 index」不等於「向量基礎設施已經全部完成」。
  </p>
  <ul>
    <li>改善方向：補 index health / corpus size / recall 監控</li>
    <li>改善方向：把本地 SQLite index 升級成 shared backend 或獨立索引服務</li>
  </ul>
</article>
"""


REPORT_OUTPUT_BUDGET_HTML = """
<article class="panel">
  <h3>Mode-based output budget</h3>
  <ul>
    <li>目前預設 latency profile：<code>fast</code></li>
    <li><code>market_summary</code>：<code>300</code></li>
    <li><code>personalized_guidance</code>：<code>320</code></li>
    <li><code>job_comparison</code>：<code>380</code></li>
    <li><code>general_chat</code>：<code>220</code></li>
    <li>報告類或較完整回答仍可切到 <code>balanced</code>，但不是目前互動主路徑預設</li>
  </ul>
  <p>
    這個設定的重點是把回答長度當成延遲與成本的第一層控管，而不是等 token 用完才事後觀察。它比一律給固定大 token 上限更像產品化做法。
  </p>
</article>
"""


def replace_section(soup: BeautifulSoup, section_id: str, html: str) -> None:
    current = soup.find("section", id=section_id)
    if current is None:
        raise RuntimeError(f"Section not found: {section_id}")
    replacement = BeautifulSoup(html, "html.parser").find("section")
    if replacement is None:
        raise RuntimeError(f"Replacement section invalid: {section_id}")
    current.replace_with(replacement)


def insert_after_section(soup: BeautifulSoup, anchor_id: str, html: str) -> None:
    new_section = BeautifulSoup(html, "html.parser").find("section")
    if new_section is None:
        raise RuntimeError("Inserted section invalid")
    existing = soup.find("section", id=new_section.get("id"))
    if existing is not None:
        existing.replace_with(new_section)
        return
    anchor = soup.find("section", id=anchor_id)
    if anchor is None:
        raise RuntimeError(f"Anchor section not found: {anchor_id}")
    anchor.insert_after(new_section)


def replace_article_by_heading(
    soup: BeautifulSoup,
    heading_text: str | Iterable[str],
    html: str,
) -> None:
    candidates = (
        [heading_text]
        if isinstance(heading_text, str)
        else list(heading_text)
    )
    heading = None
    for candidate in candidates:
        heading = soup.find(["h2", "h3"], string=candidate)
        if heading is not None:
            break
    if heading is None:
        raise RuntimeError(f"Heading not found: {candidates}")
    article = heading.find_parent("article")
    if article is None:
        raise RuntimeError(f"Article not found for heading: {heading_text}")
    replacement = BeautifulSoup(html, "html.parser").find("article")
    if replacement is None:
        raise RuntimeError(f"Replacement article invalid for heading: {heading_text}")
    article.replace_with(replacement)


def update_detail_page() -> None:
    soup = BeautifulSoup(DETAIL_PATH.read_text(encoding="utf-8"), "html.parser")
    replace_section(soup, "rag-flow", DETAIL_RAG_FLOW_HTML)
    replace_section(soup, "retrieval-deep-dive", DETAIL_RETRIEVAL_HTML)
    replace_section(soup, "assistant-modes", DETAIL_ASSISTANT_MODES_HTML)
    DETAIL_PATH.write_text(str(soup), encoding="utf-8")


def update_report_page() -> None:
    soup = BeautifulSoup(REPORT_PATH.read_text(encoding="utf-8"), "html.parser")
    replace_section(soup, "scope", REPORT_SCOPE_HTML)
    replace_section(soup, "live", REPORT_LIVE_HTML)
    replace_section(soup, "ann", REPORT_ANN_HTML)
    replace_section(soup, "embedding", REPORT_EMBEDDING_HTML)
    insert_after_section(soup, "embedding", REPORT_SALARY_HTML)
    replace_article_by_heading(
        soup,
        (
            "3. live 向量索引尚未形成穩定資料面",
            "3. 本地向量索引已存在，但 shared corpus 還未成熟",
        ),
        REPORT_VECTOR_NOTE_HTML,
    )
    replace_article_by_heading(
        soup,
        "Mode-based output budget",
        REPORT_OUTPUT_BUDGET_HTML,
    )
    REPORT_PATH.write_text(str(soup), encoding="utf-8")


def main() -> None:
    update_detail_page()
    update_report_page()


if __name__ == "__main__":
    main()
