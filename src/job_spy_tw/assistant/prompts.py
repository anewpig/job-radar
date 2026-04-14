"""Assistant helpers for prompts."""
#把「使用者問題 + 市場快照 + 履歷摘要 + 檢索到的資料 chunks」組合成一段完整的 Prompt，準備丟給 LLM 回答。
from __future__ import annotations

from typing import Literal

from ..models import AssistantResponse, MarketSnapshot, ResumeProfile
from ..resume_analysis import mask_personal_text
from ..utils import normalize_text
from .models import KnowledgeChunk


AnswerModePrompt = Literal["market_summary", "personalized_guidance", "job_comparison", "general_chat"]


def _compact_text(text: str, *, max_chars: int) -> str:
    normalized = " / ".join(line.strip() for line in text.splitlines() if line.strip())
    return normalized[:max_chars]


def _prefixed_lines(lines: list[str], prefixes: tuple[str, ...], *, limit: int) -> list[str]:
    selected = [line for line in lines if line.startswith(prefixes)]
    return selected[:limit]


def _render_chunk_context(chunk: KnowledgeChunk) -> str:
    masked = mask_personal_text(chunk.text)
    lines = [line.strip() for line in masked.splitlines() if line.strip()]

    if chunk.source_type == "job-summary":
        selected = _prefixed_lines(lines, ("職稱：", "公司：", "地點：", "薪資：", "摘要："), limit=5)
        return _compact_text("\n".join(selected or lines[:5]), max_chars=180)
    if chunk.source_type == "job-salary":
        selected = _prefixed_lines(lines, ("職稱：", "地點：", "薪資：", "更新："), limit=4)
        return _compact_text("\n".join(selected or lines[:4]), max_chars=140)
    if chunk.source_type in {"job-skills", "job-work-content"}:
        selected = _prefixed_lines(lines, ("職缺：", "公司：", "技能：", "條件：", "內容：", "工作內容："), limit=4)
        return _compact_text("\n".join(selected or lines[:4]), max_chars=160)
    if chunk.source_type.startswith("market-"):
        return _compact_text("\n".join(lines[:3]), max_chars=130)
    if chunk.source_type == "external-web":
        selected = _prefixed_lines(lines, ("標題：", "摘要：", "來源：", "查詢："), limit=4)
        return _compact_text("\n".join(selected or lines[:4]), max_chars=200)
    if chunk.source_type == "resume-summary":
        selected = _prefixed_lines(
            lines,
            ("履歷摘要：", "目標角色：", "核心技能：", "工具技能：", "領域關鍵字：", "偏好工作內容：", "履歷片段："),
            limit=4,
        )
        return _compact_text("\n".join(selected or lines[:4]), max_chars=160)
    return _compact_text(masked, max_chars=160)


def _render_conversation_context(
    conversation_context: list[AssistantResponse] | None,
    *,
    max_turns: int = 2,
) -> str:
    if not conversation_context:
        return ""

    rendered_turns: list[str] = []
    for turn in conversation_context[:max_turns]:
        question = turn.question.strip()
        if not question:
            continue
        answer_parts: list[str] = []
        if turn.summary.strip():
            answer_parts.append(f"摘要：{mask_personal_text(turn.summary.strip())}")
        if turn.key_points:
            points = "；".join(mask_personal_text(point.strip()) for point in turn.key_points[:1] if point.strip())
            if points:
                answer_parts.append(f"重點：{points}")
        if not answer_parts and turn.answer.strip():
            answer_parts.append(f"回答：{_compact_text(mask_personal_text(turn.answer), max_chars=90)}")
        if not answer_parts:
            continue
        rendered_turns.append(
            f"- Q：{mask_personal_text(question)}\n  " + "\n  ".join(answer_parts)
        )

    if not rendered_turns:
        return ""
    return "最近問答上下文：\n" + "\n".join(rendered_turns)


