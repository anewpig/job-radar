"""提供 deterministic fake client，讓 baseline 不受外部 API 波動影響。"""

from __future__ import annotations

from types import SimpleNamespace


class FakeEmbeddingsAPI:
    """依文字主題回傳固定向量，模擬 embedding 行為。"""

    def create(self, *, model, input):  # noqa: A002
        data = []
        for text in input:
            lowered = text.lower()
            if any(token in lowered for token in ("薪資", "月薪", "salary", "60,000", "80,000")):
                vector = [1.0, 0.0, 0.0, 0.0, 0.0]
            elif any(token in lowered for token in ("技能", "python", "llm", "rag", "docker", "aws", "langchain", "langgraph", "向量資料庫", "knowledge base")):
                vector = [0.0, 1.0, 0.0, 0.0, 0.0]
            elif any(token in lowered for token in ("firmware", "韌體", "rtos", "arm", "mips", "bluetooth", "embedded", "linux", "c++")):
                vector = [0.0, 0.0, 1.0, 0.0, 0.0]
            elif any(token in lowered for token in ("product", "figma", "jira", "prd", "pm", "roadmap", "mvp")):
                vector = [0.0, 0.0, 0.0, 1.0, 0.0]
            else:
                vector = [0.0, 0.0, 0.0, 0.0, 1.0]
            data.append(SimpleNamespace(embedding=vector))
        return SimpleNamespace(data=data)


