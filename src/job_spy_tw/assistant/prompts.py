"""Assistant helpers for prompts."""
#把「使用者問題 + 市場快照 + 履歷摘要 + 檢索到的資料 chunks」組合成一段完整的 Prompt，準備丟給 LLM 回答。
from __future__ import annotations

from ..models import MarketSnapshot, ResumeProfile
from ..resume_analysis import mask_personal_text
from .models import KnowledgeChunk


def build_answer_prompt( #輸出一個字串餵給 LLM 的完整 prompt
    *, #表後面的參數都必須用關鍵字方式傳入
    question: str,
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
    chunks: list[KnowledgeChunk],
) -> str:
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
            f"[{idx}] {chunk.label}\n來源類型：{chunk.source_type}\n內容：{mask_personal_text(chunk.text)}\n連結：{chunk.url or 'N/A'}"
        )

    return ( #最後 return 整個 prompt
        "你是台灣求職市場分析助理。請只根據提供的檢索內容回答，不要捏造資料。\n"
        "回答要求：\n"
        "- 使用繁體中文\n"
        "- 先給結論，再給 3-5 點重點\n"
        "- 沒有履歷或個人資料時，只能從整體市場角度回答，不能假設使用者的目標職缺\n"
        "- 若有薪資，請明確說資料中的薪資樣態與限制\n"
        "- 若資訊不足，請直接說明\n"
        "- 嚴格輸出 JSON，不要輸出 JSON 以外的文字\n"
        '- JSON schema: {"summary": "...", "key_points": ["..."], "limitations": ["..."], "next_step": "..."}\n'
        "- `summary` 必填；`key_points` 3-5 點；沒有明確限制時 `limitations` 可為空陣列\n\n"
        f"市場快照時間：{snapshot.generated_at}\n"
        f"{resume_block}\n"
        f"使用者問題：{question}\n\n"
        "檢索內容：\n"
        + "\n\n".join(context_blocks)
    )