def _build_answer_mode_block(answer_mode: AnswerModePrompt) -> str:
    if answer_mode == "market_summary":
        return (
            "回答模式：市場摘要\n"
            "- 以整體市場分布、常見技能、薪資樣態與工作內容為主\n"
            "- 不要把市場結論過度套用成個人建議\n"
            "- `summary` 必須先講目前最值得注意的市場結論\n"
            "- `key_points` 請優先用 3-4 個標記段落，每點以 `市場分布：`、`核心技能：`、`薪資樣態：`、`工作內容：`、`趨勢提醒：` 其中之一開頭\n"
            "- `next_step` 必須是使用者可直接採取的動作，例如先看哪類職缺、先比較哪個條件、或再補哪個篩選方向\n"
        )
    if answer_mode == "personalized_guidance":
        return (
            "回答模式：個人化建議\n"
            "- 優先結合履歷背景與市場需求，指出缺口、優先順序與下一步\n"
            "- 若證據不足，明確說明哪些建議仍需要更多背景才成立\n"
            "- `summary` 必須先講最值得先做的方向\n"
            "- `key_points` 請優先用 3-4 個標記段落，每點以 `市場需求：`、`目前缺口：`、`優先補強：`、`投遞建議：` 其中之一開頭\n"
            "- `next_step` 必須是短期可執行動作，例如先補哪個技能、先投哪類職缺、或先改哪段履歷\n"
        )
    if answer_mode == "job_comparison":
        return (
            "回答模式：職缺比較\n"
            "- 優先比較角色差異、技能要求、薪資揭露、工作內容與風險\n"
            "- 若問題裡沒有足夠的比較對象，明確指出目前只能做有限比較\n"
            "- `summary` 必須先點出最主要差異或選擇方向\n"
            "- `key_points` 請優先用 3-4 個比較維度，每點以 `技能：`、`工作內容：`、`薪資：`、`適合對象：`、`風險：` 其中之一開頭\n"
            "- `next_step` 必須給出使用者下一步，例如先補哪類技能、先投哪個方向、或需要再補哪些比較條件\n"
        )
    return (
        "回答模式：一般對話\n"
        "- 這題與求職市場不直接相關，可用一般知識、推理與表達能力回答\n"
        "- 不要為了迎合系統背景，硬把話題拉回求職、履歷、薪資或職缺\n"
        "- 若內容可自然延伸到學習、工作方法或 AI 實務，可補一個實用角度，但不是必須\n"
        "- `summary` 必須先給出最直接的回覆或觀點\n"
        "- `key_points` 以 2-4 點整理重點，格式不必拘泥於市場標籤\n"
        "- `next_step` 可給使用者一個自然的後續提問、練習方向或延伸思考\n"
    )


def _build_prompt_variant_block(prompt_variant: str) -> str:
    normalized = str(prompt_variant or "").strip().lower()
    if normalized == "compact_qa":
        return (
            "Prompt 變體：compact_qa\n"
            "- 回覆長度收斂成 1-2 段自然段落\n"
            "- `key_points` 最多 2 點，避免重複鋪陳\n"
            "- 若檢索證據已經足夠，優先直接回答，不要寫太多背景\n"
        )
    return (
        "Prompt 變體：control\n"
        "- 使用標準正式 QA 版回答策略\n"
        "- 在精簡與完整之間維持平衡\n"
    )


