from __future__ import annotations

from ..models import MarketSnapshot, ResumeProfile
from ..resume_analysis import mask_personal_text
from .models import KnowledgeChunk


def build_answer_prompt(
    *,
    question: str,
    snapshot: MarketSnapshot,
    resume_profile: ResumeProfile | None,
    chunks: list[KnowledgeChunk],
) -> str:
    resume_block = (
        "目前沒有履歷或個人求職資料。\n"
        "請不要假設使用者要應徵哪一種職缺、年資或背景。\n"
        "如果問題需要個人化建議，應先請使用者提供：目標職缺、年資、地點偏好、目前技能、想補強方向。"
    )
    if resume_profile is not None:
        resume_block = (
            f"履歷摘要：{mask_personal_text(resume_profile.summary)}\n"
            f"目標角色：{', '.join(resume_profile.target_roles)}\n"
            f"核心技能：{', '.join(resume_profile.core_skills)}\n"
            f"工具技能：{', '.join(resume_profile.tool_skills)}\n"
        )
    context_blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            f"[{idx}] {chunk.label}\n來源類型：{chunk.source_type}\n內容：{mask_personal_text(chunk.text)}\n連結：{chunk.url or 'N/A'}"
        )

    return (
        "你是台灣求職市場分析助理。請只根據提供的檢索內容回答，不要捏造資料。\n"
        "回答要求：\n"
        "- 使用繁體中文\n"
        "- 先給結論，再給 3-5 點重點\n"
        "- 沒有履歷或個人資料時，只能從整體市場角度回答，不能假設使用者的目標職缺\n"
        "- 若有薪資，請明確說資料中的薪資樣態與限制\n"
        "- 若資訊不足，請直接說明\n"
        "- 最後附上「參考來源」列出使用到的 [編號]\n\n"
        f"市場快照時間：{snapshot.generated_at}\n"
        f"{resume_block}\n"
        f"使用者問題：{question}\n\n"
        "檢索內容：\n"
        + "\n\n".join(context_blocks)
    )
