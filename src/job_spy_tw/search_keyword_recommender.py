from __future__ import annotations

from dataclasses import dataclass

from .utils import normalize_text, unique_preserving_order


@dataclass(frozen=True, slots=True)
class KeywordTemplate:
    aliases: tuple[str, ...]
    keywords: tuple[str, ...]


KEYWORD_TEMPLATES: tuple[KeywordTemplate, ...] = (
    KeywordTemplate(
        aliases=("ai", "llm", "rag", "machine learning", "人工智慧", "生成式", "資料科學"),
        keywords=("LLM", "RAG", "Prompt Engineering", "AI Agent", "Python", "模型部署", "MLOps"),
    ),
    KeywordTemplate(
        aliases=("軟體", "backend", "frontend", "full stack", "software", "程式"),
        keywords=("API", "系統設計", "資料庫", "Git", "Docker", "測試", "敏捷開發"),
    ),
    KeywordTemplate(
        aliases=("pm", "product", "project manager", "產品", "專案"),
        keywords=("Roadmap", "需求分析", "PRD", "跨部門協作", "利害關係人溝通", "數據分析"),
    ),
    KeywordTemplate(
        aliases=("應用工程師", "fae", "solution", "售前", "導入"),
        keywords=("客戶導入", "需求訪談", "技術簡報", "PoC", "系統整合", "客戶溝通"),
    ),
    KeywordTemplate(
        aliases=("行銷", "marketing", "growth", "brand", "社群"),
        keywords=("內容行銷", "廣告投放", "SEO", "GA4", "社群經營", "成效分析"),
    ),
    KeywordTemplate(
        aliases=("業務", "sales", "bd", "business development"),
        keywords=("陌生開發", "客戶關係", "提案簡報", "業績目標", "商務談判", "CRM"),
    ),
    KeywordTemplate(
        aliases=("設計", "designer", "ui", "ux", "平面", "視覺"),
        keywords=("Figma", "使用者研究", "Wireframe", "Prototype", "視覺設計", "設計系統"),
    ),
    KeywordTemplate(
        aliases=("會計", "財務", "accounting", "finance"),
        keywords=("帳務處理", "報表分析", "稅務申報", "成本分析", "ERP", "Excel"),
    ),
    KeywordTemplate(
        aliases=("人資", "hr", "recruit", "招募"),
        keywords=("人才招募", "面試安排", "雇主品牌", "員工關係", "勞基法", "HRIS"),
    ),
    KeywordTemplate(
        aliases=("行政", "營運", "operations", "客服", "customer service"),
        keywords=("流程管理", "文件處理", "溝通協調", "客訴處理", "排程管理", "數據整理"),
    ),
    KeywordTemplate(
        aliases=("護理", "nurse", "醫療", "藥師", "治療師"),
        keywords=("病患照護", "醫囑執行", "衛教", "急重症", "醫療文書", "證照"),
    ),
    KeywordTemplate(
        aliases=("藥師", "pharmacist"),
        keywords=("Pharmacist", "門市藥師", "臨床藥師", "藥品調劑", "用藥諮詢", "衛教", "藥局"),
    ),
    KeywordTemplate(
        aliases=("半導體", "製程", "設備", "機構", "硬體", "electrical", "mechanical"),
        keywords=("SOP", "良率分析", "設備維護", "電路", "CAD", "FAE", "問題分析"),
    ),
    KeywordTemplate(
        aliases=("鋼琴", "piano"),
        keywords=("古典鋼琴", "流行鋼琴", "Yamaha", "ABRSM", "檢定", "伴奏", "視奏"),
    ),
    KeywordTemplate(
        aliases=("老師", "教師", "講師", "tutor", "instructor"),
        keywords=("課程設計", "教學熱忱", "班級經營", "學生溝通", "家長溝通", "教案"),
    ),
    KeywordTemplate(
        aliases=("英文", "english", "美語"),
        keywords=("英檢", "多益", "口說", "文法", "教學互動", "兒童美語"),
    ),
    KeywordTemplate(
        aliases=("幼教", "保母", "托育", "幼兒"),
        keywords=("幼兒發展", "親師溝通", "活動設計", "照護安全", "教保員", "觀察紀錄"),
    ),
)