def _build_question_focus_block(question: str, answer_mode: AnswerModePrompt) -> str:
    normalized = normalize_text(question)

    if answer_mode == "general_chat":
        return (
            "這題與求職市場不直接相關\n"
            "- 可以用一般知識、推理或較自然的表達方式回答\n"
            "- 不要硬把內容拉回職缺、薪資、履歷或市場快照\n"
            "- 若問題涉及技術概念，可優先回答概念、差異、常見用法與實作提醒\n"
        )

    if answer_mode == "market_summary":
        if any(token in normalized for token in ("工作內容", "內容重點", "做什麼", "負責什麼")):
            return (
                "這題聚焦：工作內容重點\n"
                "- 只整理常見職責、任務、流程與產出\n"
                "- 優先使用動作型描述，例如開發、維護、整合、測試、優化、協作\n"
                "- 不要把技能名稱清單、地點或薪資描述當成主要工作內容\n"
            )
        if any(token in normalized for token in ("技能", "能力")):
            return (
                "這題聚焦：市場技能重點\n"
                "- 只回答最值得優先看的技能、出現頻率與重要度\n"
                "- 不要把技能題答成薪資題或地點題\n"
                "- 若薪資資料不足，只能放在 limitations，不要在 next_step 暗示可直接補出快照外資料\n"
            )

    if answer_mode == "personalized_guidance":
        return (
            "這題聚焦：市場需求與個人缺口對照\n"
            "- `市場需求：` 只能寫市場證據，不要混入個人建議\n"
            "- `目前缺口：` 只能寫履歷摘要裡尚未明確出現、且市場反覆要求的能力\n"
            "- 不要把市場常見技能直接等同於使用者缺口\n"
            "- 若履歷資訊不足，應在 limitations 明確說明，而不是假設使用者一定缺少某項能力\n"
        )

    return ""


def _build_response_style_block(question: str, answer_mode: AnswerModePrompt) -> str:
    if answer_mode == "general_chat":
        return (
            "回答風格：自然 QA\n"
            "- 先直接回答，再補 2-3 個重點\n"
            "- 可以自然一點，但不要寫成知識科普、教科書或長篇背景整理\n"
            "- 若使用者只是想快速得到答案，就停在夠用的深度，不要主動展開太多延伸知識\n"
            "- 除非使用者要求深入，否則避免長篇原理說明\n"
        )
    return (
        "回答風格：正式 QA\n"
        "- 這是工作相關問題，請用正式、專業的口吻回答\n"
        "- 先直接回答，再補 2-4 點重點\n"
        "- 回答要像 QA，不要寫成教學文章、百科整理或過長的知識科普\n"
        "- 除非使用者明確要求細講，否則不要展開太多背景歷史或原理\n"
    )


