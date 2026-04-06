"""Resume-analysis helpers for schemas."""

from __future__ import annotations

try:
    from openai import OpenAI
except Exception:  # noqa: BLE001
    OpenAI = None

try:
    from pydantic import BaseModel, Field
except Exception:  # noqa: BLE001
    BaseModel = None
    Field = None


if BaseModel is not None and Field is not None:
    class LLMResumeProfile(BaseModel):
        summary: str = Field(default="")
        target_roles: list[str] = Field(default_factory=list)
        core_skills: list[str] = Field(default_factory=list)
        tool_skills: list[str] = Field(default_factory=list)
        domain_keywords: list[str] = Field(default_factory=list)
        preferred_tasks: list[str] = Field(default_factory=list)
        generated_prompts: list[str] = Field(default_factory=list)
        match_keywords: list[str] = Field(default_factory=list)


    class TitleSimilarityItem(BaseModel):
        job_index: int = Field(default=0)
        similarity: float = Field(default=0.0)
        reason: str = Field(default="")


    class TitleSimilarityBatch(BaseModel):
        scores: list[TitleSimilarityItem] = Field(default_factory=list)
else:
    LLMResumeProfile = None
    TitleSimilarityItem = None
    TitleSimilarityBatch = None