GENERIC_SUFFIX_KEYWORDS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("工程師", "engineer"), ("問題分析", "需求分析", "跨部門協作", "專案執行")),
    (("經理", "manager"), ("團隊協作", "流程改善", "指標管理", "溝通協調")),
    (("專員", "specialist"), ("執行力", "細節管理", "溝通協調", "報表整理")),
    (("顧問", "consultant"), ("需求訪談", "提案簡報", "顧問式溝通", "專案管理")),
    (("老師", "教師", "講師", "tutor"), ("教學互動", "表達能力", "親和力", "耐心")),
)


class RoleKeywordRecommender:
    def suggest_keywords(self, role_name: str, limit: int = 8) -> list[str]:
        role_text = normalize_text(role_name).strip()
        if not role_text:
            return []

        lowered = role_text.lower()
        suggestions: list[str] = []
        for template in KEYWORD_TEMPLATES:
            if any(alias.lower() in lowered for alias in template.aliases):
                suggestions.extend(template.keywords)

        if not suggestions:
            suggestions.extend(self._generic_keywords(role_text))
        else:
            suggestions.extend(self._generic_keywords(role_text))

        return unique_preserving_order(keyword for keyword in suggestions if keyword)[:limit]

    def suggest_keywords_text(self, role_name: str, limit: int = 8) -> str:
        return ", ".join(self.suggest_keywords(role_name, limit=limit))

    def _generic_keywords(self, role_text: str) -> list[str]:
        lowered = role_text.lower()
        generic: list[str] = []
        for aliases, keywords in GENERIC_SUFFIX_KEYWORDS:
            if any(alias.lower() in lowered for alias in aliases):
                generic.extend(keywords)
        if generic:
            return generic
        return ["溝通協調", "執行力", "問題分析", "相關經驗"]


def normalize_search_role_rows(rows: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for index, row in enumerate(rows, start=1):
        priority_raw = row.get("priority", index)
        try:
            priority = int(priority_raw)
        except (TypeError, ValueError):
            priority = index
        enabled = bool(row.get("enabled", True))
        normalized.append(
            {
                "enabled": enabled,
                "priority": max(1, priority),
                "role": normalize_text(str(row.get("role", ""))).strip(),
                "keywords": normalize_text(str(row.get("keywords", ""))).strip(" ,"),
            }
        )
    return normalized


def autofill_role_keyword_rows(
    rows: list[dict],
    previous_rows: list[dict],
    recommender: RoleKeywordRecommender,
) -> tuple[list[dict], bool]:
    normalized_rows = normalize_search_role_rows(rows)
    previous_normalized = normalize_search_role_rows(previous_rows)
    changed = False
    updated_rows: list[dict] = []

    for index, row in enumerate(normalized_rows):
        previous_row = previous_normalized[index] if index < len(previous_normalized) else {}
        role = row["role"]
        keywords = row["keywords"]
        previous_role = str(previous_row.get("role", "")).strip()
        previous_keywords = str(previous_row.get("keywords", "")).strip()
        previous_auto_keywords = recommender.suggest_keywords_text(previous_role)
        current_auto_keywords = recommender.suggest_keywords_text(role)

        should_autofill = bool(role and current_auto_keywords) and (
            not keywords
            or keywords == current_auto_keywords
            or (
                role != previous_role
                and (
                    not previous_keywords
                    or keywords == previous_keywords
                    or previous_keywords == previous_auto_keywords
                )
            )
        )

        if should_autofill and keywords != current_auto_keywords:
            row["keywords"] = current_auto_keywords
            changed = True

        updated_rows.append(row)

    return updated_rows, changed