def build_answer_prompt( #輸出一個字串餵給 LLM 的完整 prompt
    *, #表後面的參數都必須用關鍵字方式傳入
    question: str,
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
    conversation_context: list[AssistantResponse] | None,
    answer_mode: AnswerModePrompt,
    chunks: list[KnowledgeChunk],
    prompt_variant: str = "control",
) -> str:
    if answer_mode == "general_chat":
        resume_block = "目前沒有額外個人背景，若問題不需要，直接用一般知識回答即可。"
        if resume_profile is not None:
            resume_block = (
                "可選個人背景（只有在問題真的相關時才使用）：\n"
                f"履歷摘要：{mask_personal_text(resume_profile.summary)}\n"
                f"目標角色：{', '.join(resume_profile.target_roles)}\n"
                f"核心技能：{', '.join(resume_profile.core_skills)}\n"
                f"工具技能：{', '.join(resume_profile.tool_skills)}\n"
            )
    else:
        resume_block = ( #防 hallucination
            "目前沒有履歷或個人求職資料。\n"
            "請不要假設使用者要應徵哪一種職缺、年資或背景。\n"
            "如果問題需要個人化建議，應先請使用者提供：目標職缺、年資、地點偏好、目前技能、想補強方向。"
        )
        if resume_profile is not None:
            resume_block = ( #如果有履歷資料，就改成履歷摘要版
                f"履歷摘要：{mask_personal_text(resume_profile.summary)}\n"
                f"目標角色：{', '.join(resume_profile.target_roles)}\n"
                f"核心技能：{', '.join(resume_profile.core_skills)}\n"
                f"工具技能：{', '.join(resume_profile.tool_skills)}\n"
            )
    context_blocks = [] #先準備一個空 list，用來收集每一個檢索回來的 chunk
    for idx, chunk in enumerate(chunks, start=1): #把每個 chunk 轉成 prompt 文字
        context_blocks.append(
            f"[{idx}] {chunk.label}\n來源類型：{chunk.source_type}\n內容：{_render_chunk_context(chunk)}\n連結：{chunk.url or 'N/A'}"
        )
    conversation_block = _render_conversation_context(conversation_context)
    answer_mode_block = _build_answer_mode_block(answer_mode)
    prompt_variant_block = _build_prompt_variant_block(prompt_variant)
    question_focus_block = _build_question_focus_block(question, answer_mode)
    response_style_block = _build_response_style_block(question, answer_mode)
    if answer_mode == "general_chat":
        prompt_header = (
            "你是求職工作台內的 AI 助理。這一題與求職市場不直接相關，可以使用一般知識、推理與表達能力回答。\n"
            "回答要求：\n"
            "- 使用繁體中文\n"
            "- 直接回答使用者問題，整體寫成自然段落式 QA\n"
            "- 不要為了迎合系統背景，硬把內容拉回職缺、履歷、薪資或市場快照\n"
            "- 若資訊不確定，請直接說明不確定之處\n"
            "- 仍請精簡回答，不要用「重點 / 限制 / 下一步」這種框架標題\n"
            "- 整體回覆請偏向問答格式，不要寫成知識文章\n"
            "- 嚴格輸出 JSON，不要輸出 JSON 以外的文字\n"
            '- JSON schema: {"answer": "...", "summary": "...", "key_points": ["..."], "limitations": ["..."], "next_step": "..."}\n'
            "- `answer` 是主要回答內容，請寫成 1-3 段自然段落，不要自行加小標\n"
            "- `summary` 供內部整理用，請用 1 句概括；`key_points` / `limitations` / `next_step` 可精簡或留空\n\n"
            f"{answer_mode_block}\n"
            f"{prompt_variant_block}\n"
            f"{response_style_block}\n"
            f"{resume_block}\n"
            "若下面附有檢索內容，可把它當成當前系統脈絡的補充語境；若幫助不大，就不要勉強引用，也不要硬把回答拉回求職。\n"
            "- 若來源類型是 `external-web`，代表這是詢問當下取得的外部搜尋摘要，只能根據摘要回覆，不要假裝已完整閱讀原文。\n"
        )
    else:
        prompt_header = (
            "你是台灣求職市場分析助理。請只根據提供的檢索內容回答，不要捏造資料。\n"
            "回答要求：\n"
            "- 使用繁體中文\n"
            "- 直接回答使用者問題，整體寫成自然段落式 QA\n"
            "- 沒有履歷或個人資料時，只能從整體市場角度回答，不能假設使用者的目標職缺\n"
            "- 若有薪資，請明確說資料中的薪資樣態與限制\n"
            "- 若資訊不足，請直接說明\n"
            "- 請精簡回答，不要用「重點 / 限制 / 下一步」這種框架標題\n"
            "- 整體回覆請偏向正式 QA，不要寫成長篇知識整理\n"
            "- 嚴格輸出 JSON，不要輸出 JSON 以外的文字\n"
            '- JSON schema: {"answer": "...", "summary": "...", "key_points": ["..."], "limitations": ["..."], "next_step": "..."}\n'
            "- `answer` 是主要回答內容，請寫成 1-3 段自然段落，不要自行加小標\n"
            "- `summary` 供內部整理用，請用 1 句概括；`key_points` / `limitations` / `next_step` 可精簡或留空\n\n"
            f"{answer_mode_block}\n"
            f"{prompt_variant_block}\n"
            f"{response_style_block}\n"
            f"市場快照時間：{snapshot.generated_at}\n"
            f"{resume_block}\n"
        )
    if question_focus_block:
        prompt_header += f"{question_focus_block}\n"
    if conversation_block:
        prompt_header += f"{conversation_block}\n"
    prompt_header += f"使用者問題：{question}\n\n"

    if answer_mode == "general_chat" and not context_blocks:
        return prompt_header + "目前沒有可用檢索內容，請直接回答使用者問題，並避免假裝引用市場資料。"

    return ( #最後 return 整個 prompt
        prompt_header
        + "檢索內容：\n"
        + "\n\n".join(context_blocks)
    )