class FakeResponsesAPI:
    """模擬 responses API，針對題型回傳固定答案。"""

    def create(self, **kwargs):
        prompt = kwargs["input"]
        question_line = prompt.splitlines()[0] if prompt else ""
        lowered_question = question_line.lower()
        if (
            any(token in question_line for token in ("104", "1111", "Cake", "LinkedIn"))
            or "來源比較" in question_line
            or "來源平台" in question_line
            or "哪個平台" in question_line
            or "哪個來源" in question_line
            or "最有代表性" in question_line
            or ("來源" in question_line and "平台" in question_line)
        ):
            text = "104 職缺量最多，Cake 偏 RAG / PM，LinkedIn 偏 AI 平台與 Embedded Linux，1111 偏韌體。"
        elif any(token in question_line for token in ("地點", "城市", "新北市", "台北市", "新竹市", "台北", "新北", "新竹")):
            text = "AI 類職缺多集中在新北市、台北市，韌體類多集中在新竹市。"
        elif any(token in question_line for token in ("新鮮人", "junior", "資深", "年資", "起薪", "幾年經驗")):
            text = "一般 AI 類月薪多在 60,000 到 80,000，資深平台職缺可到 90,000 以上。"
        elif any(token in question_line for token in ("值得優先投遞", "最值得先追", "先關注哪些職缺", "優先鎖定", "先投三種職缺", "先看成功率")):
            text = "可以優先關注 AI應用工程師、RAG AI Engineer 與 Product Manager。"
        elif any(token in question_line for token in ("重點能力", "核心技能", "技能主軸", "能力主軸", "技能組合", "市場技能角度", "市場核心技能")):
            text = "目前市場重點集中在 Python、LLM 與跨系統整合能力。"
        elif any(token in question_line for token in ("總結", "一句話摘要", "一句摘要", "三個重點", "市場快照", "市場重點", "快速整理")):
            text = "目前市場重點集中在 Python、LLM、RAG 與跨系統整合；RAG 類工作常見 Knowledge Base、向量資料庫與 API；韌體聚焦 C/C++、RTOS、ARM。"
        elif any(token in question_line for token in ("還差哪些能力", "還缺哪些能力", "還要補哪些能力", "還差哪些技能", "缺少的技術", "補哪些技能", "缺口", "還需要補足", "補足")):
            text = "目前主要缺口集中在 Docker 與 AWS，這兩項會影響部署與實務整合能力。"
        elif any(token in question_line for token in ("薪資", "月薪", "區間")) or "salary" in lowered_question:
            text = "目前 AI 類職缺多落在月薪 60,000 到 80,000，資深職缺可再往上。"
        elif any(token in question_line for token in ("韌體", "Firmware")) and any(token in question_line for token in ("最值得優先補強", "優先補強", "最值得先學")):
            text = "建議第一波先補 C/C++、RTOS、ARM，之後再延伸到 Embedded Linux。"
        elif any(token in question_line for token in ("最值得優先補強", "優先補強", "最值得先學", "先補 Python", "先補 LLM")):
            text = "建議第一波先補 Python、LLM、RAG，之後再延伸到 Docker。"
        elif any(token in lowered_question for token in ("product manager", "pm")) or "產品經理" in question_line:
            text = "產品經理相關工作通常圍繞 roadmap、PRD、MVP 定義與跨部門協作。"
        elif any(token in question_line for token in ("韌體", "Firmware")):
            text = "韌體類職缺通常聚焦 C/C++、RTOS、ARM，若能再補 Linux 會更完整。"
        elif any(token in question_line for token in ("知識庫", "向量資料庫", "RAG", "AI Agent")):
            text = "這類工作通常涵蓋 Knowledge Base、向量資料庫、RAG workflow 與 API 整合。"
        else:
            text = "目前市場重點集中在 Python、LLM 與跨系統整合能力。"
        return SimpleNamespace(output_text=text)

    def parse(self, **kwargs):
        input_text = kwargs["input"]
        lowered_context = input_text.lower()
        prefers_rag = "rag ai engineer" in lowered_context or "向量資料庫" in lowered_context or "知識庫系統" in lowered_context
        prefers_firmware = "韌體工程師" in input_text or "bluetooth" in lowered_context or "rtos" in lowered_context or "arm" in lowered_context
        prefers_pm = "product manager" in lowered_context or "roadmap" in lowered_context or "prd" in lowered_context
        prefers_ai_engineer = any(token in lowered_context for token in ("machine learning engineer", "ml engineer", "ai engineer", "pytorch", "tensorflow"))
        prefers_software = any(token in lowered_context for token in ("backend engineer", "software engineer", "api design", "system design", "rest api"))
        prefers_solution = any(token in lowered_context for token in ("application engineer", "field application engineer", "solution engineer", "technical support", "requirement analysis", "customer communication", "fae"))
        scores = []
        for line in input_text.splitlines():
            if "job_index=" not in line:
                continue
            index = int(line.split("job_index=")[1].split(";")[0].strip())
            lowered = line.lower()
            if "ai應用工程師" in lowered:
                similarity = 0.91 if prefers_rag else 0.97
                reason = "中文職稱完全命中" if not prefers_rag else "與 RAG 職稱相近，但不如 RAG 專職精準"
            elif "rag ai engineer" in lowered or "ai / ai agent" in lowered:
                similarity = 0.98 if prefers_rag else 0.95
                reason = "RAG / AI Agent 職類與 AI 應用工程高度相近"
            elif "machine learning engineer" in lowered:
                similarity = 0.98 if prefers_ai_engineer else 0.88
                reason = "AI / ML 職類與模型訓練技能高度匹配" if prefers_ai_engineer else "AI 職類相近，但履歷訊號不夠集中"
            elif "backend engineer" in lowered:
                similarity = 0.98 if prefers_software else 0.86
                reason = "Backend / API / System Design 與軟體工程職類高度匹配" if prefers_software else "軟體工程職類相近，但訊號不夠集中"
            elif "ai solution engineer" in lowered:
                similarity = 0.98 if prefers_solution else 0.85
                reason = "應用工程、FAE 與客戶導入能力高度匹配" if prefers_solution else "應用工程職類相近，但導入訊號不足"
            elif "project manager / ai delivery" in lowered:
                similarity = 0.97 if prefers_pm else 0.84
                reason = "專案交付與利害關係人協作能力高度匹配" if prefers_pm else "PM 職類相近，但交付訊號不夠集中"
            elif "藍牙韌體設計工程師" in lowered or "embedded linux firmware engineer" in lowered or "韌體工程師" in lowered:
                if "藍牙韌體設計工程師" in lowered and prefers_firmware:
                    similarity = 0.98
                    reason = "Bluetooth 韌體背景與履歷技能高度匹配"
                elif prefers_firmware:
                    similarity = 0.93
                    reason = "韌體職稱與嵌入式技能高度匹配"
                else:
                    similarity = 0.94
                    reason = "韌體職稱與嵌入式技能高度匹配"
            elif "senior ai platform engineer" in lowered:
                similarity = 0.84
                reason = "AI 平台職類相近，但不如精準職稱"
            elif "product manager" in lowered or "pm" in lowered:
                similarity = 0.95 if prefers_pm else 0.92
                reason = "產品職類高度匹配"
            else:
                similarity = 0.12
                reason = "職類差距較大"
            scores.append(SimpleNamespace(job_index=index, similarity=similarity, reason=reason))
        return SimpleNamespace(output_parsed=SimpleNamespace(scores=scores))


class FakeOpenAIClient:
    """整合 fake embeddings 與 fake responses。"""

    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsAPI()
        self.responses = FakeResponsesAPI()
